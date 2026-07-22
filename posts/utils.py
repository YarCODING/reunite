import requests
import time
from django.utils import translation
from django.core.mail import EmailMessage
from django.conf import settings
from pgvector.django import CosineDistance
from .models import Item
from django.utils.translation import gettext as _

MODEL_URL = "https://router.huggingface.co/hf-inference/models/intfloat/multilingual-e5-large/pipeline/feature-extraction"

def get_text_embedding(text):
    headers = {"Authorization": f"Bearer {settings.HF_API_KEY}"}
    
    payload = {"inputs": text}
    
    for attempt in range(3):
        try:
            response = requests.post(MODEL_URL, headers=headers, json=payload, timeout=10)
            result = response.json()
            
            if response.status_code == 200:
                if isinstance(result, list) and len(result) > 0 and isinstance(result[0], list):
                    return result[0]
                return result
                
            elif isinstance(result, dict) and "currently loading" in result.get("error", ""):
                time.sleep(5)
                continue
                
            else:
                print(f"Hugging Face returned an error: {result}")
                
        except requests.exceptions.RequestException as e:
            print(f"Network error (Attempt {attempt + 1}): {e}")
            time.sleep(2)
            continue
            
        break
        
    return None

def check_matches_and_notify(new_post):
    if not new_post.embedding:
        full_text = f"{new_post.title} {new_post.description}"
        new_post.embedding = get_text_embedding(full_text)
        new_post.save(update_fields=['embedding'])
    
    if not new_post.embedding:
        return

    opposite_type = 'found' if new_post.type == 'lost' else 'lost'
    
    DISTANCE_THRESHOLD = 0.12
    
    matches = (
        Item.objects.filter(type=opposite_type)
        .annotate(distance=CosineDistance('embedding', new_post.embedding))
        .filter(distance__lt=DISTANCE_THRESHOLD)
        .order_by('distance')
    )
    
    for post in matches:
        lost_post = new_post if new_post.type == 'lost' else post
        found_post = post if new_post.type == 'lost' else new_post

        user_lang = lost_post.user.profile.lang
        
        with translation.override(user_lang):
            subject = _("Match found!")
            body = _(
                "Hello!\n\n"
                "AI checked new listings and believes that the item from the listing '{lost_title}' "
                "might match the found item '{found_title}'.\n\n"
                "Take a look at the description of the found item:\n{found_description}"
            ).format(
                lost_title=lost_post.title,
                found_title=found_post.title,
                found_description=found_post.description
            )
            
            email = EmailMessage(
                subject=subject,
                body=body,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[lost_post.user.email],
            )
            
            email.content_subtype = "plain"
            email.encoding = "utf-8"
            
            email.send(fail_silently=True)