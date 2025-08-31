from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.template.loader import render_to_string
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt

from authentication.models import Supplier
from authentication.forms.supplier import SupplierForm


class OwnerFilterMixin:
    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        if not getattr(user, 'role', None) or getattr(user.role, 'name', '').upper() != 'ADMIN':
            qs = qs.filter(created_by=user)
        return qs


class SupplierListView(LoginRequiredMixin, OwnerFilterMixin, ListView):
    model = Supplier
    template_name = 'supplier/list.html'
    context_object_name = 'supplier_list'

    def get_queryset(self):
        qs = super().get_queryset().select_related('brand')
        search = self.request.GET.get('search_input', '').strip()
        if search:
            qs = qs.filter(Q(name__icontains=search) | Q(phone__icontains=search) | Q(email__icontains=search))
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search'] = self.request.GET.get('search', '')

        queryset = context.get('supplier_list')
        paginator = Paginator(queryset, 50)
        page_number = self.request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        context['supplier_list'] = page_obj
        return context

    def render_to_response(self, context, **response_kwargs):
        if self.request.headers.get('x-requested-with') == 'XMLHttpRequest':
            html = render_to_string('supplier/_table_fragment.html', context=context, request=self.request)
            return JsonResponse({'html': html})
        return super().render_to_response(context, **response_kwargs)


class SupplierDetailView(LoginRequiredMixin, OwnerFilterMixin, DetailView):
    model = Supplier
    template_name = 'supplier/form.html'
    context_object_name = 'supplier'


class SupplierCreateView(LoginRequiredMixin, CreateView):
    model = Supplier
    form_class = SupplierForm
    template_name = 'supplier/form.html'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    def form_valid(self, form):
        supplier = form.save(commit=False)
        supplier.created_by = self.request.user
        supplier.save()
        messages.success(self.request, "Supplier created successfully.")
        return redirect('supplier_list')

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


class SupplierUpdateView(LoginRequiredMixin, UpdateView):
    model = Supplier
    form_class = SupplierForm
    template_name = 'supplier/form.html'
    pk_url_kwarg = 'pk'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    def form_valid(self, form):
        supplier = form.save(commit=False)
        supplier.updated_by = self.request.user
        supplier.save()
        messages.success(self.request, "Supplier updated successfully.")
        return redirect('supplier_list')

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


class SupplierDeleteView(LoginRequiredMixin, DeleteView):
    model = Supplier
    success_url = reverse_lazy('supplier_list')
    pk_url_kwarg = 'pk'

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.delete()
        messages.success(self.request, "Supplier deleted successfully.")
        return redirect(self.success_url)


@require_POST
@login_required
def create_supplier_ajax(request):
    """
    AJAX endpoint for creating suppliers from the purchase form modal
    """
    try:
        # Get form data
        name = request.POST.get('name', '').strip()
        phone = request.POST.get('phone', '').strip()
        address = request.POST.get('address', '').strip()
        brand_id = request.POST.get('brand_id', '').strip()
        
        # Validate required fields
        if not name:
            return JsonResponse({
                'success': False,
                'message': 'Supplier name is required'
            })
        
        # Handle brand relationship
        brand = None
        if brand_id:
            try:
                from product.models import Brand
                brand = Brand.objects.get(id=brand_id)
            except Brand.DoesNotExist:
                pass
        
        # Create supplier
        supplier = Supplier.objects.create(
            name=name,
            phone=phone,
            address=address,
            brand=brand,
            created_by=request.user
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Supplier created successfully',
            'supplier': {
                'id': supplier.id,
                'name': supplier.name,
                'phone': supplier.phone,
                'address': supplier.address,
                'brand': supplier.brand.name if supplier.brand else None
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error creating supplier: {str(e)}'
        })