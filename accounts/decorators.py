from django.contrib.auth.decorators import user_passes_test

def admin_required(view_func):
    return user_passes_test(lambda u: u.is_authenticated and u.groups.filter(name="admin").exists())(view_func)

def student_required(view_func):
    return user_passes_test(lambda u: u.is_authenticated and u.groups.filter(name="student").exists())(view_func)