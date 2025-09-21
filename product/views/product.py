from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.template.loader import render_to_string
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST

from product.models import Product, ProductCategory
from product.forms.product import ProductForm
from commons.utils import is_ajax  # assuming same utility exists

# Reusable owner filter mixin (admin vs own)
class OwnerFilterMixin:
    def get_queryset(self):
        qs = super().get_queryset()
        return qs


class ProductListView(LoginRequiredMixin, OwnerFilterMixin, ListView):
    model = Product
    template_name = 'product/list.html'
    context_object_name = 'product_list'

    def get_queryset(self):
        qs = super().get_queryset().select_related('category')
        search = self.request.GET.get('search_input', '').strip()
        category_slug = self.request.GET.get('category', '').strip()
        if search:
            qs = qs.filter(Q(name__icontains=search) | Q(sku__icontains=search))
        if category_slug:
            qs = qs.filter(category__slug=category_slug)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search'] = self.request.GET.get('search', '')

        # product_list here is a Page object from the ListView pagination
        queryset = context.get('product_list')
        paginator = Paginator(queryset, 50)
        page_number = self.request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        context['product_list'] = page_obj
        return context

    def render_to_response(self, context, **response_kwargs):
        if self.request.headers.get('x-requested-with') == 'XMLHttpRequest':
            # Render only the table+pagination fragment
            html = render_to_string('product/_table_fragment.html', context=context, request=self.request)
            return JsonResponse({'html': html})
        return super().render_to_response(context, **response_kwargs)
    


class ProductDetailView(LoginRequiredMixin, OwnerFilterMixin, DetailView):
    model = Product
    template_name = 'product/form.html'
    context_object_name = 'product'


class ProductCreateView(LoginRequiredMixin, CreateView):
    model = Product
    form_class = ProductForm
    template_name = 'product/form.html'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    def form_valid(self, form):
        from inventory.models import InventoryTransaction
        from django.db import transaction as db_transaction
        
        with db_transaction.atomic():
            product: Product = form.save(commit=False)
            product.save()
            
            # Handle initial stock if provided
            initial_stock = form.cleaned_data.get('initial_stock', 0)
            if initial_stock and initial_stock > 0:
                # Update the existing INITIAL_STOCK transaction created by signal
                try:
                    initial_transaction = InventoryTransaction.objects.get(
                        product=product,
                        transaction_type=InventoryTransaction.TransactionType.INITIAL_STOCK
                    )
                    initial_transaction.quantity = int(initial_stock)
                    initial_transaction.note = f"Initial stock for product {product.name}: {initial_stock} units"
                    initial_transaction.save()
                except InventoryTransaction.DoesNotExist:
                    # Create if signal didn't create it for some reason
                    InventoryTransaction.objects.create(
                        product=product,
                        transaction_type=InventoryTransaction.TransactionType.INITIAL_STOCK,
                        quantity=int(initial_stock),
                        note=f"Initial stock for product {product.name}: {initial_stock} units",
                        reference_code=f"INIT-{product.sku}"
                    )
        
        messages.success(self.request, "Product created successfully.")
        return redirect('product_list')

    def form_invalid(self, form):
        errors = []
        field_errors = {f: e for f, e in form.errors.items() if f != '__all__'}
        non_field = form.non_field_errors()
        errors.extend(non_field)
        for err_list in field_errors.values():
            errors.extend(err_list)
        context = self.get_context_data(form=form)
        context.update({'messages': errors, 'is_error': True})
        return render(self.request, self.template_name, context, status=400)


class ProductUpdateView(LoginRequiredMixin, UpdateView):
    model = Product
    form_class = ProductForm
    template_name = 'product/form.html'
    pk_url_kwarg = 'pk'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    def form_valid(self, form):
        product: Product = form.save(commit=False)
        product.updated_by = self.request.user
        product.sku = form.cleaned_data['sku']
        product.save()
        messages.success(self.request, "Product updated successfully.")
        return redirect('product_list')

    def form_invalid(self, form):
        errors = []
        field_errors = {f: e for f, e in form.errors.items() if f != '__all__'}
        non_field = form.non_field_errors()
        errors.extend(non_field)
        for err_list in field_errors.values():
            errors.extend(err_list)
        context = self.get_context_data(form=form)
        context.update({'messages': errors, 'is_error': True})
        return render(self.request, self.template_name, context, status=400)


class ProductDeleteView(LoginRequiredMixin, DeleteView):
    model = Product
    success_url = reverse_lazy('product_list')
    pk_url_kwarg = 'pk'

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.delete()
        messages.success(self.request, "Product deleted successfully.")
        return redirect(self.success_url)


@require_POST
@login_required
def create_product_ajax(request):
    """
    AJAX endpoint for creating products from the sales form modal
    """
    try:
        # Get form data
        name = request.POST.get('name', '').strip()
        sku = request.POST.get('sku', '').strip().upper()
        category_id = request.POST.get('category', '').strip()
        brand_id = request.POST.get('brand', '').strip()
        unit_id = request.POST.get('unit', '').strip()
        color_id = request.POST.get('color', '').strip()
        price = request.POST.get('price', '').strip()
        description = request.POST.get('description', '').strip()
        
        # Validate required fields
        if not name:
            return JsonResponse({
                'success': False,
                'message': 'Product name is required'
            })
        
        
        if not price:
            return JsonResponse({
                'success': False,
                'message': 'Price is required'
            })
        
        # Check if product with SKU already exists
        if Product.objects.filter(sku__isnull=False, sku__iexact=sku).exists():
            return JsonResponse({
                'success': False,
                'message': 'Product with this SKU already exists'
            })
        
        # Validate price
        try:
            price = float(price)
            if price < 0:
                return JsonResponse({
                    'success': False,
                    'message': 'Price cannot be negative'
                })
        except ValueError:
            return JsonResponse({
                'success': False,
                'message': 'Invalid price format'
            })
        
        # Get related objects
        category = None
        if category_id:
            try:
                from product.models import ProductCategory
                category = ProductCategory.objects.get(id=category_id)
            except ProductCategory.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'message': 'Selected category does not exist'
                })
        
        brand = None
        if brand_id:
            try:
                from product.models import Brand
                brand = Brand.objects.get(id=brand_id)
            except Brand.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'message': 'Selected brand does not exist'
                })
        
        unit = None
        if unit_id:
            try:
                from product.models import Unit
                unit = Unit.objects.get(id=unit_id)
            except Unit.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'message': 'Selected unit does not exist'
                })
        
        color = None
        if color_id:
            try:
                from product.models import Color
                color = Color.objects.get(id=color_id)
            except Color.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'message': 'Selected color does not exist'
                })
        
        # Create product
        product = Product.objects.create(
            name=name,
            sku=sku,
            category=category,
            brand=brand,
            unit=unit,
            color=color,
            price=price,
            description=description if description else None,
            is_active=True,
            created_by=request.user
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Product created successfully',
            'product': {
                'id': product.id,
                'name': product.name,
                'sku': product.sku,
                'price': str(product.price),
                'category_name': product.category.name if product.category else None,
                'brand_name': product.brand.name if product.brand else None,
                'unit_name': product.unit.name if product.unit else None,
                'color_name': product.color.name if product.color else None
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error creating product: {str(e)}'
        })
