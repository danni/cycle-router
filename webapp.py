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
from urlparse import urljoin

from flask import Flask, Response, \
                  redirect, request, url_for, stream_with_context, \
                  render_template
from rk import RK


app = Flask(__name__)


class FlaskRK(RK):

    @property
    def redirect_uri(self):
        return urljoin(request.url_root, url_for('authorized'))


rk = FlaskRK()

@app.route('/')
def index():
    """
    Pretty landing page.
    """

    return render_template('index.html')


@app.route('/authorize')
def authorize():
    """
    Redirect to the authorization process.
    """

    return redirect(rk.authorisation_uri)


@app.route('/authorized')
def authorized():
    """
    Pretty authorized page
    """

    return render_template('authorized.html')


@app.route('/get-token')
def get_token():
    """
    Retrieve the RK code, redirect the user somewhere nice
    """

    def yield_json(**kwargs):
        return 'data: ' + json.dumps(kwargs) + '\n\n'

    @stream_with_context
    def generate():
        """
        This generator progressively returns data to the browser.
        """

        try:
            rk.extract_code(request.url)
            yield yield_json(output="Requesting session token...")
            rk.request_token()

            yield yield_json(output="Identify")
            profile = rk.get_profile()
            yield yield_json(output=profile['name'])
            yield yield_json(output=profile['normal_picture'])

            yield yield_json(output="Downloading")
            for item in rk.get_fitness_items():
                item = rk.get_fitness_item(item)
                yield yield_json(output='*')

            yield yield_json(
                output="Transfer complete. Terminating connection",
                state='complete')
        except Exception as e:
            yield yield_json(
                output="CARRIER TERMINATED",
                error=e.message,
                state='failed')
            raise e

    return Response(generate(), mimetype='text/event-stream')


if __name__ == "__main__":
    app.run(debug=True, threaded=True)
