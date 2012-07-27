from django.core.exceptions import ImproperlyConfigured
from .decorators import cache_page
from .settings import HIVER_SETTINGS


class CacheMixin(object):

    cache_path = None
    cache_duration = HIVER_SETTINGS['cache_duration']

    def dispatch(self, request, *args, **kwargs):
        # Verify class settings
        if self.cache_path == None:
            raise ImproperlyConfigured("'CacheMixin' requires "
                "'cache_path' attribute to be set.")
        if self.cache_duration == None:
            raise ImproperlyConfigured("'CacheMixin' requires "
                "'cache_duration' attribute to be set.")

        return cache_page(self.cache_duration, self.cache_path)(super(
            CacheMixin, self).dispatch)(request, *args, **kwargs)
