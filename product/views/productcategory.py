from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.template.loader import render_to_string
from django.http import JsonResponse
from django.core.paginator import Paginator

from product.models import ProductCategory
from product.forms.productcategory import ProductCategoryForm

class ProductCategoryListView(LoginRequiredMixin, ListView):
    model = ProductCategory
    template_name = 'productcategory/list.html'
    context_object_name = 'category_list'

    def get_queryset(self):
        qs = super().get_queryset()
        search = self.request.GET.get('search_input', '').strip()
        if search:
            qs = qs.filter(name__icontains=search)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        paginator = Paginator(context['category_list'], 10)
        page_number = self.request.GET.get('page')
        context['category_list'] = paginator.get_page(page_number)
        context['filter_search_input'] = self.request.GET.get('search_input', '')
        return context

    def render_to_response(self, context, **response_kwargs):
        if self.request.headers.get('x-requested-with') == 'XMLHttpRequest':
            html = render_to_string('productcategory/_table_fragment.html', context=context, request=self.request)
            return JsonResponse({'html': html})
        return super().render_to_response(context, **response_kwargs)


class ProductCategoryDetailView(LoginRequiredMixin, DetailView):
    model = ProductCategory
    template_name = 'productcategory/form.html'
    context_object_name = 'category'


class ProductCategoryCreateView(LoginRequiredMixin, CreateView):
    model = ProductCategory
    form_class = ProductCategoryForm
    template_name = 'productcategory/form.html'

    def form_valid(self, form):
        form.save()
        messages.success(self.request, "Category created successfully.")
        return redirect('productcategory_list')

    def form_invalid(self, form):
        errors = []
        errors += form.non_field_errors()
        for err in form.errors.values():
            errors += err
        context = self.get_context_data(form=form)
        context.update({'messages': errors, 'is_error': True})
        return render(self.request, self.template_name, context, status=400)


class ProductCategoryUpdateView(LoginRequiredMixin, UpdateView):
    model = ProductCategory
    form_class = ProductCategoryForm
    template_name = 'productcategory/form.html'
    pk_url_kwarg = 'pk'

    def form_valid(self, form):
        form.save()
        messages.success(self.request, "Category updated successfully.")
        return redirect('productcategory_list')

    def form_invalid(self, form):
        return ProductCategoryCreateView._handle_invalid(self, form)


class ProductCategoryDeleteView(LoginRequiredMixin, DeleteView):
    model = ProductCategory
    success_url = reverse_lazy('productcategory_list')
    pk_url_kwarg = 'pk'

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.delete()
        messages.success(request, "Category deleted successfully.")
        return redirect(self.success_url)
