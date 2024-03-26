PROJECT="Game Interface Flows API"

run:
	python manage.py runserver

venv:
	source .venv/bin/activate

pretty:
	black .
	isort .

superuser:
	python manage.py createsuperuser

migrate:
	python manage.py makemigrations
	python manage.py migrate

.PHONY: run
