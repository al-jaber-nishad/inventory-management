from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse

from authentication.models import User
from sms.models import Package
from sms.forms import AssignedPackageForm


@login_required
def assigned_package_list(request):
    assigned_package_list = User.objects.all()  # Fetch all assigned_package history
    if not request.user.role.name == "ADMIN":
        assigned_package_list = assigned_package_list.filter(owner_user=request.user)

    
    print(assigned_package_list)
    context = {'assigned_package_list': assigned_package_list}
    return render(request, 'sms/assigned_package/list.html', context)



@login_required
def assigned_package_detail(request, pk):
    assigned_package = get_object_or_404(User, pk=pk)
    if request.user.role.name != "ADMIN":
        messages.error(request, 'You do not have permission to update this user group.')
        return redirect('assigned_package_list')
    
    context = {'assigned_package': assigned_package}
    return render(request, 'sms/assigned_package/detail.html', context)


@login_required
def assigned_package_create(request):
    if request.method == 'POST':
        print("this is a post")
        form = AssignedPackageForm(request.POST, request=request)
        if form.is_valid():
            form.save()
            print("after saving")
            messages.success(request, 'Package been assigned successfully.')
            return redirect('assigned_package_list')
        else:
            # Capture field errors and non-field errors
            field_errors = {field: error for field, error in form.errors.items() if field != '__all__'}
            non_field_errors = form.non_field_errors()

            # Combine all errors into a single list
            errors = list(non_field_errors) + [error for field, error_list in field_errors.items() for error in error_list]
            
            return render(request, 'sms/assigned_package/create.html', {
                'form': form,
                'errors': errors,
            })
    else:
        form = AssignedPackageForm(request=request)

    return render(request, 'sms/assigned_package/create.html', {'form': form})




@login_required
def assigned_package_update(request, pk):
    assigned_package = get_object_or_404(User, pk=pk)
    if request.user.role.name != "ADMIN":
        messages.error(request, 'You do not have permission to update this user group.')
        return redirect('assigned_package_list')
    
    if request.method == 'POST':
        form = AssignedPackageForm(request.POST, instance=assigned_package)
        if form.is_valid():
            form.save()
            return redirect('assigned_package_list')  # Redirect to list view after update
    else:
        form = AssignedPackageForm(instance=assigned_package)
        
    context = {'form': form, 'assigned_package': assigned_package}
    return render(request, 'sms/assigned_package/detail.html', context)


@login_required
def assigned_package_delete(request, pk):
    assigned_package = get_object_or_404(User, pk=pk)
    if request.user.role.name != "ADMIN":
        messages.error(request, 'You do not have permission to update this user group.')
        return redirect('assigned_package_list')
    
    if request.method == 'POST':
        assigned_package.delete()
        messages.success(request, 'AssignedPackage successfully deleted.')
        return redirect('assigned_package_list')
    context = {'assigned_package': assigned_package}
    return render(request, 'sms/assigned_package/confirm_delete.html', context)