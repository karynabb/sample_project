FROM python:3.11-slim as base
LABEL maintainer="dev@example.com"

ARG HOST_USER_ID="1000"
ARG HOST_GROUP_ID="100"

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    POETRY_VIRTUALENVS_CREATE=0 \
    POETRY_NO_INTERACTION=1 \
    VIRTUAL_ENV=/opt/venv

ENV PATH="${VIRTUAL_ENV}/bin:${PATH}"

RUN mkdir -p /srv/http && \
    python -m venv ${VIRTUAL_ENV}

RUN groupadd -f -g ${HOST_GROUP_ID} appuser \
    && useradd -u ${HOST_USER_ID} -g ${HOST_GROUP_ID} -m -s /bin/bash appuser \
    && chown -R "${HOST_USER_ID}:${HOST_GROUP_ID}" ${VIRTUAL_ENV} \
    && chown -R "${HOST_USER_ID}:${HOST_GROUP_ID}" /srv/http

WORKDIR /srv/http


FROM base as poetry-install

ENV PATH="/root/.local/bin:${PATH}"

RUN apt-get update && apt-get install --no-install-recommends -y openssh-client

RUN mkdir -m 0700 ~/.ssh && ssh-keyscan github.com >> ~/.ssh/known_hosts   # add hostname to known_hosts

ADD --chown=appuser:appuser https://install.python-poetry.org/ install-poetry.py
RUN POETRY_VERSION=1.8.5 python install-poetry.py -y

COPY --chown=appuser:appuser poetry.lock pyproject.toml ./

RUN --mount=type=ssh poetry install --only main

RUN python -m spacy download en_core_web_lg && \
    python -m nltk.downloader -d /usr/local/share/nltk_data wordnet


FROM poetry-install as dev

RUN --mount=type=ssh poetry install

COPY --chown=appuser:appuser entrypoint-dev.sh /usr/local/bin/entrypoint
RUN chmod +x /usr/local/bin/entrypoint

ENTRYPOINT [ "entrypoint" ]

CMD ["python", "manage.py", "runserver", "0:8000"]


FROM base as dist

USER appuser

COPY --chown=appuser:appuser --from=poetry-install $VIRTUAL_ENV $VIRTUAL_ENV
COPY --from=poetry-install /usr/local/share/nltk_data /usr/local/share/nltk_data

COPY --chown=appuser:appuser . .

COPY --chown=appuser:appuser entrypoint-dist.sh /usr/local/bin/entrypoint
RUN chmod +x /usr/local/bin/entrypoint

ENTRYPOINT [ "entrypoint" ]

CMD ["gunicorn", \
    "app.wsgi:application", \
    "--bind=0.0.0.0:8000", \
    "--timeout 60", \
    "--access-logfile", \
    "-", \
    "--error-logfile", \
    "-", \
    "--capture-output" ]
