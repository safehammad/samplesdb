# -*- coding: utf-8 -*-
# vim: set et sw=4 sts=4:

# Copyright 2012 Dave Hughes.
#
# This file is part of samplesdb.
#
# samplesdb is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later
# version.
#
# samplesdb is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
# A PARTICULAR PURPOSE.  See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with
# samplesdb.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import (
    unicode_literals,
    print_function,
    absolute_import,
    division,
    )

import logging
from datetime import datetime

import pytz
from pyramid.view import view_config, forbidden_view_config
from pyramid.security import remember, forget
from pyramid.httpexceptions import HTTPFound
from pyramid.chameleon_text import render_template
from pyramid_mailer.message import Message
from formencode import validators

from samplesdb.views import BaseView
from samplesdb.forms import BaseSchema, Form, FormRenderer
from samplesdb.security import authenticate
from samplesdb.models import (
    DBSession,
    EmailAddress,
    EmailVerification,
    User,
    VERIFICATION_TIMEOUT,
    )


class LoginSchema(BaseSchema):
    """Schema for account login form"""
    username = validators.Email(
        not_empty=True, resolve_domain=False,
        max=EmailAddress.__table__.c.email.type.length)
    password = validators.UnicodeString(not_empty=True, max=100)
    came_from = validators.UnicodeString()


class AccountCreateSchema(BaseSchema):
    """Schema for account creation form"""
    email = validators.Email(
        not_empty=True, resolve_domain=True,
        max=EmailAddress.__table__.c.email.type.length)
    email_confirm = validators.UnicodeString()
    password = validators.UnicodeString(not_empty=True, max=100)
    password_confirm = validators.UnicodeString()
    salutation = validators.OneOf([
        '', 'Mr.', 'Mrs.', 'Miss', 'Ms.', 'Dr.', 'Prof.'])
    given_name = validators.UnicodeString(
        not_empty=True, max=User.__table__.c.given_name.type.length)
    surname = validators.UnicodeString(
        not_empty=True, max=User.__table__.c.surname.type.length)
    organization = validators.UnicodeString(
        max=User.__table__.c.organization.type.length)
    limits_id = validators.OneOf([
        'academic', 'commercial'])
    timezone = validators.OneOf(pytz.all_timezones)
    chained_validators = [
        validators.FieldsMatch('email', 'email_confirm'),
        validators.FieldsMatch('password', 'password_confirm'),
        ]


class AccountView(BaseView):
    """Handler for account related views"""

    def __init__(self, request):
        self.request = request

    @view_config(
        route_name='account_login',
        renderer='../templates/account/login.pt')
    @forbidden_view_config(renderer='../templates/account/login.pt')
    def login(self):
        referer = self.request.url
        if referer == self.request.route_url('account_login'):
            referer = self.request.route_url('collections_index')
        form = Form(
            self.request,
            schema=LoginSchema,
            defaults=dict(came_from=referer))
        if form.validate():
            username = form.data['username']
            password = form.data['password']
            if authenticate(username, password):
                return HTTPFound(
                    location=form.data['came_from'],
                    headers=remember(self.request, username))
            else:
                self.request.session.flash('Invalid login')
        return dict(form=FormRenderer(form))

    @view_config(route_name='account_logout')
    def logout(self):
        return HTTPFound(
            location=self.request.route_url('home'),
            headers=forget(self.request))

    @view_config(
        route_name='account_index',
        renderer='../templates/account/index.pt')
    def index(self):
        return {}

    @view_config(
        route_name='account_create',
        renderer='../templates/account/create.pt')
    def create(self):
        # TODO Determine user timezone as default
        # Build a nice sorted list of (timezone_id, description) for the 
        now = datetime(2000, 1, 1, 0, 0, 0)
        timezones = sorted((
            (tz, '(UTC%s) %s' % (
                pytz.timezone(tz).localize(now).strftime('%z'), tz.replace('_', ' ')))
            for tz in pytz.common_timezones
            if tz != 'GMT'),
            key=lambda t: (pytz.timezone(t[0]).localize(now), t[0]))
        form = Form(self.request, schema=AccountCreateSchema)
        if form.validate():
            new_user = form.bind(User())
            DBSession.add(new_user)
            new_email = form.bind(EmailAddress())
            new_email.user = new_user
            DBSession.add(new_email)
            new_collection = Collection()
            new_collection.name = 'Default'
            owner_role = DBSession.query(Role).filter(Role.id=='owner').one()
            new_user.collections[new_collection] = owner_role
            return HTTPFound(location=self.request.route_url(
                'account_verify_email', email=form.data['email']))
        return dict(form=FormRenderer(form), timezones=timezones)

    @view_config(
        route_name='account_verify_email',
        renderer='../templates/account/verify_email.pt')
    def verify_email(self):
        email = self.request.matchdict['email']
        new_verification = EmailVerification(email)
        DBSession.add(new_verification)
        DBSession.flush()
        user = new_verification.email.user
        mailer = self.request.registry['mailer']
        message = Message(
            recipients=[email],
            subject='%s email verification' % self.request.registry.settings['site_title'],
            body=render_template('../templates/account/verify_email.txt',
                request=self.request,
                user=user,
                verification=new_verification))
        mailer.send(message)
        return dict(email=email, timeout=VERIFICATION_TIMEOUT)

    @view_config(
        route_name='account_verify_complete',
        renderer='../templates/account/verify_complete.pt')
    def verify_complete(self):
        return {}

    @view_config(
        route_name='account_verify_cancel',
        renderer='../templates/account/verify_cancel.pt')
    def verify_cancel(self):
        return {}

