cycle-router
============

This project aims to be an application for finding where people cycle, when,
and if we can get the data, estimate good ways to cycle on any given day by
looking at things like weather and wind forecasts.

There are several parts to this project:

 * a Flask WSGI app for letting people connect their RunKeeper accounts
 * a PostGIS ORM based on SQLAlchemy and GeoAlchemy
 * some super experimental processing to generate outputs, this bit is
   definitely a work in progress.

The app is designed to run on Redhat OpenShift, except that OpenShift
currently does not support Postgres 9.2/PostGIS 2.0.

RunKeeper API
-------------

People may find rk.py useful, which is a Python module to talk the RunKeeper
API. Please use your own client ID and client secret if you use this module.

Thanks :)

What about Strava?
------------------

I am open to adding other cycle tracking services, e.g. Strava. The only
requirement is they have an API we can access data from (currently Strava
does not). If you desparately want an additional API, send me a pull request.
