from django.urls import path
from . import views

urlpatterns = [
    path('create/', views.create_community, name='create_community'),
    path('my_communities/', views.my_communities, name='my_communities'),
    path('explore/', views.find_community, name='find_community'),
    path('view/<slug:slug>/', views.community_detail, name='community_detail'),
    path('edit/<slug:slug>/', views.edit_community, name='edit_community'),
    path('delete/<slug:slug>/', views.delete_community, name='delete_community'),
    path('community/<slug:slug>/join/', views.join_community, name='join_community'),
    path('community/<slug:slug>/leave/', views.leave_community, name='leave_community'),        
    path('<slug:slug>/manage-member/', views.manage_member, name='manage_member'),
    path('event/<int:event_id>/', views.event_detail, name='event_detail'),
    path('<slug:slug>/add-event/', views.add_event, name='add_event'),
    path('event/edit/<int:event_id>/', views.edit_event, name='edit_event'),
    path('event/delete/<int:event_id>/', views.delete_event, name='delete_event'),
]