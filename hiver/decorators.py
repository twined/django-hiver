# hiver

import urllib
import hashlib

from django.contrib import messages
from django.core.cache import cache
from django.http import HttpResponse
from django.utils import translation
from django.utils.encoding import iri_to_uri

from redis.exceptions import ConnectionError

from .settings import HIVER_SETTINGS

__all__ = ('cache_page',)


def cache_page(cache_duration, path):
    '''
    Decorates the view object or function - enabling us to cache
    the view's response, or serve from cache if it already exists.

    Arguments:
    cache_duration -- How many seconds to store the view in cache,
                      usually specified like 60*10 for 10 minutes.
    path           -- Path should be an unique identifier, making it
                      easier to mass delete from cache on invalidation
                      I.e: "application.view"
    '''
    def cache_page_decorator(func):
        def wrapped(request, *args, **kwargs):
            if request_is_cacheable(request):
                try:
                    key = get_cache_key(request, path)
                except ConnectionError:
                    if HIVER_SETTINGS['debug']:
                        raise
                    return func(request, *args, **kwargs)

                # checks if the key exists, and if it does, retrieves
                # response from cache, sets ETag and return response
                try:
                    cached = cache.get(key)
                except ConnectionError:
                    if HIVER_SETTINGS['debug']:
                        raise
                    return func(request, *args, **kwargs)

                if cached is not None:
                    response = HttpResponse(cached)
                    response["ETag"] = key
                    return response

                # generates a response by calling decorated function
                response = func(request, *args, **kwargs)
                # checks if it is something we can stick in cache
                if response_is_cacheable(request, response):
                    # we can. grabs the properly rendered content
                    # and sets the cache
                    content = get_content(response)
                    try:
                        cache.set(key, content, timeout=cache_duration,
                            version=get_cache_generation())
                    except ConnectionError:
                        if HIVER_SETTINGS['debug']:
                            raise
                        return func(request, *args, **kwargs)

                # sets the response's ETag header to the key we made,
                # and returns the response to client
                response["ETag"] = key
                return response

            # request is not retrievable, return the wrapped function
            return func(request, *args, **kwargs)

        return wrapped

    return cache_page_decorator


def get_content(response):
    '''
    Returns a rendered response, ready to be inserted into cache.

    Arguments:
    response -- The Django response object, which we check to see if
                needs rendering, or not.
    '''
    return response.render() if hasattr(response, 'render') and \
        callable(response.render) else response.content


def get_cache_generation():
    '''
    Queries cache for a generation number. If none is found, it is
    added to the cache with a value of 1.
    '''
    generation_number = cache.get(HIVER_SETTINGS['global_generation_id'])
    if not generation_number:
        cache.set(HIVER_SETTINGS['global_generation_id'], 1, 0)
        generation_number = 1

    return generation_number


def get_cache_key(request, path):
    '''
    Builds an unique cachekey base on prefix, generation id,
    request.path, any GET parameters, language and current
    authenticated user's id (if any).

    Arguments:
    request -- The Django request we are building a key for
    path    -- Path should be an unique identifier, making it easier
               to mass delete from cache on invalidation
               I.e: "application.view"
    '''

    user_id = ""
    try:
        if request.user.is_authenticated():
            user_id = str(request.user.id)
    except AttributeError:
        # auth not installed? not our problem.
        pass

    # builds the key
    key = "/".join((
        HIVER_SETTINGS['cache_prefix'],
        str(get_cache_generation()),
        iri_to_uri(request.path),
        urllib.urlencode(request.GET),
        translation.get_language(),
        user_id,
    ))

    # return the hashed key, but with our path prepended, so we can
    # easily delete its pattern with redis.
    return path + '/' + hashlib.md5(key).hexdigest()


def request_is_cacheable(request):
    '''
    Checks if we can cache the request. The request must be a GET
    and also cannot have any messages waiting to be displayed.
    '''
    return (not HIVER_SETTINGS['disabled']) and \
            request.method == "GET" and \
            len(messages.get_messages(request)) == 0


def response_is_cacheable(request, response):
    '''
    Checks if we can cache the response. Only returns True if
    response has status_code 200, and is not explicitly set with a
    "no-cache" header, as well as any Vary cookies in it.
    '''
    return (not HIVER_SETTINGS['disabled']) and \
            response.status_code == 200 and \
            response.get('Pragma', None) != "no-cache" and \
            response.get('Vary', None) != "Cookie" and \
            not request.META.get("CSRF_COOKIE_USED", None)
