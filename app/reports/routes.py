from . import reports_bp

@reports_bp.route("/")
def overview():
    return "<h1>General overview</h1>"


@reports_bp.route("/categories")
def categories():
    return "<h1>Categories report</h1>"


@reports_bp.route("/monthly")
def monthly():
    return "<h1>Monthly statistics</h1>"
