FROM python:slim

RUN useradd pythonldapadmin

WORKDIR /home/pythonldapadmin

COPY app app
COPY boot.sh app
COPY config.py app
COPY pythonldapadmin.py app
COPY requirements.txt app

run apt-get update -y
run apt-get install build-essential python3-dev python2.7-dev \
    libldap2-dev libsasl2-dev ldap-utils tox \
    lcov valgrind -y

RUN python3 -m venv venv
RUN venv/bin/pip3 install -r app/requirements.txt
RUN venv/bin/pip3 install gunicorn

RUN chmod +x app/boot.sh

ENV FLASK_APP pythonldapadmin.py

RUN chown -R pythonldapadmin:pythonldapadmin ./
USER pythonldapadmin

EXPOSE 5000

ENTRYPOINT ["./app/boot.sh"]
