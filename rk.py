
from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler
import json
import subprocess
from urllib import urlencode
from urlparse import urlparse, parse_qs
from tempfile import NamedTemporaryFile

from httplib2 import Http

CLIENT_ID = '970809bbcfe94e18b0a1ccedd9f1810c'
CLIENT_SECRET = '20db9043724d4bf59fdb542391c49415'

AUTHORIZATION_URL = 'https://runkeeper.com/apps/authorize'
ACCESS_TOKEN_URL = 'https://runkeeper.com/apps/token'

class AuthenticationException(Exception):
    pass

class Client(Http):
    def request(self, uri, data, method='GET', headers={}, body=None):

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
