from django.conf.urls.defaults import patterns, include, url

from passwords.views import *
# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns('',
        ('^users/$', UserView.as_view()),
        ('^users/(?P<user_name>.+)/$', UserView.as_view()),
        ('^passwords/(?P<user_name>.+)/$', PasswordView.as_view()),
)
