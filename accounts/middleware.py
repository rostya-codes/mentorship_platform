"""
Middleware — это класс (или функция), который обрабатывает каждый HTTP-запрос и/или ответ.
Он может:

    Модифицировать запрос до того, как он попадёт во view.
    Модифицировать ответ, который возвращается пользователю.
    Выполнять "глобальные" проверки (например, аутентификацию, логирование, ограничение по времени и т.д.).
"""
from datetime import datetime

import redis
from django.contrib.auth import get_user_model
from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin

"""
Для чего ещё может пригодиться middleware?

    Ограничение количества запросов (rate limiting)
    Глобальная обработка ошибок (например, кастомные 403/404/500 страницы)

"""

"""

    process_request(self, request) — вызывается до обработки view
    process_view(self, request, view_func, view_args, view_kwargs) — вызывается перед вызовом view-функции
    process_response(self, request, response) — вызывается после обработки view

"""
import logging

from django.shortcuts import redirect
from django.urls import reverse
from django.utils import timezone

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

    def __call__(self, request, *args, **kwargs):
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


    def __call__(self, request, *args, **kwargs):
        response = self.get_response(request)
        response['X-My-Custom-Header'] = 'Value'
        response.set_cookie('my_cookie', 'cookie_value')
        return response


class RequestsLimitMiddleware:
    """
    Middleware для ограничения количества запросов от одного клиента (по IP) за определённый интервал времени.
    Использует Redis для хранения счётчиков.
    """

    LIMIT = 30
    PERIOD = 60

    def __init__(self, get_response):
        self.get_response = get_response
        self.redis = redis.Redis(host='localhost', port=6379, db=0)

    def __call__(self, request):
        client_id = self.get_client_id(request)
        redis_key = f'rl:{client_id}'

        try:
            # Если Redis недоступен — просто пропускаем (или можно вернуть ошибку)
            current = self.redis.incr(redis_key)
            if current == 1:
                self.redis.expire(redis_key, self.PERIOD)
        except redis.exceptions.ConnectionError:
            # Если Redis недоступен — просто пропускаем (или можно вернуть ошибку)
            return self.get_response(request)

        if current > self.LIMIT:
            # Лимит превышен — возвращаем ошибку 429
            retry_after = self.redis.ttl(redis_key)
            return JsonResponse(
                {
                    'error': 'Too Many Requests',
                    'detail': f'Requests limit of {self.LIMIT} per {self.PERIOD} seconds exceeded.',
                    'retry_after': retry_after,
                },
                status=429,
                headers={'Retry-After': str(retry_after)}
            )
        # Если лимит не превышен — продолжаем обработку
        return self.get_response(request)

    def get_client_id(self, request):
        # Пример: по IP-адресу (для продакшена учтите X-Forwarded-For)
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
