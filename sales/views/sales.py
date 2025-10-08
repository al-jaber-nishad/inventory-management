import weasyprint
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
from utils.pillow_image import img_base64

from sales.models import Sale, SaleItem
from sales.forms.sales import SaleForm, SaleItemForm
from product.models import Product


class OwnerFilterMixin:
    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        if not getattr(user, 'role', None) or getattr(user.role, 'name', '').upper() != 'ADMIN':
            qs = qs.filter(created_by=user)
        return qs


class SaleListView(LoginRequiredMixin, OwnerFilterMixin, ListView):
    model = Sale
    template_name = 'sales/list.html'
    context_object_name = 'sale_list'
    ordering = ['-id']
    paginate_by = 50

    def get_queryset(self):
        qs = super().get_queryset().select_related('customer')
        search = self.request.GET.get('search_input', '').strip()
        status = self.request.GET.get('status', '').strip()
        
        if search:
            qs = qs.filter(
                Q(invoice_number__icontains=search) | 
                Q(customer__name__icontains=search)
            )
        if status:
            qs = qs.filter(status=status)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search'] = self.request.GET.get('search', '')
        context['selected_status'] = self.request.GET.get('status', '')
        context['status_choices'] = Sale.Status.choices

        queryset = context.get('sale_list')
        paginator = Paginator(queryset, 50)
        page_number = self.request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        context['sale_list'] = page_obj
        return context

    def render_to_response(self, context, **response_kwargs):
        if self.request.headers.get('x-requested-with') == 'XMLHttpRequest':
            html = render_to_string('sales/_table_fragment.html', context=context, request=self.request)
            return JsonResponse({'html': html})
        return super().render_to_response(context, **response_kwargs)


class SaleDetailView(LoginRequiredMixin, OwnerFilterMixin, DetailView):
    model = Sale
    template_name = 'sales/form.html'
    context_object_name = 'sale'


class SaleCreateView(LoginRequiredMixin, CreateView):
    model = Sale
    form_class = SaleForm
    template_name = 'sales/form.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        SaleItemFormSet = inlineformset_factory(
            Sale, SaleItem,
            form=SaleItemForm,
            extra=1,
            can_delete=True
        )

        form = context.get('form')
        instance = getattr(self, 'object', None)

        # Sale date
        if form and form.is_bound:
            context['sale_date'] = form.data.get('sale_date', '')
        else:
            context['sale_date'] = (
                instance.sale_date.strftime('%d-%m-%Y')
                if instance and instance.sale_date else ''
            )

        # Item formset
        if self.request.POST:
            context['item_formset'] = SaleItemFormSet(self.request.POST, instance=self.object)
        else:
            context['item_formset'] = SaleItemFormSet(instance=self.object)

        return context

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    def form_valid(self, form):
        context = self.get_context_data()
        item_formset = context['item_formset']

        print("form", form)

        if form.is_valid() and item_formset.is_valid():
            sale = form.save(commit=False)
            sale.created_by = self.request.user
            sale.save()

            item_formset.instance = sale
            item_formset.save()

            # Calculate totals
            self.calculate_sale_totals(sale)

            messages.success(self.request, "Sale created successfully.")
            return redirect('sale_list')
        else:
            return self.form_invalid(form)

    def form_invalid(self, form):
        context = self.get_context_data(form=form)
        errors = []

        # Add form field errors with field names
        for field, err_list in form.errors.items():
            if field == '__all__':
                errors.extend(err_list)
            else:
                field_label = form.fields[field].label or field.replace('_', ' ').title()
                for err in err_list:
                    errors.append(f"{field_label}: {err}")

        # Add formset errors with item context
        if 'item_formset' in context:
            for idx, form_errors in enumerate(context['item_formset'].errors):
                if form_errors:
                    for field, field_errors in form_errors.items():
                        if field == '__all__':
                            for err in field_errors:
                                errors.append(f"Item {idx + 1}: {err}")
                        else:
                            for err in field_errors:
                                errors.append(f"Item {idx + 1} - {field.replace('_', ' ').title()}: {err}")

        context.update({'messages': errors, 'is_error': True})
        return render(self.request, self.template_name, context, status=400)

    def calculate_sale_totals(self, sale):
        items = sale.items.all()
        subtotal = sum(item.total_price for item in items)
        
        sale.subtotal = subtotal
        sale.total = subtotal - sale.discount + sale.tax
        sale.save()


