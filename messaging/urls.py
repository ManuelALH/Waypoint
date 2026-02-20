from django.urls import path
from . import views

urlpatterns = [
    path('inbox/', views.inbox, name='inbox'),
    path('send/', views.send_message, name='send_message'),
    path('message/read/<int:message_id>/', views.mark_as_read, name='mark_as_read'),
    path('chat/<str:username>/', views.chat_room, name='chat_room'),
    path('hx/messages/<str:username>/', views.get_chat_messages, name='hx_get_messages'),
    path('hx/sidebar/', views.get_sidebar_chats, name='hx_get_sidebar'),
    path('report/<str:username>/', views.report_user, name='report_user'),
    path('block/<str:username>/', views.block_user, name='block_user'),
    path('unblock/<str:username>/', views.unblock_user, name='unblock_user'),
    path('settings/blocked/', views.blocked_list, name='blocked_list'),
    path('hx/unread-count/', views.hx_unread_count, name='hx_unread_count'),
    path('support/', views.support_ticket, name='support_ticket'),
]