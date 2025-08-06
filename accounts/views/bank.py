from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.template.loader import render_to_string
from django.http import JsonResponse
from django.core.paginator import Paginator

from accounts.models import Bank
from accounts.forms import BankForm

class BankListView(LoginRequiredMixin, ListView):
    model = Bank
    template_name = 'bank/list.html'
    context_object_name = 'bank_list'

    def get_queryset(self):
        queryset = super().get_queryset()
        search = self.request.GET.get('search_input', '').strip()
        if search:
            queryset = queryset.filter(name__icontains=search)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        queryset = context.get('bank_list')
        paginator = Paginator(queryset, 50)
        page_number = self.request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        context['bank_list'] = page_obj
        context['filter_search_input'] = self.request.GET.get('search_input', '')
        return context

    def render_to_response(self, context, **response_kwargs):
        if self.request.headers.get('x-requested-with') == 'XMLHttpRequest':
            html = render_to_string('bank/_table_fragment.html', context=context, request=self.request)
            return JsonResponse({'html': html})
        return super().render_to_response(context, **response_kwargs)


class BankDetailView(LoginRequiredMixin, DetailView):
    model = Bank
    template_name = 'bank/form.html'
    context_object_name = 'bank'


class BankCreateView(LoginRequiredMixin, CreateView):
    model = Bank
    form_class = BankForm
    template_name = 'bank/form.html'

    def form_valid(self, form):
        bank = form.save()
        messages.success(self.request, "Bank created successfully.")
        return redirect('bank_list')

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


class BankUpdateView(LoginRequiredMixin, UpdateView):
    model = Bank
    form_class = BankForm
    template_name = 'bank/form.html'
    pk_url_kwarg = 'pk'

    def form_valid(self, form):
        form.save()
        messages.success(self.request, "Bank updated successfully.")
        return redirect('bank_list')

    def form_invalid(self, form):
        return BankCreateView._handle_invalid(self, form)


class BankDeleteView(LoginRequiredMixin, DeleteView):
    model = Bank
    success_url = reverse_lazy('bank_list')
    pk_url_kwarg = 'pk'

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.delete()
        messages.success(request, "Bank deleted successfully.")
        return redirect(self.success_url)