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
    """

    В методе __call__ логируй нужную информацию
    Обычно это:

        метод (GET, POST и т.д.)
        путь (request.path)
        user (если аутентифицирован)
        IP-адрес
        возможно, user-agent
        время запроса (timestamp)

    Не забудь вызвать self.get_response(request)
    После логирования запрос должен идти дальше.

    Зарегистрируй middleware в settings.py
    Добавь свой класс в список MIDDLEWARE.

    В настройках Django определи логгер
    В секции LOGGING настрой хендлер для записи в файл, укажи имя логгера, уровень и путь к файлу.

    Перезапусти сервер и проверь файл логов
    Убедись, что каждый запрос теперь попадает в файл.

    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Получаем данные для лога
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

        # Формируем строку лога
        log_line = (
            f"{timestamp} | method={method} | path={path} | user={username} | ip={ip} | agent={user_agent}\n"
        )

        # Записываем в файл
        with open("request_logs.log", "a") as file:
            file.write(log_line)

        # Передаём запрос дальше
        response = self.get_response(request)
        return response
