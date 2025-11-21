from . import transactions_bp

@transactions_bp.route("/")
def transaction_main():
    return "<h1>Transactions page</h1>"


@transactions_bp.route("/add")
def add_transaction():
    return "<h1>Add a transaction</h1>"


@transactions_bp.route("/delete")
def delete_transaction():
    return "<h1>Delete transaction</h1>"
