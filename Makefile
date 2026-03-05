.PHONY: venv install all quick app test smoke docker-build docker-run

venv:
	python -m venv .venv

install:
	python -m pip install -r requirements.txt
	python -m pip install -e .

all:
	python -m traffic_analytics_demo.cli all

quick:
	python -m traffic_analytics_demo.cli all --days 30 --seed 7 --road-segments 24 --accidents 500 --violations 1600 --sensors-rows 5000

app:
	streamlit run app/streamlit_app.py

test:
	python -m pytest -q

smoke:
	python -m compileall src app
	python -m pytest tests/test_cli_runtime.py tests/test_streamlit_app.py -q

docker-build:
	docker build -t traffic-safety-analytics .

docker-run:
	docker run --rm -p 8501:8501 traffic-safety-analytics
