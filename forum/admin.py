from django.contrib import admin
from .models import Course, Topic, Thread, Reply, ChatSession, ChatMessage

admin.site.register(Course)
admin.site.register(Topic)
admin.site.register(Thread)
admin.site.register(Reply)
admin.site.register(ChatSession)
admin.site.register(ChatMessage)