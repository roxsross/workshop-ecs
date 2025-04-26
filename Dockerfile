
FROM python:3.13-alpine

WORKDIR /app

COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

COPY . /app/

EXPOSE 8080

CMD ["flask", "run", "--host=0.0.0.0", "--port=8080"]
