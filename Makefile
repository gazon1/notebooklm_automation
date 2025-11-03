SHELL := /bin/bash

ifneq (,$(wildcard ./.env))
	include .env
	export $(shell sed 's/=.*//' .env)
endif

install:
	@echo "Установка зависимостей..."
	source dacha/bin/activate
	poetry self add poetry-plugin-export

update:
	poetry update

req:
	poetry export --without-hashes --without-urls | awk '{ print $1 }' FS=';' > requirements.txt

install_req:
	pip install -r requirements.txt


ytb-dlp:
	yt-dlp \
	--cookies tmp/youtube_cookies.txt \
	--skip-download --write-info-json --write-description --write-thumbnail \
	--print "%(title)s|%(webpage_url)s" \
	https://www.youtube.com/playlist?list=WL \
	> youtube_video_links.txt


update-db-alembic:
	python -m alembic revision --autogenerate -m "Add review status columns"
	alembic upgrade head