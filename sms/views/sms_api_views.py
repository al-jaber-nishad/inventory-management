# from django.shortcuts import render, redirect, get_object_or_404
# from django.contrib import messages
# from django.contrib.auth.decorators import login_required

# from sms.models import SmsAPI
# from sms.forms import SmsAPIForm


# @login_required
# def sms_api_list(request):
#     sms_api_list = SmsAPI.objects.all()  # Fetch all sms_api history
#     print(sms_api_list)
#     context = {'sms_api_list': sms_api_list}
#     return render(request, 'sms/sms_api/list.html', context)



# @login_required
# def sms_api_detail(request, pk):
#     sms_api = get_object_or_404(SmsAPI, pk=pk)
#     if request.user.role.name != "ADMIN":
#         messages.error(request, 'You do not have permission to update this user group.')
#         return redirect('sms_api_list')
    
#     context = {'sms_api': sms_api}
#     return render(request, 'sms/sms_api/detail.html', context)


# @login_required
# def sms_api_create(request):
#     if request.method == 'POST':
#         form = SmsAPIForm(request.POST)
#         if form.is_valid():
#             priority = form.cleaned_data.get('priority')
#             form.save()

#             same_priority_api = SmsAPI.objects.filter(priority=priority)
#             if same_priority_api.exists():
#                 print("Yes, it exists..")
#                 greater_priority_apis = SmsAPI.objects.filter(priority__gte=priority)
#                 print("greater values", greater_priority_apis)
#                 for api in greater_priority_apis:
#                     print("api", api, api.priority)
#                     api.priority += 1
#                     api.save()
#                     print("api", api, api.priority)


#             return redirect('sms_api_list')
#     else:
#         form = SmsAPIForm()
#     context = {'form': form}
#     return render(request, 'sms/sms_api/create.html', context)


# @login_required
# def sms_api_update(request, pk):
#     sms_api = get_object_or_404(SmsAPI, pk=pk)
#     if request.method == 'POST':
#         form = SmsAPIForm(request.POST, instance=sms_api)
#         if form.is_valid():
#             print("form", form)
#             priority = form.cleaned_data.get('priority')
#             form.save()
#             print("After saving the form")
#             return redirect('sms_api_list')

#             # same_priority_api = SmsAPI.objects.filter(priority=priority)
#             # if same_priority_api.exists():
#             #     greater_priority_apis = SmsAPI.objects.filter(priority__gte=priority)
#             #     for api in greater_priority_apis:
#             #         api.priority += 1
#             #         api.save()
#         else:
#             print("error -------------------")
#             # Capture field errors and non-field errors
#             field_errors = {field: error for field, error in form.errors.items() if field != '__all__'}
#             non_field_errors = form.non_field_errors()

#             # Combine all errors into a single list
#             errors = list(non_field_errors) + [error for field, error_list in field_errors.items() for error in error_list]
            
#             return render(request, 'sms/sms_api/detail.html', {
#                 'form': form,
#                 'errors': errors,
#             })
#     else:
#         form = SmsAPIForm(instance=sms_api)
#     context = {'form': form}
#     return render(request, 'sms/sms_api/detail.html', context)



# # @login_required
# # def sms_api_update(request, pk):
# #     sms_api = get_object_or_404(SmsAPI, pk=pk)
# #     if request.user.role.name != "ADMIN":
# #         messages.error(request, 'You do not have permission to update this user group.')
# #         return redirect('sms_api_list')
    
# #     if request.method == 'POST':
# #         form = SmsAPIForm(request.POST, instance=sms_api)
# #         print("form", form)
# #         if form.is_valid():
# #             form.save()
# #             priority = form.cleaned_data.get('priority')
# #             print("new priority", priority)
# #             print("saved priority", sms_api.priority)

