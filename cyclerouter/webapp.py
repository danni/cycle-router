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
from urlparse import urljoin

from flask import Flask, Response, \
                  redirect, request, url_for, stream_with_context, \
                  render_template
from sqlalchemy import func

from rk import RK


# Flask application, create this before importing the orm
app = Flask(__name__)


class FlaskRK(RK):
    """
    Implement the RK authorisation routine for Flask
    """

    @property
    def redirect_uri(self):
        return urljoin(request.url_root, url_for('authorized'))


def omg(code):
    def inner(e):
        return render_template('omg.html', error=e), code

    return inner

for error in range(400, 420) + range(500, 506):
    app.error_handler_spec[None][error] = omg(error)


from views import *


if __name__ == "__main__":
    app.config['SQLALCHEMY_DATABASE_URI'] = \
        'postgresql://cyclerouter:bikes@localhost/cyclerouter'
    app.run(debug=True, threaded=True)
