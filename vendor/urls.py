from django.urls import path
from . import views
from accounts import views as account_views


urlpatterns=[
    path("",account_views.vendorDashboard),
    path('profile/',views.vprofile,name='vprofile')
    


]