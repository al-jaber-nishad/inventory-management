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

from product.models import Color
from product.forms.color import ColorForm
from commons.utils import is_ajax

class ColorListView(LoginRequiredMixin, ListView):
    model = Color
    template_name = 'color/list.html'
    context_object_name = 'color_list'

    def get_queryset(self):
        qs = super().get_queryset()
        search = self.request.GET.get('search_input', '').strip()
        if search:
            qs = qs.filter(name__icontains=search)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        paginator = Paginator(context['color_list'], 10)
        page_number = self.request.GET.get('page')
        context['color_list'] = paginator.get_page(page_number)
        context['filter_search_input'] = self.request.GET.get('search_input', '')
        return context

    def render_to_response(self, context, **response_kwargs):
        if self.request.headers.get('x-requested-with') == 'XMLHttpRequest':
            html = render_to_string('color/_table_fragment.html', context=context, request=self.request)
            return JsonResponse({'html': html})
        return super().render_to_response(context, **response_kwargs)


class ColorDetailView(LoginRequiredMixin, DetailView):
    model = Color
    template_name = 'color/form.html'
    context_object_name = 'color'


class ColorCreateView(LoginRequiredMixin, CreateView):
    model = Color
    form_class = ColorForm
    template_name = 'color/form.html'

    def form_valid(self, form):
        form.save()
        messages.success(self.request, "Color created successfully.")
        return redirect('color_list')

    def form_invalid(self, form):
        return self._handle_invalid(form)

    def _handle_invalid(self, form):
        errors = []
        errors += form.non_field_errors()
        for err in form.errors.values():
            errors += err
        context = self.get_context_data(form=form)
        context.update({'messages': errors, 'is_error': True})
        return render(self.request, self.template_name, context, status=400)


class ColorUpdateView(LoginRequiredMixin, UpdateView):
    model = Color
    form_class = ColorForm
    template_name = 'color/form.html'
    pk_url_kwarg = 'pk'

    def form_valid(self, form):
        form.save()
        messages.success(self.request, "Color updated successfully.")
        return redirect('color_list')

    def form_invalid(self, form):
        return ColorCreateView._handle_invalid(self, form)


class ColorDeleteView(LoginRequiredMixin, DeleteView):
    model = Color
    success_url = reverse_lazy('color_list')
    pk_url_kwarg = 'pk'

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.delete()
        messages.success(request, "Color deleted successfully.")
        return redirect(self.success_url)


@require_POST
@login_required
def create_color_ajax(request):
    """
    AJAX endpoint for creating colors from the product form modal
    """
    try:
        # Get form data
        name = request.POST.get('name', '').strip()
        hex_code = request.POST.get('hex_code', '').strip()
        
        # Validate required fields
        if not name:
            return JsonResponse({
                'success': False,
                'message': 'Color name is required'
            })
        
        # Validate hex code if provided
        if hex_code:
            # Remove # if present and validate format
            hex_code = hex_code.replace('#', '')
            if len(hex_code) != 6 or not all(c in '0123456789ABCDEFabcdef' for c in hex_code):
                return JsonResponse({
                    'success': False,
                    'message': 'Please enter a valid 6-digit hex color code (e.g., FF0000)'
                })
            hex_code = '#' + hex_code.upper()
        
        # Check if color already exists
        if Color.objects.filter(name__iexact=name).exists():
            return JsonResponse({
                'success': False,
                'message': 'Color with this name already exists'
            })
        
        # Create color
        color = Color.objects.create(
            name=name,
            hex_code=hex_code if hex_code else None,
            created_by=request.user
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Color created successfully',
            'color': {
                'id': color.id,
                'name': color.name,
                'hex_code': color.hex_code
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error creating color: {str(e)}'
        })