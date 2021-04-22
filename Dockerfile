FROM python:3.7

RUN mkdir -p /app
WORKDIR /app
COPY . /app/

RUN pip install --upgrade pip pipenv && pipenv install


# RUN pip install -r requirements.txt

CMD ["sh", "docker-entrypoint.sh"]
