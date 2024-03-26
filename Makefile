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

docker_build:
	docker image build -t game-interface-flows-backend .

docker_run:
	docker run -p 3000:3000 game-interface-flows-backend


.PHONY: run
