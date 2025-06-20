"""
Middleware — это класс (или функция), который обрабатывает каждый HTTP-запрос и/или ответ.
Он может:

    Модифицировать запрос до того, как он попадёт во view.
    Модифицировать ответ, который возвращается пользователю.
    Выполнять "глобальные" проверки (например, аутентификацию, логирование, ограничение по времени и т.д.).
"""
from datetime import datetime

from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied
from django.http import Http404, JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils import timezone

import redis

User = get_user_model()


class BlockedUserMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = getattr(request, 'user', None)
        blocked_url = reverse('blocked_page')
        allowed_urls = [reverse('logout'), reverse('admin:login'), blocked_url]

        if user and user.is_authenticated:
            is_blocked = (
                (hasattr(user, 'blocked_until') and user.blocked_until and user.blocked_until > timezone.now())
                or (hasattr(user, 'is_active') and not user.is_active)
            )
            if is_blocked:
                # Если уже на странице блокировки — не редиректим!
                if request.path not in allowed_urls:
                    return redirect('blocked_page')

        return self.get_response(request)


class LogAllRequestsMiddleware:

    def __init__(self, get_response):
        """
        если есть другие middleware после твоего — они будут вызваны,
        если твоё middleware последнее — будет вызван view-функция, которая и формирует ответ пользователю.
        """
        self.get_response = get_response

    def __call__(self, request):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        method = request.method
        path = request.path
        username = (
            request.user.username if hasattr(request, "user") and request.user.is_authenticated else "Anonymous"
        )
        ip = (
            request.META.get("HTTP_X_FORWARDED_FOR", "").split(",")[0]
            if request.META.get("HTTP_X_FORWARDED_FOR")
            else request.META.get("REMOTE_ADDR", "")
        )
        user_agent = request.META.get("HTTP_USER_AGENT", "-")

        before = datetime.now()
        # 1. ДО — код выполнится **до вью**
        response = self.get_response(request)
        # 2. ПОСЛЕ — код выполнится **после вью**
        after = datetime.now()
        response_time_ms = int((after - before).total_seconds() * 1000)

        log_line = (
            f"{timestamp} | method={method} | path={path} | user={username} | ip={ip} "
            f"| agent={user_agent} | response_time={response_time_ms}ms\n"
        )

        with open("request_logs.log", "a") as file:
            file.write(log_line)
        return response


class SaveLastActiveTimeMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if hasattr(request, 'user') and request.user.is_authenticated:
            # Обновляем поле last_active_time только для залогиненных пользователей
            user = request.user
            user.last_active_time = timezone.now()
            user.save(update_fields=['last_active_time'])
        return response


class InsertHeadersOrCookiesMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response


    def __call__(self, request):
        response = self.get_response(request)
        response['X-My-Custom-Header'] = 'Value'
        response.set_cookie('my_cookie', 'cookie_value')
        return response


class RequestsLimitMiddleware:
    """
    Middleware to limit the number of requests from a single client (by IP) within a certain time period.
    Uses Redis to store request counters.
    """

    LIMIT = 120
    PERIOD = 60

    def __init__(self, get_response):
        # print("Middleware initialized")
        self.get_response = get_response
        self.redis = redis.Redis(host='localhost', port=6379, db=0)

    def __call__(self, request):
        client_id = self.get_client_id(request)
        redis_key = f'rl:{client_id}'
        # print(f"\n--- New request ---")
        # print(f"Client IP: {client_id}")
        # print(f"Redis key: {redis_key}")

        try:
            # Increase the request counter for this client in Redis
            current = self.redis.incr(redis_key)
            # print(f'Limit of requests: {self.LIMIT} per {self.PERIOD} seconds.')
            # print(f"Current number of requests for this client: {current}")
            # If this is the first request, set the expiration time for the key
            if current == 1:
                self.redis.expire(redis_key, self.PERIOD)
                # print(f"Set expire for key {redis_key}: {self.PERIOD} seconds")
        except redis.exceptions.ConnectionError:
            # If Redis is unavailable, just let the request pass (or you can return an error)
            print("Redis is unavailable! Passing the request without limiting.")
            return self.get_response(request)

        # If the request limit is exceeded, return HTTP 429
        if current > self.LIMIT:
            retry_after = self.redis.ttl(redis_key)
            # print(f"Limit exceeded! Current: {current}, Limit: {self.LIMIT}")
            # print(f"Seconds until the limit resets: {retry_after}")
            return JsonResponse(
                {
                    'error': 'Too Many Requests',
                    'detail': f'Requests limit of {self.LIMIT} per {self.PERIOD} seconds exceeded.',
                    'retry_after': retry_after,
                },
                status=429,
                headers={'Retry-After': str(retry_after)}
            )
        # If the limit is not exceeded, continue processing the request
        # print("Limit not exceeded, request passes through.")
        return self.get_response(request)

    def get_client_id(self, request):
        # Determine client by IP address (for production use, consider the full X-Forwarded-For chain)
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
            # print(f"IP from X-Forwarded-For: {ip}")
        else:
            ip = request.META.get('REMOTE_ADDR')
            # print(f"IP from REMOTE_ADDR: {ip}")
        return ip


class CustomErrorPagesMiddleware:
    def  __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        try:
            response = self.get_response(request)
        except Http404:
            return render(request, '404.html', status=404)
        except PermissionDenied:
            return render(request, '403.html', status=403)
        except Exception:
            return render(request, '500.html', status=500)
        return response
