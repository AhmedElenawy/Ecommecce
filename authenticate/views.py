from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse
from .forms import RegestrationForm, LoginForm, ResetForm, OtpForm, ResetPasswordForm
from django.contrib.auth import login, authenticate, logout
from django.views.decorators.http import require_POST
from django.utils.translation import gettext as _
# from django.contrib.auth.backends import ModelBackend
# from django.contrib.auth.forms import AuthenticationForm
from .otp import Otp
from ecommerce.redis_client import r
from django.contrib.auth.models import User


def register(request):
    if request.method == 'POST':
        form = RegestrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            #  should be placed by set_password to be hashed
            user.set_password(form.cleaned_data['password2'])
            user.is_active = False
            user.username = user.email.split('@')[0]
            user.save()
            request.session['email'] = user.email
            request.session.set_expiry(600)
            try:
                Otp(user.email, "register").send_otp()
                # otp_form = OtpForm(initial={'email': email})
                request.session['purpose'] = "register"
                return redirect('authenticate:confirm_otp')
            except Exception as e:
                form.add_error('email', str(e))
        
    else:
        form = RegestrationForm()
    return render(request, 'authenticate/register.html', {'form': form})


def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            # loops over outh bachends
            user = authenticate(username=username, password=password)
            if user is not None and user.is_active:
                login(request, user)
                return redirect('store:product_list_category')
            # elif user is not None and not user.is_active:
            #     request.session['email'] = user.email
            #     request.session.set_expiry(600)
            #     try:
            #         Otp(user.email, "register").send_otp()
            #         # otp_form = OtpForm(initial={'email': email})
            #         request.session['purpose'] = "register"
            #         return redirect('authenticate:confirm_otp')
            #     except Exception as e:
            #         form.add_error('username', str(e))
                
            else:
                form.add_error('username', _('Invalid email or password'))
    else:
        form = LoginForm()
    return render(request, 'authenticate/login.html', {'form': form})


@require_POST
def logout_view(request):
    logout(request)
    return redirect('authenticate:login')

    
def password_reset(request):
    if request.method == 'POST':
        form = ResetForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            request.session['email'] = email
            # will it be for every session
            request.session.set_expiry(600)

            try:
                Otp(email, "password_reset").send_otp()
                request.session['purpose'] = "password_reset"
                # otp_form = OtpForm(initial={'email': email})
                return redirect('authenticate:confirm_otp')
            except Exception as e:
                form.add_error('email', str(e))
    else:
        form = ResetForm()
    return render(request, 'authenticate/reset_form.html', {'form': form})



def confirm_otp(request):
    if request.method == 'POST':
        form = OtpForm(request.POST)
        if form.is_valid():
            user_otp = form.cleaned_data['otp']
            email = form.cleaned_data['email']
            if email != request.session.get('email') or not request.session.get('purpose'):
                return render(request, 'authenticate/error.html', {'message': _("unauthorized")})
            
            purpose = request.session.get('purpose')
            try:
                otp = Otp(email, purpose)
                otp.validate_otp(user_otp)
                
            except Exception as e:
                form.add_error('otp', e)
                return render(request, 'authenticate/confirm_otp.html', {'form': form})
            

            request.session['otp_verified'] = True
            request.session["verified_email"] = email
            # password_reset_form = ResetPasswordForm(initial={'email': email})
            # return render(request, 'authenticate/new_password.html', {"form": password_reset_form})
            if purpose == "register":
                user = User.objects.get(email=email)
                user.is_active = True
                user.save()
                request.session.flush()
                return redirect('authenticate:login')
            
            return redirect('authenticate:new_password')
            
    else:
        email = request.session.get('email')
        if not email:
            return render(request, 'authenticate/error.html', {'message': _("Email not found")})
        
        form = OtpForm(initial={'email': email})
    return render(request, 'authenticate/confirm_otp.html', {'form': form})

def resend_otp(request):
    email = request.session.get('email')
    purpose = request.session.get('purpose')
    if not email or not purpose:
        return JsonResponse({'status': 'error', 'message': _('email not found')})
    try:
        Otp(email, purpose).send_otp()
        return JsonResponse({'status': 'sent', 'message': _('email resent')})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)})

def new_password(request):
    if request.method == 'POST':
        form = ResetPasswordForm(request.POST)
        if form.is_valid():
            password = form.cleaned_data['password2']
            email = form.cleaned_data['email']
            if  email != request.session.get('email') or not request.session.get('otp_verified'):
                return render(request, 'authenticate/error.html', {'message': _("unauthorized")})
            
            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                return render(request, 'authenticate/error.html', {'message': _("User not found")})

            user.set_password(password)
            user.save()
            Otp(email, "password_reset").delete_otp()
            request.session.flush()
            return redirect('authenticate:login')
    else:
        email = request.session.get('verified_email')
        if not email:
            return render(request, 'authenticate/error.html', {'message': _("Email not found")})
        form = ResetPasswordForm(initial={'email': email})
    return render(request, 'authenticate/new_password.html', {'form': form})
    
    


