from django.urls import path
from . import views

urlpatterns = [
    path('create/', views.create_character, name='create_character'),
    path('my_characters/', views.my_characters, name='my_characters'),
    path('view/<int:pk>/', views.character_sheet, name='character_sheet'),
    path('edit/<int:pk>/', views.edit_character, name='edit_character'),
    path('delete/<int:pk>/', views.delete_character, name='delete_character'),
    path('<int:char_id>/log/', views.character_full_log, name='character_full_log'),
]