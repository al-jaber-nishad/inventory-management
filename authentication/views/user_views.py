from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib import messages
from authentication.forms.user import CustomLoginForm, CustomUserUpdateForm, UserForm, CustomUserCreationForm, UserProfileForm
from authentication.models import DeveloperApi, User, Transaction
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.db import transaction
from django.utils.dateparse import parse_date
from django.core.paginator import Paginator
import string
import random
import secrets

from django.contrib.auth import login, logout
from django.contrib.auth import get_user_model
from django.db.models import Q, Sum

# from sms.models import Package, SingleSms
from sms.utils.report_utils import export_to_pdf, export_transaction_report_to_excel
# from commons.utils import is_ajax


from django.db.models import Sum, Count, Q
from django.utils import timezone

from authentication.models import Customer, Supplier
from product.models import Product
from sales.models import Sale, SaleItem
from purchase.models import Purchase, PurchaseItem
from inventory.models import InventoryTransaction



@login_required
def home(request):
    """
    Dashboard view with aggregated data for inventory management system
    """
    
    # Get date range for filtering (current month)
    today = timezone.now().date()
    current_month_start = today.replace(day=1)
    
    # Purchase metrics
    purchase_due_total = Purchase.objects.filter(
        status__in=['confirmed', 'received']
    ).aggregate(total_due=Sum('due'))['total_due'] or Decimal('0')
    
    # Sales metrics
    sales_due_total = Sale.objects.filter(
        status__in=['confirmed', 'delivered']
    ).aggregate(total_due=Sum('due'))['total_due'] or Decimal('0')
    
    # Total sales amount (all time)
    total_sales_amount = Sale.objects.filter(
        status__in=['confirmed', 'delivered']
    ).aggregate(total=Sum('total'))['total'] or Decimal('0')
    
    # Count metrics
    total_customers = Customer.objects.filter(is_active=True).count()
    total_suppliers = Supplier.objects.filter(is_active=True).count()
    total_purchase_invoices = Purchase.objects.filter(status__in=['confirmed', 'received']).count()
    total_sales_invoices = Sale.objects.filter(status__in=['confirmed', 'delivered']).count()
    
    # Recently added products (last 10)
    recent_products = Product.objects.filter(is_active=True).order_by('-created_at')[:10]
    
    # Chart data - Monthly sales and purchase data for current year
    current_year = today.year
    monthly_data = []
    
    for month in range(1, 13):
        month_start = datetime(current_year, month, 1).date()
        if month == 12:
            month_end = datetime(current_year + 1, 1, 1).date()
        else:
            month_end = datetime(current_year, month + 1, 1).date()
        
        # Monthly sales
        monthly_sales = Sale.objects.filter(
            sale_date__gte=month_start,
            sale_date__lt=month_end,
            status__in=['confirmed', 'delivered']
        ).aggregate(total=Sum('total'))['total'] or Decimal('0')
        
        # Monthly purchases
        monthly_purchases = Purchase.objects.filter(
            purchase_date__gte=month_start,
            purchase_date__lt=month_end,
            status__in=['confirmed', 'received']
        ).aggregate(total=Sum('total'))['total'] or Decimal('0')
        
        monthly_data.append({
            'month': month_start.strftime('%b'),
            'sales': float(monthly_sales),
            'purchases': float(monthly_purchases)
        })
    
    # Low stock products (products with stock <= 10)
    low_stock_products = []
    for product in Product.objects.filter(is_active=True):
        if product.stock <= 10:
            low_stock_products.append({
                'product': product,
                'stock': product.stock
            })
    
    # Sort by stock level (lowest first)
    low_stock_products.sort(key=lambda x: x['stock'])
    
    context = {
        'purchase_due_total': purchase_due_total,
        'sales_due_total': sales_due_total,
        'total_sales_amount': total_sales_amount,
        'total_customers': total_customers,
        'total_suppliers': total_suppliers,
        'total_purchase_invoices': total_purchase_invoices,
        'total_sales_invoices': total_sales_invoices,
        'recent_products': recent_products,
        'monthly_data': monthly_data,
        'low_stock_products': low_stock_products[:10],  # Show top 10 low stock items
        'current_year': current_year,
    }
    
    return render(request, 'inventory/index.html', context)






# @login_required()
# def profile(request):
#   p_form = ProfileUpdateForm(instance=request.user)

#   context = {
#     'p_form': {}
#   }

#   return render(request, 'users/profile.html', context)


