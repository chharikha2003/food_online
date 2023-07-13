
from django.http import HttpResponse
from django.shortcuts import render,redirect
from django.contrib import messages,auth
from accounts.forms import UserForm
from accounts.models import User, UserProfile
from accounts.utils import detectUser,send_verification_email
from vendor.forms import VendorForm
from django.contrib.auth.decorators import login_required,user_passes_test
from django.core.exceptions import PermissionDenied
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_decode
from vendor.models import Vendor
from django.template.defaultfilters import slugify


# Restrict vendor from accessing customer page 
def check_role_vendor(user):
    if user.role==1:
        return True
    else:
        raise PermissionDenied
# Restrict customer from accessing vendor page 
def check_role_customer(user):
    if user.role==2:
        return True
    else:
        raise PermissionDenied

def registerUser(request):
    if request.user.is_authenticated:
        messages.warning(request,"you are already logged in")
        return redirect('myAccount')
    elif request.method=='POST':
        form=UserForm(request.POST)
        
        if form.is_valid():
            
            #password=form.cleaned_data['password']
            #user=form.save(commit=False)
            #user.set_password(password)
            #user.role=User.CUSTOMER
            #user.save()

            first_name = form.cleaned_data['first_name']
            last_name = form.cleaned_data['last_name']
            username = form.cleaned_data['username']
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            user = User.objects.create_user(first_name=first_name, last_name=last_name, username=username, email=email, password=password)
            user.role = User.CUSTOMER
            user.save()
            #send verification email
            email_subject='Please activate your account'
            email_template='accounts/emails/account_verification_email.html'
            send_verification_email(request,user,email_subject,email_template)
            messages.success(request,"your account has been successfully registered")


            return redirect('registerUser')
        else:
            print("invalid")
    else:
        form=UserForm()
    context={
        'form':form
    }
    return render(request,'accounts/registerUser.html',context)
def registerVendor(request):
    if request.user.is_authenticated:
        messages.warning(request,"you are already logged in")
        return redirect('dashboard')
    elif request.method=='POST':
        #store the data and create the user
        form=UserForm(request.POST)
        v_form=VendorForm(request.POST,request.FILES)
        if form.is_valid() and v_form.is_valid():
            first_name=form.cleaned_data['first_name']
            last_name=form.cleaned_data['last_name']
            username=form.cleaned_data['first_name']
            email=form.cleaned_data['email']
            password=form.cleaned_data['password']
            user=User.objects.create_user(first_name=first_name,last_name=last_name,username=username,email=email,password=password)
            user.role=User.RESTAURENT
            user.save()

            vendor=v_form.save(commit=False)
            vendor.user=user 
            vendor_name=v_form.cleaned_data['vendor_name']
            vendor.vendor_slug=slugify(vendor_name)+"-"+str(user.id)
            user_profile=UserProfile.objects.get(user=user)
            vendor.user_profile=user_profile
            vendor.save()
            email_subject='Please activate your account'
            email_template='accounts/emails/account_verification_email.html'
            send_verification_email(request,user,email_subject,email_template)
            messages.success(request, 'Your account has been registered successfully! Please wait for the approval')
            return redirect('registerVendor')
        else:

            print('invalid form')
            print(form.errors)

    else:
        form=UserForm()
        v_form=VendorForm()

    context={
        'form':form,
        'v_form':v_form,
    }
    return render(request,'accounts/registerVendor.html',context)
def login(request):
    if request.user.is_authenticated:
        messages.warning(request,"you are already logged in")
        return redirect('myAccount')
    if request.method=='POST':
        email=request.POST['email']
        password=request.POST['password']
        user=auth.authenticate(email=email,password=password)
        if user!=None:
            auth.login(request,user)
            messages.success(request,'You are now loggedIn')
            return redirect('myAccount')
        else:
            messages.error(request,'Invalid Credentials')
            return redirect('login')

    return render(request,'accounts/login.html')
def activate(request,uidb64,token):
    try:
        uid=urlsafe_base64_decode(uidb64).decode()
        user=User._default_manager.get(pk=uid)
    except(TypeError,ValueError,OverflowError,User.DoesNotExist):
        user=None
    if user is not None and default_token_generator.check_token(user,token):
        user.is_active=True
        user.save()
        messages.success(request,"congratulations your account is activated")
        return redirect('myAccount')
    else:
        messages.error(request,'Invalid link')
        return redirect('myAccount')    



def logout(request):
    auth.logout(request)
    messages.info(request,"You logged out")
    return redirect("login")

    pass
@login_required(login_url='login')
def myAccount(request):
    user=request.user
    redirecturl=detectUser(user)
    return redirect(redirecturl)

   
@login_required(login_url='login')
@user_passes_test(check_role_customer)
def custDashboard(request):
    return render(request,'accounts/custDashboard.html')
@login_required(login_url='login')
@user_passes_test(check_role_vendor)
def vendorDashboard(request):
    
    return render(request,'accounts/vendorDashboard.html')

def forgotpassword(request):
    if request.method=='POST':
        email=request.POST['email']
        if User.objects.filter(email=email).exists():
            user=User.objects.get(email__exact=email)
            email_subject='Reset your password'
            email_template='accounts/emails/reset_password_email.html'
            send_verification_email(request,user,email_subject,email_template)
            messages.success(request,'password verification link has been sent to your email address')
            return redirect('login')
        else:
            messages.error(request,'Account does not exist')
            return redirect('forgotpassword')

    return render(request,'accounts/forgotpassword.html')

def resetpasswordvalidate(request,uidb64,token):
    try:
        uid=urlsafe_base64_decode(uidb64).decode()
        user=User._default_manager.get(pk=uid)
    except(TypeError,ValueError,OverflowError,User.DoesNotExist):
        user=None
    if user is not None and default_token_generator.check_token(user,token):
        request.session['uid']=uid
        messages.info(request,'Plese reset your password')
        return redirect('resetpassword')
    else:
        messages.success(request,'password reset successful')
        return redirect('login')

    return 

def resetpassword(request):
    if request.method=='POST':
        password=request.POST['password']
        confirm_password=request.POST['confirm_password']
        if password==confirm_password:
            pk=request.session.get('uid')
            user=User.objects.get(pk=pk)
            user.set_password(password)
            user.is_active=True
            user.save()
            messages.error(request,'link expired')
            return redirect('myAccount')

        else:
            messages.error(request,'Passwords dont match')
        return redirect('resetpassword')
    return render(request,'accounts/resetpassword.html')