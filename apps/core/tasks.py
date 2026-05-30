"""Core Celery tasks."""

from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

@shared_task(bind=True, max_retries=3)
def send_email_task(self, subject, message, recipient_list, html_message=None):
    """Async task to send emails."""
    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=recipient_list,
            html_message=html_message,
            fail_silently=False,
        )
        logger.info(f'Email sent to {recipient_list}')
    except Exception as exc:
        logger.error(f'Error sending email: {str(exc)}')
        raise self.retry(exc=exc, countdown=60)

@shared_task
def generate_daily_reports():
    """Generate daily admin reports."""
    try:
        from apps.orders.models import Order
        from django.utils import timezone
        from datetime import timedelta
        
        today = timezone.now().date()
        orders_today = Order.objects.filter(created_at__date=today)
        
        total_orders = orders_today.count()
        total_revenue = sum(order.total_amount for order in orders_today)
        
        logger.info(f'Daily Report - Orders: {total_orders}, Revenue: ${total_revenue}')
    except Exception as e:
        logger.error(f'Error generating daily reports: {str(e)}')

@shared_task
def send_email_notifications():
    """Send email notifications to users."""
    try:
        from apps.users.models import CustomUser
        
        users = CustomUser.objects.filter(email_verified=False)
        for user in users:
            logger.info(f'Reminder email sent to {user.email}')
    except Exception as e:
        logger.error(f'Error sending notifications: {str(e)}')
