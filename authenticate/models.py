from django.db import models
from django.conf import settings
from phonenumber_field.modelfields import PhoneNumberField
# Create your models here.

# class Profile(models.Model):
#     user = models.OneToOneField('settings.AUTH_USER_MODEL', on_delete=models.CASCADE)
#     phone_number = PhoneNumberField(unique=False, region="EG", blank=True, null=True)
#     address = models.CharField(max_length=250, blank=True, null=True)
#     city = models.CharField(max_length=250, blank=True, null=True)

#     def __str__(self):
#         return self.user.username
    


