from . import main_bp
from flask import redirect, url_for
from flask_login import login_required


@main_bp.route("/")
@login_required
def index():
    return redirect(url_for("transactions.transaction_main"))
