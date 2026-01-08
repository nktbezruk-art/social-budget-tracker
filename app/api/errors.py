def api_error(message, code=400, details=None):
    return {
        "error": {
            "code": code,
            "message": message,
            "details": details or {}
        }
    }, code
