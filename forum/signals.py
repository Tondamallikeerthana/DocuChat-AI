import re
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Reply, Thread, Course, Topic
from .services.rag import get_rag_response


@receiver(post_save, sender=Reply)
def trigger_ai_response_from_reply(sender, instance, created, **kwargs):
    if created and not instance.is_ai_response:
        if re.search(r'@AI\b', instance.content, re.IGNORECASE):
            clean_query = re.sub(r'@AI\b', '', instance.content, flags=re.IGNORECASE).strip()
            try:
                ai_reply = get_rag_response(
                    query=clean_query,
                    thread=instance.thread
                )
            except Exception as e:
                print(f"[ERROR] Reply AI trigger failed: {e}")
                ai_reply = "Sorry, I was unable to process your question right now."
            
            Reply.objects.create(
                thread=instance.thread,
                content=ai_reply,
                is_ai_response=True,
                author=None
            )


@receiver(post_save, sender=Thread)
def trigger_ai_response_from_thread(sender, instance, created, **kwargs):
    if created:
        combined_text = f"{instance.title} {instance.description}"
        if re.search(r'@AI\b', combined_text, re.IGNORECASE):
            clean_query = re.sub(r'@AI\b', '', combined_text, flags=re.IGNORECASE).strip()
            try:
                ai_reply = get_rag_response(
                    query=clean_query,
                    thread=instance
                )
            except Exception as e:
                print(f"[ERROR] Thread AI trigger failed: {e}")
                ai_reply = "Sorry, I was unable to process your question right now."

            Reply.objects.create(
                thread=instance,
                content=ai_reply,
                is_ai_response=True,
                author=None
            )

@receiver(post_save, sender=Course)
def create_general_topic(sender, instance, created, **kwargs):
    if created:
        Topic.objects.create(
            name='General Discussion',
            description='General discussion Forum',
            course=instance
        )