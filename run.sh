#!/bin/bash
set -e

if ! command -v poetry >/dev/null
then
    >&2 echo "poetry not installed"
    exit 1
fi

poetry run python scrape.py

