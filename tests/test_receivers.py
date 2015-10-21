# -*- coding: utf-8 -*-
#
# This file is part of Zenodo.
# Copyright (C) 2015 CERN.
#
# Zenodo is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Zenodo is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Zenodo. If not, see <http://www.gnu.org/licenses/>.
#
# In applying this licence, CERN does not waive the privileges and immunities
# granted to it by virtue of its status as an Intergovernmental Organization
# or submit itself to any jurisdiction.

"""Test signal receivers."""

from __future__ import absolute_import, print_function

from flask_email.backends import locmem as mail
from mock import patch

from invenio.base.globals import cfg

from .helpers import BaseTestCase


class ReceiversTestCase(BaseTestCase):
    """Test signal receivers."""

    config = {
        "EMAIL_BACKEND": "flask.ext.email.backends.locmem.Mail"
    }

    # Note Flask-Testing 0.4.2 has a bug that causes render_templates to switch
    # off template rendering not only for this test case but for all subsequent
    # ones as well. Thus this test case should be run last.
    render_templates = False

    def tearDown(self):
        """Clean test mailbox."""
        if len(mail.outbox) != 0:
            mail.outbox = []
        super(ReceiversTestCase, self).tearDown()

    def test_send_notification(self):
        """Test sending of notifications."""
        from zenodo_accessrequests.receivers import \
            _send_notification

        _send_notification(
            "info@invenio-software.org",
            "Test subject",
            "accessrequests/emails/accepted.tpl",
            var1="value1",
        )
        self.assertEqual(len(mail.outbox), 1)

        msg = mail.outbox[0]
        self.assertEqual(msg.to, ["info@invenio-software.org"])
        self.assertEqual(msg.subject, "Test subject")
        self.assertEqual(msg.from_email, cfg["CFG_SITE_SUPPORT_EMAIL"])
        self.assertContext("var1", "value1")
        self.assertTemplateUsed("accessrequests/emails/accepted.tpl")

    @patch('zenodo_accessrequests.receivers.get_record')
    def test_create_secret_link(self, get_record):
        """Test creation of secret link."""
        from zenodo_accessrequests.receivers import \
            create_secret_link

        # Patch get_record
        record = dict(
            title="Record Title",
        )
        get_record.return_value = record

        r = self.get_request(confirmed=True)

        create_secret_link(r)

        self.assertEqual(r.link.title, "Record Title")
        self.assertEqual(r.link.description, "")
        self.assertTemplateUsed("accessrequests/link_description.tpl")
        self.assertContext("request", r)
        self.assertContext("record", record)

    @patch('zenodo_accessrequests.receivers.get_record')
    def test_create_secret_link_norecord(self, get_record):
        """Test creation of secret link with no record."""
        from zenodo_accessrequests.errors import RecordNotFound
        from zenodo_accessrequests.receivers import \
            create_secret_link

        # Patch get_record
        get_record.return_value = None

        r = self.get_request(confirmed=True)
        self.assertRaises(RecordNotFound, create_secret_link, r)
