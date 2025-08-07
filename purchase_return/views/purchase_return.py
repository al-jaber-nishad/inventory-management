from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.template.loader import render_to_string
from django.http import JsonResponse, HttpResponse
from django.core.paginator import Paginator
from django.forms import inlineformset_factory
from django.contrib.auth.decorators import login_required
import weasyprint
from django.conf import settings
import os

from purchase_return.models import PurchaseReturn, PurchaseReturnItem
from purchase_return.forms.purchase_return import PurchaseReturnForm, PurchaseReturnItemForm


class OwnerFilterMixin:
    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        if not getattr(user, 'role', None) or getattr(user.role, 'name', '').upper() != 'ADMIN':
            qs = qs.filter(created_by=user)
        return qs


class PurchaseReturnListView(LoginRequiredMixin, OwnerFilterMixin, ListView):
    model = PurchaseReturn
    template_name = 'purchase_return/list.html'
    context_object_name = 'purchase_return_list'

    def get_queryset(self):
        qs = super().get_queryset().select_related('supplier', 'original_purchase')
        search = self.request.GET.get('search_input', '').strip()
        status = self.request.GET.get('status', '').strip()
        
        if search:
            qs = qs.filter(
                Q(return_number__icontains=search) | 
                Q(supplier__name__icontains=search) |
                Q(original_purchase__invoice_number__icontains=search)
            )
        if status:
            qs = qs.filter(status=status)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search'] = self.request.GET.get('search', '')
        context['selected_status'] = self.request.GET.get('status', '')
        context['status_choices'] = PurchaseReturn.Status.choices

        queryset = context.get('purchase_return_list')
        paginator = Paginator(queryset, 50)
        page_number = self.request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        context['purchase_return_list'] = page_obj
        return context

    def render_to_response(self, context, **response_kwargs):
        if self.request.headers.get('x-requested-with') == 'XMLHttpRequest':
            html = render_to_string('purchase_return/_table_fragment.html', context=context, request=self.request)
            return JsonResponse({'html': html})
        return super().render_to_response(context, **response_kwargs)


class PurchaseReturnDetailView(LoginRequiredMixin, OwnerFilterMixin, DetailView):
    model = PurchaseReturn
    template_name = 'purchase_return/form.html'
    context_object_name = 'purchase_return'


class PurchaseReturnCreateView(LoginRequiredMixin, CreateView):
    model = PurchaseReturn
    form_class = PurchaseReturnForm
    template_name = 'purchase_return/form.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        PurchaseReturnItemFormSet = inlineformset_factory(
            PurchaseReturn, PurchaseReturnItem, 
            form=PurchaseReturnItemForm,
            extra=1, 
            can_delete=True
        )

        instance = self.object
        if instance and instance.return_date:
            context['return_date'] = instance.return_date.strftime('%d-%m-%Y')
        else:
            context['return_date'] = ''
        
        if self.request.POST:
            context['item_formset'] = PurchaseReturnItemFormSet(self.request.POST, instance=self.object)
        else:
            context['item_formset'] = PurchaseReturnItemFormSet(instance=self.object)
        
        return context

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    def form_valid(self, form):
        context = self.get_context_data()
        item_formset = context['item_formset']
        
        if form.is_valid() and item_formset.is_valid():
            purchase_return = form.save(commit=False)
            purchase_return.created_by = self.request.user
            purchase_return.save()
            
            item_formset.instance = purchase_return
            item_formset.save()
            
            # Calculate totals
            self.calculate_return_totals(purchase_return)
            
            messages.success(self.request, "Purchase return created successfully.")
            return redirect('purchase_return_list')
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

    def calculate_return_totals(self, purchase_return):
        items = purchase_return.items.all()
        subtotal = sum(item.total_price for item in items)
        
        purchase_return.subtotal = subtotal
        purchase_return.total = subtotal - purchase_return.discount + purchase_return.tax
        purchase_return.save()


class PurchaseReturnUpdateView(LoginRequiredMixin, UpdateView):
    model = PurchaseReturn
    form_class = PurchaseReturnForm
    template_name = 'purchase_return/form.html'
    pk_url_kwarg = 'pk'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        PurchaseReturnItemFormSet = inlineformset_factory(
            PurchaseReturn, PurchaseReturnItem, 
            form=PurchaseReturnItemForm,
            extra=0, 
            can_delete=True
        )

        instance = self.object
        if instance and instance.return_date:
            context['return_date'] = instance.return_date.strftime('%d-%m-%Y')
        else:
            context['return_date'] = ''
        
        if self.request.POST:
            context['item_formset'] = PurchaseReturnItemFormSet(self.request.POST, instance=self.object)
        else:
            context['item_formset'] = PurchaseReturnItemFormSet(instance=self.object)
        
        return context

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    def form_valid(self, form):
        context = self.get_context_data()
        item_formset = context['item_formset']
        
        if form.is_valid() and item_formset.is_valid():
            purchase_return = form.save(commit=False)
            purchase_return.updated_by = self.request.user
            purchase_return.save()
            
            item_formset.instance = purchase_return
            item_formset.save()
            
            # Calculate totals
            self.calculate_return_totals(purchase_return)
            
            messages.success(self.request, "Purchase return updated successfully.")
            return redirect('purchase_return_list')
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

    def calculate_return_totals(self, purchase_return):
        items = purchase_return.items.all()
        subtotal = sum(item.total_price for item in items)
        
        purchase_return.subtotal = subtotal
        purchase_return.total = subtotal - purchase_return.discount + purchase_return.tax
        purchase_return.save()


class PurchaseReturnDeleteView(LoginRequiredMixin, DeleteView):
    model = PurchaseReturn
    success_url = reverse_lazy('purchase_return_list')
    pk_url_kwarg = 'pk'

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.delete()
        messages.success(self.request, "Purchase return deleted successfully.")
        return redirect(self.success_url)


@login_required
def purchase_return_invoice_pdf(request, pk):
    """Generate and download PDF invoice for a purchase return"""
    purchase_return = get_object_or_404(PurchaseReturn, pk=pk)
    
    # Check permissions - only allow if user owns the return or is admin
    user = request.user
    if not getattr(user, 'role', None) or getattr(user.role, 'name', '').upper() != 'ADMIN':
        if purchase_return.created_by != user:
            messages.error(request, "You don't have permission to access this purchase return.")
            return redirect('purchase_return_list')
    
    # Render the template to HTML
    html_string = render_to_string('purchase_return/invoice_pdf.html', {
        'purchase_return': purchase_return,
    }, request=request)
    
    # Generate PDF
    html = weasyprint.HTML(string=html_string, base_url=request.build_absolute_uri())
    pdf = html.write_pdf()
    
    # Create response
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="purchase_return_{purchase_return.return_number}.pdf"'
    
    return response