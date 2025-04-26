hass_config := absolute_path('config')
custom_components := absolute_path('custom_components')

default: run

# Install dependencies needed for development and test
setup:
    python -m pip install --requirement requirements.txt

# Start Home Assistant with Drooff fire+ integration
run:
    #! /usr/bin/env bash
    set -e

    if [[ ! -d "{{ hass_config }}" ]]; then
        mkdir -p "{{ hass_config }}"
        hass --config "{{ hass_config }}" --script ensure_config
    fi

    export PYTHONPATH="${PYTHONPATH}:{{ custom_components }}"

    hass --config "{{ hass_config }}" --debug

# Format sources
format:
    ruff format .

# Apply linting rules with `ruff`
check:
    ruff check --fix .
