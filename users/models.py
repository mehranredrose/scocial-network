from django.db import models
#from django.contrib.auth.models import User
from django.contrib.auth.base_user import BaseUserManager, AbstractBaseUser
from django.contrib.auth.models import PermissionsMixin
from extensions.validators import number_validator, email_validator, username_validator
from django.core.validators import MinLengthValidator
from extensions.base_models import BaseModel

class UserManager(BaseUserManager):
    def create_user(self, phone_number, email, username, password):
        if not phone_number:
            raise ValueError('user must have phone number')

        if not email:
            raise ValueError('user must have email')

        if not username:
            raise ValueError('user must have full name')

        user = self.model(phone_number=phone_number, email=self.normalize_email(email), username=username)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, phone_number, email, username, password):
        user = self.create_user(phone_number, email, username, password)
        user.is_admin = True
        user.is_superuser = True
        user.save(using=self._db)
        return user



class User(BaseModel, AbstractBaseUser, PermissionsMixin):
    phone_number = models.CharField(max_length=11, unique=True,
                                    validators=[
                                        number_validator,
                                        MinLengthValidator(11),
                                    ])
    email = models.EmailField(max_length=255, unique=True,
                              validators=[
                                  email_validator,
                              ])
    username = models.CharField(max_length=100, unique=True,
                                 validators=[
                                     username_validator,
                                 ])
    is_active = models.BooleanField(default=True)
    is_admin = models.BooleanField(default=False)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['phone_number', 'username']

    def __str__(self):
        return f'{self.username}'

    @property
    def is_staff(self):
        return self.is_admin

# Now, specify custom related names for the groups and user_permissions fields
User._meta.get_field('groups').related_name = 'user_groups'
User._meta.get_field('user_permissions').related_name = 'user_permissions'

class OtpCode(BaseModel):
    phone_number = models.CharField(max_length=11, unique=True)
    code = models.PositiveIntegerField()

    def __str__(self):
        return f'{self.phone_number} - {self.code} - {self.created_at}'

""" Model for User Profile """

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    is_online = models.BooleanField(default=False)
    following = models.ManyToManyField(User, related_name="following", blank=True)
    friends = models.ManyToManyField(User, related_name='my_friends', blank=True)
    bio = models.CharField(default="",blank=True,null=True,max_length=350)
    date_of_birth = models.CharField(blank=True,max_length=150)
    updated = models.DateTimeField(auto_now=True)
    created = models.DateTimeField(auto_now_add=True)


    def profile_posts(self):
        return self.user.post_set.all()

    def get_friends(self):
        return self.friends.all()

    def get_friends_no(self):
        return self.friends.all().count()

    def __str__(self):
        return f'{self.user.username} Profile'



STATUS_CHOICES = (
    ('send','send'),
    ('accepted','accepted')
)

class Relationship(models.Model):
    sender = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='friend_sender')
    receiver = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='friend_receiver')
    status = models.CharField(max_length=8, choices=STATUS_CHOICES)
    updated = models.DateTimeField(auto_now=True)
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.sender}-{self.receiver}-{self.status}"

