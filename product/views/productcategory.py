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


@login_required
def get_categories_api(request):
    """
    API endpoint to get all active categories for parent category dropdown
    """
    try:
        categories = ProductCategory.objects.filter(is_active=True).values('id', 'name').order_by('name')
        return JsonResponse(list(categories), safe=False)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@require_POST
@login_required
def create_category_ajax(request):
    """
    AJAX endpoint for creating categories from the product form modal
    """
    try:
        # Get form data
        name = request.POST.get('name', '').strip()
        description = request.POST.get('description', '').strip()
        parent_id = request.POST.get('parent', '').strip()
        image = request.FILES.get('image', None)
        
        # Validate required fields
        if not name:
            return JsonResponse({
                'success': False,
                'message': 'Category name is required'
            })
        
        # Check if category already exists
        if ProductCategory.objects.filter(name__iexact=name).exists():
            return JsonResponse({
                'success': False,
                'message': 'Category with this name already exists'
            })
        
        # Get parent category if specified
        parent = None
        if parent_id:
            try:
                parent = ProductCategory.objects.get(id=parent_id)
            except ProductCategory.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'message': 'Selected parent category does not exist'
                })
        
        # Create category
        category = ProductCategory.objects.create(
            name=name,
            description=description if description else None,
            parent=parent,
            image=image,
            created_by=request.user
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Category created successfully',
            'category': {
                'id': category.id,
                'name': category.name,
                'description': category.description,
                'parent_name': category.parent.name if category.parent else None
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error creating category: {str(e)}'
        })
