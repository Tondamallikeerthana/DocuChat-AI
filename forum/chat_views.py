import os

from django.conf import settings
from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST

from langchain_core.documents import Document

from .models import ChatSession, ChatMessage
from .services.rag_pipeline.session_builder import (
    load_single_file,
    build_session_store_from_documents,
    load_session_store,
)
from .services.rag_pipeline.qa import answer_from_store


class ForumLoginView(auth_views.LoginView):
    template_name = 'forum/login.html'


@login_required
def home_view(request):
    return redirect('my-sessions')


@login_required
def mode_select_view(request):
    return render(request, 'forum/mode_select.html')


@login_required
def create_session_view(request):
    if request.method != 'POST':
        return redirect('mode-select')

    source_type = request.POST.get('source_type')
    if source_type not in ('document', 'text'):
        return render(request, 'forum/mode_select.html', {'error': 'Please choose a source type.'})

    session = ChatSession.objects.create(user=request.user, source_type=source_type)

    try:
        if source_type == 'document':
            uploaded_file = request.FILES.get('document')
            if not uploaded_file:
                session.delete()
                return render(request, 'forum/mode_select.html', {'error': 'Please choose a file to upload.'})

            upload_dir = os.path.join(settings.MEDIA_ROOT, 'session_uploads', str(session.id))
            os.makedirs(upload_dir, exist_ok=True)
            file_path = os.path.join(upload_dir, uploaded_file.name)
            with open(file_path, 'wb+') as dest:
                for chunk in uploaded_file.chunks():
                    dest.write(chunk)

            documents = load_single_file(file_path)
            session.title = uploaded_file.name
        else:
            text = request.POST.get('text_content', '').strip()
            if not text:
                session.delete()
                return render(request, 'forum/mode_select.html', {'error': 'Please paste some text.'})

            documents = [Document(page_content=text, metadata={'source': 'pasted-text'})]
            session.title = (text[:40] + '...') if len(text) > 40 else text

        build_session_store_from_documents(session.id, documents)
        session.is_ready = True
        session.save()

    except Exception as e:
        session.delete()
        return render(request, 'forum/mode_select.html', {'error': f'Could not process your input: {e}'})

    return redirect('chat-session', session_id=session.id)


@login_required
def chat_session_view(request, session_id):
    session = get_object_or_404(ChatSession, id=session_id, user=request.user)
    messages = session.messages.order_by('created_at')
    return render(request, 'forum/chat.html', {'session': session, 'messages': messages})


@login_required
@require_POST
def send_message_view(request, session_id):
    session = get_object_or_404(ChatSession, id=session_id, user=request.user)
    content = (request.POST.get('content') or '').strip()
    if not content:
        return JsonResponse({'error': 'Empty message'}, status=400)

    ChatMessage.objects.create(session=session, role='user', content=content)

    try:
        store = load_session_store(session.id)
        answer = answer_from_store(store, content)
    except Exception as e:
        answer = f"Sorry, I couldn't process that: {e}"

    ChatMessage.objects.create(session=session, role='ai', content=answer)

    return JsonResponse({'answer': answer})


@login_required
def my_sessions_view(request):
    sessions = request.user.chat_sessions.order_by('-created_at')
    return render(request, 'forum/session_list.html', {'sessions': sessions})