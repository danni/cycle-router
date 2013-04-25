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

from urlparse import urlparse, urlunparse

from flask import Flask, Response, \
                  redirect, request, url_for, stream_with_context
from rk import RK


app = Flask(__name__)


class FlaskRK(RK):

    @property
    def redirect_uri(self):
        o = urlparse(request.url)

        return urlunparse((o.scheme,
                           o.netloc,
                           url_for('authorize_next'),
                           None,
                           None,
                           None))


rk = FlaskRK()

@app.route('/')
def index():
    """
    Pretty landing page.
    """

    return '<a href="authorize">Authorize</a>'


@app.route('/authorize')
def authorize():
    """
    Redirect to the authorization process.
    """

    return redirect(rk.authorisation_uri)


@app.route('/authorized')
def authorize_next():
    """
    Retrieve the RK code, redirect the user somewhere nice
    """

    @stream_with_context
    def generate():
        """
        This generator progressively returns data to the browser.
        """

        try:
            yield "Carrier detected\n"
            yield "Acquiring authorization code... "
            rk.extract_code(request.url)
            yield "{}\n".format(rk.code)
            yield "Requesting session token... "
            rk.request_token()
            yield "done.\n"

            yield "Identify...\n"
            yield str(rk.get_profile())

            yield "Downloading"
            for item in rk.get_fitness_items():
                yield str(rk.get_fitness_item(item['uri']))

            yield "Transfer complete. Terminating connection."
        except Exception as e:
            yield "\nCARRIER TERMINATED\n{}".format(e.message)
            raise e

    return Response(generate(), mimetype='text/plain')


if __name__ == "__main__":
    app.run(debug=False)
