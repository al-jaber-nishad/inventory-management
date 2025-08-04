import os
import base64
import pandas as pd
from io import BytesIO
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.safestring import mark_safe
from weasyprint import HTML
from django.http import HttpResponse


def img_base64(img_path):
    image_path = os.path.join(settings.BASE_DIR, 'static', img_path)
    with open(image_path, 'rb') as image_file:
        base64_string = base64.b64encode(image_file.read()).decode('utf-8')
        return mark_safe(f'data:image/png;base64,{base64_string}')


def export_to_pdf(request, instances, template_path):
    logo_image = img_base64('img/full-logo.png')
    html_string = render_to_string(template_path, {'request': request, 'instances': instances, 'logo_image': logo_image})
    html = HTML(string=html_string)
    result = html.write_pdf()

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'inline; filename=report.pdf'
    response.write(result)
    return response


def export_history_report_to_excel(request, instances):
    data = []
    columns = ['Receiver', 'Text', 'Status', 'Gateway Type', 'Date']

    # Add columns based on the user's role
    if request.user.role.name == "ADMIN":
        columns += ['Route API', 'Reseller']
    if request.user.role.name != "CLIENT":
        columns.append('Client')

    for instance in instances:
        row = [
            instance.receiver,
            instance.message,
            instance.status,
            instance.gateway_type,
            instance.sent_at.replace(tzinfo=None) if instance.sent_at.tzinfo else instance.sent_at
        ]

        # Add data based on the user's role
        if request.user.role.name == "ADMIN":
            row.append(instance.sms_api.name if instance.sms_api else None)
            row.append(instance.sender.owner_user.username if instance.sender and instance.sender.owner_user else None)
        if request.user.role.name != "CLIENT":
            row.append(instance.sender.username if instance.sender else None)

        data.append(row)

    # Create DataFrame with dynamic columns
    df = pd.DataFrame(data, columns=columns)

    response = export_to_excel(df)
    return response


def export_api_report_to_excel(request, instances):
    data = []
    columns = ['Receiver', 'Text', 'Status', 'Gateway Type', 'Date']

    # Add columns based on the user's role
    if request.user.role.name == "ADMIN":
        columns += ['Route API', 'Reseller']
    if request.user.role.name != "CLIENT":
        columns.append('Client')

    for instance in instances:
        row = [
            instance.receiver,
            instance.message,
            instance.status,
            instance.gateway_type,
            instance.sent_at.replace(tzinfo=None) if instance.sent_at.tzinfo else instance.sent_at
        ]

        # Add data based on the user's role
        if request.user.role.name == "ADMIN":
            row.append(instance.sms_api.name if instance.sms_api else None)
            row.append(instance.sender.owner_user.username if instance.sender and instance.sender.owner_user else None)
        if request.user.role.name != "CLIENT":
            row.append(instance.sender.email if instance.sender else None)

        data.append(row)

    # Create DataFrame with dynamic columns
    df = pd.DataFrame(data, columns=columns)

    response = export_to_excel(df)
    return response


def export_transaction_report_to_excel(request, instances):
    data = []
    for transaction in instances:
        data.append([
            f"Transaction ID: {transaction.transaction_id}\n"
            f"Transaction Date: {transaction.created_at}\n"
            f"Expiry Date: {transaction.balance_valid_till}\n"
            f"Remarks: {transaction.remakrs}",
            transaction.transaction_type,
            transaction.balance,
            transaction.recharged_by,
            transaction.recharged_to,
            transaction.respective_package_price,
            transaction.message_amount
        ])

    df = pd.DataFrame(data, columns=[
        'Transaction Detail', 
        'Type', 
        'Amount', 
        'From', 
        'To', 
        'Rate per message', 
        'Message Quantity'
    ])

    return export_to_excel(df)


def export_to_excel(df):
    output = BytesIO()
    writer = pd.ExcelWriter(output, engine='xlsxwriter')
    df.to_excel(writer, sheet_name='Report', index=False)

    # Close the Pandas Excel writer and output the Excel file to the buffer
    writer.close()

    # Seek the beginning of the stream
    output.seek(0)

    # Create an HTTP response with the appropriate content type and header
    response = HttpResponse(output, content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename=report.xlsx'

    return response


def export_receivers_to_excel(request, instances):
    data = []
    columns = ['Numbers']

    for instance in instances:
        row = [
            instance.receiver,
        ]
        data.append(row)

    # Create DataFrame with dynamic columns
    df = pd.DataFrame(data, columns=columns)

    response = export_to_excel(df)
    return response