#!/usr/bin/env sh

DATABASE=$1
USER="cyclerouter"

if [ "x$1" = "x" ]; then
    echo "Please provide database name"
    exit 1
fi

sudo su postgres -c 'psql' << EOF
CREATE DATABASE $DATABASE;
\c $DATABASE;
GRANT ALL ON DATABASE $DATABASE TO "$USER";
CREATE EXTENSION postgis;
GRANT ALL ON spatial_ref_sys TO "$USER";
GRANT ALL ON geometry_columns TO "$USER";
EOF
