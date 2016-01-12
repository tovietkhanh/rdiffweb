#!/usr/bin/python
# -*- coding: utf-8 -*-
# rdiffweb, A web interface to rdiff-backup repositories
# Copyright (C) 2014 rdiffweb contributors
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import absolute_import
from __future__ import unicode_literals

from builtins import str
from builtins import bytes
import cherrypy
import logging
import os

from rdiffweb import librdiff
from rdiffweb import page_main
from rdiffweb.i18n import ugettext as _
from rdiffweb.rdw_helpers import unquote_url


# Define the logger
logger = logging.getLogger(__name__)


class BrowsePage(page_main.MainPage):

    """This contoller provide a browser view to the user. It displays file in a
    repository."""

    def _cp_dispatch(self, vpath):
        """Used to handle permalink URL.
        ref http://cherrypy.readthedocs.org/en/latest/advanced.html"""
        # Notice vpath contains bytes.
        if len(vpath) > 0:
            # /the/full/path/
            path = []
            while len(vpath) > 0:
                path.append(unquote_url(vpath.pop(0)))
            cherrypy.request.params['path'] = b"/".join(path)
            return self

        return vpath

    @cherrypy.expose
    def index(self, path=b"", restore=""):
        assert isinstance(path, bytes)
        assert isinstance(restore, str)
        restore = bool(restore)

        logger.debug("browsing [%r]", path)

        # Check user access to the given repo & path
        try:
            (repo_obj, path_obj) = self.validate_user_path(path)
        except librdiff.FileError as e:
            logger.exception("invalid user path")
            return self._compile_error_template(str(e))

        # Build the parameters
        try:
            parms = self._get_parms_for_page(repo_obj, path_obj, restore)
        except librdiff.FileError as e:
            logger.exception("can't create params")
            return self._compile_error_template(str(e))

        return self._compile_template("browse.html", **parms)

    def _get_parms_for_page(self, repo_obj, path_obj, restore):
        assert isinstance(repo_obj, librdiff.RdiffRepo)
        assert isinstance(path_obj, librdiff.RdiffPath)

        # Build "parent directories" links
        # TODO This Should to me elsewhere. It contains logic related to librdiff encoding.
        parents = []
        parents.append({"path": b"", "name": repo_obj.display_name})
        parent_path_b = b""
        for part_b in path_obj.path.split(b'/'):
            if part_b:
                parent_path_b = os.path.join(parent_path_b, part_b)
                display_name = repo_obj._decode(repo_obj.unquote(part_b))
                parents.append({"path": parent_path_b,
                                "name": display_name})

        # Set up warning about in-progress backups, if necessary
        warning = ""
        if repo_obj.in_progress:
            warning = _("""A backup is currently in progress to this repository. The displayed data may be inconsistent.""")

        dir_entries = []
        restore_dates = []
        if restore:
            restore_dates = path_obj.restore_dates
        else:
            # Get list of actual directory entries
            dir_entries = path_obj.dir_entries

        return {"repo_name": repo_obj.display_name,
                "repo_path": repo_obj.path,
                "path": path_obj.path,
                "dir_entries": dir_entries,
                "parents": parents,
                "restore_dates": restore_dates,
                "warning": warning}
