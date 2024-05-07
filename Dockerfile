FROM python:3.11-slim-buster

CMD ["sudo", "apt-get", "install", "gcc"]

RUN apt-get update \
    && apt-get -y install libpq-dev gcc

RUN apt-get install -y libgl1-mesa-glx

RUN pip install --upgrade pip

ENV PIP_ROOT_USER_ACTION=ignore

COPY requirements /app/requirements

RUN pip install --no-cache-dir -r /app/requirements/prod.txt

COPY .env /app/.env

COPY manage.py /app

COPY config app/config

COPY apps /app/apps

WORKDIR /app

EXPOSE 8000

RUN python manage.py collectstatic --noinput
