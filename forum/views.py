from django.shortcuts import render, get_object_or_404

# Create your views here.

from django.contrib.auth.models import User
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Course, Topic, Thread, Reply
from .serializers import (CourseSerializer, TopicSerializer,
                           ThreadSerializer, ReplySerializer)

from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

def get_user():
    return User.objects.get(username='admin')
    
@method_decorator(csrf_exempt, name='dispatch')
class CourseListView(APIView):
    def get(self, request):
        courses = Course.objects.all()
        serializer = CourseSerializer(courses, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = CourseSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data,status=status.HTTP_201_CREATED)
        return Response(serializer.errors,status=status.HTTP_400_BAD_REQUEST)

@method_decorator(csrf_exempt, name='dispatch')
class TopicListView(APIView):
    def get(self, request):
        course_id = request.query_params.get('course')
        if course_id:
            topics = Topic.objects.filter(course_id=course_id)
        else:
            topics = Topic.objects.all()
        serializer = TopicSerializer(topics, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = TopicSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data,status=status.HTTP_201_CREATED)
        return Response(serializer.errors,status=status.HTTP_400_BAD_REQUEST)

@method_decorator(csrf_exempt, name='dispatch')
class ThreadListView(APIView):
    def get(self, request):
        topic_id = request.query_params.get('topic')
        if topic_id:
            threads = Thread.objects.filter(topic_id=topic_id).order_by('-created_at')
        else:
            threads = Thread.objects.all().order_by('-created_at')
        serializer = ThreadSerializer(threads, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = ThreadSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(created_by=get_user())
            return Response(serializer.data,status=status.HTTP_201_CREATED)
        return Response(serializer.errors,status=status.HTTP_400_BAD_REQUEST)

@method_decorator(csrf_exempt, name='dispatch')
class ReplyListView(APIView):
    def get(self, request, thread_id):
        replies = Reply.objects.filter(thread_id=thread_id)
        serializer = ReplySerializer(replies, many=True)
        return Response(serializer.data)

    def post(self, request, thread_id):
        serializer = ReplySerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(
                thread_id=thread_id,
                author=get_user(),
                is_ai_response=False
            )
            return Response(serializer.data,status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



def course_list_view(request):
    courses = Course.objects.all()
    return render(request, 'forum/course_list.html', {
        'courses': courses
    })

def course_forum_view(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    topics = Topic.objects.filter(course=course).order_by('id')
    general = topics.filter(name='General Discussion')
    other = topics.exclude(name='General Discussion')
    topics = list(general) + list(other)
    return render(request, 'forum/course_forum.html', {
        'course': course,
        'topics': topics
    })
