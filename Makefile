SRCS_DIR = src
UV_PY = uv run python3
MYPY_FLAGS = --warn-return-any --warn-unused-ignores --ignore-missing-imports --disallow-untyped-defs --check-untyped-defs
VENV = .venv


install:
	uv sync
	$(UV_PY) -m spacy download en_core_web_lg

run:
	$(UV_PY) -m src $(ARGS)

debug:
	$(UV_PY) -m src --debug

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
	rm -rf __pycache__ .mypy_cache .pytest_cache
	rm -rf data/output
	rm -rf data/processed
# 	rm -rf $(VENV)

lint:
	$(UV_PY) -m flake8 $(SRCS_DIR)
	$(UV_PY) -m mypy $(SRCS_DIR) $(MYPY_FLAGS)

lint-strict:
	$(UV_PY) -m flake8 $(SRCS_DIR)
	$(UV_PY) -m mypy $(SRCS_DIR) $(MYPY_FLAGS) --strict

