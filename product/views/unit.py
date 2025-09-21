from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.template.loader import render_to_string
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST

from product.models import Unit
from product.forms.unit import UnitForm
from commons.utils import is_ajax  # reuse if available

class UnitListView(LoginRequiredMixin, ListView):
    model = Unit
    template_name = 'unit/list.html'
    context_object_name = 'unit_list'

    def get_queryset(self):
        queryset = super().get_queryset()
        search = self.request.GET.get('search_input', '').strip()
        if search:
            queryset = queryset.filter(name__icontains=search)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        queryset = context.get('unit_list')
        paginator = Paginator(queryset, 50)
        page_number = self.request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        context['unit_list'] = page_obj
        context['filter_search_input'] = self.request.GET.get('search_input', '')
        return context

    def render_to_response(self, context, **response_kwargs):
        if self.request.headers.get('x-requested-with') == 'XMLHttpRequest':
            html = render_to_string('unit/_table_fragment.html', context=context, request=self.request)
            return JsonResponse({'html': html})
        return super().render_to_response(context, **response_kwargs)


class UnitDetailView(LoginRequiredMixin, DetailView):
    model = Unit
    template_name = 'unit/form.html'
    context_object_name = 'unit'


class UnitCreateView(LoginRequiredMixin, CreateView):
    model = Unit
    form_class = UnitForm
    template_name = 'unit/form.html'

    def form_valid(self, form):
        unit = form.save()
        messages.success(self.request, "Unit created successfully.")
        return redirect('unit_list')

    def form_invalid(self, form):
        return self._handle_invalid(form)

    def _handle_invalid(self, form):
        errors = []
        field_errors = {f: e for f, e in form.errors.items() if f != '__all__'}
        non_field = form.non_field_errors()
        errors.extend(non_field)
        for err_list in field_errors.values():
            errors.extend(err_list)
        context = self.get_context_data(form=form)
        context.update({'messages': errors, 'is_error': True})
        return render(self.request, self.template_name, context, status=400)


class UnitUpdateView(LoginRequiredMixin, UpdateView):
    model = Unit
    form_class = UnitForm
    template_name = 'unit/form.html'
    pk_url_kwarg = 'pk'

    def form_valid(self, form):
        form.save()
        messages.success(self.request, "Unit updated successfully.")
        return redirect('unit_list')

    def form_invalid(self, form):
        return UnitCreateView._handle_invalid(self, form)


class UnitDeleteView(LoginRequiredMixin, DeleteView):
    model = Unit
    success_url = reverse_lazy('unit_list')
    pk_url_kwarg = 'pk'

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.delete()
        messages.success(request, "Unit deleted successfully.")
        return redirect(self.success_url)


@require_POST
@login_required
def create_unit_ajax(request):
    """
    AJAX endpoint for creating units from the product form modal
    """
    try:
        # Get form data
        name = request.POST.get('name', '').strip()
        
        # Validate required fields
        if not name:
            return JsonResponse({
                'success': False,
                'message': 'Unit name is required'
            })
        
        # Check if unit already exists
        if Unit.objects.filter(name__iexact=name).exists():
            return JsonResponse({
                'success': False,
                'message': 'Unit with this name already exists'
            })
        
        # Create unit
        unit = Unit.objects.create(
            name=name,
            created_by=request.user
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Unit created successfully',
            'unit': {
                'id': unit.id,
                'name': unit.name,
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error creating unit: {str(e)}'
        })
