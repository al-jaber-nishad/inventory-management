from decimal import Decimal
from celery import shared_task
from authentication.models import User
from sms.models import BalanceLog


def decrease_user_balance(user_id, msg_part_count):
    user = User.objects.get(id=user_id)
    is_prefix_based = user.package.prefix_based
    
    # Balance log 
    BalanceLog.objects.create(
        sender=user,
        current_balance=user.local_non_masking_message_amount,
        after_operation_balance=Decimal(user.local_non_masking_message_amount-msg_part_count),
        number_of_sms_count=msg_part_count,
        note="decreasing balance"
    )

    is_low_balance = False
    if is_prefix_based:
        if user.region_type == 'local':
            if (user.local_non_masking_balance <= Decimal(msg_part_count * user.package.non_masking_national_msg_charge)) or (user.owner_user.local_non_masking_balance <= Decimal(msg_part_count * user.package.non_masking_national_msg_charge)):
                is_low_balance = True
            else:
                user.local_non_masking_balance -= Decimal(msg_part_count * user.package.non_masking_national_msg_charge)
                user.owner_user.local_non_masking_balance -= Decimal(msg_part_count * user.package.non_masking_national_msg_charge)
        elif user.region_type == 'international':
            if (user.internation_non_masking_balance <= Decimal(msg_part_count * user.package.non_masking_international_msg_charge)) or (user.owner_user.internation_non_masking_balance <= Decimal(msg_part_count * user.package.non_masking_international_msg_charge)):
                is_low_balance=True
            else:
                user.internation_non_masking_balance -= Decimal(msg_part_count * user.package.non_masking_international_msg_charge)
                user.owner_user.internation_non_masking_balance -= Decimal(msg_part_count * user.package.non_masking_international_msg_charge)
    else:
        if user.region_type == 'local':
            if (user.local_non_masking_message_amount <= msg_part_count) or (user.owner_user.local_non_masking_message_amount <= msg_part_count):
                is_low_balance=True
            else:
                user.local_non_masking_message_amount -= Decimal(msg_part_count)
                user.owner_user.local_non_masking_message_amount -= Decimal(msg_part_count)
        elif user.region_type == 'international':
            if (user.internation_non_masking_message_amount <= msg_part_count) or (user.owner_user.internation_non_masking_message_amount <= msg_part_count):
                is_low_balance=True
            else:
                user.internation_non_masking_message_amount -= Decimal(msg_part_count)
                user.owner_user.internation_non_masking_message_amount -= Decimal(msg_part_count)

    # *TODO: Add masking balance check 
    
    if not is_low_balance:
        user.save()
        user.owner_user.save()
        return is_low_balance

    return is_low_balance


@shared_task
def increase_user_balance(user_id, msg_part_count):
    user = User.objects.get(id=user_id)
    is_prefix_based = user.package.prefix_based

    # Balance log 
    BalanceLog.objects.create(
        sender=user,
        current_balance=user.local_non_masking_message_amount,
        after_operation_balance=Decimal(user.local_non_masking_message_amount+msg_part_count),
        number_of_sms_count=msg_part_count,
        note="increasing balance"
    )

    print("before: ", user.local_non_masking_message_amount)
    if is_prefix_based:
        if user.region_type == 'local':
            user.local_non_masking_balance += Decimal(msg_part_count * user.package.non_masking_national_msg_charge)
            user.owner_user.local_non_masking_balance += Decimal(msg_part_count * user.package.non_masking_national_msg_charge)
        elif user.region_type == 'international':
            user.internation_non_masking_balance += Decimal(msg_part_count * user.package.non_masking_international_msg_charge)
            user.owner_user.internation_non_masking_balance += Decimal(msg_part_count * user.package.non_masking_international_msg_charge)
    else:
        if user.region_type == 'local':
            user.local_non_masking_message_amount += Decimal(msg_part_count)
            user.owner_user.local_non_masking_message_amount += Decimal(msg_part_count)
        elif user.region_type == 'international':
            user.internation_non_masking_message_amount += Decimal(msg_part_count)
            user.owner_user.internation_non_masking_message_amount += Decimal(msg_part_count)

    user.save()
    user.owner_user.save()
    print("after: ", user.local_non_masking_message_amount)

