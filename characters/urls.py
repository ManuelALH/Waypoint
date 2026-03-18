from django.urls import path
from . import views

urlpatterns = [
    path('create/', views.create_character, name='create_character'),
    path('my_characters/', views.my_characters, name='my_characters'),
    path('view/<int:pk>/', views.character_sheet, name='character_sheet'),
    path('edit/<int:pk>/', views.edit_character, name='edit_character'),
    path('delete/<int:pk>/', views.delete_character, name='delete_character'),
    path('<int:char_id>/log/', views.character_full_log, name='character_full_log'),
    path('<int:pk>/inventory/add/', views.add_inventory, name='add_inventory'),
    path('<int:pk>/inventory/<str:item_id>/edit/', views.edit_inventory, name='edit_inventory'),
    path('<int:pk>/inventory/<str:item_id>/delete/', views.delete_inventory, name='delete_inventory'),
    path('<int:pk>/inventory/<str:item_id>/favorite/', views.favorite_inventory, name='favorite_inventory'),
    path('<int:pk>/inventory/', views.character_inventory, name='character_inventory'),
    path('<int:pk>/actions/add/', views.add_action, name='add_action'),
    path('<int:pk>/actions/<str:action_id>/edit/', views.edit_action, name='edit_action'),
    path('<int:pk>/actions/<str:action_id>/delete/', views.delete_action, name='delete_action')
]