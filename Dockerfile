FROM python:3.10

ADD src/ /app
COPY requirements.txt /app/requirements.txt
RUN pip install -r /app/requirements.txt
RUN pip install gunicorn

EXPOSE 8000
WORKDIR /app/
ENTRYPOINT ["gunicorn", "--workers=2", "-b", "0.0.0.0:8000", "cdn:app"]