FROM python:3.8-slim-buster

CMD ["sudo", "apt-get", "install", "gcc"]

RUN apt-get update \
    && apt-get -y install libpq-dev gcc

RUN pip install --upgrade pip

ENV PIP_ROOT_USER_ACTION=ignore

COPY requirements /app/requirements

RUN pip install --no-cache-dir -r /app/requirements/prod.txt

COPY . /app

WORKDIR /app

EXPOSE 8000

RUN python manage.py collectstatic --noinput

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]