from . import social_bp

@social_bp.route("/")
def social_main():
    return "<h1>Social features</h1>"


@social_bp.route("/friends")
def friends():
    return "<h1>Friends</h1>"
