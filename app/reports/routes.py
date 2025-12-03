from . import reports_bp
from flask_login import login_required

@reports_bp.route("/")
@login_required
def overview():
    return "<h1>General overview</h1>"


@reports_bp.route("/categories")
@login_required
def categories():
    return "<h1>Categories report</h1>"


@reports_bp.route("/monthly")
@login_required
def monthly():
    return "<h1>Monthly statistics</h1>"
