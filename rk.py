# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# Authors: Danielle Madeley <danielle@madeley.id.au>

from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler
import json
import subprocess
from urllib import urlencode
from urlparse import urlparse, parse_qs
from tempfile import NamedTemporaryFile

from httplib2 import Http

CLIENT_ID = '970809bbcfe94e18b0a1ccedd9f1810c'
CLIENT_SECRET = '20db9043724d4bf59fdb542391c49415'

API_URL = 'https://api.runkeeper.com'
AUTHORIZATION_URL = 'https://runkeeper.com/apps/authorize'
ACCESS_TOKEN_URL = 'https://runkeeper.com/apps/token'

class AuthenticationException(Exception):
    pass

class Client(Http):
    def request(self, uri, data={}, method='GET', headers={}, body=None):

        if method == 'POST':
            headers['Content-Type'] = content_type = \
                headers.get('Content-Type', 'application/x-www-form-urlencoded')

            if not body and content_type == 'application/x-www-form-urlencoded':
                body = urlencode(data)

        else:
            uri = uri + '?' + urlencode(data)

        return Http.request(self, uri,
                            method=method,
                            headers=headers,
                            body=body)

class HTTPRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-Type', 'text/plain')
        self.end_headers()

        p = urlparse(self.path)
        qs = parse_qs(p.query)

        print >> self.wfile, "Thanks, you may close this window now"

        self.server.code = qs['code'][0]

class RK(object):
    def __init__(self):

        self.client = Client()
        self.pages = None
        self.accepts = {
            'fitness_activity': 'FitnessActivity',
            'fitness_activities': 'FitnessActivityFeed',
        }

    def authorize(self):

        # start a web browser that we can use to collect the answer to the token
        server_address = ('localhost', 0)
        httpd = HTTPServer(server_address, HTTPRequestHandler)

        redirect_uri = 'http://{server_name}:{server_port}/'.format(**httpd.__dict__)

        # open a web browser to allow the user to accept the token
        subprocess.check_call(['xdg-open',
                               AUTHORIZATION_URL + '?' +
                               urlencode(dict(client_id=CLIENT_ID,
                                              response_type='code',
                                              redirect_uri=redirect_uri))
                              ])
        httpd.handle_request()

        # now request an authorisation token
        resp, content = self.client.request(ACCESS_TOKEN_URL, method='POST',
                data=dict(grant_type='authorization_code',
                          code=httpd.code,
                          client_id=CLIENT_ID,
                          client_secret=CLIENT_SECRET,
                          redirect_uri=redirect_uri))

        content = json.loads(content)

        if 'error' in content:
            raise AuthenticationException(content['error'])

        self.token = content['access_token']

        return self.token

    def _request(self, path, accepts=None, **kwargs):

        if not accepts:
            accepts = path[1:].title()

        headers={
            'Authorization': 'Bearer {}'.format(self.token),
            'Accept': 'application/vnd.com.runkeeper.{}+json'.format(accepts),
        }

        headers.update(kwargs.get('headers', {}))

        _, content = self.client.request(API_URL + path, headers=headers,
                                         **kwargs)
        content = json.loads(content)

        return content

    def __getattr__(self, name):
        if name.startswith('get_'):
            if not self.pages:
                self.get_user()

            page = name[4:]
            try:
                uri = self.pages[page]
                accepts = self.accepts.get(page, None)

                return lambda: self._request(uri, accepts=accepts)
            except KeyError as e:
                raise AttributeError(e)

    def get_user(self):
        self.pages = {}
        self.pages = self._request('/user')

        return self.pages

    def get_fitness_items(self):
        """
        Yields the items from the fitness feed.
        """

        r = self.get_fitness_activities()

        while r:

            for i in r['items']:
                yield i

            if 'next' not in r:
                break

            r = self._request(r['next'],
                              accepts=self.accepts['fitness_activities'])

    def get_fitness_item(self, path):
        """
        Returns a single fitness item
        """

        return self._request(path, accepts=self.accepts['fitness_activity'])
