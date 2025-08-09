from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.template.loader import render_to_string
from django.http import JsonResponse
from django.core.paginator import Paginator

from inventory.models import InventoryAdjustment
from inventory.forms.adjustment import InventoryAdjustmentForm


class AdjustmentListView(LoginRequiredMixin, ListView):
    model = InventoryAdjustment
    template_name = 'adjustment/list.html'
    context_object_name = 'adjustment_list'

    def get_queryset(self):
        qs = super().get_queryset().select_related('product').order_by('-date')
        search = self.request.GET.get('search_input', '').strip()
        if search:
            qs = qs.filter(
                Q(product__name__icontains=search) |
                Q(product__sku__icontains=search) |
                Q(reason__icontains=search)
            )
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search'] = self.request.GET.get('search', '')

        # adjustment_list here is a Page object from the ListView pagination
        queryset = context.get('adjustment_list')
        paginator = Paginator(queryset, 50)
        page_number = self.request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        context['adjustment_list'] = page_obj
        return context

    def render_to_response(self, context, **response_kwargs):
        if self.request.headers.get('x-requested-with') == 'XMLHttpRequest':
            # Render only the table+pagination fragment
            html = render_to_string('adjustment/_table_fragment.html', context=context, request=self.request)
            return JsonResponse({'html': html})
        return super().render_to_response(context, **response_kwargs)


class AdjustmentDetailView(LoginRequiredMixin, DetailView):
    model = InventoryAdjustment
    template_name = 'adjustment/form.html'
    context_object_name = 'adjustment'


class AdjustmentCreateView(LoginRequiredMixin, CreateView):
    model = InventoryAdjustment
    form_class = InventoryAdjustmentForm
    template_name = 'adjustment/form.html'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    def form_valid(self, form):
        adjustment = form.save(commit=False)
        adjustment.save()
                
        messages.success(
            self.request, "Stock adjusted successfully!"
        )
        return redirect('adjustment_list')

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


class AdjustmentUpdateView(LoginRequiredMixin, UpdateView):
    model = InventoryAdjustment
    form_class = InventoryAdjustmentForm
    template_name = 'adjustment/form.html'
    pk_url_kwarg = 'pk'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    def form_valid(self, form):
        adjustment = form.save(commit=False)
        adjustment.save()
        
        messages.success(self.request, "Adjustment updated successfully.")
        return redirect('adjustment_list')

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


class AdjustmentDeleteView(LoginRequiredMixin, DeleteView):
    model = InventoryAdjustment
    success_url = reverse_lazy('adjustment_list')
    pk_url_kwarg = 'pk'

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.delete()
        messages.success(self.request, "Adjustment deleted successfully.")
        return redirect(self.success_url)