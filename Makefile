.PHONY: run test

run:
	PYTHONPATH=src python -m able_to_answer --reload --host 0.0.0.0 --port 8000

test:
	PYTHONPATH=src python -m pytest tests/ -v
