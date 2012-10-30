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

from pyramid.renderers import get_renderer
from pyramid.security import authenticated_userid

from samplesdb.models import (
    DBSession,
    Collection,
    Sample,
    )

class BaseView(object):
    """Abstract base class for view handlers"""

    def __init__(self, request):
        self.request = request
        # Every handler needs the master template, the authenticated user, and
        # the sample and collection selected (if any)
        self.master = get_renderer('../templates/master.pt').implementation()
        self.user = authenticated_userid(request)
