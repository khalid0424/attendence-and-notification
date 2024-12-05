from django.views.generic import ListView, CreateView, UpdateView, DeleteView, View, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse, HttpResponse, HttpResponseBadRequest
from django.shortcuts import redirect, get_object_or_404, render
from django.db.models import Q, Count
from django.urls import reverse_lazy
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login, authenticate
from django.views.generic.edit import FormView
from django.contrib.auth.models import User
from .models import Student, Class, Teacher, Attendens, Subject, TelegramGroup2, SendMessage
from django.utils import timezone
import csv
from datetime import datetime, timedelta
from functools import wraps
from googletrans import Translator
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .telegram_bot_updated import send_notification
from django.views.decorators.csrf import csrf_protect

def require_ajax(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.is_ajax():
            return HttpResponseBadRequest()
        return view_func(request, *args, **kwargs)
    return wrapper

class AttendanceListView(LoginRequiredMixin, ListView):
    model = Attendens
    template_name = 'attendance_list.html'
    context_object_name = 'attendance_list'
    paginate_by = 20

    def get_queryset(self):
        class_id = self.request.GET.get('class_id')
        if not class_id:
            return Attendens.objects.none()
            
        students = Student.objects.filter(class_id=class_id)
        queryset = Attendens.objects.filter(user__in=students).select_related('user').order_by('-created_at')

        date_from = self.request.GET.get('date_from')
        date_to = self.request.GET.get('date_to')
        if date_from:
            queryset = queryset.filter(created_at__date__gte=date_from)
        if date_to:
            queryset = queryset.filter(created_at__date__lte=date_to)

        status = self.request.GET.get('status')
        if status == 'present':
            queryset = queryset.filter(omad=True)
        elif status == 'absent':
            queryset = queryset.filter(omad=False)
        elif status == 'late':
            queryset = queryset.filter(Q(is_late=True) | Q(dercard=True))

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        class_id = self.request.GET.get('class_id')
        
        if class_id:
            selected_class = Class.objects.get(id=class_id)
            context['selected_class'] = selected_class
            students = Student.objects.filter(
                class_id=class_id,
                is_active=True
            ).distinct()
            
            student_stats = []
            today = timezone.now().date()
            
            for student in students:
                total = Attendens.objects.filter(
                    user=student,
                    created_at__date=today
                )
                
                present = total.filter(omad=True).count()
                absent = total.filter(Q(omad=False) & Q(is_late=False) & Q(dercard=False)).count()
                late = total.filter(Q(is_late=True) | Q(dercard=True)).count()
                
                all_days = present + absent + late
                percent = (present / all_days * 100) if all_days > 0 else 0
                
                student_stats.append({
                    'student': student,
                    'present_count': present,
                    'absent_count': absent,
                    'late_count': late,
                    'attendance_percentage': round(percent, 2)
                })
            
            context['student_stats'] = student_stats
            today = timezone.now().date()
            today_attendance = Attendens.objects.filter(
                user__in=students,
                created_at__date=today
            )
            present_count = today_attendance.filter(omad=True).count()
            late_count = today_attendance.filter(Q(is_late=True) | Q(dercard=True)).count()
            total_students = students.count()
            absent_count = total_students - present_count
            if absent_count < 0:
                absent_count = 0
            
            context['today_stats'] = {
                'present': present_count,
                'absent': absent_count,
                'late': late_count,
                'total_students': total_students
            }
        
        context['classes'] = Class.objects.all()
        return context

    def render_to_response(self, context, **response_kwargs):
        if self.request.GET.get('export') == 'csv':
            return self.export_csv(context['attendance_list'])
        return super().render_to_response(context, **response_kwargs)

    def export_csv(self, attendances):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="attendance_{timezone.now().date()}.csv"'
        
        writer = csv.writer(response)
        writer.writerow(['Студент', 'Курс', 'Время прихода', 'Время ухода', 'Статус', 'Комментарий'])
        
        for item in attendances:
            if item.omad:
                status = 'Присутствует'
            elif item.dercard:
                status = 'Опаздывает'
            else:
                status = 'Отсутствует'
                
            writer.writerow([
                f"{item.user.f_name} {item.user.l_name}",
                ', '.join(c.name for c in item.user.class_id.all()),
                item.attended_time.strftime('%H:%M') if item.attended_time else '-',
                item.timeout_time.strftime('%H:%M') if item.timeout_time else '-',
                status,
                item.comment or '-'
            ])
        
        return response

class TeacherListView(LoginRequiredMixin, ListView):
    model = Teacher
    template_name = 'teacher_list.html'
    context_object_name = 'teachers'
    
    def get_queryset(self):
        queryset = Teacher.objects.all()
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(Q(f_name__icontains=search) | Q(l_name__icontains=search))
        return queryset

class ClassListView(LoginRequiredMixin, ListView):
    model = Class
    template_name = 'class_list.html'
    context_object_name = 'classes'
    paginate_by = 10

    def get_queryset(self):
        queryset = Class.objects.all().prefetch_related('subject', 'subject__teacher')
        search = self.request.GET.get('search')
        subject = self.request.GET.get('subject')
        teacher = self.request.GET.get('teacher')

        if search:
            queryset = queryset.filter(name__icontains=search)
        
        if subject:
            queryset = queryset.filter(subject__id=subject)
            
        if teacher:
            queryset = queryset.filter(subject__teacher__id=teacher)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['subjects'] = Subject.objects.all()
        context['teachers'] = Teacher.objects.all()
        context['search'] = self.request.GET.get('search', '')
        context['selected_subject'] = self.request.GET.get('subject', '')
        context['selected_teacher'] = self.request.GET.get('teacher', '')

        today = timezone.now().date()
        for class_obj in context['classes']:
            students = Student.objects.filter(class_id=class_obj)
            student_ids = students.values_list('id', flat=True)
            
            class_obj.today_stats = {
                'present': Attendens.objects.filter(
                    user__in=student_ids,
                    created_at__date=today,
                    omad=True
                ).count(),
                'absent': Attendens.objects.filter(
                    user__in=student_ids,
                    created_at__date=today,
                    omad=False
                ).count(),
                'late': Attendens.objects.filter(
                    user__in=student_ids,
                    created_at__date=today,
                    dercard=True
                ).count()
            }
        
        return context

class MarkAttendanceView(LoginRequiredMixin, View):
    def post(self, request):
        student_id = request.POST.get('student_id')
        status = request.POST.get('status')
        comment = request.POST.get('comment', '')
        
        if not student_id or not status:
            return JsonResponse({'status': 'error', 'message': 'Необходимо указать студента и статус'}, status=400)
        
        student = get_object_or_404(Student, id=student_id)
        attendance = Attendens(user=student, comment=comment, created_at=timezone.now())
        
        if status == 'present':
            attendance.attended_time = timezone.now()
            attendance.omad = True
        elif status == 'absent':
            attendance.missed_time = timezone.now()
            attendance.omad = False
        elif status == 'late':
            attendance.timeout_time = timezone.now()
            attendance.dercard = True
        else:
            return JsonResponse({'status': 'error', 'message': 'Неверный статус'}, status=400)
        
        today = timezone.now().date()
        existing_attendance = Attendens.objects.filter(user=student, created_at__date=today).exists()
        
        if existing_attendance:
            return JsonResponse({'status': 'error', 'message': 'Студент уже отмечен сегодня'}, status=400)
        
        attendance.save()
        return JsonResponse({'status': 'success', 'message': 'Посещаемость успешно отмечена'})

class StudentCreateView(LoginRequiredMixin, CreateView):
    model = Student
    fields = ['f_name', 'l_name']
    template_name = 'attendance_list.html'
    success_url = reverse_lazy('attendance_list')

    def form_valid(self, form):
        response = super().form_valid(form)
        class_id = self.request.POST.get('class_id')
        if class_id:
            class_obj = Class.objects.get(id=class_id)
            class_obj.student_set.add(self.object)
            messages.success(self.request, f'Студент {self.object.f_name} {self.object.l_name} успешно добавлен')
        return response

    def form_invalid(self, form):
        messages.error(self.request, 'Ошибка при добавлении студента')
        return redirect('attendance_list')

class StudentUpdateView(LoginRequiredMixin, UpdateView):
    model = Student
    fields = ['f_name', 'l_name']
    template_name = 'attendance_list.html'
    success_url = reverse_lazy('attendance_list')
    pk_url_kwarg = 'student_id'

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, 'Данные студента успешно обновлены')
        return response

    def form_invalid(self, form):
        messages.error(self.request, 'Ошибка при обновлении данных')
        return redirect('attendance_list')

