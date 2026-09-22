FROM python:3.14-slim

WORKDIR /code

RUN apt-get update && \
    apt-get install -y --no-install-recommends curl && \
    rm -rf /var/lib/apt/lists/*

COPY ./requirements.txt /code/requirements.txt

RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

COPY . .

EXPOSE 8000

CMD ["gunicorn", "app.main:app", "-c", "gunicorn_conf.py"]
