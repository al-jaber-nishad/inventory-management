from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.template.loader import render_to_string
from django.http import JsonResponse
from django.core.paginator import Paginator

from accounts.models import LedgerAccount, PaymentVoucher
from accounts.forms import PaymentVoucherForm




class PaymentVoucherListView(LoginRequiredMixin, ListView):
    model = PaymentVoucher
    template_name = 'paymentvoucher/list.html'
    context_object_name = 'paymentvoucher_list'

    def get_queryset(self):
        queryset = super().get_queryset()
        search = self.request.GET.get('search_input', '').strip()
        if search:
            queryset = queryset.filter(invoice_no__icontains=search)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        queryset = context.get('paymentvoucher_list')
        paginator = Paginator(queryset, 50)
        page_number = self.request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        context['paymentvoucher_list'] = page_obj
        context['filter_search_input'] = self.request.GET.get('search_input', '')
        return context

    def render_to_response(self, context, **response_kwargs):
        if self.request.headers.get('x-requested-with') == 'XMLHttpRequest':
            html = render_to_string('paymentvoucher/_table_fragment.html', context=context, request=self.request)
            return JsonResponse({'html': html})
        return super().render_to_response(context, **response_kwargs)


class PaymentVoucherDetailView(LoginRequiredMixin, DetailView):
    model = PaymentVoucher
    template_name = 'paymentvoucher/form.html'
    context_object_name = 'paymentvoucher'


class PaymentVoucherCreateView(LoginRequiredMixin, CreateView):
    model = PaymentVoucher
    form_class = PaymentVoucherForm
    template_name = 'paymentvoucher/form.html'

    def form_valid(self, form):
        paymentvoucher = form.save(commit=False)
        expense_ledger, _ = LedgerAccount.objects.get_or_create(name='Expenses')
        paymentvoucher.expense_ledger = expense_ledger
        paymentvoucher.invoice_no = self.generate_invoice_number()
        paymentvoucher.save()
        messages.success(self.request, "Expense created successfully.")
        return redirect('paymentvoucher_list')

    def form_invalid(self, form):
        return self._handle_invalid(form)

    def _handle_invalid(self, form):
        errors = {}

        for field, field_errors in form.errors.items():
            errors[field] = field_errors.get_json_data(escape_html=True)

        context = self.get_context_data(form=form)
        errors = [f"{field}: {', '.join([item['message'] for item in messages])}" for field, messages in errors.items()]

        context.update({
            'messages': errors,
            'is_error': True
        })
        return render(self.request, self.template_name, context, status=400)
    

    def generate_invoice_number(self):
        import datetime
        today = datetime.date.today()
        prefix = f"PV-{today.year}-"
        
        # Find the last payment voucher of this year
        last_payment_voucher = PaymentVoucher.objects.filter(
            invoice_no__startswith=prefix
        ).order_by('-invoice_no').first()
        
        if last_payment_voucher:
            try:
                last_number = int(last_payment_voucher.invoice_no.split('-')[-1])
                new_number = last_number + 1
            except (ValueError, IndexError):
                new_number = 1
        else:
            new_number = 1
        
        return f"{prefix}{new_number:05d}"

class PaymentVoucherUpdateView(LoginRequiredMixin, UpdateView):
    model = PaymentVoucher
    form_class = PaymentVoucherForm
    template_name = 'paymentvoucher/form.html'
    pk_url_kwarg = 'pk'

    def form_valid(self, form):
        form.save()
        messages.success(self.request, "Expense updated successfully.")
        return redirect('paymentvoucher_list')

    def form_invalid(self, form):
        return PaymentVoucherCreateView._handle_invalid(self, form)


class PaymentVoucherDeleteView(LoginRequiredMixin, DeleteView):
    model = PaymentVoucher
    success_url = reverse_lazy('paymentvoucher_list')
    pk_url_kwarg = 'pk'

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.delete()
        messages.success(request, "Expense deleted successfully.")
        return redirect(self.success_url)