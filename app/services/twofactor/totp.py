import pyotp


def get_otp(token: str) -> str:
    totp = pyotp.TOTP(token)
    return totp.now()