@login_required
def profile(request):
    user = request.user
    if request.method == 'POST':
        profile_picture = request.POST.get('profile_picture')
        print("profile_picture", profile_picture)

        form = UserProfileForm(request.POST, request.FILES, instance=user)
        if form.is_valid():
            user_instance = form.save(commit=False)
            user_instance.profile_picture = profile_picture
            user_instance.save()

            messages.success(request, 'Your profile has been updated successfully.')
            return redirect('profile')
        else:
            messages.error(request, 'Please correct the error below.')
    else:
        form = UserProfileForm(instance=user)
    
    return render(request, 'users/profile.html', {'form': form})


# @login_required
# def edit_profile(request, pk):
#   if request.method == 'POST':
#     # u_form = UserUpdateForm(request.POST, instance=request.user)
#     p_form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user.profile)

#     if p_form.is_valid():
#       # u_form.save()
#       p_form.save()

#       messages.success(request, 'You account has been updated!')
#       return redirect('profile')
      
#   else:
#     # if pk:
#     posts = Post.objects.filter(author_id=pk)
#     p_form = ProfileUpdateForm(instance=request.user.profile)
    
#   context = {
#     'p_form': p_form,
#     'posts': posts,

#   }
#   return render(request, 'profile.html', context)


def LoginView(request):
    if request.method == 'POST':
        form = CustomLoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')

            if username.startswith('+'):
                username = username
            elif not username.startswith('+') and username.isdigit():
                username = '+88' + username[-11:]

            UserModel = get_user_model()
            try:
                user = UserModel.objects.get(Q(primary_phone__exact=username) | Q(email__exact=username) | Q(username__exact=username))
                if not user.is_active:
                    messages.error(request, 'This account is not active anymore')
                    return redirect('login')
            except UserModel.DoesNotExist:
                messages.error(request, 'Wrong username or email or primary phone.')
            else:
                if user.check_password(password):
                    login(request, user)
                    # messages.success(request, 'You have successfully logged in.')
                    return redirect('home')  # Ensure 'home' is correctly defined in urls.py
                else:
                    messages.error(request, 'Wrong password.')
        else:
            print("Form errors: ", form.errors)
            messages.error(request, 'Please correct the error below.')
    else:
        form = CustomLoginForm()

    return render(request, 'registration/login.html', {'form': form})




@login_required
def LogoutView(request):
    successfull = logout(request)
    print("loging out", successfull)
    if successfull:
        return render(request, 'registration/login.html') 
    else:
        return redirect('home')




@login_required
def user_list(request):
    user_list = User.objects.all()
    if not request.user.role.name == "ADMIN":
        user_list = user_list.filter(owner_user=request.user)

    # Count the number of users with roles "Reseller" and "Client"
    reseller_count = user_list.filter(role__name='RESELLER').count()
    client_count = user_list.filter(role__name='CLIENT').count()
    print(user_list)
    context = {
        'user_list': user_list,
        'reseller_count': reseller_count,
        'client_count': client_count
    }
    return render(request, 'users/list.html', context)



@login_required
def reseller_list(request):
    user_list = User.objects.filter(role__name='RESELLER')
    if not request.user.role.name == "ADMIN":
        user_list = user_list.filter(owner_user=request.user)

    context = {
        'user_list': user_list,
    }
    return render(request, 'users/list.html', context)



@login_required
def client_list(request):
    user_list = User.objects.filter(role__name='CLIENT')
    if not request.user.role.name == "ADMIN":
        user_list = user_list.filter(owner_user=request.user)
        
    print(user_list)
    context = {
        'user_list': user_list,
    }
    return render(request, 'users/list.html', context)



@login_required
def user_detail(request, pk):
    user = get_object_or_404(User, pk=pk)  # Get specific user history
    if request.user.role.name != "ADMIN" and user.owner_user != request.user:
        messages.error(request, 'You do not have permission to update this user group.')
        return redirect('user_group_list')
    
    context = {'user': user}
    return render(request, 'users/detail.html', context)


@login_required
@transaction.atomic
def user_create(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST, request.FILES, request=request)
        try:
            if form.is_valid():
                user = form.save(commit=False)
                user.owner_user = request.user
                user.save()

                messages.success(request, 'User created successfully.')
                return redirect('user_list')
            else:
                # Capture field errors and non-field errors
                field_errors = {field: error for field, error in form.errors.items() if field != '__all__'}
                non_field_errors = form.non_field_errors()

                # Combine all errors into a single list
                errors = list(non_field_errors) + [error for field, error_list in field_errors.items() for error in error_list]

                return render(request, 'users/create.html', {
                    'form': form,
                    'errors': errors,
                })
        except Exception as e:
            transaction.set_rollback(True)
            return render(request, 'users/create.html', {
                'form': form,
                'errors': [str(e)],
            })
    else:
        form = CustomUserCreationForm(request=request)

    return render(request, 'users/create.html', {'form': form})



