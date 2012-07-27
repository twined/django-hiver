from django.conf import settings

HIVER_SETTINGS = {
    'cache_duration': 15,
    'cache_prefix': 'hiver',
    'disabled': False,
    'global_generation_id': 'hiver.gen',
}

HIVER_SETTINGS.update(getattr(settings, 'HIVER_SETTINGS', {}))
