from django.db import models

# Create your models here.
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
    


class Student(models.Model):
    telegram_id = models.CharField(max_length=150, null=True)
    username = models.CharField(max_length=150, unique=True)
    f_name = models.CharField(max_length=150, null=True)
    l_name = models.CharField(max_length=150, null=True)
    class_id = models.ManyToManyField(Class)
    created_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True, null=True)
    def __str__(self):
        return self.username
    
class Attendens(models.Model):
    user = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="attendens")
    comment = models.TextField(null=True)
    attended_time = models.DateTimeField(null=True, blank=True)
    missed_time = models.DateTimeField(null=True, blank=True)
    timeout_time = models.DateTimeField(null=True, blank=True)
    omad = models.BooleanField(default=False, null=True)
    raft = models.BooleanField(default=False, null=True)
    dercard = models.BooleanField(default=False, null=True)
    created_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True, null=True)

    def __str__(self):
        return f"{self.user.__str__}"
    


class SendMessage(models.Model):
    image = models.ImageField(upload_to='static/images', null=True, blank=True)  
    message = models.TextField(null=True, blank=True)  
    time = models.DateTimeField(auto_now=True, auto_now_add=False)
    chat_id = models.CharField(max_length=250, null=True, blank=True)
    def __str__(self):
        return f"{self.id}"

