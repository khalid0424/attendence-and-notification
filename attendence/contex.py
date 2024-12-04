from django.utils import timezone
from attendence.models import Student, Attendens, Class
from django.db.models import Q

def save_students(message):
    first_name = message.chat.first_name if message.chat.first_name else None
    last_name = message.chat.last_name if message.chat.last_name else None
    student = Student.objects.create(
        telegram_id=message.chat.id,
        username=message.chat.username,
        f_name=first_name,
        l_name=last_name,
        created_at=timezone.now(),
        is_active=True
    )

def save_students_come(message):
    """Отметка о приходе через бот"""
    student = Student.objects.get(telegram_id=message.chat.id)
    current_date = timezone.now().date()
    
    # Проверяем существующую запись
    attendance = Attendens.objects.filter(
        user=student,
        created_at__date=current_date
    ).first()
    
    if attendance and not attendance.confirmed:
        # Если есть автоматическая отметка об отсутствии и она не подтверждена,
        # обновляем на присутствие
        attendance.omad = True
        attendance.attended_time = timezone.now()
        attendance.missed_time = None
        attendance.comment = None
        attendance.save()
    else:
        # Создаем новую запись о присутствии
        attendance = Attendens.objects.create(
            user=student,
            attended_time=timezone.now(),
            omad=True,
            created_at=timezone.now(),
            is_active=True
        )
    
    return attendance

def save_students_notcome(message, prichina):
    """Подтверждение отсутствия через бот"""
    student = Student.objects.get(telegram_id=message.chat.id)
    current_date = timezone.now().date()
    
    # Обновляем или создаем запись
    attendance, created = Attendens.objects.update_or_create(
        user=student,
        created_at__date=current_date,
        defaults={
            'missed_time': timezone.now(),
            'omad': False,
            'comment': prichina,
            'is_active': True,
            'confirmed': True  # Подтверждено через бот
        }
    )
    return attendance

def save_students_late(message, prichina):
    """Save late arrival"""
    student = Student.objects.get(telegram_id=message.chat.id)
    Attendens.objects.create(
        user=student,
        comment=prichina,
        timeout_time=timezone.now(),
        omad=False,
        raft=False,
        dercard=True,
        is_late=True,
        created_at=timezone.now(),
        is_active=True
    )

def save_students_come2(message, username):
    first_name = message.chat.first_name if message.chat.first_name else None
    last_name = message.chat.last_name if message.chat.last_name else None
    Student.objects.create(
        telegram_id=message.chat.id,
        username=username,
        f_name=first_name,
        l_name=last_name
    )

def get_student(id):
    """Check if student can mark attendance for today"""
    current_date = timezone.now().date()
    
    # Проверяем существующую отметку
    attendance = Attendens.objects.filter(
        user__telegram_id=id,
        created_at__date=current_date
    ).first()
    
    # Если есть автоматическая отметка об отсутствии и она не подтверждена - можно отметиться
    if attendance and not attendance.confirmed and not attendance.omad:
        return True
        
    # Если есть подтвержденная отметка об отсутствии - нельзя отметиться
    if attendance and attendance.confirmed and not attendance.omad:
        return False
        
    # Если уже отмечен как присутствующий - нельзя отметиться снова
    if attendance and attendance.omad:
        return False
        
    # Если опоздал - можно отметиться
    if attendance and attendance.is_late:
        return True
        
    # Если нет никакой отметки - можно отметиться
    return not attendance

def get_student3(id):
    """Check if student can mark absence for today"""
    current_date = timezone.now().date()
    # Cannot mark absence if already marked attendance or absence
    return not Attendens.objects.filter(
        user__telegram_id=id,
        created_at__date=current_date
    ).exists()

def get_student4(id):
    """Check if student can mark late arrival"""
    current_date = timezone.now().date()
    
    # Получаем текущую отметку за сегодня
    attendance = Attendens.objects.filter(
        user__telegram_id=id,
        created_at__date=current_date
    ).first()
    
    # Если нет отметки или есть автоматическая отметка об отсутствии - можно отметить опоздание
    if not attendance or (attendance and not attendance.confirmed and not attendance.omad):
        return True
        
    # Если уже отмечен как присутствующий или опаздывающий - нельзя отметиться
    if attendance and (attendance.omad or attendance.dercard):
        return False
        
    # Если есть подтвержденная отметка об отсутствии - нельзя отметиться
    if attendance and attendance.confirmed and not attendance.omad:
        return False
        
    return True

def get_student1(id):
    student_exists = Student.objects.filter(telegram_id=id).exists()
    return not student_exists

def show_who_be1(id):
    current_date = timezone.now()
    student_attendance = Attendens.objects.filter(
        user__telegram_id=id,
        omad=True,
        attended_time__date=current_date.date(),
        raft__isnull=True
    ).first()

    return student_attendance

def update_out(id):
    """Mark student as left for the day"""
    try:
        student = Student.objects.get(telegram_id=id)
        # Find today's attendance record where student came and hasn't left
        attendance = Attendens.objects.filter(
            user=student,
            attended_time__date=timezone.now().date(),
            omad=True,
            raft=False
        ).first()
        
        if attendance:
            attendance.timeout_time = timezone.now()
            attendance.raft = True
            attendance.save()
            return True
        return False
    except Student.DoesNotExist:
        return False

def handle_late_arrival(id):
    """Handle when late student arrives"""
    current_date = timezone.now().date()
    late_record = Attendens.objects.filter(
        user__telegram_id=id,
        timeout_time__date=current_date,
        is_late=True,
        attended_time__isnull=True
    ).first()
    
    if late_record:
        late_record.attended_time = timezone.now()
        late_record.omad = True
        late_record.save()
        return True
    return False

def update_user(id, group):
    student = Student.objects.get(telegram_id=id)
    group_instance = Class.objects.get(name=group)
    student.class_id.add(group_instance)
    student.save()

def get_groups():
    return Class.objects.all()

def mark_absent_students():
    """Автоматически отмечает отсутствующих студентов"""
    current_date = timezone.now().date()
    
    # Получаем всех активных студентов
    students = Student.objects.filter(is_active=True)
    
    for student in students:
        # Проверяем, есть ли уже отметка за сегодня
        attendance_exists = Attendens.objects.filter(
            user=student,
            created_at__date=current_date
        ).exists()
        
        # Если отметки нет - создаем отметку об отсутствии
        if not attendance_exists:
            Attendens.objects.create(
                user=student,
                missed_time=timezone.now(),
                omad=False,
                comment="Автоматическая отметка об отсутствии",
                created_at=timezone.now(),
                is_active=True,
                confirmed=False  # Не подтверждено через бот
            )
