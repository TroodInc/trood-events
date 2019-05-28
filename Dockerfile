FROM python:3.7

RUN mkdir -p /app
WORKDIR /app
COPY . /app/

RUN pip install --upgrade pip pipenv && pipenv install

CMD ["sh", "docker-entrypoint.sh"]
