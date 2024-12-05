from django.urls import path
from django.contrib.auth import views as auth_views
from .views import *

urlpatterns = [
    path('', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('register/', RegisterView.as_view(), name='register'),
    path('profile/', ProfileView.as_view(), name='profile'),
    path('profile/edit/', EditProfileView.as_view(), name='edit_profile'),
    path('students/', StudentListView.as_view(), name='student_list'),
    path('students/add/', StudentCreateView.as_view(), name='add_student'),
    path('student/<int:student_id>/edit/', StudentUpdateView.as_view(), name='edit_student'),  
    path('student/<int:student_id>/delete/', StudentDeleteView.as_view(), name='delete_student'),
    path('attendance/', AttendanceListView.as_view(), name='attendance_list'),
    path('teachers/', TeacherListView.as_view(), name='teacher_list'),
    path('courses/', CourseListView.as_view(), name='course_list'),
    path('courses/create/', CourseCreateView.as_view(), name='course_create'),
    path('courses/<int:pk>/update/', CourseUpdateView.as_view(), name='course_update'),
    path('courses/<int:pk>/delete/', CourseDeleteView.as_view(), name='course_delete'), 
    path('classes/', ClassListView.as_view(), name='class_list'),
    path('classes/create/', ClassCreateView.as_view(), name='class_create'),
    path('classes/<int:pk>/update/', ClassUpdateView.as_view(), name='class_update'),
    path('classes/<int:pk>/delete/', ClassDeleteView.as_view(), name='class_delete'),
    path('classes/<int:pk>/', ClassDetailView.as_view(), name='class_detail'),
    path('class/<int:class_id>/students/', ClassStudentManageView.as_view(), name='class_students'),
    path('translate/', TranslateView.as_view(), name='translate'),
    # path('send-message/', send_message_view, name='send_message'),
]