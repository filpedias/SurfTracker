# -*- coding: utf-8 -*-
from django import forms
from django.utils.translation import gettext_lazy as _
from main.models import Surfer


class AuthenticateForm(forms.Form):
    username = forms.CharField(
        label=_("Username"),
        widget=forms.TextInput({'placeholder': _(u'username'), 'class': 'form-control'}))

    password = forms.CharField(
        label=_("Password"),
        widget=forms.PasswordInput({'placeholder': _(u'password'), 'class': 'form-control'}))

    def __init__(self, data=None, *args, **kwargs):
        super(AuthenticateForm, self).__init__(data, *args, **kwargs)

    def clean(self):
        # Username
        username = self.cleaned_data.get('username')
        users = Surfer.objects.filter(username=username)
        if users.count() == 0:
            self.add_error('username', _(u"The username does not exist"))

        # Password
        password = self.cleaned_data.get('password')
        if users.count() == 1:
            user = users[0]
            if not user.check_password(password):
                self.add_error('password', _(u"Incorrect password"))
