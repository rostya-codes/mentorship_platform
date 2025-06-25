class ClientIPMixin:
    @staticmethod
    def get_client_ip(request):
        # Попробуем корректно вытащить IP даже если есть прокси
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(",")[0].strip()
        return request.META.get('REMOTE_ADDR')
