from django import forms
from django.contrib.auth.models import User
from django.contrib.auth import get_user_model

from django.contrib.auth.password_validation import validate_password
from phonenumber_field.formfields import PhoneNumberField
from phonenumber_field.widgets import PhoneNumberPrefixWidget
from phonenumber_field.phonenumber import PhoneNumber
from django.conf import settings

from django.contrib.auth.forms import AuthenticationForm
from django.utils.translation import gettext_lazy as _

# Context	What to use?	Why?
# forms.py	get_user_model()	Forms need the Class to inspect fields.
# views.py	get_user_model()	Logic needs the Class to query data.
# models.py	settings.AUTH_USER_MODEL	ForeignKeys prefer a String to avoid import loops.


class InActiveError(forms.ValidationError):
    pass
class RegestrationForm(forms.ModelForm):
    # forms.PasswordInput is widget not type
    password = forms.CharField(label=_("Password"),
                               widget=forms.PasswordInput,)
                            #    validators=[validate_password],
                            #    help_text='Password must be at least 8 characters')
    
    password2 = forms.CharField(label=_("Confirm Password"), widget=forms.PasswordInput)

    class Meta:
        model = get_user_model()
        fields = ["first_name", "last_name", "email"]


    def clean_password2(self):
        dt = self.cleaned_data

        try:
            password = dt['password']
            password2 = dt['password2']
        except KeyError:
            raise forms.ValidationError(_("Enter strong password."))
        
        if password == password2:
            return password2
        
        raise forms.ValidationError(_("Passwords don't match."))

    # def clean_password2(self):
    #     password = self.cleaned_data['password']
    #     password2 = self.cleaned_data['password2']
        
    #     if password and password2:
    #         if password == password2:
    #             return password2
            
        # Django's form validation catches the exception:
        # - Sees it as a validation error
        # - Adds error message to form
        # - Sets form.is_valid() = False

        # Form.is_valid() returns: False ❌ (Correct!)
        # User sees error: "This email address is already registered."

    #   raise forms.ValidationError("Password doesn't match")
    
    def clean_email(self):
        email = self.cleaned_data.get('email', '').lower().strip()
        try:
            user = User.objects.get(email__iexact=email)
        except User.DoesNotExist:
            return email
        if user and not user.is_active:
            user.delete()
            return email
        raise forms.ValidationError(_("This email address is already registered."))    
        
    
class LoginForm(forms.Form):
    username = forms.EmailField(label=_("Email"))
    password = forms.CharField(label=_("Password"),
                               widget=forms.PasswordInput)
        
    
class ResetForm(forms.Form):
    email = forms.EmailField(label=_("Email Address"))

    def clean_email(self):
        email = self.cleaned_data.get('email', '').lower().strip()
        if User.objects.filter(email__iexact=email).exists():
            return email
        raise forms.ValidationError(_("This email address is not registered."))


class OtpForm(forms.Form):
    otp = forms.CharField(max_length=6, min_length=6, widget=forms.NumberInput, label=_("OTP"))
    email = forms.EmailField(widget=forms.HiddenInput)


class ResetPasswordForm(forms.Form):
    password = forms.CharField(label=_("Password"),
                               widget=forms.PasswordInput,)
    password2 = forms.CharField(label=_("Confirm Password"), widget=forms.PasswordInput)
    email = forms.EmailField(widget=forms.HiddenInput)
    
    def clean_password2(self):
        data = self.cleaned_data
        password = data['password']
        password2 = data['password2']
        
        if password and password2:
            if password == password2:
                return password2
        raise forms.ValidationError(_("Password doesn't match"))
    