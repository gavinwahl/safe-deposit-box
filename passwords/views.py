from django.views.generic.base import View
from django.http import HttpResponse
import json

from passwords.models import *

class UserView(View):
    def get(self, request, user_name):
        user = User.objects.get_by_id(user_name)

        return HttpResponse(json.dumps(user.as_dict()))

    def post(self, request):
        user = User(name=request.POST['name'])
        user.save()
        resp =  HttpResponse()
        resp.status_code = 201
        resp['Location'] = '/users/%s/' % (user.name)
        return resp


class PasswordView(View):
    def get(self, request, user_name):
        user = User.objects.with_passwords(user_name)
        passwords = user.passwords

        return HttpResponse(json.dumps(passwords))

    def post(self, request, user_name):
        password = Password()
        password.password = request.POST['password']
        password.user = user_name
        password.save()
        resp =  HttpResponse()
        resp.status_code = 201
        resp['Location'] = '/passwords/%s/%s/' % (user_name, password._id)
        return resp
