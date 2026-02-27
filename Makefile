.PHONY: run

run:
	uvicorn able_to_answer.api.main:app --reload --host 0.0.0.0 --port 8000
