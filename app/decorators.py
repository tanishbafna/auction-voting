from functools import wraps
from flask import redirect
from flask_login import current_user

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_admin:
            return redirect('/', code=401)
        return f(*args, **kwargs)
    return decorated_function