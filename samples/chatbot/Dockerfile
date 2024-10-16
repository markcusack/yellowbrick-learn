FROM python:3.9-alpine

COPY requirements.txt requirements.txt

# rust is required to pip install tiktoken
RUN apk add --no-cache rust cargo

RUN \
 apk add --no-cache curl && \
 apk add --no-cache postgresql-libs && \
 apk add --no-cache --virtual .build-deps gcc musl-dev postgresql-dev && \
 python3 -m pip install -r requirements.txt --no-cache-dir && \
 apk --purge del .build-deps

HEALTHCHECK --interval=5m --timeout=3s \
  CMD curl -f http://localhost:8080/health || exit 1

COPY app.py .
ENV FLASK_RUN_PORT=8080
EXPOSE 8080
CMD [ "python3", "-m" , "flask", "run", "--host=0.0.0.0"]
