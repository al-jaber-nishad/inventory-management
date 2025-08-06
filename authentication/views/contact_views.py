from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from authentication.models import Contact, ContactGroup
from authentication.forms.user import ContactForm
from authentication.serializers import ContactSerializer, ContactListSerializer
from authentication.filters import ContactFilter
from django.db.models import Q
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from commons.utils import is_ajax

# Create your views here.


@login_required
def contact_list(request):
    contact_list = Contact.objects.select_related(
        'owner_user__owner_user',
        'contact_group'
    )

    if not request.user.role.name == 'ADMIN':
        contact_list = contact_list.filter(owner_user=request.user)

    filter_search_input = request.GET.get('search_input', None)
    print("filter_search_input", filter_search_input)
    if filter_search_input:
        contact_list = contact_list.filter(Q(contact_no__icontains=filter_search_input) | Q(name__icontains=filter_search_input))
    
    # Pagination
    paginator = Paginator(contact_list, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'contact_list': page_obj,
        'filter_search_input': filter_search_input    
    }
    
    # Return the full page if not an AJAX request
    if not is_ajax(request):
        return render(request, 'authentication/contact/list.html', context)
    
    # For AJAX requests, return only the necessary parts (table + pagination)
    return render(request, 'authentication/contact/contact_list_ajax.html', context)


@login_required
def django_contact_list(request):
    contact_list = Contact.objects.all()
    paginator = Paginator(contact_list, 25)  # Show 25 contacts per page.

    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)
    return render(request, "authentication/contact/django_table_list.html", {"page_obj": page_obj})




@login_required
def contact_create(request):
    if request.method == 'POST':
        form = ContactForm(request.POST, request=request)
        if form.is_valid():
            name = form.cleaned_data.get('name')
            contact_no = str(form.cleaned_data.get('contact_no'))
            contact_group = form.cleaned_data.get('contact_group')

            if not contact_no or contact_no=='' or len(contact_no)<9:
                return render(request, 'authentication/contact/create.html', {
                    'form': form,
                    'messages': ['Please fill up the form correctly!'],
                    'is_error': True
                }, status=400)

            Contact.objects.get_or_create(
                contact_no='8801'+contact_no[-9:],
                contact_group=contact_group,
                defaults={
                    'name' : name,
                    'owner_user' : request.user,
                    'created_by': request.user
                }
            )
            
            messages.success(request, 'Contact created successfully.')
            return redirect('contact_list')
        else:
            # Capture field errors and non-field errors
            field_errors = {field: error for field, error in form.errors.items() if field != '__all__'}
            non_field_errors = form.non_field_errors()

            # Combine all errors into a single list
            errors = list(non_field_errors) + [error for field, error_list in field_errors.items() for error in error_list]

            return render(request, 'authentication/contact/create.html', {
                'form': form,
                'messages': errors,
                'is_error': True
            }, status=400)
    else:
        form = ContactForm(request=request)
    return render(request, 'authentication/contact/create.html', {'form': form})

@login_required
def contact_update(request, pk):
    contact = get_object_or_404(Contact, pk=pk)
    if request.method == 'POST':
        form = ContactForm(request.POST, instance=contact, request=request)
        if form.is_valid():
            name = form.cleaned_data.get('name')
            contact_no = str(form.cleaned_data.get('contact_no'))
            contact_group = form.cleaned_data.get('contact_group')

            if not contact_no or contact_no=='' or len(contact_no)<9:
                return render(request, 'authentication/contact/detail.html', {
                    'form': form,
                    'messages': ['Please fill up the form correctly!'],
                    'is_error': True
                }, status=400)

            # Get the object and update information
            contact = Contact.objects.get(id=pk)
            contact.name=name
            contact.contact_no='8801'+contact_no[-9:]
            contact.contact_group=contact_group
            contact.save()

            messages.success(request, 'Contact updated successfully.')
            return redirect('contact_list')
        else:
            # Capture field errors and non-field errors
            field_errors = {field: error for field, error in form.errors.items() if field != '__all__'}
            non_field_errors = form.non_field_errors()

            # Combine all errors into a single list
            errors = list(non_field_errors) + [error for field, error_list in field_errors.items() for error in error_list]

            return render(request, 'authentication/contact/detail.html', {
                'form': form,
                'messages': errors,
                'is_error': True
            }, status=400)
    else:
        form = ContactForm(instance=contact, request=request)
    return render(request, 'authentication/contact/detail.html', {'form': form})

@login_required
def contact_delete(request, pk):
    contact = get_object_or_404(Contact, pk=pk)
    if request.method == 'POST':
        contact.delete()
        messages.success(request, 'Contact deleted successfully.')
        return redirect('contact_list')
    return render(request, 'authentication/contact/confirm_delete.html', {'contact': contact})