@login_required
def user_update(request, pk):
    user = get_object_or_404(User, pk=pk)
    
    if request.user.role.name != "ADMIN" and user.owner_user != request.user:
        messages.error(request, 'You do not have permission to update this user group.')
        return redirect('user_group_list')
    
    if request.method == 'POST':
        form = CustomUserUpdateForm(request.POST, request.FILES, request=request, instance=user)
        if form.is_valid():
            user = form.save(commit=False) 
            
            user.save()
            messages.success(request, 'User updated successfully.')
            return redirect('user_list')
        else:
            # Combine all errors into a single list with field names
            errors = []
            for field, error_list in form.errors.items():
                for error in error_list:
                    if field != '__all__':
                        errors.append(f"{form.fields[field].label}: {error}")
                    else:
                        errors.append(error)

            return render(request, 'users/detail.html', {
                'form': form,
                'errors': errors,
            })
    else:
        form = CustomUserUpdateForm(request=request, instance=user)

    return render(request, 'users/detail.html', {
        'form': form,
    })


@login_required
@require_POST
def user_change_password(request, pk):
    user = get_object_or_404(User, pk=pk)
    if request.user.role.name != 'ADMIN':
        return JsonResponse({'success': False, 'message': 'Permission denied.'}, status=403)
    
    new_password = request.POST.get('new_password')
    confirm_password = request.POST.get('confirm_password')
    
    if not new_password or not confirm_password:
        return JsonResponse({'success': False, 'message': 'Both password fields are required.'})
    
    if new_password != confirm_password:
        return JsonResponse({'success': False, 'message': 'Passwords do not match.'})
    
    user.set_password(new_password)
    user.save()
    
    return JsonResponse({'success': True, 'message': 'Password changed successfully.'})


@login_required
def user_delete(request, pk):
    user = get_object_or_404(User, pk=pk)
    if request.user.role.name != "ADMIN" and user.owner_user != request.user:
        messages.error(request, 'You do not have permission to delete this user.')
        return redirect('user_list')
    
    try:
        user.delete()
        print("deleted user")
        messages.success(request, 'User successfully deleted.')
    except Exception as e:
        print(str(e))
        messages.error(request, f'Error deleting user: {str(e)}')

    return redirect('user_list')

def get_user_balance(request, pk):
    user = get_object_or_404(User, id=pk)
    if user.package:
        data = {
            'is_prefix_based': user.package.prefix_based,
            'local_masking_balance': user.local_masking_balance,
            'local_non_masking_balance': user.local_non_masking_balance,
            'local_masking_message_amount': user.local_masking_message_amount,
            'local_non_masking_message_amount': user.local_non_masking_message_amount,
        }
    else:
        data = {}
    return JsonResponse(data)


def generate_transaction_id(length=10):
    characters = string.ascii_uppercase + string.digits
    transaction_id = ''.join(random.choice(characters) for _ in range(length))
    return transaction_id


def is_ajax(request):
    return request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest'


@login_required
def transaction_report(request):
    if is_ajax(request):
        print("request.META.get('HTTP_X_REQUESTED_WITH')", type(request.META.get('HTTP_X_REQUESTED_WITH')))
        print("ajax report is being generated")
    else:
        print("normal report is being generated")
    # Get filter inputs
    transaction_id = request.GET.get('transaction_id')
    recharged_by = request.GET.get('recharged_by')
    recharged_to = request.GET.get('recharged_to')
    filter_date_from = request.GET.get('date_from')
    filter_date_to = request.GET.get('date_to')
    export_format = request.GET.get('export_format', None)

    # Initial SMS list
    transactions = Transaction.objects.all()
    
    users = User.objects.all()
    senders = users.values_list('username', flat=True)
    user_groups = users.values_list('user_group__name', flat=True)

    # Apply filters
    if transaction_id and transaction_id != 'None':
        transactions = transactions.filter(transaction_id__icontains=transaction_id)
    if recharged_to and recharged_to != 'None':
        transactions = transactions.filter(recharged_to__username__icontains=recharged_to)
    if recharged_by and recharged_by != '':
        transactions = transactions.filter(recharged_by__username__icontains=recharged_by)
    if filter_date_from and filter_date_from!='None':
        date_from = datetime.strptime(filter_date_from, "%d-%m-%Y").strftime("%Y-%m-%d")
        transactions = transactions.filter(created_at__date__gte=date_from)
    if filter_date_to and filter_date_to!='None':
        date_to = datetime.strptime(filter_date_to, "%d-%m-%Y").strftime("%Y-%m-%d")
        transactions = transactions.filter(created_at__date__lte=date_to)

    filter_search_input = request.GET.get('search_input', None)
    print("filter_search_input", filter_search_input)
    if filter_search_input:
        transactions = transactions.filter(transaction_id__icontains=filter_search_input)
    
    if not request.user.role.name == 'ADMIN':
        transactions = transactions.filter(recharged_to=request.user)

    if export_format == 'pdf':
        return export_to_pdf(request, transactions, 'sms/sms/report/transactions_pdf_template.html')
    elif export_format == 'excel':
        return export_transaction_report_to_excel(request, transactions)

    # Pagination
    paginator = Paginator(transactions, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'users': users,
        'senders': senders,
        'user_groups': user_groups,
        'transactions': page_obj,
        'transaction_id': transaction_id,
        'recharged_by': recharged_by,
        'recharged_to': recharged_to,
        'filter_date_from': filter_date_from,
        'filter_date_to': filter_date_to,
        'filter_search_input': filter_search_input    
    }
    
    # Return the full page if not an AJAX request
    if is_ajax(request):
        print("ajax report is being generated")
        return render(request, 'sms/sms/report/transactions_ajax.html', context)

    # For AJAX requests, return only the necessary parts (table + pagination)
    return render(request, 'sms/sms/report/transactions.html', context)




