# base image
FROM python:3.7.2-alpine

# install dependencies
RUN apk update && \
    apk add --virtual build-deps gcc python-dev musl-dev && \
    apk add postgresql-dev && \
    apk add netcat-openbsd

# set working directory
WORKDIR /usr/src/app

# add and install requirements
COPY ./requirements.txt /usr/src/app/requirements.txt
RUN pip install -r requirements.txt

# add app
COPY . /usr/src/app

# run server
# OLD: "CMD python manage.py run -h 0.0.0.0"

# this calls a bash script that first sets up some things and then does the
# "python manage.py run ... " stuff
CMD ["/usr/src/app/entrypoint.sh"]
