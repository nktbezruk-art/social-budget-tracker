from . import social_bp
from flask_login import login_required

@social_bp.route("/")
@login_required
def social_main():
    return "<h1>Social features</h1>"


@social_bp.route("/friends")
@login_required
def friends():
    return "<h1>Friends</h1>"
