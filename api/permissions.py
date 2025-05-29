from rest_framework.permissions import BasePermission


class IsMentor(BasePermission):
    """
    Разрешает доступ только пользователям с ролью 'mentor'.
    Предполагается, что у user есть поле 'role'.
    """

    def has_permission(self, request, view):
        return request.user.is_authenticated and getattr(request.user, 'is_mentor', False)
