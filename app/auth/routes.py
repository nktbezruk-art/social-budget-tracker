from . import auth_bp

@auth_bp.route("/login")
def login():
    return "<h1>Login page</h1>"


@auth_bp.route("/register")
def registration():
    return "<h1>Register page</h1>"


@auth_bp.route("/logout")
def logout():
    return "<h1>Logout page</h1>"
