FROM python:3.9-alpine

COPY requirements.txt requirements.txt

# rust is required to pip install tiktoken
RUN apk add --no-cache rust cargo

RUN \
 apk add --no-cache postgresql-libs && \
 apk add --no-cache --virtual .build-deps gcc musl-dev postgresql-dev && \
 python3 -m pip install -r requirements.txt --no-cache-dir && \
 apk --purge del .build-deps

COPY app.py .

CMD [ "python3", "-m" , "flask", "run", "--host=0.0.0.0"]