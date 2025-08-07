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

from sales_return.models import SaleReturn, SaleReturnItem
from sales_return.forms.sales_return import SaleReturnForm, SaleReturnItemForm


class OwnerFilterMixin:
    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        if not getattr(user, 'role', None) or getattr(user.role, 'name', '').upper() != 'ADMIN':
            qs = qs.filter(created_by=user)
        return qs


class SaleReturnListView(LoginRequiredMixin, OwnerFilterMixin, ListView):
    model = SaleReturn
    template_name = 'sales_return/list.html'
    context_object_name = 'sale_return_list'

    def get_queryset(self):
        qs = super().get_queryset().select_related('customer', 'original_sale')
        search = self.request.GET.get('search_input', '').strip()
        status = self.request.GET.get('status', '').strip()
        
        if search:
            qs = qs.filter(
                Q(return_number__icontains=search) | 
                Q(customer__name__icontains=search) |
                Q(original_sale__invoice_number__icontains=search)
            )
        if status:
            qs = qs.filter(status=status)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search'] = self.request.GET.get('search', '')
        context['selected_status'] = self.request.GET.get('status', '')
        context['status_choices'] = SaleReturn.Status.choices

        queryset = context.get('sale_return_list')
        paginator = Paginator(queryset, 50)
        page_number = self.request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        context['sale_return_list'] = page_obj
        return context

    def render_to_response(self, context, **response_kwargs):
        if self.request.headers.get('x-requested-with') == 'XMLHttpRequest':
            html = render_to_string('sales_return/_table_fragment.html', context=context, request=self.request)
            return JsonResponse({'html': html})
        return super().render_to_response(context, **response_kwargs)


class SaleReturnDetailView(LoginRequiredMixin, OwnerFilterMixin, DetailView):
    model = SaleReturn
    template_name = 'sales_return/form.html'
    context_object_name = 'sale_return'


class SaleReturnCreateView(LoginRequiredMixin, CreateView):
    model = SaleReturn
    form_class = SaleReturnForm
    template_name = 'sales_return/form.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        SaleReturnItemFormSet = inlineformset_factory(
            SaleReturn, SaleReturnItem, 
            form=SaleReturnItemForm,
            extra=1, 
            can_delete=True
        )

        instance = self.object
        if instance and instance.return_date:
            context['return_date'] = instance.return_date.strftime('%d-%m-%Y')
        else:
            context['return_date'] = ''
        
        if self.request.POST:
            context['item_formset'] = SaleReturnItemFormSet(self.request.POST, instance=self.object)
        else:
            context['item_formset'] = SaleReturnItemFormSet(instance=self.object)
        
        return context

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    def form_valid(self, form):
        context = self.get_context_data()
        item_formset = context['item_formset']
        
        if form.is_valid() and item_formset.is_valid():
            sale_return = form.save(commit=False)
            sale_return.created_by = self.request.user
            sale_return.save()
            
            item_formset.instance = sale_return
            item_formset.save()
            
            # Calculate totals
            self.calculate_return_totals(sale_return)
            
            messages.success(self.request, "Sale return created successfully.")
            return redirect('sale_return_list')
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

    def calculate_return_totals(self, sale_return):
        items = sale_return.items.all()
        subtotal = sum(item.total_price for item in items)
        
        sale_return.subtotal = subtotal
        sale_return.total = subtotal - sale_return.discount + sale_return.tax
        sale_return.save()


class SaleReturnUpdateView(LoginRequiredMixin, UpdateView):
    model = SaleReturn
    form_class = SaleReturnForm
    template_name = 'sales_return/form.html'
    pk_url_kwarg = 'pk'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        SaleReturnItemFormSet = inlineformset_factory(
            SaleReturn, SaleReturnItem, 
            form=SaleReturnItemForm,
            extra=0, 
            can_delete=True
        )

        instance = self.object
        if instance and instance.return_date:
            context['return_date'] = instance.return_date.strftime('%d-%m-%Y')
        else:
            context['return_date'] = ''
        
        if self.request.POST:
            context['item_formset'] = SaleReturnItemFormSet(self.request.POST, instance=self.object)
        else:
            context['item_formset'] = SaleReturnItemFormSet(instance=self.object)
        
        return context

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    def form_valid(self, form):
        context = self.get_context_data()
        item_formset = context['item_formset']
        
        if form.is_valid() and item_formset.is_valid():
            sale_return = form.save(commit=False)
            sale_return.updated_by = self.request.user
            sale_return.save()
            
            item_formset.instance = sale_return
            item_formset.save()
            
            # Calculate totals
            self.calculate_return_totals(sale_return)
            
            messages.success(self.request, "Sale return updated successfully.")
            return redirect('sale_return_list')
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

    def calculate_return_totals(self, sale_return):
        items = sale_return.items.all()
        subtotal = sum(item.total_price for item in items)
        
        sale_return.subtotal = subtotal
        sale_return.total = subtotal - sale_return.discount + sale_return.tax
        sale_return.save()


class SaleReturnDeleteView(LoginRequiredMixin, DeleteView):
    model = SaleReturn
    success_url = reverse_lazy('sale_return_list')
    pk_url_kwarg = 'pk'

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.delete()
        messages.success(self.request, "Sale return deleted successfully.")
        return redirect(self.success_url)


@login_required
def sale_return_invoice_pdf(request, pk):
    """Generate and download PDF invoice for a sale return"""
    sale_return = get_object_or_404(SaleReturn, pk=pk)
    
    # Check permissions - only allow if user owns the return or is admin
    user = request.user
    if not getattr(user, 'role', None) or getattr(user.role, 'name', '').upper() != 'ADMIN':
        if sale_return.created_by != user:
            messages.error(request, "You don't have permission to access this sale return.")
            return redirect('sale_return_list')
    
    # Render the template to HTML
    html_string = render_to_string('sales_return/invoice_pdf.html', {
        'sale_return': sale_return,
    }, request=request)
    
    # Generate PDF
    html = weasyprint.HTML(string=html_string, base_url=request.build_absolute_uri())
    pdf = html.write_pdf()
    
    # Create response
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="sale_return_{sale_return.return_number}.pdf"'
    
    return response