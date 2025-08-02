from django.conf import settings

def site_context(request):
    """Add site-wide context variables"""
    return {
        'SITE_NAME': 'GYWAN',
        'SITE_DESCRIPTION': 'Girls and Young Women\'s Advocacy Network',
        'STRIPE_PUBLIC_KEY': getattr(settings, 'STRIPE_PUBLIC_KEY', ''),
        'DEBUG': settings.DEBUG,
    }
