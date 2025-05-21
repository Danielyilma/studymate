
FROM python:3.10-alpine

WORKDIR /app

COPY . /app

RUN pip install --no-cache-dir -r requirements.txt

# RUN python3 manage.py migrate

EXPOSE 8000

CMD ["daphne", "studymate.asgi:application"]
