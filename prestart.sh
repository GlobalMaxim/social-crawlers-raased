#! /usr/bin/env bash

# Let the DB start
poetry run python3 ./app/backend_pre_start.py

# Run migrations
poetry run alembic upgrade head

# Create initial data in DB
poetry run python3 ./app/initial_data.py
