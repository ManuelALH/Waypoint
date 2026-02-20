from django.urls import path
from . import views

urlpatterns = [
    path('create/', views.create_table, name='create_table'),
    path('my_tables/', views.my_tables, name='my_tables'),
    path('view/<int:pk>/', views.table_detail, name='table_detail'),
    path('edit/<int:pk>/', views.edit_table, name='edit_table'),    
    path('delete/<int:pk>/', views.delete_table, name='delete_table'), 
    path('invite/<int:pk>/', views.invite_player, name='invite_player'),
    path('invitation/cancel/<int:invitation_id>/', views.cancel_invitation, name='cancel_invitation'),
    path('invitation/respond/<int:invitation_id>/<str:response>/', views.respond_invitation, name='respond_invitation'),
    path('remove-player/<int:table_id>/<int:user_id>/', views.remove_player, name='remove_player'),
    path('promote-player/<int:table_id>/<int:user_id>/', views.promote_player, name='promote_player'),
    path('table/<int:pk>/leave/', views.leave_table, name='leave_table'),
    path('table/<int:pk>/join-character/', views.join_table_character, name='join_table_character'),
    path('table/<int:pk>/leave-character/', views.leave_table_character, name='leave_table_character'),
    path('table/<int:pk>/add-log/', views.add_log_entry, name='add_log_entry'),
    path('table/<int:pk>/log/', views.campaign_log_view, name='campaign_log'), 
    path('log/<int:log_id>/edit/', views.edit_log_entry, name='edit_log_entry'),
    path('log/<int:log_id>/delete/', views.delete_log_entry, name='delete_log_entry'),
    path('find/', views.find_table, name='find_table'),
]