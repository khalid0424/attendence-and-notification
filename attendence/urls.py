from django.urls import path
from . import views

urlpatterns = [
    path('', views.StudentListView.as_view(), name='student_list'),
    path('attendance/', views.AttendanceListView.as_view(), name='attendance_list'),
    path('classes/', views.ClassListView.as_view(), name='class_list'),
    path('teachers/', views.TeacherListView.as_view(), name='teacher_list'),
    path('update-student/<int:student_id>/', views.StudentUpdateView.as_view(), name='update_student'),
    path('mark-attendance/', views.MarkAttendanceView.as_view(), name='mark_attendance'),
]
