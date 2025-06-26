"""
Middleware — это класс (или функция), который обрабатывает каждый HTTP-запрос и/или ответ.
Он может:

    Модифицировать запрос до того, как он попадёт во view.
    Модифицировать ответ, который возвращается пользователю.
    Выполнять "глобальные" проверки (например, аутентификацию, логирование, ограничение по времени и т.д.).
"""
import os
import shutil
from datetime import datetime, date
import hashlib
import time
import re
import logging

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied
from django.http import Http404, JsonResponse, HttpResponseForbidden
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils import timezone

import redis

from .middleware_base import ClientIPMixin

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


class RequestFingerprintMiddleware(ClientIPMixin):
    """
    Middleware для фиксации и проверки 'отпечатка' пользователя на основе IP и user-agent.
    Logout если меняется user-agent
    """

    FINGERPRINT_KEY = '_request_fingerprint'

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Получаем значения для отпечатка
        ip = self.get_client_ip(request)
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        # Можно добавить и другие параметры, например, cookie или language
        raw_fingerprint = f'{ip}|{user_agent}'
        fingerprint = hashlib.sha256(raw_fingerprint.encode()).hexdigest()
        session = getattr(request, 'session', None)

        # Если сессии нет (например, для анонимных пользователей без cookies), пропускаем
        if session is not None:
            stored_fp = session.get(self.FINGERPRINT_KEY)
            if stored_fp is None:
                # Первый запрос — сохраняем отпечаток
                session[self.FINGERPRINT_KEY] = fingerprint
            else:
                if stored_fp != fingerprint:
                    # Отпечаток изменился — можно разлогинить, залогировать или выдать предупреждение
                    # Например, разлогиним пользователя:
                    from django.contrib.auth import logout
                    logout(request)
                    session.flush()  # очищает сессию
                    from django.http import HttpResponseForbidden
                    return HttpResponseForbidden('Session fingerprint mismatch detected. You have been logged out for security reasons.')
        response = self.get_response(request)
        return response


class AntiDoubleSubmitMiddleware:
    """
    Middleware для предотвращения повторной отправки одинаковых POST-запросов (anti-double submit).
    Сохраняет хеш последнего POST-запроса в сессии. Если такой же запрос повторяется в течение короткого времени — блокирует его.
    """

    SESSION_KEY = '_last_post_hash'
    TIME_KEY = '_last_post_time'
    BLOCK_INTERVAL = 10  # секунд, в течение которых повтор считается дубликатом

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.method == 'POST':
            # Получаем уникальный хеш для этого запроса
            unique_string = (
                    request.path +
                    str(sorted(request.POST.items())) +
                    str(sorted(request.FILES.items()))  # Сортировка нужна, чтобы порядок полей не влиял на хеш
            )

            # Создаём криптографический хеш этой строки.
            # Это важно, чтобы быстро сравнивать содержимое
            # (а не хранить большие объёмы данных в сессии).
            post_hash = hashlib.sha256(unique_string.encode()).hexdigest()
            session = getattr(request, 'session', None)
            now = time.time()

            if session is not None:
                last_hash = session.get(self.SESSION_KEY)
                last_time = session.get(self.TIME_KEY, 0)
                # Если совпадает хеш и прошло мало времени — считаем дубликатом
                if last_hash == post_hash and now - last_time < self.BLOCK_INTERVAL:
                    from django.http import HttpResponse
                    return HttpResponse('Form was already sent. Please don\'t send it again.')

                # Если дубликата нет — сохраняем новый хеш и время в сессии пользователя.
                # Это нужно для сравнения при следующем запросе.
                session[self.SESSION_KEY] = post_hash
                session[self.TIME_KEY] = now

        return self.get_response(request)


logger = logging.getLogger('sql_injection_protection')

