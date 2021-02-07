FROM python:3.6.3-alpine
COPY . /app
WORKDIR /app
ADD requirements.txt /app/requirements.txt

RUN apk update && \
    apk add --no-cache libstdc++ graphviz postgresql-libs && \
    apk add --no-cache --virtual .build-deps python-dev g++ make swig linux-headers postgresql-dev graphviz-dev && \
    pip3 install -r /app/requirements.txt && \
    apk del .build-deps
EXPOSE 8080
ENTRYPOINT ["python"]
CMD ["Tests.py"]