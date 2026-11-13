from django.contrib.auth.decorators import user_passes_test


def es_admin(user):
    """El administrador del complejo es un usuario con is_staff."""
    return user.is_authenticated and user.is_staff


# Decorador para las vistas del panel de administración.
solo_admin = user_passes_test(es_admin, login_url='app_usuarios:login')
