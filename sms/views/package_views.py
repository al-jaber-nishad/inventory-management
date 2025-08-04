# views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from sms.models import Package
from sms.forms import PackageForm



@login_required
def package_list(request):
    package_list = Package.objects.all()  # Fetch all package history
    if not request.user.role.name == 'ADMIN':
        package_list = package_list.filter(owner_user=request.user)
    print(package_list)
    context = {'package_list': package_list}
    return render(request, 'sms/package/list.html', context)


@login_required
def package_create(request):
    if request.method == 'POST':
        form = PackageForm(request.POST)
        if form.is_valid():
            package = form.save(commit=False)
            package.owner_user = request.user
            package.save()

            print("form", form)
            messages.success(request, 'Package created successfully.')
            return redirect('package_list')
    else:
        form = PackageForm()
    return render(request, 'sms/package/create.html', {'form': form})

@login_required
def package_update(request, pk):
    package = get_object_or_404(Package, pk=pk)
    if request.method == 'POST':
        form = PackageForm(request.POST, instance=package)
        if form.is_valid():
            package = form.save(commit=False)
            package.save()
            messages.success(request, 'Package updated successfully.')
            return redirect('package_list')
    else:
        form = PackageForm(instance=package)
    return render(request, 'sms/package/detail.html', {'form': form})

@login_required
def package_delete(request, pk):
    package = get_object_or_404(Package, pk=pk)
    if request.method == 'POST':
        package.delete()
        messages.success(request, 'Package deleted successfully.')
        return redirect('package_list')
    return render(request, 'sms/package/confirm_delete.html', {'package': package})
