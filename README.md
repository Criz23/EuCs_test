# EU-CS_platform

EU-CS_platform is a web platform for Citizen Science. It is built with [Python][0] using the [Django Web Framework][1].

## Requirements
```
sudo apt install python3-venv
sudo apt install python3-pip
sudo apt install libpq-dev
sudo apt install postgresql
sudo apt install gettext
python3 -m venv EuCs
source EuCs/bin/activate
```

## Configure postgres
```
sudo -u postgres psql
create database eucitizenscience;
create user eucitizenscience with password 'XXXXXXXXXXXXXX';
grant all on  database eucitizenscience to eucitizenscience;
ALTER ROLE eucitizenscience WITH LOGIN;
ALTER ROLE eucitizenscience WITH SUPERUSER;
ALTER ROLE eucitizenscience WITH CREATEDB;
ALTER ROLE eucitizenscience WITH CREATEROLE;
ALTER ROLE eucitizenscience WITH INHERIT;
ALTER ROLE eucitizenscience WITH REPLICATION;
```

## Installation
First of all, install Python v3
```
sudo apt install python3-dev
sudo apt install libpq-dev
sudo apt-get install gdal-bin
sudo apt install postgis postgresql-postgis
```

In source directory:
```
pip3 install -r requirements.txt
```
Copy file local settings for edit <br/>
And edit this last file with database and email configuration
```
cd src
cp eucs_platform/settings/local.sample.reference.env eucs_platform/settings/local.env
```


### Modificar la referencias de Sequence para python 3.10
Open file wiht nano
```
/venv/EuCs/lib/python3.10/site-packages/leaflet/utils.py
```
Edit "from collections import Sequence"
```
from collections.abc import Sequence
```
Run migration
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

## Apache server configuration
```
sudo apt install apache2 libapache2-mod-wsgi-py3
```
Edit file conf
```
sudo nano /etc/apache2/sites-available/000-default.conf
service apache2 restart
```
Update access Permission
```
sudo chmod -R 775 /home/<name_folder>
sudo chmod 775 /home/<user>
sudo chmod a+rwx logs/project.log
```