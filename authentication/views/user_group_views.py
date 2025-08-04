from django.contrib import messages
from django.urls import reverse_lazy
from django.db.models.deletion import RestrictedError
from authentication.forms import  UserGroupForm
from authentication.models import User, UserGroup
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404



@login_required
def user_group_list(request):
    user_group_list = UserGroup.objects.all()  # Fetch all user_group history
    if not request.user.role.name == "ADMIN":
        user_group_list = user_group_list.filter(owner_user=request.user)
        
    print(user_group_list)
    context = {'user_group_list': user_group_list}
    return render(request, 'authentication/user_groups/list.html', context)



@login_required
def user_group_detail(request, pk):
    user_group = get_object_or_404(UserGroup, pk=pk)  # Get specific user_group history
    if request.user.role.name != "ADMIN" and user_group.owner_user != request.user:
        messages.error(request, 'You do not have permission to update this user group.')
        return redirect('user_group_list')
    
    context = {'user_group': user_group}
    return render(request, 'authentication/user_groups/detail.html', context)


@login_required
def user_group_create(request):
    if request.method == 'POST':
        print('------------------')
        form = UserGroupForm(request.POST)
        if form.is_valid():
            user_group = form.save(commit=False) 
            user_group.owner_user = request.user
            user_group.save()
            return redirect('user_group_list')  # Redirect to list view after creation

    else:
        form = UserGroupForm()
    context = {'form': form}
    return render(request, 'authentication/user_groups/create.html', context)


@login_required
def user_group_update(request, pk):
    user_group = get_object_or_404(UserGroup, pk=pk)
    if request.user.role.name != "ADMIN" and user_group.owner_user != request.user:
        messages.error(request, 'You do not have permission to update this user group.')
        return redirect('user_group_list')
    
    if request.method == 'POST':
        form = UserGroupForm(request.POST, instance=user_group)
        if form.is_valid():
            form.save()
            return redirect('user_group_list')  # Redirect to list view after update
    else:
        form = UserGroupForm(instance=user_group)
    context = {'form': form}
    return render(request, 'authentication/user_groups/detail.html', context)


@login_required
def user_group_delete(request, pk):
    user_group = get_object_or_404(UserGroup, pk=pk)
    if request.user.role.name != "ADMIN" and user_group.owner_user != request.user:
        messages.error(request, 'You do not have permission to update this user group.')
        return redirect('user_group_list')
    
    if request.method == 'POST':
        try:
            user_group.delete()
            messages.success(request, 'UserGroup successfully deleted.')
            return redirect('user_group_list')
        except RestrictedError as e:
            messages.error(request, f'Cannot delete this UserGroup because it is referenced by other records: {e.args[1]}')
            return redirect('user_group_list')
        
    context = {'user_group': user_group}
    return render(request, 'authentication/user_groups/confirm_delete.html', context)