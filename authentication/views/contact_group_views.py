from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from authentication.models import Contact, ContactGroup
from authentication.forms.user import ContactGroupForm
from authentication.serializers import ContactGroupSerializer, ContactGroupListSerializer
from authentication.filters import ContactGroupFilter
from django.db import transaction
import pandas as pd

# Create your views here.



@login_required
def contact_group_list(request):
    contact_group_list = ContactGroup.objects.all()  # Fetch all contact_group history
    if not request.user.role.name == 'ADMIN':
        contact_group_list = contact_group_list.filter(owner_user=request.user)
    print(contact_group_list)
    context = {'contact_group_list': contact_group_list}
    return render(request, 'authentication/contact_group/list.html', context)


@login_required
@transaction.atomic
def contact_group_create(request):
    if request.method == 'POST':
        form = ContactGroupForm(request.POST)
        if form.is_valid():
            contact_group = form.save(commit=False)
            contact_group.owner_user = request.user
            contact_group.save()

            excel_file = request.FILES.get('excel_file', None)
            if excel_file:
                response, message = import_contacts(request, str(contact_group.name))
                if not response:
                    messages.error(request, message)
                    contact_group.delete()
                    return redirect('contact_group_list')

            messages.success(request, 'ContactGroup created successfully.')
            return redirect('contact_group_list')
    else:
        form = ContactGroupForm()
    return render(request, 'authentication/contact_group/create.html', {'form': form})


@login_required
@transaction.atomic
def contact_group_update(request, pk):
    contact_group = get_object_or_404(ContactGroup, pk=pk)
    contacts = Contact.objects.filter(contact_group=contact_group)
    form = ContactGroupForm(instance=contact_group)

    if request.method == 'POST':
        form = ContactGroupForm(request.POST, instance=contact_group)
        if form.is_valid():
            contact_group = form.save(commit=False)
            contact_group.save()

            excel_file = request.FILES.get('excel_file', None)
            if excel_file:
                
                response, message = import_contacts(request, str(contact_group.name))
                if not response:
                    messages.error(request, message)
                    contact_group.delete()
                    return redirect('contact_group_list')
            
            messages.success(request, 'ContactGroup updated successfully.')
            return redirect('contact_group_list')
    else:
        field_errors = {field: error for field, error in form.errors.items() if field != '__all__'}
        non_field_errors = form.non_field_errors()

        # Combine all errors into a single list
        errors = list(non_field_errors) + [error for field, error_list in field_errors.items() for error in error_list]

        return render(request, 'authentication/contact_group/detail.html', {
            'form': form,
            'messages': errors,
            'contacts': contacts,
        })
    return render(request, 'authentication/contact_group/detail.html', {'form': form, 'contacts': contacts})

@login_required
def contact_group_delete(request, pk):
    contact_group = get_object_or_404(ContactGroup, pk=pk)
    if request.method == 'POST':
        Contact.objects.filter(contact_group=pk).delete()
        contact_group.delete()

        messages.success(request, 'ContactGroup deleted successfully.')
        return redirect('contact_group_list')
    return render(request, 'authentication/contact_group/confirm_delete.html', {'contact_group': contact_group})



@transaction.atomic
def import_contacts(request, group_name):
    
    excel_file = request.FILES['excel_file']
    
    try:
        df = pd.read_excel(excel_file)
    except Exception as e:
        return False, f"Error reading Excel file: {str(e)}"

    expected_columns = ['NAME', 'CONTACT']
    if not all(col in df.columns for col in expected_columns):
        return False, "Excel file must contain following columns: NAME, CONTACT"

    for _, row in df.iterrows():
        try:
            name = row['NAME']
            contact_no = row['CONTACT']
            contact_group = None

            contact_no = str(contact_no).replace(" ", "")

            if not contact_no or contact_no == '' or len(str(contact_no)) < 9:
                continue

            if not ContactGroup.objects.filter(name=group_name, owner_user=request.user).exists():
                contact_group = ContactGroup.objects.create(name=group_name, owner_user=request.user)
            else:
                contact_group = ContactGroup.objects.get(name=group_name, owner_user=request.user)

            Contact.objects.get_or_create(
                contact_no='8801'+contact_no[-9:],
                contact_group=contact_group,
                defaults={
                    'name' : name,
                    'owner_user' : request.user,
                    'created_by': request.user
                }
            )
        except Exception as e:
            transaction.rollback(True)

    return True, f"Contacts imported successfully"
