PROJECT="Game Interface Flows API"

run:
	python manage.py runserver

venv:
	source .venv/bin/activate

pretty:
	black .
	isort .

test:
	python manage.py test

superuser:
	python manage.py createsuperuser

migrate:
	python manage.py makemigrations
	python manage.py migrate

static:
	python manage.py collectstatic

docker_build:
	docker image build -t game-interface-flows-backend .

docker_run:
	docker run -p 8000:8000 game-interface-flows-backend


.PHONY: run
