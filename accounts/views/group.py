from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.template.loader import render_to_string
from django.http import JsonResponse
from django.core.paginator import Paginator

from accounts.models import Group
from accounts.forms import GroupForm

class GroupListView(LoginRequiredMixin, ListView):
    model = Group
    template_name = 'group/list.html'
    context_object_name = 'group_list'

    def get_queryset(self):
        queryset = super().get_queryset()
        search = self.request.GET.get('search_input', '').strip()
        if search:
            queryset = queryset.filter(name__icontains=search)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        queryset = context.get('group_list')
        paginator = Paginator(queryset, 50)
        page_number = self.request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        context['group_list'] = page_obj
        context['filter_search_input'] = self.request.GET.get('search_input', '')
        return context

    def render_to_response(self, context, **response_kwargs):
        if self.request.headers.get('x-requested-with') == 'XMLHttpRequest':
            html = render_to_string('group/_table_fragment.html', context=context, request=self.request)
            return JsonResponse({'html': html})
        return super().render_to_response(context, **response_kwargs)


class GroupDetailView(LoginRequiredMixin, DetailView):
    model = Group
    template_name = 'group/form.html'
    context_object_name = 'group'


class GroupCreateView(LoginRequiredMixin, CreateView):
    model = Group
    form_class = GroupForm
    template_name = 'group/form.html'

    def form_valid(self, form):
        group = form.save()
        messages.success(self.request, "Group created successfully.")
        return redirect('group_list')

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


class GroupUpdateView(LoginRequiredMixin, UpdateView):
    model = Group
    form_class = GroupForm
    template_name = 'group/form.html'
    pk_url_kwarg = 'pk'

    def form_valid(self, form):
        form.save()
        messages.success(self.request, "Group updated successfully.")
        return redirect('group_list')

    def form_invalid(self, form):
        return GroupCreateView._handle_invalid(self, form)


class GroupDeleteView(LoginRequiredMixin, DeleteView):
    model = Group
    success_url = reverse_lazy('group_list')
    pk_url_kwarg = 'pk'

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.delete()
        messages.success(request, "Group deleted successfully.")
        return redirect(self.success_url)