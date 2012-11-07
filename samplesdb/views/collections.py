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

import transaction
from pyramid.view import view_config
from pyramid.decorator import reify
from pyramid.httpexceptions import HTTPFound
from formencode import validators, foreach

from samplesdb.views import BaseView
from samplesdb.forms import (
    BaseSchema,
    Form,
    FormRenderer,
    ValidRole,
    ValidUser,
    ValidCollectionName,
    )
from samplesdb.security import (
    OWNER_ROLE,
    EDITOR_ROLE,
    AUDITOR_ROLE,
    VIEWER_ROLE,
    CREATE_COLLECTION,
    VIEW_COLLECTION,
    EDIT_COLLECTION,
    MANAGE_COLLECTIONS,
    )
from samplesdb.models import (
    DBSession,
    EmailAddress,
    Collection,
    Sample,
    Role,
    )


class CollectionUserSchema(BaseSchema):
    user = ValidUser()
    role = ValidRole()


class CollectionSchema(BaseSchema):
    name = ValidCollectionName()
    users = foreach.ForEach(CollectionUserSchema())


class CollectionCreateSchema(CollectionSchema):
    pass


class CollectionsView(BaseView):
    """Handler for collection related views"""

    def __init__(self, request):
        self.request = request

    @reify
    def roles(self):
        return [
            (role.id, role.id.title())
            for role in DBSession.query(Role)
            ]

    @view_config(
        route_name='collections_index',
        renderer='../templates/collections/index.pt',
        permission=MANAGE_COLLECTIONS)
    def index(self):
        return {}

    @view_config(
        route_name='collections_create',
        renderer='../templates/collections/create.pt',
        permission=CREATE_COLLECTION)
    def create(self):
        form = Form(
            self.request, schema=CollectionSchema, variable_decode=True)
        if form.validate():
            new_collection = form.bind(Collection())
            # Hard-code ownership to currently authenticated user
            new_collection.users[self.user] = DBSession.query(Role).\
                filter(Role.id==OWNER_ROLE).one()
            DBSession.add(new_collection)
            return HTTPFound(
                location=self.request.route_url('collections_index'))
        return dict(form=FormRenderer(form))

    @view_config(
        route_name='collections_edit',
        renderer='../templates/collections/edit.pt',
        permission=EDIT_COLLECTION)
    def edit(self):
        return {}

    @view_config(
        route_name='collections_view',
        renderer='../templates/collections/view.pt',
        permission=VIEW_COLLECTION)
    def view(self):
        return {}

