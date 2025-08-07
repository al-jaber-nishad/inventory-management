from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.template.loader import render_to_string
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.forms import inlineformset_factory

from purchase.models import Purchase, PurchaseItem
from purchase.forms.purchase import PurchaseForm, PurchaseItemForm


class OwnerFilterMixin:
    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        if not getattr(user, 'role', None) or getattr(user.role, 'name', '').upper() != 'ADMIN':
            qs = qs.filter(created_by=user)
        return qs


class PurchaseListView(LoginRequiredMixin, OwnerFilterMixin, ListView):
    model = Purchase
    template_name = 'purchase/list.html'
    context_object_name = 'purchase_list'

    def get_queryset(self):
        qs = super().get_queryset().select_related('supplier')
        search = self.request.GET.get('search_input', '').strip()
        status = self.request.GET.get('status', '').strip()
        
        if search:
            qs = qs.filter(
                Q(invoice_number__icontains=search) | 
                Q(supplier__name__icontains=search)
            )
        if status:
            qs = qs.filter(status=status)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search'] = self.request.GET.get('search', '')
        context['selected_status'] = self.request.GET.get('status', '')
        context['status_choices'] = Purchase.Status.choices

        queryset = context.get('purchase_list')
        paginator = Paginator(queryset, 50)
        page_number = self.request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        context['purchase_list'] = page_obj
        return context

    def render_to_response(self, context, **response_kwargs):
        if self.request.headers.get('x-requested-with') == 'XMLHttpRequest':
            html = render_to_string('purchase/_table_fragment.html', context=context, request=self.request)
            return JsonResponse({'html': html})
        return super().render_to_response(context, **response_kwargs)


class PurchaseDetailView(LoginRequiredMixin, OwnerFilterMixin, DetailView):
    model = Purchase
    template_name = 'purchase/form.html'
    context_object_name = 'purchase'


class PurchaseCreateView(LoginRequiredMixin, CreateView):
    model = Purchase
    form_class = PurchaseForm
    template_name = 'purchase/form.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        PurchaseItemFormSet = inlineformset_factory(
            Purchase, PurchaseItem, 
            form=PurchaseItemForm,
            extra=1, 
            can_delete=True
        )

        instance = self.object
        if instance and instance.purchase_date:
            context['purchase_date'] = instance.purchase_date.strftime('%d-%m-%Y')
        else:
            context['purchase_date'] = ''

        if instance and instance.due_date:
            context['due_date'] = instance.due_date.strftime('%d-%m-%Y')
        else:
            context['due_date'] = ''
        
        if self.request.POST:
            context['item_formset'] = PurchaseItemFormSet(self.request.POST, instance=self.object)
        else:
            context['item_formset'] = PurchaseItemFormSet(instance=self.object)
        
        return context

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    def form_valid(self, form):
        context = self.get_context_data()
        item_formset = context['item_formset']
        
        if form.is_valid() and item_formset.is_valid():
            purchase = form.save(commit=False)
            purchase.created_by = self.request.user
            purchase.save()
            
            item_formset.instance = purchase
            item_formset.save()
            
            # Calculate totals
            self.calculate_purchase_totals(purchase)
            
            messages.success(self.request, "Purchase created successfully.")
            return redirect('purchase_list')
        else:
            return self.form_invalid(form)

    def form_invalid(self, form):
        context = self.get_context_data(form=form)
        errors = []
        field_errors = {f: e for f, e in form.errors.items() if f != '__all__'}
        non_field = form.non_field_errors()
        errors.extend(non_field)
        for err_list in field_errors.values():
            errors.extend(err_list)
        
        # Add formset errors
        if 'item_formset' in context:
            for form_errors in context['item_formset'].errors:
                for field, field_errors in form_errors.items():
                    errors.extend(field_errors)
        
        context.update({'messages': errors, 'is_error': True})
        return render(self.request, self.template_name, context, status=400)

    def calculate_purchase_totals(self, purchase):
        items = purchase.items.all()
        subtotal = sum(item.total_price for item in items)
        
        purchase.subtotal = subtotal
        purchase.total = subtotal - purchase.discount + purchase.tax
        purchase.save()


class PurchaseUpdateView(LoginRequiredMixin, UpdateView):
    model = Purchase
    form_class = PurchaseForm
    template_name = 'purchase/form.html'
    pk_url_kwarg = 'pk'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        PurchaseItemFormSet = inlineformset_factory(
            Purchase, PurchaseItem, 
            form=PurchaseItemForm,
            extra=0, 
            can_delete=True
        )

        instance = self.object
        if instance and instance.purchase_date:
            context['purchase_date'] = instance.purchase_date.strftime('%d-%m-%Y')
        else:
            context['purchase_date'] = ''

        if instance and instance.due_date:
            context['due_date'] = instance.due_date.strftime('%d-%m-%Y')
        else:
            context['due_date'] = ''
        
        if self.request.POST:
            context['item_formset'] = PurchaseItemFormSet(self.request.POST, instance=self.object)
        else:
            context['item_formset'] = PurchaseItemFormSet(instance=self.object)
        
        return context

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    def form_valid(self, form):
        context = self.get_context_data()
        item_formset = context['item_formset']
        
        if form.is_valid() and item_formset.is_valid():
            purchase = form.save(commit=False)
            purchase.updated_by = self.request.user
            purchase.save()
            
            item_formset.instance = purchase
            item_formset.save()
            
            # Calculate totals
            self.calculate_purchase_totals(purchase)
            
            messages.success(self.request, "Purchase updated successfully.")
            return redirect('purchase_list')
        else:
            return self.form_invalid(form)

    def form_invalid(self, form):
        context = self.get_context_data(form=form)
        errors = []
        field_errors = {f: e for f, e in form.errors.items() if f != '__all__'}
        non_field = form.non_field_errors()
        errors.extend(non_field)
        for err_list in field_errors.values():
            errors.extend(err_list)
        
        # Add formset errors
        if 'item_formset' in context:
            for form_errors in context['item_formset'].errors:
                for field, field_errors in form_errors.items():
                    errors.extend(field_errors)
        
        context.update({'messages': errors, 'is_error': True})
        return render(self.request, self.template_name, context, status=400)

    def calculate_purchase_totals(self, purchase):
        items = purchase.items.all()
        subtotal = sum(item.total_price for item in items)
        
        purchase.subtotal = subtotal
        purchase.total = subtotal - purchase.discount + purchase.tax
        purchase.save()


class PurchaseDeleteView(LoginRequiredMixin, DeleteView):
    model = Purchase
    success_url = reverse_lazy('purchase_list')
    pk_url_kwarg = 'pk'

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.delete()
        messages.success(self.request, "Purchase deleted successfully.")
        return redirect(self.success_url)