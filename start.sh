#!/bin/bash
export $(grep -v '^#' .env | sed 's/"//g' | xargs -d '\n')
poetry run uvicorn src.ticketing_system.api.index:app --host 0.0.0.0 --port 8000 --log-level info
