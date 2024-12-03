from django.shortcuts import render
from attendence.models import SendMessage , Teacher
from django.shortcuts import render, redirect, get_object_or_404
from .models import SendMessage, Teacher
from .sendmbot import send_message_to_telegram 
from django.contrib import messages


def send_message_list(request):
    messages_list = SendMessage.objects.all().order_by('-time')
    return render(request, 'send_message_list.html', {'messages_list': messages_list})


def send_message_create(request):
    
    if request.method == "POST":
        message_text = request.POST.get('message')
        chat_id = request.POST.get('chat_id')
        image = request.FILES.get('image')
        teacher_id = request.POST.get('sent_by')

        sent_by = get_object_or_404(Teacher, id=teacher_id)

        new_message = SendMessage.objects.create(
            message=message_text,
            chat_id=chat_id,
            image=image,
            sent_by=sent_by,
        )

        image_path = new_message.image.path if new_message.image else None
        send_message_to_telegram(chat_id, text=message_text, image_path=image_path)

        new_message.history = True
        new_message.save()

        messages.success(request, "паём бо мувафақият фиристода шуд!")
        return redirect('send_message_list')

    teachers = Teacher.objects.all()  
    return render(request, 'send_message_form.html', {'teachers': teachers})


def send_message_detail(request, message_id):
    
    message = get_object_or_404(SendMessage, id=message_id)
    return render(request, 'send_message_detail.html', {'message': message})


def send_message_delete(request, message_id):
  
    message = get_object_or_404(SendMessage, id=message_id)
    message.delete()
    messages.success(request, "паём бо муваффақият ҳазф шуд!")
    return redirect('send_message_list')