class SaleUpdateView(LoginRequiredMixin, UpdateView):
    model = Sale
    form_class = SaleForm
    template_name = 'sales/form.html'
    pk_url_kwarg = 'pk'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        SaleItemFormSet = inlineformset_factory(
            Sale, SaleItem,
            form=SaleItemForm,
            extra=0,
            can_delete=True
        )

        form = context.get('form')
        instance = getattr(self, 'object', None)

        # Sale date
        if form and form.is_bound:
            context['sale_date'] = form.data.get('sale_date', '')
        else:
            context['sale_date'] = (
                instance.sale_date.strftime('%d-%m-%Y')
                if instance and instance.sale_date else ''
            )

        # Item formset
        if self.request.POST:
            context['item_formset'] = SaleItemFormSet(self.request.POST, instance=self.object)
        else:
            context['item_formset'] = SaleItemFormSet(instance=self.object)

        return context

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    def form_valid(self, form):
        context = self.get_context_data()
        item_formset = context['item_formset']

        if form.is_valid() and item_formset.is_valid():
            sale = form.save(commit=False)
            sale.updated_by = self.request.user
            sale.save()

            item_formset.instance = sale
            item_formset.save()

            # Calculate totals
            self.calculate_sale_totals(sale)

            messages.success(self.request, "Sale updated successfully.")
            return redirect('sale_list')
        else:
            return self.form_invalid(form)

    def form_invalid(self, form):
        context = self.get_context_data(form=form)
        errors = []

        # Add form field errors with field names
        for field, err_list in form.errors.items():
            if field == '__all__':
                errors.extend(err_list)
            else:
                field_label = form.fields[field].label or field.replace('_', ' ').title()
                for err in err_list:
                    errors.append(f"{field_label}: {err}")

        # Add formset errors with item context
        if 'item_formset' in context:
            for idx, form_errors in enumerate(context['item_formset'].errors):
                if form_errors:
                    for field, field_errors in form_errors.items():
                        if field == '__all__':
                            for err in field_errors:
                                errors.append(f"Item {idx + 1}: {err}")
                        else:
                            for err in field_errors:
                                errors.append(f"Item {idx + 1} - {field.replace('_', ' ').title()}: {err}")

        context.update({'messages': errors, 'is_error': True})
        return render(self.request, self.template_name, context, status=400)

    def calculate_sale_totals(self, sale):
        items = sale.items.all()
        subtotal = sum(item.total_price for item in items)
        
        sale.subtotal = subtotal
        sale.total = subtotal - sale.discount + sale.tax
        sale.save()


class SaleDeleteView(LoginRequiredMixin, DeleteView):
    model = Sale
    success_url = reverse_lazy('sale_list')
    pk_url_kwarg = 'pk'

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.delete()
        messages.success(self.request, "Sale deleted successfully.")
        return redirect(self.success_url)


@login_required
def sale_invoice_pdf(request, pk):
    """Generate and download PDF invoice for a sale"""
    sale = get_object_or_404(Sale, pk=pk)
    
    # Check permissions - only allow if user owns the sale or is admin
    user = request.user
    if not getattr(user, 'role', None) or getattr(user.role, 'name', '').upper() != 'ADMIN':
        if sale.created_by != user:
            messages.error(request, "You don't have permission to access this sale.")
            return redirect('sale_list')

    
    
    # Render the template to HTML
    logo_image = img_base64('img/full-logo.png')

    # # Logo image (base64 or static path)
    # logo_image = img_base64('img/full-logo.png')

    # # Render invoice HTML directly
    # return render(request, 'sales/invoice_pdf.html', {
    #     'sale': sale,
    #     'logo_image': logo_image
    # })
    
    html_string = render_to_string('sales/invoice_pdf.html', {
        'invoice': sale,
        'logo_image': logo_image
    }, request=request)
    
    # Generate PDF
    html = weasyprint.HTML(string=html_string, base_url=request.build_absolute_uri())
    pdf = html.write_pdf()
    
    # Create response
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="sale_invoice_{sale.invoice_number}.pdf"'
    
    return response


@login_required
def get_product_price(request, product_id):
    """API endpoint to get product price"""
    try:
        product = Product.objects.get(pk=product_id, is_active=True)
        return JsonResponse({'price': float(product.price)})
    except Product.DoesNotExist:
        return JsonResponse({'error': 'Product not found'}, status=404)