.PHONY: setup train evaluate demo test eda clean

setup:
	python -m venv venv
	.\venv\Scripts\pip install -r requirements.txt

train:
	.\venv\Scripts\python -m src.ingestion
	.\venv\Scripts\python -m src.features
	.\venv\Scripts\python -m src.split
	.\venv\Scripts\python -m src.train
	.\venv\Scripts\python -m src.evaluate

evaluate:
	.\venv\Scripts\python -m src.evaluate

demo:
	.\venv\Scripts\streamlit run src/dashboard.py

test:
	.\venv\Scripts\pytest tests/test_pipeline_smoke.py

eda:
	.\venv\Scripts\python -m src.eda

clean:
	Remove-Item -Recurse -Force data\raw\* -ErrorAction SilentlyContinue
	Remove-Item -Recurse -Force data\processed\* -ErrorAction SilentlyContinue
	Remove-Item -Recurse -Force models\* -ErrorAction SilentlyContinue
	Remove-Item -Recurse -Force reports\figures\* -ErrorAction SilentlyContinue
	Remove-Item -Force reports\*.md -ErrorAction SilentlyContinue
