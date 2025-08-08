from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.template.loader import render_to_string
from django.http import JsonResponse
from django.core.paginator import Paginator

from accounts.models import LedgerAccount, ReceiptVoucher
from accounts.forms import ReceiptVoucherForm




class ReceiptVoucherListView(LoginRequiredMixin, ListView):
    model = ReceiptVoucher
    template_name = 'receiptvoucher/list.html'
    context_object_name = 'receiptvoucher_list'

    def get_queryset(self):
        queryset = super().get_queryset()
        search = self.request.GET.get('search_input', '').strip()
        if search:
            queryset = queryset.filter(invoice_no__icontains=search)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        queryset = context.get('receiptvoucher_list')
        paginator = Paginator(queryset, 50)
        page_number = self.request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        context['receiptvoucher_list'] = page_obj
        context['filter_search_input'] = self.request.GET.get('search_input', '')
        return context

    def render_to_response(self, context, **response_kwargs):
        if self.request.headers.get('x-requested-with') == 'XMLHttpRequest':
            html = render_to_string('receiptvoucher/_table_fragment.html', context=context, request=self.request)
            return JsonResponse({'html': html})
        return super().render_to_response(context, **response_kwargs)


class ReceiptVoucherDetailView(LoginRequiredMixin, DetailView):
    model = ReceiptVoucher
    template_name = 'receiptvoucher/form.html'
    context_object_name = 'receiptvoucher'


class ReceiptVoucherCreateView(LoginRequiredMixin, CreateView):
    model = ReceiptVoucher
    form_class = ReceiptVoucherForm
    template_name = 'receiptvoucher/form.html'

    def form_valid(self, form):
        receiptvoucher = form.save(commit=False)
        income_ledger, _ = LedgerAccount.objects.get_or_create(name='Income')
        receiptvoucher.income_ledger = income_ledger
        receiptvoucher.invoice_no = self.generate_invoice_number()
        receiptvoucher.save()
        messages.success(self.request, "Income created successfully.")
        return redirect('receiptvoucher_list')

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
        prefix = f"RV-{today.year}-"
        
        # Find the last receipt voucher of this year
        last_receipt_voucher = ReceiptVoucher.objects.filter(
            invoice_no__startswith=prefix
        ).order_by('-invoice_no').first()
        
        if last_receipt_voucher:
            try:
                last_number = int(last_receipt_voucher.invoice_no.split('-')[-1])
                new_number = last_number + 1
            except (ValueError, IndexError):
                new_number = 1
        else:
            new_number = 1
        
        return f"{prefix}{new_number:05d}"

class ReceiptVoucherUpdateView(LoginRequiredMixin, UpdateView):
    model = ReceiptVoucher
    form_class = ReceiptVoucherForm
    template_name = 'receiptvoucher/form.html'
    pk_url_kwarg = 'pk'

    def form_valid(self, form):
        form.save()
        messages.success(self.request, "Income updated successfully.")
        return redirect('receiptvoucher_list')

    def form_invalid(self, form):
        return ReceiptVoucherCreateView._handle_invalid(self, form)


class ReceiptVoucherDeleteView(LoginRequiredMixin, DeleteView):
    model = ReceiptVoucher
    success_url = reverse_lazy('receiptvoucher_list')
    pk_url_kwarg = 'pk'

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.delete()
        messages.success(request, "Income deleted successfully.")
        return redirect(self.success_url)