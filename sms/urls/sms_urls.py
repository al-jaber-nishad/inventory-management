
from django.urls import path
from sms.views import sms_views, sms_management, sms_processing, sms_reports


urlpatterns = [
	path('all_sms_list/', sms_management.all_sms_list, name='all_sms_list'),

	path('sent_sms_list/', sms_management.sent_sms_list, name='sent_sms_list'),

	path('inbox_sms_list/', sms_management.inbox_sms_list, name='inbox_sms_list'),

	path('queued_sms_list/', sms_management.queued_sms_list, name='queued_sms_list'),

	path('get_queued_sms_number/', sms_management.get_queued_sms_number, name='get_queued_sms_number'),

	path('failed_sms_list/', sms_management.failed_sms_list, name='failed_sms_list'),
	
	path('send_sms/', sms_views.send_sms, name='send_sms'),

	path('failed_and_pending_sms_list/', sms_management.failed_and_pending_sms_list, name='failed_and_pending_sms_list'),

	path('send_group_sms/', sms_views.send_group_sms, name='send_group_sms'),

	path('sms_detail/<int:pk>', sms_management.sms_detail, name='sms_detail'),

	# report
    path('sms_group_report/', sms_reports.sms_group_report, name='sms_group_report'),
    
    path('summary_report/', sms_reports.sms_summary_report, name='sms_report_summary'),

    path('history_report/', sms_reports.sms_history_report, name='sms_history_report'),

    path('balance_log_report/', sms_reports.balance_log_report, name='balance_log_report'),

    # path('sms_history_report_data/', views.sms_history_report_data, name='sms_history_report_data'),

    path('api_history_report/', sms_reports.api_history_report, name='api_history_report'),

    path('api_summary_report/', sms_reports.sms_api_summary_report, name='sms_api_summary_report'),

	path('get_dashboard_data/', sms_reports.get_dashboard_data, name='get_dashboard_data'),

	path('api/sendsms', sms_views.send_sms_api, name='send_sms_api'),

]