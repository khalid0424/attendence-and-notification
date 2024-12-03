from django.views.generic import ListView, UpdateView, View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy
from .models import Student, Class, Teacher, Attendens, Subject
from django.utils import timezone

class StudentListView(ListView):
    model = Student
    template_name = 'student_list.html'
    context_object_name = 'students'
    
    def get_queryset(self):
        queryset = Student.objects.all().order_by('-created_at')
        class_id = self.request.GET.get('class_id')
        if class_id:
            queryset = queryset.filter(class_id=class_id)
        subject_id = self.request.GET.get('subject_id')
        if subject_id:
            queryset = queryset.filter(class_id__subject=subject_id)
        search_query = self.request.GET.get('search')
        if search_query:
            queryset = queryset.filter(
                Q(f_name__icontains=search_query) |
                Q(l_name__icontains=search_query) |
                Q(username__icontains=search_query)
            )
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['classes'] = Class.objects.all()
        context['subjects'] = Subject.objects.all()
        context['selected_class'] = self.request.GET.get('class_id')
        context['selected_subject'] = self.request.GET.get('subject_id')
        context['search_query'] = self.request.GET.get('search')
        return context

class StudentUpdateView(View):
    def post(self, request, student_id):
        student = get_object_or_404(Student, id=student_id)
        try:
            student.f_name = request.POST.get('f_name', student.f_name)
            student.l_name = request.POST.get('l_name', student.l_name)
            student.username = request.POST.get('username', student.username)
            student.is_active = request.POST.get('is_active', student.is_active)
            
            class_ids = request.POST.getlist('class_id')
            if class_ids:
                student.class_id.set(class_ids)
            
            student.save()
            return JsonResponse({'status': 'success'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

class AttendanceListView(ListView):
    model = Attendens
    template_name = 'attendance_list.html'
    context_object_name = 'attendances'
    
    def get_queryset(self):
        queryset = Attendens.objects.all().order_by('-created_at')
        student_id = self.request.GET.get('student_id')
        if student_id:
            queryset = queryset.filter(user_id=student_id)
        date = self.request.GET.get('date')
        if date:
            queryset = queryset.filter(
                Q(attended_time__date=date) |
                Q(missed_time__date=date) |
                Q(timeout_time__date=date)
            )
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['students'] = Student.objects.all()
        context['selected_student'] = self.request.GET.get('student_id')
        context['selected_date'] = self.request.GET.get('date')
        return context

class MarkAttendanceView(View):
    def post(self, request):
        student_id = request.POST.get('student_id')
        status = request.POST.get('status')
        comment = request.POST.get('comment', '')
        
        student = get_object_or_404(Student, id=student_id)
        attendance = Attendens(user=student, comment=comment)
        
        if status == 'present':
            attendance.attended_time = timezone.now()
            attendance.omad = True
        elif status == 'absent':
            attendance.missed_time = timezone.now()
            attendance.dercard = True
        elif status == 'late':
            attendance.timeout_time = timezone.now()
            attendance.raft = True
            
        attendance.save()
        return JsonResponse({'status': 'success'})

class TeacherListView(ListView):
    model = Teacher
    template_name = 'teacher_list.html'
    context_object_name = 'teachers'

class ClassListView(ListView):
    model = Class
    template_name = 'class_list.html'
    context_object_name = 'classes'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['subjects'] = Subject.objects.all()
        return context
