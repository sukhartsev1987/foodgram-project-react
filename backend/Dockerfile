FROM python:3.9
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["gunicorn", "foodgram.wsgi:application", "--bind", "0:8000" ]
# ONBUILD RUN python manage.py migrate
# ONBUILD RUN python manage.py collectstatic --noinput