class StudentDeleteView(LoginRequiredMixin, DeleteView):
    model = Student
    success_url = reverse_lazy('attendance_list')
    pk_url_kwarg = 'student_id'

    def delete(self, request, *args, **kwargs):
        student = self.get_object()
        name = f'{student.f_name} {student.l_name}'
        response = super().delete(request, *args, **kwargs)
        messages.success(request, f'Студент {name} успешно удален')
        return response

    def get(self, request, *args, **kwargs):
        return self.post(request, *args, **kwargs)

class StudentListView(LoginRequiredMixin, ListView):
    model = Student
    template_name = 'student_list.html'
    context_object_name = 'students'
    paginate_by = 10
    
    def get_queryset(self):
        queryset = Student.objects.all().prefetch_related('class_id', 'attendens')
        
        search_query = self.request.GET.get('search')
        if search_query:
            queryset = queryset.filter(Q(f_name__icontains=search_query) | Q(l_name__icontains=search_query) | Q(username__icontains=search_query) | Q(telegram_id__icontains=search_query))
        
        class_id = self.request.GET.get('class')
        if class_id:
            queryset = queryset.filter(class_id=class_id)
            
        teacher_id = self.request.GET.get('teacher')
        if teacher_id:
            queryset = queryset.filter(class_id__subject__teacher=teacher_id).distinct()
            
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['classes'] = Class.objects.all()
        context['teachers'] = Teacher.objects.all()
        context['selected_class'] = self.request.GET.get('class')
        context['selected_teacher'] = self.request.GET.get('teacher')
        context['search_query'] = self.request.GET.get('search')
        
        today = timezone.now().date()
        for student in context['students']:
            latest_attendance = student.attendens.filter(created_at__date=today).first()
            student.today_status = latest_attendance
            
        return context

