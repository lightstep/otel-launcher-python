test:
	pip install -e .[test]
	pytest

cover:
	pytest --cov src/opentelemetry/lightstep

lint:
	black . --diff --check
	isort --recursive . 
	flake8 .

clean-dist:
	rm -Rf ./dist

dist: clean-dist
	mkdir -p ./dist
	python setup.py sdist      # source distribution
	python setup.py bdist_wheel

publish: dist
	twine upload dist/*

publish-test:
	twine upload --repository-url https://test.pypi.org/legacy/ dist/*

changelog:
	pip install pystache gitchangelog
	gitchangelog
