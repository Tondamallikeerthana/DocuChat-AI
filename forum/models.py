from django.db import models

# Create your models here.

from django.contrib.auth.models import User

class Course(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name

class Topic(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE,related_name='topics')
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)

    def __str__(self):
        return f"{self.course.name} → {self.name}"
    
class Thread(models.Model):
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE,related_name='threads')
    title = models.CharField(max_length=500)
    description = models.TextField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title
    
class Reply(models.Model):
    thread = models.ForeignKey(Thread, on_delete=models.CASCADE,related_name='replies')
    content = models.TextField()
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    is_ai_response = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        label = 'AI' if self.is_ai_response else str(self.author)
        return f"Reply in '{self.thread.title}' by {label}"
    
    
class ChatSession(models.Model):
    SOURCE_CHOICES = [('document', 'Document Upload'), ('text', 'Text Upload')]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='chat_sessions')
    source_type = models.CharField(max_length=10, choices=SOURCE_CHOICES)
    title = models.CharField(max_length=255, blank=True)
    is_ready = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.get_source_type_display()} - {self.created_at:%Y-%m-%d %H:%M}"


class ChatMessage(models.Model):
    ROLE_CHOICES = [('user', 'User'), ('ai', 'AI')]

    session = models.ForeignKey(ChatSession, on_delete=models.CASCADE, related_name='messages')
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"[{self.role}] {self.content[:40]}"