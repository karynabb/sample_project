#!/usr/bin/env bash

set -o pipefail
set -o errexit
set -o nounset

export WEB_CONCURRENCY=$((2 * `nproc` + 1))

poetry install

postgres_ready() {
  python manage.py check --database default
}

until postgres_ready; do
  >&2 echo 'Waiting for PostgreSQL to become available...'
  sleep 1
done

python manage.py migrate
python manage.py createsuperuser --no-input > /dev/null 2>&1 || true

exec ${@}