class RegisterView(FormView):
    template_name = 'registration/register.html'
    form_class = UserCreationForm
    success_url = reverse_lazy('student_list')

    def form_valid(self, form):
        user = form.save()
        login(self.request, user)
        messages.success(self.request, 'Регистрация успешно завершена!')
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, 'Ошибка при регистрации')
        return super().form_invalid(form)

class ProfileView(LoginRequiredMixin, View):
    def get(self, request):
        return render(request, 'profile.html', {'user': request.user})

class EditProfileView(LoginRequiredMixin, View):
    def post(self, request):
        user = request.user
        user.first_name = request.POST.get('first_name', '')
        user.last_name = request.POST.get('last_name', '')
        user.email = request.POST.get('email', '')
        
        current_password = request.POST.get('current_password')
        new_password = request.POST.get('new_password')
        if current_password and new_password:
            if user.check_password(current_password):
                user.set_password(new_password)
                messages.success(request, 'Пароль успешно обновлен')
            else:
                messages.error(request, 'Неверный текущий пароль')
                return redirect('profile')
        
        user.save()
        messages.success(request, 'Профиль успешно обновлен')
        return redirect('profile')

class ClassStudentManageView(LoginRequiredMixin, View):
    def get(self, request, class_id):
        class_obj = get_object_or_404(Class, id=class_id)
        class_students = Student.objects.filter(class_id=class_obj)
        available_students = Student.objects.exclude(class_id=class_obj)
        
        return render(request, 'class_students.html', {
            'class': class_obj,
            'class_students': class_students,
            'available_students': available_students
        })

    def post(self, request, class_id):
        class_obj = get_object_or_404(Class, id=class_id)
        action = request.POST.get('action')
        student_id = request.POST.get('student_id')
        
        if not student_id:
            messages.error(request, 'Студент не выбран')
            return redirect('class_students', class_id=class_id)
            
        student = get_object_or_404(Student, id=student_id)
        
        if action == 'add':
            student.class_id.add(class_obj)
            messages.success(request, f'Студент {student.f_name} {student.l_name} добавлен в класс {class_obj.name}')
        elif action == 'remove':
            student.class_id.remove(class_obj)
            messages.success(request, f'Студент {student.f_name} {student.l_name} удален из класса {class_obj.name}')
        
        return redirect('class_students', class_id=class_id)

class TranslateView(View):
    def post(self, request):
        translator = Translator()
        text = request.POST.get('text', '')
        target_lang = request.POST.get('lang', 'en')
        
        if not text:
            return JsonResponse({'error': 'No text provided'}, status=400)
            
        try:
            translation = translator.translate(text, dest=target_lang)
            return JsonResponse({'translated': translation.text})
        except Exception as e:
            print(f"Translation error: {str(e)}") 
            return JsonResponse({'error': str(e)}, status=400)

