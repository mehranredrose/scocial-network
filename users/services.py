import random

from django.db import transaction

from .models import OtpCode, User, Profile

from sms_ir import SmsIr


def send_otp(phone_number):
    code = random.randint(10000, 100000)
    number = 30007732901955
    api_key = '1J8wpKE4VbdH6vYRkWItvpZj3nEXmesJVV84zI5NDL1WHYWf0PTg9rOuAKw68r5k'
    message = f"""با سلام. این پیام برای فعال سازی اکانت شما در wish forum است. 
code : {code}
اگر شما برای فعال سازی اکانت اقدام نفرمودید این پیام را نادیده بگیرید.
    """
    sms_ir = SmsIr(
        api_key,
        number,
    )
    response = sms_ir.send_sms(
        phone_number,
        message,
        number,
    )
    OtpCode.objects.create(phone_number=phone_number, code=code)
    print(response)


def create_user(email: str, phone_number: str, username: str, password: str) -> User:
    return User.objects.create_user(email=email, phone_number=phone_number, username=username, password=password)


@transaction.atomic
def register_user(email: str, phone_number: str, username: str, password: str, bio: str) -> User:
    user = create_user(email=email, phone_number=phone_number, username=username, password=password)
    #create_profile(user=user, bio=bio)
    return user

