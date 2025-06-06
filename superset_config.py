ENABLE_PROXY_FIX = True
FEATURE_FLAGS = {
    "ENABLE_TEMPLATE_PROCESSING": True
}
SECRET_KEY = 'oHevZfjXw5MX6h4x5CqDeupZtIhR8oU6v3KdF0No1r='

PUBLIC_ROLE_LIKE_GAMMA = True
TALISMAN_ENABLED = False
TALISMAN_CONFIG = {
    'content_security_policy': {
        'default-src': ["'self'"],
        'script-src': ["'self'", "'unsafe-inline'"],
        'style-src': ["'self'", "'unsafe-inline'"]
    }
}