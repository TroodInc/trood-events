default: run

install:
	@pipenv install

build-docs:
	@pipenv run sphinx-build -a -c docs docs docs/_build

run:
	@pipenv run python setup.py install
	@make build-docs
	@pipenv run python events/server.py

console-client:
	@pipenv run python console_client.py

test:
	@pipenv run pytest -x

.PHONY: default run test
