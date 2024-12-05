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
    student = Student.objects.get(telegram_id=message.chat.id)
    current_date = timezone.now().date()
    
    existing_attendance = Attendens.objects.filter(
        user=student,
        created_at__date=current_date
    )
    
    if existing_attendance.filter(Q(omad=True) & Q(attended_time__isnull=False)).exists():
        return None
        
    late_record = existing_attendance.filter(is_late=True).first()
    if late_record:
        late_record.attended_time = timezone.now()
        late_record.omad = True
        late_record.save()
        return late_record
    
    auto_absent = existing_attendance.filter(confirmed=False).first()
    if auto_absent:
        auto_absent.omad = True
        auto_absent.attended_time = timezone.now()
        auto_absent.missed_time = None
        auto_absent.comment = None
        auto_absent.save()
        return auto_absent
    
    attendance = Attendens.objects.create(
        user=student,
        attended_time=timezone.now(),
        omad=True,
        created_at=timezone.now(),
        is_active=True
    )
    return attendance

def save_students_notcome(message, prichina):
    student = Student.objects.get(telegram_id=message.chat.id)
    current_date = timezone.now().date()
    
    attendance, created = Attendens.objects.update_or_create(
        user=student,
        created_at__date=current_date,
        defaults={
            'missed_time': timezone.now(),
            'omad': False,
            'comment': prichina,
            'is_active': True,
            'confirmed': True
        }
    )
    return attendance

def save_students_late(message, prichina):
    student = Student.objects.get(telegram_id=message.chat.id)
    current_date = timezone.now().date()

    existing = Attendens.objects.filter(
        user=student,
        created_at__date=current_date
    ).first()

    if existing:
        if existing.is_late or existing.omad or existing.dercard:
            return None
        existing.is_late = True
        existing.dercard = True
        existing.comment = prichina
        existing.timeout_time = timezone.now()
        existing.save()
        return existing
    
    return Attendens.objects.create(
        user=student,
        comment=prichina,
        timeout_time=timezone.now(),
        omad=False,
        raft=False,
        is_late=True,
        dercard=True,
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
    current_date = timezone.now().date()
    attendance = Attendens.objects.filter(
        user__telegram_id=id,
        created_at__date=current_date
    ).first()

    if not attendance:
        return True

    if attendance.omad and attendance.attended_time:
        return False

    if attendance.confirmed and not attendance.omad:
        return False

    if attendance.is_late and not attendance.attended_time or attendance.confirmed == False:
        return True

    return False 

def get_student3(id):
    current_date = timezone.now().date()
    return not Attendens.objects.filter(Q(user__telegram_id=id,created_at__date=current_date) & Q(confirmed = True)).exists()

def get_student4(id):
    current_date = timezone.now().date()
    attendance = Attendens.objects.filter(
        user__telegram_id=id,
        created_at__date=current_date
    ).first()
    
    if not attendance:
        return True
        
    if attendance.is_late or attendance.dercard or attendance.omad:
        return False
        
    if attendance.confirmed and not attendance.omad:
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
    try:
        student = Student.objects.get(telegram_id=id)
        current_date = timezone.now().date()
        
        # Ищем запись о приходе на сегодня
        attendance = Attendens.objects.filter(
            user=student,
            created_at__date=current_date,
            omad=True,  # Должен быть отмечен как пришедший
            attended_time__isnull=False,  # Должно быть время прихода
            raft=False  # Еще не ушел
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
    current_date = timezone.now().date()
    
    existing_attendance = Attendens.objects.filter(
        user__telegram_id=id,
        created_at__date=current_date,
        omad=True
    ).exists()
    
    if existing_attendance:
        return False
    
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
    current_date = timezone.now().date()
    active_students = Student.objects.filter(is_active=True)
    
    for student in active_students:
        attendance_exists = Attendens.objects.filter(
            user=student,
            created_at__date=current_date
        ).exists()
        
        if not attendance_exists:
            Attendens.objects.create(
                user=student,
                omad=False,
                created_at=timezone.now(),
                is_active=True,
                confirmed=False
            )
