# EU-CS_platform

EU-CS_platform is a web platform for Citizen Science. It is built with [Python][0] using the [Django Web Framework][1].

## Requirements
sudo apt install python3-venv
sudo apt install python3-pip
sudo apt install libpq-dev
sudo apt install postgresql
sudo apt install gettext
python3 -m venv EuCs
source EuCs/bin/activate

## Configure postgres
sudo -u postgres psql
create database eucitizenscience;
create user eucitizenscience with password 'XXXXXXXXXXXXXX';
//grant all on eucitizenscience.* to eucitizenscience
grant all on  database eucitizenscience to eucitizenscience;

```
ALTER ROLE eucitizenscience WITH LOGIN;
ALTER ROLE eucitizenscience WITH SUPERUSER;
ALTER ROLE eucitizenscience WITH CREATEDB;
ALTER ROLE eucitizenscience WITH CREATEROLE;
ALTER ROLE eucitizenscience WITH INHERIT;
ALTER ROLE eucitizenscience WITH REPLICATION;
```

## Installation
First of all, install Python v3 <br/>
sudo apt install python3-dev
sudo apt install libpq-dev


In source directory: <br/>
    ```
    pip install -r requirements.txt
    pip3 install -r requirements.txt
    ```
```
cd src
cp eucs_platform/settings/local.sample.reference.env eucs_platform/settings/local.env
And edit this last file with database and email configuration
```

```
sudo apt-get install gdal-bin
sudo apt install postgis postgresql-postgis
```

### Modificar la referencias de Sequence para python 3.10
Abrir el archivo /venv/EuCs/lib/python3.10/site-packages/leaflet/utils.py
Modificar from collections import Sequence // from collections.abc import Sequence

```
python manage.py migrate
```

```
python manage.py loaddata projects/fixtures/topics.json
python manage.py loaddata projects/fixtures/status.json
python manage.py loaddata projects/fixtures/participationtasks.json
python manage.py loaddata projects/fixtures/geographicextend.json
python manage.py loaddata resources/fixtures/categories.json
python manage.py loaddata resources/fixtures/themes.json
python manage.py loaddata resources/fixtures/audiences.json
python manage.py loaddata organisations/fixtures/organisation_types.json
```


## Launch
```
python manage.py runserver
```

## Cron jobs commands
```
python manage.py runcrons
python manage.py runcrons --force
And to do this automatically:
python manage.py crontab add
```

## Configuración del servidor

sudo apt install nginx
sudo apt install supervisor
sudo systemctl enable supervisor
sudo systemctl start supervisor

sudo apte install gunicorn
pip3 install gunicorn
cd ../..
sudo nano bin/gunicorn_srtat


[0]: https://www.python.org/
[1]: https://www.djangoproject.com/


## Información de GUNICORN
#! /bin/bash

NAME="EuCs_Test"
DIR=/home/eu-cs/Desktop/Repositorios/EuCs_Test
USER=eu-cs
GROUP=eu-cs
WORKERS=3
BIN=unix: /home/eu-cs/run/gunicorn.sock
DJANGO_SETTINGS_MODDULE=eu-cs.src.eucs_platform.settings.base
DJANGO_WSGI_MODDULE=eu-cs.src.eucs_platform.wsgi
LOG_LEVEL=error

cd $DIR

source ../bin/activate

export DJANGO_SETTINGS_MODDULE_=$DJANGO_SETTINGS_MODDULE
export PYTHONPATH=$DIR:$PYTHONPATH

exec ../bin/guncorn ${DJANGO_WSGI_MODDULE}:application \
