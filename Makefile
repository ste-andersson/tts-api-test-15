.PHONY: install run dev lint format zip test test-unit test-api-mock test-full-mock test-elevenlabs test-pipeline clear-output

VENV?=.venv
PY?=python3.13

install:
	$(PY) -m venv $(VENV)
	. $(VENV)/bin/activate && pip install -U pip && pip install -r requirements.txt

run:
	. $(VENV)/bin/activate && uvicorn app.main:app --host 0.0.0.0 --port $${PORT:-8080}

dev:
	. $(VENV)/bin/activate && uvicorn app.main:app --reload --host 0.0.0.0 --port $${PORT:-8080}

format:
	. $(VENV)/bin/activate && python -m pip install ruff==0.6.9 && ruff format .

lint:
	. $(VENV)/bin/activate && python -m pip install ruff==0.6.9 && ruff check .

zip:
	python tools/make_zip.py

test:
	. $(VENV)/bin/activate && python -m pytest tests/ -v

test-unit:
	. $(VENV)/bin/activate && python -m pytest tests/test_receive_text.py -v

test-api-mock:
	. $(VENV)/bin/activate && python -m pytest tests/test_text_to_audio.py tests/test_send_audio.py -v

test-full-mock:
	. $(VENV)/bin/activate && python -m pytest tests/test_full_tts_pipeline.py -v

test-elevenlabs:
	. $(VENV)/bin/activate && python -m pytest tests/test_real_elevenlabs.py -v -s

test-pipeline:
	. $(VENV)/bin/activate && python -m pytest tests/test_full_chain.py -v -s

clear-output:
	@echo "🧹 Rensar test_output-mappen..."
	@rm -rf test_output
	@echo "✅ test_output rensad!"
