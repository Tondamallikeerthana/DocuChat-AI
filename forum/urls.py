from django.contrib.auth import views as auth_views
from django.urls import path
from . import views, chat_views

urlpatterns = [
    # --- auth ---
    path('login/', chat_views.ForumLoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),

    # --- chatbot ---
    path('', chat_views.home_view, name='home'),
    path('chat/new/', chat_views.mode_select_view, name='mode-select'),
    path('chat/create/', chat_views.create_session_view, name='create-session'),
    path('chat/sessions/', chat_views.my_sessions_view, name='my-sessions'),
    path('chat/<int:session_id>/', chat_views.chat_session_view, name='chat-session'),
    path('chat/<int:session_id>/send/', chat_views.send_message_view, name='send-message'),

    # --- old forum API + pages (kept, unlinked from nav) ---
    path('api/courses/', views.CourseListView.as_view()),
    path('api/topics/', views.TopicListView.as_view()),
    path('api/threads/', views.ThreadListView.as_view()),
    path('api/threads/<int:thread_id>/replies/', views.ReplyListView.as_view()),
    path('courses/', views.course_list_view, name='course-list'),
    path('course/<int:course_id>/forum/', views.course_forum_view, name='forum'),
]