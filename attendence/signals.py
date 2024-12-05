from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from django.core.cache import cache
from django.conf import settings
from .models import Student, Attendens
# signals.py
from django.db.models.signals import m2m_changed
from django.dispatch import receiver
from django.utils import timezone
from .models import Student, Attendens

@receiver(m2m_changed, sender=Student.class_id.through)
def create_attendens_on_class_add(sender, instance, action, **kwargs):
    if action == 'post_add':  
        for class_instance in instance.class_id.all():
            Attendens.objects.create(
                user=instance,  
                omad=False,
                created_at=timezone.now(),
                is_active=True,
                confirmed=False
            )

def mark_students_absent():
    current_date = timezone.now().date()
    current_time = timezone.now().time()
    school_start_time = timezone.now().replace(
        hour=getattr(settings, 'SCHOOL_START_HOUR', 8),
        minute=0,
        second=0,
        microsecond=0
    ).time()
    
    if current_time >= school_start_time:
        students = Student.objects.filter(is_active=True).exclude(
            attendens__created_at__date=current_date
        )
        for student in students:
            Attendens.objects.create(
                user=student,
                missed_time=timezone.now(),
                omad=False,
                created_at=timezone.now(),
                is_active=True,
                confirmed=False 
            )
