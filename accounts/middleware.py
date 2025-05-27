"""
Middleware — это класс (или функция), который обрабатывает каждый HTTP-запрос и/или ответ.
Он может:

    Модифицировать запрос до того, как он попадёт во view.
    Модифицировать ответ, который возвращается пользователю.
    Выполнять "глобальные" проверки (например, аутентификацию, логирование, ограничение по времени и т.д.).
"""
from datetime import datetime

"""
Для чего ещё может пригодиться middleware?

    Логирование всех запросов (в файл или БД)
    Автоматическое обновление последнего времени активности пользователя
    Вставка заголовков или кук во все ответы
    Ограничение количества запросов (rate limiting)
    Глобальная обработка ошибок (например, кастомные 403/404/500 страницы)

"""
import logging

from django.shortcuts import redirect
from django.urls import reverse
from django.utils import timezone


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