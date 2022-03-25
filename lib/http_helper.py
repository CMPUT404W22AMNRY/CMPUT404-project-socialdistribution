from posts.models import ContentType

def is_image_content(content_type: str) -> bool:
    return content_type.startswith('image')

def is_b64_image_content(content_type: str) -> bool:
    return content_type == ContentType.PNG or content_type == ContentType.JPG
