#!/bin/sh
set -e

if [ "$ENV" = "DEV" ]; then
	echo "Running Development Application"
	pip install --no-deps -e .
	exec python mosquittoChat/server.py


elif [ "$ENV" = "UNIT_TEST" ]; then
	echo "Running Unit Tests"
	pip install --no-deps -e .
	exec pytest -v -s --cov=./mosquittoChat tests/unit 
	# exec tox -e unit

elif [ "$ENV" = "CONTRACT_TEST" ]; then
	echo "Running Contract Tests"
	pip install --no-deps -e .
	exec pytest -v -s --cov=./mosquittoChat tests/contract
	# exec tox -e contract

elif [ "$ENV" = "INTEGRATION_TEST" ]; then
	echo "Running Integration Tests"
	pip install --no-deps -e .
	exec pytest -v -s --cov=./mosquittoChat tests/integration
	# exec tox -e integration

elif [ "$ENV" = "COMPONENT_TEST" ]; then
	echo "Running Component Tests"
	pip install --no-deps .
	exec python mosquittoChat/server.py

elif [ "$ENV" = "END_TO_END_TEST" ]; then
	echo "Running End_To_End Tests"
	pip install --no-deps .
	exec python mosquittoChat/server.py

elif [ "$ENV" = "LOAD" ]; then
	echo "Running Load Tests"
	pip install --no-deps .
	exec python mosquittoChat/server.py

elif [ "$ENV" = "PROD" ]; then 
	echo "Running Production Application"
	pip install --no-deps .
	exec python mosquittoChat/server.py

else
	echo "Please provide an environment"
	echo "Stopping"
fi
