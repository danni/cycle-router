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

import json
import subprocess
from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler
from urllib import urlencode
from urlparse import urlparse, parse_qs
from tempfile import NamedTemporaryFile

from httplib2 import Http, ServerNotFoundError

from keys import * # API keys: CLIENT_ID, CLIENT_SECRET


API_URL = 'https://api.runkeeper.com'
AUTHORIZATION_URL = 'https://runkeeper.com/apps/authorize'
ACCESS_TOKEN_URL = 'https://runkeeper.com/apps/token'


class AuthenticationException(Exception):
    pass


class HttpException(Exception):
    def __init__(self, headers):
        self.headers = headers

    def __repr__(self):
        return '{} ({})'.format(self.__class__.__name__, self.headers.status)


class NotModified(HttpException):
    pass


class PermissionDenied(HttpException):
    pass


class FileNotFound(HttpException):
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

class RK(object):
    """
    A class for talking to the RunKeeper health graph API.

    Implement redirect_uri

    The authentication flow then goes like this:
    - direct the user to rk.authorisation_uri
    - when you get the returned request path, call rk.extract_code(path)
    - call rk.request_token()
    """

    def __init__(self, token=None):

        self.client = Client()
        self.code = None
        self.token = token
        self.pages = None
        self.accepts = {
            'fitness_activity': 'FitnessActivity',
            'fitness_activities': 'FitnessActivityFeed',
        }

    @property
    def redirect_uri(self):
        """
        The URI to redirect the user to to get an authorization code
        """

        raise NotImplemented()

    @property
    def authorisation_uri(self):
        """
        The URI to visit for authorization
        """

        return AUTHORIZATION_URL + '?' + \
               urlencode(dict(client_id=CLIENT_ID,
                              response_type='code',
                              redirect_uri=self.redirect_uri))

    def extract_code(self, uri):
        """
        Extract the authorization code from the returned URL
        """

        p = urlparse(uri)
        qs = parse_qs(p.query)

        try:
            self.code = qs['code'][0]
        except KeyError:
            raise AuthenticationException("Code was not supplied")

        return self.code

    def request_token(self):
        """
        Request an authorization token. Assumes self.code must be set.

        This method blocks.
        """

        if not self.code:
            raise AuthenticationException(
                "Need authorization code before session token")

        try:
            resp, content = self.client.request(ACCESS_TOKEN_URL, method='POST',
                    data=dict(grant_type='authorization_code',
                              code=self.code,
                              client_id=CLIENT_ID,
                              client_secret=CLIENT_SECRET,
                              redirect_uri=self.redirect_uri))
        except ServerNotFoundError:
            raise AuthenticationException("Could not contact RunKeeper")

        content = json.loads(content)

        if 'error' in content:
            raise AuthenticationException(content['error'])

        self.token = content['access_token']

        return self.token

    def _request(self, path, accepts=None, **kwargs):

        if not self.token:
            raise AuthenticationException("You are not authenticated")

        if not accepts:
            accepts = path[1:].title()

        headers={
            'Authorization': 'Bearer {}'.format(self.token),
            'Accept': 'application/vnd.com.runkeeper.{}+json'.format(accepts),
        }

        headers.update(kwargs.pop('headers', {}))

        resp, content = self.client.request(API_URL + path, headers=headers,
                                            **kwargs)

        exceptions = {
            '304': NotModified,
            '403': PermissionDenied,
            '404': FileNotFound,
        }

        status = resp['status']

        if status in exceptions:
            raise exceptions[status](resp)
        elif status != '200':
            raise HttpException(resp)

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

    def get_fitness_item(self, item, if_modified_since=None):
        """
        Returns a single fitness item

        if_modified_since assumes GMT
        """

        if isinstance(item, basestring):
            path = item
        else:
            path = item['uri']

        headers = {}

        if if_modified_since is not None:
            headers['If-Modified-Since'] = \
                if_modified_since.strftime('%a, %d %b %Y %H:%M:%S GMT')

        return self._request(path, accepts=self.accepts['fitness_activity'],
                             headers=headers)


class HTTPRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-Type', 'text/plain')
        self.end_headers()

        self.server.path = self.path

        print >> self.wfile, "Thanks, you may close this window now"


class CommandLineClient(RK):
    """
    Implement RK client able to be used on the command line.
    """

    def authorize(self):
        server_address = ('localhost', 0)
        self.httpd = HTTPServer(server_address, HTTPRequestHandler)

        # open a web browser for the user
        subprocess.check_call(['xdg-open', self.authorisation_uri])
        self.httpd.handle_request()

        self.extract_code(self.httpd.path)
        self.request_token()

    @property
    def redirect_uri(self):
        return 'http://{server_name}:{server_port}/'.format(
            **self.httpd.__dict__)
