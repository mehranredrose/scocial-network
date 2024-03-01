from .models import User, OtpCode


def get_otp_code(phone_number):
    try:
        code_instance = OtpCode.objects.get(phone_number=phone_number)
        return code_instance
    except OtpCode.DoesNotExist:
        return None


def get_user(email):
    return User.objects.get(email=email)
