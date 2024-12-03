from django.urls import path
from . import views

urlpatterns = [
    path('', views.send_message_list, name='send_message_list'),
    path('create/', views.send_message_create, name='send_message_create'),
    path('<int:message_id>/', views.send_message_detail, name='send_message_detail'),
    path('<int:message_id>/delete/', views.send_message_delete, name='send_message_delete'),
]