class InstantSQLInjectionBlockMiddleware(ClientIPMixin):
    """
    Middleware для мгновенной блокировки/логирования при попытке SQL-инъекции.
    Проверяет query string и body на подозрительные паттерны.
    """

    # Список регулярных выражений для поиска типичных SQL-инъекций
    SQLI_PATTERNS = [
        r"(?i)(\bOR\b|\bAND\b)\s+\d+=\d+",  # ... OR 1=1, AND 1=1 и т.д.
        r"(?i)union\s+select",  # UNION SELECT
        r"(?i)select.+from",  # SELECT ... FROM
        r"(?i)insert\s+into",  # INSERT INTO
        r"(?i)drop\s+table",  # DROP TABLE
        r"(?i)update\s+\w+\s+set",  # UPDATE x SET
        r"(?i)delete\s+from",  # DELETE FROM
        r"(?i)--",  # SQL комментарий --
        r"(?i)\bxp_cmdshell\b",  # xp_cmdshell (MSSQL backdoor)
        r"(?i)benchmark\s*\(",  # BENCHMARK (MySQL)
        r"(?i)sleep\s*\(",  # SLEEP (MySQL)
        r"(?i)information_schema",  # INFORMATION_SCHEMA
        r"(?i)\bload_file\s*\(",  # LOAD_FILE(
        r"(?i)\boutfile\b",  # INTO OUTFILE
        r"(?i)char\([^)]+\)",  # char(ASCII,...)
        r"(?i)waitfor\s+delay",  # WAITFOR DELAY
        r"(?i)';?\s*--",  # '; --
        r"(?i)\";?\s*--",  # "; --
        r"(?i)\bexec\b",  # exec
        r"(?i)cast\s*\(",  # cast(
        r"(?i)having\s+\d+=\d+",  # HAVING 1=1
    ]

    def __init__(self, get_response):
        self.get_response = get_response
        self.compiled_patterns = [re.compile(pattern) for pattern in self.SQLI_PATTERNS]


    def __call__(self, request):
        # Составляем все строки для проверки: query string, POST, URL
        suspect_sources = []
        suspect_sources.append(request.get_full_path())
        suspect_sources.extend([f'{k}={v}' for k, v in request.GET.items()])
        suspect_sources.extend([f'{k}={v}' for k, v in request.POST.items()])

        # Проверяем на все паттерны
        for value in suspect_sources:
            for regex in self.compiled_patterns:
                if regex.search(value):
                    user_ip = self.get_client_ip(request)
                    logger.warning(f'[SQLI BLOCK] IP {user_ip} tried SQL injection: {value}')
                    # Здесь можно добавить бан IP (например, в Redis или БД)
                    return HttpResponseForbidden('Suspicious activity detected and blocked.')
        return self.get_response(request)


class DynamicTemplateByHolidayMiddleware:
    """
    Middleware для автоматической подмены шаблона по празднику/дате.
    Например, 1 января — подставить 'new_year.html' вместо стандартного шаблона.
    """

    # Карта дат в формате (month, day): 'template_name.html'
    DATE_TO_TEMPLATE = {
        (1, 1): 'base_new_year.html',  # 1 января — Новогодний шаблон
        (12, 31): 'base_new_year_eve.html',  # 31 декабря — шаблон для Нового года
        (3, 8): 'base_womens_day.html',  # 8 марта — Международный женский день
        (6, 26): 'base_test_today.html',  # Today test
    }

    def __init__(self, get_response):
        self.get_response = get_response
        self._already_swapped = False

    def __call__(self, request):
        today = date.today()
        key = (today.month, today.day)

        # Путь до папки с шаблонами. Исправь, если у тебя иначе!
        template_dir = os.path.join(settings.BASE_DIR, 'templates')
        base_path = os.path.join(template_dir, 'base.html')
        backup_path = os.path.join(template_dir, 'base_original.html')

        # Если сегодня праздник и шаблон ещё не подменён
        if key in self.DATE_TO_TEMPLATE:
            holiday_template = os.path.join(template_dir, self.DATE_TO_TEMPLATE[key])
            if os.path.exists(holiday_template):
                if not os.path.exists(backup_path):
                    shutil.copy2(base_path, backup_path)  # Создание резервной копии
                shutil.copy2(holiday_template, base_path)  # Вставка праздничного шаблона в рабочий шаблон

        # Если сегодня НЕ праздник, а backup существует — всегда восстанавливаем!
        elif os.path.exists(backup_path):
            shutil.copy2(backup_path, base_path)
            os.remove(backup_path)

        response = self.get_response(request)
        return response
