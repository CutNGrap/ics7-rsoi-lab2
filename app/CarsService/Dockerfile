FROM python:3.10

WORKDIR /code

ARG database_url="postgresql://program:test@postgres:5432/cars"

ENV DATABASE_URL=$database_url

COPY ./requirements.txt /code/requirements.txt

RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

COPY ./app/CarsService /code/app

CMD ["fastapi", "run", "app/main.py", "--port", "8070"]