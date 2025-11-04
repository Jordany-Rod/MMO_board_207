from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import send_mail
from django.conf import settings
from .models import Reply


@receiver(post_save, sender=Reply)
def notify_about_new_reply(sender, instance, created, **kwargs):
    """
    Отправка уведомления автору объявления о новом отклике
    """
    if created:  # Только при создании нового отклика
        subject = f'Новый отклик на ваше объявление "{instance.post.title}"'
        message = f'''Пользователь {instance.author.username} оставил отклик:

{instance.text}

Просмотреть все отклики: {settings.SITE_URL}/profile/''' # Ссылка на приватную страницу

        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[instance.post.author.email], # Отправка автору объявления
            fail_silently=False, # Выбрасывать исключение при ошибке отправки
        )


@receiver(post_save, sender=Reply)
def notify_about_accepted_reply(sender, instance, **kwargs):
    """
    Отправка уведомления автору отклика о его принятии
    """
    if instance.is_accepted and instance.pk:  # Если отклик принят и уже существует в БД
        # Проверяем, изменился ли статус принятия
        try:
            old_instance = Reply.objects.get(pk=instance.pk)
            if not old_instance.is_accepted:  # Если статус изменился с непринятого на принятый
                subject = f'Ваш отклик принят!'
                message = f'''Ваш отклик на объявление "{instance.post.title}" был принят автором.

Текст отклика:
{instance.text}

Связаться с автором: {instance.post.author.email}'''

                send_mail(
                    subject=subject,
                    message=message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[instance.author.email],
                    fail_silently=False,
                )
        except Reply.DoesNotExist:
            pass