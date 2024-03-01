from django import forms
from .models import Profile, OtpCode, User
from django.core.validators import MinLengthValidator
from captcha.fields import ReCaptchaField
from captcha.widgets import ReCaptchaV2Checkbox
from django.core.exceptions import ValidationError
from extensions.validators import (number_validator,
                                   username_validator,
                                   special_char_validator,
                                   letter_validator,
                                   email_validator)

class UserCreationForm(forms.ModelForm):
    password = forms.CharField(label='password', widget=forms.PasswordInput)
    confirm_password = forms.CharField(label='confirm password', widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ('email', 'phone_number', 'username', 'password', 'confirm_password',)

    def clean_confirm_password(self):
        cd = self.cleaned_data
        if cd.get('password') and cd.get('confirm_password') and cd['password'] != cd['confirm_password']:
            raise forms.ValidationError('Passwords do not match')
        return cd['confirm_password']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])
        if commit:
            user.save()
        return user


class UserRegisterForm(UserCreationForm):
    #email = forms.EmailField()
    email = forms.EmailField(validators=[
        email_validator
    ])
    phone_number = forms.CharField(max_length=11, validators=[
        number_validator,
        MinLengthValidator(limit_value=11)
    ])
    username = forms.CharField(max_length=255, validators=[
        username_validator,
        MinLengthValidator(limit_value=4)
    ])
    password = forms.CharField(widget=forms.PasswordInput, validators=[
        special_char_validator,
        letter_validator,
        number_validator,
        MinLengthValidator(limit_value=10),
    ])
    confirm_password = forms.CharField(widget=forms.PasswordInput)
    bio = forms.CharField(required=False)
    #captcha = ReCaptchaField(widget=ReCaptchaV2Checkbox)
    def clean_email(self):
        email = self.cleaned_data['email']
        user = User.objects.filter(email=email).exists()
        if user:
            raise ValidationError('This email already exists')
        return email

    def clean_phone_number(self):
        phone = self.cleaned_data['phone_number']
        user = User.objects.filter(phone_number=phone).exists()
        if user:
            raise ValidationError('This phone number already exists')
        OtpCode.objects.filter(phone_number=phone).delete()
        return phone

    # class Meta:
    #     model = User
    #     fields = ['first_name','last_name','username','email','password1','password2']

class UserEnterVerifyCodeForm(forms.Form):
    code = forms.CharField(max_length=5, validators=[
        number_validator,
        MinLengthValidator(5),
    ])

class UserUpdateForm(forms.ModelForm):
    email = forms.EmailField()

    class Meta:
        model = User
        fields = ('email', 'phone_number', 'username',)


class ProfileUpdateForm(forms.ModelForm):
    x = forms.FloatField(widget=forms.HiddenInput(), required=False)
    y = forms.FloatField(widget=forms.HiddenInput(), required=False)
    width = forms.FloatField(widget=forms.HiddenInput(), required=False)
    height = forms.FloatField(widget=forms.HiddenInput(), required=False)

    class Meta:
        model = Profile
        fields = ['bio','date_of_birth',]
    
class UserLoginForm(forms.Form):
    email = forms.EmailField()
    password = forms.CharField(widget=forms.PasswordInput)  
    
    
class UserResetPasswordForm(forms.ModelForm):
    # password = forms.CharField(widget=forms.PasswordInput(), required=True)
    new_password = forms.CharField(widget=forms.PasswordInput(), required=True,
                                   validators=[
                                       special_char_validator,
                                       letter_validator,
                                       number_validator,
                                       MinLengthValidator(limit_value=10),
                                   ])
    confirm_password = forms.CharField(widget=forms.PasswordInput(), required=True)
    captcha = ReCaptchaField(widget=ReCaptchaV2Checkbox)

    class Meta:
        model = User
        fields = ('new_password', 'confirm_password', 'captcha',)

    def clean_confirm_password(self):
        cd = self.cleaned_data
        password = cd.get('new_password')
        confirm_password = cd.get('confirm_password')
        if password != confirm_password and password and confirm_password:
            raise forms.ValidationError("New Password and Confirm Password don't match")