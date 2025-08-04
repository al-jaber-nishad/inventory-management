from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse

from authentication.models import User
from sms.models import AssignSmsAPI, SmsAPI
from sms.forms import AssignSmsAPIForm


@login_required
def assigned_sms_api_list(request):
    assigned_sms_api_list = AssignSmsAPI.objects.all().order_by('user__username', 'priority')  # Fetch all assigned_sms_api history
    
    print(assigned_sms_api_list)
    context = {'assigned_sms_api_list': assigned_sms_api_list}
    return render(request, 'sms/assigned_sms_api/list.html', context)



@login_required
def assigned_sms_api_detail(request, pk):
    assigned_sms_api = get_object_or_404(AssignSmsAPI, pk=pk)
    if request.user.role.name != "ADMIN":
        messages.error(request, 'You do not have permission to update this user group.')
        return redirect('assigned_sms_api_list')
    
    context = {'assigned_sms_api': assigned_sms_api}
    return render(request, 'sms/assigned_sms_api/detail.html', context)


@login_required
def assigned_sms_api_create(request):
    if request.method == 'POST':
        print("this is a post")
        form = AssignSmsAPIForm(request.POST)
        if form.is_valid():
            assign_sms_api = form.save(commit=False)
            assign_sms_api.save()
            user = form.cleaned_data['user']

            # Update the priority list properly
            priority = form.cleaned_data.get('priority')
            same_priority_api = AssignSmsAPI.objects.filter(user=user, priority=priority).exclude(pk=assign_sms_api.pk)
            if same_priority_api.exists():
                greater_priority_apis = AssignSmsAPI.objects.filter(user=user, priority__gte=priority).exclude(pk=assign_sms_api.pk)
                for api in greater_priority_apis:
                    api.priority += 1
                    api.save()

            messages.success(request, 'SMS API has been assigned successfully.')
            return redirect('assigned_sms_api_list')
        else:
            messages.error(request, form.errors)
    else:
        form = AssignSmsAPIForm()

    return render(request, 'sms/assigned_sms_api/create.html', {'form': form})



@login_required
def assigned_sms_api_update(request, pk):
    assigned_sms_api = get_object_or_404(AssignSmsAPI, pk=pk)
    assign_sms_apis = AssignSmsAPI.objects.all().exclude(pk=pk)
    old_priority = assigned_sms_api.priority
    if request.user.role.name != "ADMIN":
        messages.error(request, 'You do not have permission to update this user group.')
        return redirect('assigned_sms_api_list')
    
    if request.method == 'POST':
        form = AssignSmsAPIForm(request.POST, instance=assigned_sms_api)
        if form.is_valid():
            # Update the priority list properly
            new_priority = form.cleaned_data.get('priority')
            same_priority_api = assign_sms_apis.filter(user=assigned_sms_api.user, priority=new_priority)
            if same_priority_api.exists():
                if new_priority < old_priority:
                    greater_priority_apis = assign_sms_apis.filter(user=assigned_sms_api.user, priority__gte=new_priority, priority__lte=old_priority)
                    for api in greater_priority_apis:
                        api.priority += 1
                        api.save()
                else:
                    lesser_priority_apis = assign_sms_apis.filter(user=assigned_sms_api.user, priority__lte=new_priority, priority__gte=old_priority)
                    for api in lesser_priority_apis:
                        api.priority -= 1
                        api.save()

            form.save()
            return redirect('assigned_sms_api_list') 
    else:
        form = AssignSmsAPIForm(instance=assigned_sms_api)
    context = {'form': form}
    return render(request, 'sms/assigned_sms_api/detail.html', context)


@login_required
def assigned_sms_api_delete(request, pk):
    assigned_sms_api = get_object_or_404(AssignSmsAPI, pk=pk)
    if request.user.role.name != "ADMIN":
        messages.error(request, 'You do not have permission to update this user group.')
        return redirect('assigned_sms_api_list')
    
    if request.method == 'POST':
        assigned_sms_api.delete()
        messages.success(request, 'AssignSmsAPI successfully deleted.')
        return redirect('assigned_sms_api_list')
    context = {'assigned_sms_api': assigned_sms_api}
    return render(request, 'sms/assigned_sms_api/confirm_delete.html', context)






@login_required
def assign_sms_api(request):
    if request.method == 'POST':
        form = AssignSmsAPIForm(request.POST)
        if form.is_valid():
            user = form.cleaned_data['user']
            user_obj = User.objects.get(id=user)
            sms_apis = form.cleaned_data['sms_api']
            is_active = form.cleaned_data['is_active']

            sms_api_priorities = request.POST.getlist('sms_api_priorities')

            for priority_data in sms_api_priorities:
                sms_api_id, priority = priority_data.split(':')
                sms_api = SmsAPI.objects.get(pk=sms_api_id)
                AssignSmsAPI.objects.create(
                    user=user_obj,
                    sms_api=sms_api,
                    priority=int(priority),
                    is_active=is_active,
                    created_by=request.user,
                    updated_by=request.user
                )
            messages.success(request, 'SMS APIs have been assigned successfully.')
            return redirect('assign_sms_api')
        else:
            messages.error(request, 'There was an error assigning SMS APIs.')
    else:
        form = AssignSmsAPIForm()

    return render(request, 'sms/assign_sms_api.html', {'form': form})



@login_required
def update_priority(request):
    if request.method == 'POST':
        data = request.POST.getlist('priority[]')
        for index, id in enumerate(data):
            assign_sms_api = get_object_or_404(AssignSmsAPI, id=id)
            assign_sms_api.priority = index
            assign_sms_api.save(update_fields=['priority'])
        return JsonResponse({'status': 'success'})
    return JsonResponse({'status': 'fail'}, status=400)

