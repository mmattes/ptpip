init:
	pip install -r requirements.txt -t .pip

clean-pyc:
	find . -name '*.pyc' -exec rm --force {} +
	find . -name '*.pyo' -exec rm --force {} +
	find . -name '*~' -exec rm --force  {} +

clean-build:
	rm --force --recursive build/
	rm --force --recursive .pip/
	rm --force --recursive dist/
	rm --force --recursive *.egg-info

.PHONY: clean-pyc clean-build
