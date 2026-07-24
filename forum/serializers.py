from rest_framework import serializers
from .models import Course, Topic, Thread, Reply

class CourseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Course
        fields = ['id', 'name', 'description']

class TopicSerializer(serializers.ModelSerializer):
    class Meta:
        model = Topic
        fields = ['id', 'name', 'description', 'course']

class ReplySerializer(serializers.ModelSerializer):
    author_name = serializers.SerializerMethodField()

    class Meta:
        model = Reply
        fields = ['id', 'content', 'author_name', 'is_ai_response', 'created_at']
    
    def get_author_name(self, obj):
        if obj.is_ai_response:
            return 'AI'
        return obj.author.username if obj.author else 'Unknown'
    
class ThreadSerializer(serializers.ModelSerializer):
    replies = ReplySerializer(many=True, read_only=True)
    created_by_name = serializers.SerializerMethodField()

    class Meta:
        model = Thread
        fields = ['id', 'title', 'description', 'topic', 'created_by_name','created_at', 'replies']
    
    def get_created_by_name(self, obj):
        return obj.created_by.username