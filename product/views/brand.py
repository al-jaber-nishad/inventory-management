from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.template.loader import render_to_string
from django.http import JsonResponse
from django.core.paginator import Paginator

from product.models import Brand
from product.forms.brand import BrandForm
from commons.utils import is_ajax

class BrandListView(LoginRequiredMixin, ListView):
    model = Brand
    template_name = 'brand/list.html'
    context_object_name = 'brand_list'

    def get_queryset(self):
        qs = super().get_queryset()
        search = self.request.GET.get('search_input', '').strip()
        if search:
            qs = qs.filter(name__icontains=search)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        paginator = Paginator(context['brand_list'], 10)
        page_number = self.request.GET.get('page')
        context['brand_list'] = paginator.get_page(page_number)
        context['filter_search_input'] = self.request.GET.get('search_input', '')
        return context

    def render_to_response(self, context, **response_kwargs):
        if self.request.headers.get('x-requested-with') == 'XMLHttpRequest':
            html = render_to_string('brand/_table_fragment.html', context=context, request=self.request)
            return JsonResponse({'html': html})
        return super().render_to_response(context, **response_kwargs)


class BrandDetailView(LoginRequiredMixin, DetailView):
    model = Brand
    template_name = 'brand/form.html'
    context_object_name = 'brand'


class BrandCreateView(LoginRequiredMixin, CreateView):
    model = Brand
    form_class = BrandForm
    template_name = 'brand/form.html'

    def form_valid(self, form):
        form.save()
        messages.success(self.request, "Brand created successfully.")
        return redirect('brand_list')

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


class BrandUpdateView(LoginRequiredMixin, UpdateView):
    model = Brand
    form_class = BrandForm
    template_name = 'brand/form.html'
    pk_url_kwarg = 'pk'

    def form_valid(self, form):
        form.save()
        messages.success(self.request, "Brand updated successfully.")
        return redirect('brand_list')

    def form_invalid(self, form):
        return BrandCreateView._handle_invalid(self, form)


class BrandDeleteView(LoginRequiredMixin, DeleteView):
    model = Brand
    success_url = reverse_lazy('brand_list')
    pk_url_kwarg = 'pk'

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.delete()
        messages.success(request, "Brand deleted successfully.")
        return redirect(self.success_url)
