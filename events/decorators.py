from django.contrib.auth.decorators import user_passes_test

def organizer_required(view_func):
    decorator = user_passes_test(lambda u: u.is_authenticated and u.groups.filter(name="organizer").exists())
    return decorator(view_func)

def admin_required(view_func):
    decorator = user_passes_test(lambda u: u.is_authenticated and u.groups.filter(name="admin").exists())
    return decorator(view_func)