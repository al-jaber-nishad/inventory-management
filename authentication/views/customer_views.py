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

from authentication.models import Customer
from authentication.forms.customer import CustomerForm


class OwnerFilterMixin:
    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        if not getattr(user, 'role', None) or getattr(user.role, 'name', '').upper() != 'ADMIN':
            qs = qs.filter(created_by=user)
        return qs


class CustomerListView(LoginRequiredMixin, OwnerFilterMixin, ListView):
    model = Customer
    template_name = 'customer/list.html'
    context_object_name = 'customer_list'

    def get_queryset(self):
        qs = super().get_queryset()
        search = self.request.GET.get('search_input', '').strip()
        if search:
            qs = qs.filter(Q(name__icontains=search) | Q(phone__icontains=search))
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search'] = self.request.GET.get('search', '')

        queryset = context.get('customer_list')
        paginator = Paginator(queryset, 50)
        page_number = self.request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        context['customer_list'] = page_obj
        return context

    def render_to_response(self, context, **response_kwargs):
        if self.request.headers.get('x-requested-with') == 'XMLHttpRequest':
            html = render_to_string('customer/_table_fragment.html', context=context, request=self.request)
            return JsonResponse({'html': html})
        return super().render_to_response(context, **response_kwargs)


class CustomerDetailView(LoginRequiredMixin, OwnerFilterMixin, DetailView):
    model = Customer
    template_name = 'customer/form.html'
    context_object_name = 'customer'


class CustomerCreateView(LoginRequiredMixin, CreateView):
    model = Customer
    form_class = CustomerForm
    template_name = 'customer/form.html'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    def form_valid(self, form):
        customer = form.save(commit=False)
        customer.created_by = self.request.user
        customer.save()
        messages.success(self.request, "Customer created successfully.")
        return redirect('customer_list')

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


class CustomerUpdateView(LoginRequiredMixin, UpdateView):
    model = Customer
    form_class = CustomerForm
    template_name = 'customer/form.html'
    pk_url_kwarg = 'pk'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    def form_valid(self, form):
        customer = form.save(commit=False)
        customer.updated_by = self.request.user
        customer.save()
        messages.success(self.request, "Customer updated successfully.")
        return redirect('customer_list')

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


class CustomerDeleteView(LoginRequiredMixin, DeleteView):
    model = Customer
    success_url = reverse_lazy('customer_list')
    pk_url_kwarg = 'pk'

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.delete()
        messages.success(self.request, "Customer deleted successfully.")
        return redirect(self.success_url)


@require_POST
@login_required
def create_customer_ajax(request):
    """
    AJAX endpoint for creating customers from the sales form modal
    """
    try:
        # Get form data
        name = request.POST.get('name', '').strip()
        phone = request.POST.get('phone', '').strip()
        address = request.POST.get('address', '').strip()
        
        # Validate required fields
        if not name:
            return JsonResponse({
                'success': False,
                'message': 'Customer name is required'
            })
        
        # Create customer
        customer = Customer.objects.create(
            name=name,
            phone=phone,
            address=address,
            created_by=request.user
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Customer created successfully',
            'customer': {
                'id': customer.id,
                'name': customer.name,
                'phone': customer.phone,
                'address': customer.address
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error creating customer: {str(e)}'
        })