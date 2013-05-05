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

SPHEROID = 'SPHEROID["WGS 84",6378137,298.257223563]'

import json

from flask import Flask, Response, \
                  redirect, request, url_for, stream_with_context, \
                  render_template
from sqlalchemy import func


from webapp import app, FlaskRK
from orm import User, Track, pg_functions, db


@app.route('/')
def index():
    """
    Pretty landing page.
    """

    nusers = db.session.query(Track.user_pk).distinct().count()

    try:
        nkms = db.session.query(
            func.sum(pg_functions.length_spheroid(Track.points, SPHEROID))
        ).select_from(Track).scalar() / 1000.
    except TypeError:
        nkms = 0.

    return render_template('index.html', **locals())


@app.route('/authorize')
def authorize():
    """
    Redirect to the authorization process.
    """

    rk = FlaskRK()

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

    rk = FlaskRK()

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

            # store to the database
            User.from_rk(rk)

            yield yield_json(output="Accessing profile...")

            profile = rk.get_profile()
            items = list(rk.get_fitness_items())
            nitems = len(items)

            yield yield_json(profile=profile, nitems=nitems, state='complete')
            raise StopIteration

            # FIXME pass this off to a celery task
            for n, item in enumerate(items):
                item = rk.get_fitness_item(item)
                yield yield_json(n=n, nitems=nitems)

            yield yield_json(
                output="Transfer complete. Terminating connection",
                state='complete')
        except StandardError as e:
            yield yield_json(
                output="CARRIER TERMINATED",
                error=e.message,
                state='failed')
            raise e

    return Response(generate(), mimetype='text/event-stream')