class CourseListView(LoginRequiredMixin, ListView):
    model = Subject
    template_name = 'course_list.html'
    context_object_name = 'courses'
    paginate_by = 10

    def get_queryset(self):
        queryset = Subject.objects.all().prefetch_related('teacher')
        search = self.request.GET.get('search')
        teacher = self.request.GET.get('teacher')

        if search:
            queryset = queryset.filter(
                Q(name_subject__icontains=search) |
                Q(teacher__f_name__icontains=search) |
                Q(teacher__l_name__icontains=search)
            )
        
        if teacher:
            queryset = queryset.filter(teacher=teacher)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['teachers'] = Teacher.objects.all()
        context['search'] = self.request.GET.get('search', '')
        context['selected_teacher'] = self.request.GET.get('teacher', '')
        return context

class CourseCreateView(LoginRequiredMixin, CreateView):
    model = Subject
    template_name = 'course_form.html'
    fields = ['name_subject', 'teacher']
    success_url = reverse_lazy('course_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Добавить курс'
        return context

    def form_valid(self, form):
        messages.success(self.request, 'Курс успешно создан')
        return super().form_valid(form)

class CourseUpdateView(LoginRequiredMixin, UpdateView):
    model = Subject
    template_name = 'course_form.html'
    fields = ['name_subject', 'teacher']
    success_url = reverse_lazy('course_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Редактировать курс'
        return context

    def form_valid(self, form):
        messages.success(self.request, 'Курс успешно обновлен')
        return super().form_valid(form)

class CourseDeleteView(LoginRequiredMixin, DeleteView):
    model = Subject
    template_name = 'course_confirm_delete.html'
    success_url = reverse_lazy('course_list')

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, 'Курс успешно удален')
        return super().delete(request, *args, **kwargs)

class ClassCreateView(LoginRequiredMixin, CreateView):
    model = Class
    template_name = 'class_form.html'
    fields = ['name', 'time', 'subject']
    success_url = reverse_lazy('class_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Добавить класс'
        return context

    def form_valid(self, form):
        messages.success(self.request, 'Класс успешно создан')
        return super().form_valid(form)

class ClassUpdateView(LoginRequiredMixin, UpdateView):
    model = Class
    template_name = 'class_form.html'
    fields = ['name', 'time', 'subject']
    success_url = reverse_lazy('class_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Редактировать класс'
        return context

    def form_valid(self, form):
        messages.success(self.request, 'Класс успешно обновлен')
        return super().form_valid(form)

class ClassDeleteView(LoginRequiredMixin, DeleteView):
    model = Class
    template_name = 'class_confirm_delete.html'
    success_url = reverse_lazy('class_list')

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, 'Класс успешно удален')
        return super().delete(request, *args, **kwargs)

class ClassDetailView(LoginRequiredMixin, DetailView):
    model = Class
    template_name = 'class_detail.html'
    context_object_name = 'class'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        class_obj = self.get_object()
        
        students = Student.objects.filter(
            class_id=class_obj,
            is_active=True
        ).distinct()
        
        context['students'] = students
        context['total_students'] = students.count()
        
        today = timezone.now().date()
        
        latest_attendance = {}
        for attendance in Attendens.objects.filter(
            user__in=students,
            created_at__date=today
        ).order_by('user', '-created_at'):
            if attendance.user_id not in latest_attendance:
                latest_attendance[attendance.user_id] = attendance
        
        today_present = sum(1 for att in latest_attendance.values() if att.omad)
        today_late = sum(1 for att in latest_attendance.values() if att.dercard)  
        today_absent = sum(1 for att in latest_attendance.values() if not att.omad) 
        
        students_without_attendance = context['total_students'] - len(latest_attendance)
        today_absent += students_without_attendance
        
        context['today_attendance'] = {
            'present': today_present,
            'absent': today_absent,
            'late': today_late
        }
        
        for student in context['students']:
            student.today_status = latest_attendance.get(student.id)
        
        return context

@login_required
@csrf_protect
def send_message_view(request):
    groups = TelegramGroup2.objects.filter(is_active=True)
    
    if request.method == 'POST':
        message_text = request.POST.get('message')
        image = request.FILES.get('image')
        try:
            message_obj = SendMessage(
                message=message_text,
                image=image if image else None
            )
            message_obj.save()
            send_notification(message_obj)
            messages.success(request, 'Сообщение успешно отправлено во все активные группы!')
            return redirect('send_message')
        except Exception as e:
            messages.error(request, f'Ошибка при отправке сообщения: {str(e)}')
    
    context = {
        'groups': groups
    }
    return render(request, 'send_message.html', context)