# @login_required
# def developer_api(request):
#     developer_api_instance = DeveloperApi.objects.filter(user=request.user)

#     has_api = True
#     if len(developer_api_instance) <1:
#         has_api = False
    
#     context = {
#         'has_api': has_api,
#         'developer_api_instance': developer_api_instance
#     }
#     return render(request, 'users/developer_api.html', context)




# @login_required
# def generate_api_key(request):
#     developer_api_instance = DeveloperApi.objects.filter(user=request.user).first()

#     current_host = request.get_host()
#     base_url = f"http://{current_host}"

#     if developer_api_instance:
#         # Regenerate API key
#         developer_api_instance.api_key = secrets.token_urlsafe(32)
#         developer_api_instance.api_url = f"{base_url}/api/send?api_key={developer_api_instance.api_key}&type=text&phone=8801XXXXXXXXX&senderid=XXXX&message=YourMessage"
#         developer_api_instance.save()
#         has_api = True
#     else:
#         # Generate new API key
#         api_key = secrets.token_urlsafe(32)
#         api_url = f"{base_url}/api/send?api_key={api_key}&type=text&phone=8801XXXXXXXXX&senderid=XXXX&message=YourMessage"
#         DeveloperApi.objects.create(
#             user=request.user,
#             api_key=api_key,
#             api_url=api_url,
#             created_by=request.user,
#             updated_by=request.user
#         )
#         has_api = True

#     context = {
#         'has_api': has_api,
#         'developer_api_instance': DeveloperApi.objects.filter(user=request.user).first()
#     }
#     return render(request, 'users/developer_api.html', context)

@login_required
def generate_api_key(request):
    if request.method == 'POST':
        developer_api_instance, created = DeveloperApi.objects.get_or_create(user=request.user)
        api_key = secrets.token_urlsafe(32)  # Generate a secure API key
        api_url = f"{request.scheme}://{request.get_host()}/api/sendsms?api_key={api_key}&type=text&phone=8801XXXXXXXXX&senderid=YOUR_SENDER_ID&message=YourMessage"

        developer_api_instance.api_key = api_key
        developer_api_instance.api_url = api_url
        developer_api_instance.save()

        return JsonResponse({'success': True, 'message': 'API Key generated successfully.'})
    
    return JsonResponse({'success': False, 'message': 'Invalid request method.'})



@login_required
def regenerate_api_key(request):
    if request.method == 'POST':
        developer_api_instance = get_object_or_404(DeveloperApi, user=request.user)
        api_key = secrets.token_urlsafe(32)  # Generate a new secure API key
        api_url = f"{request.scheme}://{request.get_host()}/api/sendsms?api_key={api_key}&type=text&phone=8801XXXXXXXXX&senderid=YOUR_SENDER_ID&message=YourMessage"

        developer_api_instance.api_key = api_key
        developer_api_instance.api_url = api_url
        developer_api_instance.save()

        return JsonResponse({'success': True, 'message': 'API Key regenerated successfully.'})
    
    return JsonResponse({'success': False, 'message': 'Invalid request method.'})



@login_required
def developer_api(request):
    developer_api_instance = DeveloperApi.objects.filter(user=request.user).first()

    has_api = developer_api_instance is not None

    context = {
        'has_api': has_api,
        'developer_api_instance': developer_api_instance
    }
    return render(request, 'users/developer_api.html', context)