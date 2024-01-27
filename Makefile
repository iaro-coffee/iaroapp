all:
	npm ci
	rm -r staticfiles
	python manage.py collectstatic
