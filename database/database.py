def init_db():
    return {
        "user_template": {
            "login": str,
            "password": str,
        },
        "users": {}
    }