# #             same_priority_api = SmsAPI.objects.filter(priority=priority)
# #             if same_priority_api.exists():
# #                 print("Yes, it exists..")
# #                 greater_priority_apis = SmsAPI.objects.filter(priority__gte=priority)
# #                 print("greater values", greater_priority_apis)
# #                 for api in greater_priority_apis:
# #                     print("api", api, api.priority)
# #                     api.priority += 1
# #                     api.save()
# #                     print("api", api, api.priority)
# #             print("sms_api", sms_api, sms_api.priority)
# #             return redirect('sms_api_list')  # Redirect to list view after update
# #         else:
# #             print("err", form.errors)
# #             messages.error(form.errors)
# #     else:
# #         form = SmsAPIForm(instance=sms_api)
# #     context = {'form': form}
# #     return render(request, 'sms/sms_api/detail.html', context)


# @login_required
# def sms_api_delete(request, pk):
#     sms_api = get_object_or_404(SmsAPI, pk=pk)
#     if request.user.role.name != "ADMIN":
#         messages.error(request, 'You do not have permission to update this user group.')
#         return redirect('sms_api_list')
    
#     if request.method == 'POST':
#         sms_api.delete()
#         messages.success(request, 'SmsAPI successfully deleted.')
#         return redirect('sms_api_list')
#     context = {'sms_api': sms_api}
#     return render(request, 'sms/sms_api/confirm_delete.html', context)



# views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from sms.models import AssignSmsAPI, SmsAPI
from sms.forms import SmsAPIForm



@login_required
def sms_api_list(request):
    sms_api_list = SmsAPI.objects.all()  # Fetch all sms_api history
    if not request.user.role.name == 'ADMIN':
        assigned_api_list = AssignSmsAPI.objects.filter(user=request.user).values_list('id', flat=True)

        sms_api_list = sms_api_list.filter(id__in=assigned_api_list)
    print(sms_api_list)
    context = {'sms_api_list': sms_api_list}
    return render(request, 'sms/sms_api/list.html', context)


@login_required
def sms_api_create(request):
    if request.method == 'POST':
        form = SmsAPIForm(request.POST)
        if form.is_valid():
            sms_api = form.save(commit=False)
            sms_api.save()

            # Update the priority list properly
            priority = form.cleaned_data.get('priority')
            same_priority_api = SmsAPI.objects.filter(priority=priority).exclude(pk=sms_api.pk)
            if same_priority_api.exists():
                greater_priority_apis = SmsAPI.objects.filter(priority__gte=priority).exclude(pk=sms_api.pk)
                for api in greater_priority_apis:
                    api.priority += 1
                    api.save()

            messages.success(request, 'SmsAPI created successfully.')
            return redirect('sms_api_list')
    else:
        form = SmsAPIForm()
    return render(request, 'sms/sms_api/create.html', {'form': form})

@login_required
def sms_api_update(request, pk):
    sms_api = get_object_or_404(SmsAPI, pk=pk)
    old_priority = sms_api.priority
    if request.method == 'POST':
        form = SmsAPIForm(request.POST, instance=sms_api)
        if form.is_valid():
            sms_api = form.save(commit=False)
            print("sms api", sms_api)
            sms_api.save()

            # Update the priority list properly
            new_priority = form.cleaned_data.get('priority')
            same_priority_api = SmsAPI.objects.filter(priority=new_priority).exclude(pk=pk)
            if same_priority_api.exists():
                if new_priority < old_priority:
                    greater_priority_apis = SmsAPI.objects.filter(priority__gte=new_priority, priority__lte=old_priority).exclude(pk=pk)
                    for api in greater_priority_apis:
                        api.priority += 1
                        api.save()
                else:
                    greater_priority_apis = SmsAPI.objects.filter(priority__lte=new_priority, priority__gte=old_priority).exclude(pk=pk)
                    for api in greater_priority_apis:
                        api.priority -= 1
                        api.save()

            messages.success(request, 'SmsAPI updated successfully.')
            return redirect('sms_api_list')
    else:
        form = SmsAPIForm(instance=sms_api)
    return render(request, 'sms/sms_api/detail.html', {'form': form})


@login_required
def sms_api_delete(request, pk):
    sms_api = get_object_or_404(SmsAPI, pk=pk)
    if request.method == 'POST':
        sms_api.delete()
        messages.success(request, 'SmsAPI deleted successfully.')
        return redirect('sms_api_list')
    return render(request, 'sms/sms_api/confirm_delete.html', {'sms_api': sms_api})
