"""Core utility functions."""

import uuid
from django.utils.text import slugify
from django.core.mail import send_mail
from django.conf import settings
from PIL import Image
from io import BytesIO
import os

def generate_unique_slug(base_slug, model_class, exclude_id=None):
    """Generate a unique slug for a model."""
    slug = slugify(base_slug)
    original_slug = slug
    counter = 1
    
    query = model_class.objects.filter(slug=slug)
    if exclude_id:
        query = query.exclude(id=exclude_id)
    
    while query.exists():
        slug = f'{original_slug}-{counter}'
        query = model_class.objects.filter(slug=slug)
        if exclude_id:
            query = query.exclude(id=exclude_id)
        counter += 1
    
    return slug


def compress_image(image_field, max_width=1200, max_height=1200, quality=85):
    """Compress image for optimization."""
    try:
        img = Image.open(image_field)
        
        # Convert RGBA to RGB
        if img.mode in ('RGBA', 'LA', 'P'):
            rgb_img = Image.new('RGB', img.size, (255, 255, 255))
            rgb_img.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
            img = rgb_img
        
        # Resize if larger than max dimensions
        img.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)
        
        # Save compressed image
        output = BytesIO()
        img.save(output, format='JPEG', quality=quality, optimize=True)
        output.seek(0)
        
        return output
    except Exception as e:
        print(f'Error compressing image: {str(e)}')
        return image_field


def send_email(subject, message, recipient_list, html_message=None):
    """Send email with error handling."""
    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=recipient_list,
            html_message=html_message,
            fail_silently=False,
        )
        return True
    except Exception as e:
        print(f'Error sending email: {str(e)}')
        return False


def generate_order_number():
    """Generate unique order number."""
    import datetime
    timestamp = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
    unique_id = uuid.uuid4().hex[:6].upper()
    return f'ORD-{timestamp}-{unique_id}'


def calculate_discount(price, discount_percentage):
    """Calculate discounted price."""
    if discount_percentage > 0:
        discount_amount = (price * discount_percentage) / 100
        return price - discount_amount
    return price
