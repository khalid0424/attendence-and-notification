from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

class Teacher(models.Model):
    f_name = models.CharField(max_length=150, null=True)
    l_name = models.CharField(max_length=150, null=True)

    def __str__(self):
        return f"{self.f_name} {self.l_name}"

class Subject(models.Model):
    name_subject = models.CharField(max_length=150)
    teacher = models.ManyToManyField(Teacher)

    def __str__(self):
        return self.name_subject

class Class(models.Model):
    name = models.CharField(max_length=150)
    time = models.CharField(max_length=50)
    subject = models.ManyToManyField(Subject)

    def __str__(self):
        return self.name


class StudentClass(models.Model):
    student = models.ForeignKey('Student', on_delete=models.CASCADE)
    class_item = models.ForeignKey(Class, on_delete=models.CASCADE)
    
    class Meta:
        db_table = 'attendence_student_class'


class Student(models.Model):
    telegram_id = models.CharField(max_length=150, null=True)
    username = models.CharField(max_length=150, unique=True)
    f_name = models.CharField(max_length=150, null=True)
    l_name = models.CharField(max_length=150, null=True)
    class_id = models.ManyToManyField(Class)
    created_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True, null=True)

    def __str__(self):
        return f"{self.f_name} {self.l_name}"

@receiver(post_save, sender=Student)
def set_default_class(sender, instance, created, **kwargs):
    if created:
        default_class = Class.objects.filter(id=1).first()
        if default_class:
            instance.class_id.add(default_class)

class Attendens(models.Model):
    user = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="attendens")
    comment = models.TextField(null=True)
    attended_time = models.DateTimeField(null=True, blank=True)
    missed_time = models.DateTimeField(null=True, blank=True)
    timeout_time = models.DateTimeField(null=True, blank=True)
    omad = models.BooleanField(default=False, null=True)
    raft = models.BooleanField(default=False, null=True) 
    dercard = models.BooleanField(default=False, null=True)
    is_late = models.BooleanField(default=False, null=True)
    created_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True, null=True)
    confirmed = models.BooleanField(default=False)

    class Meta:
        indexes = [
            models.Index(fields=['user', 'created_at']),
        ]
        verbose_name = 'Attendance'
        verbose_name_plural = 'Attendances'

    def __str__(self):
        return f"{self.user.username} - {self.created_at.date()}"


class TelegramGroup(models.Model):
    group_id = models.CharField(max_length=150, unique=True)
    group_name = models.CharField(max_length=200, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    added_at = models.DateTimeField(auto_now_add=True)
    class_id = models.ForeignKey(Class, on_delete=models.CASCADE, null=True, blank=True)
    def __str__(self):
        return f"{self.group_name} ({self.group_id})"



class TelegramGroup2(models.Model):
    group_id = models.CharField(max_length=150, unique=True)
    group_name = models.CharField(max_length=200, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    added_at = models.DateTimeField(auto_now_add=True)
    class_id = models.ForeignKey(Class, on_delete=models.CASCADE, null=True, blank=True)
    def __str__(self):
        return f"{self.group_name} ({self.group_id})"


class SendMessage(models.Model):
    image = models.ImageField(upload_to='static/images', null=True, blank=True)
    message = models.TextField(null=True, blank=True)
    time = models.DateTimeField(auto_now=True, auto_now_add=False)
    chat_id = models.CharField(max_length=250, null=True, blank=True)

    def __str__(self):
        return f"{self.id}"