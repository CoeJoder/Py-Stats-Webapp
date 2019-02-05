# Py Stats Webapp
Framework for generating a single-page application from a collection of data analysis scripts.  Uses Python 2.7 and Flask.

![Sample image](/sample_output.png "Sample output")

## Deployment (Ubuntu 18.04 + [Gunicorn](https://gunicorn.org/))
This is just one way to deploy the application; adjust as necessary.  The webapp will start on boot, listening on port 8000.
```shell
# System setup
sudo apt install git
sudo apt install python
sudo apt install python-pip
sudo -H pip install virtualenv

# User and filesystem prep
sudo mkdir /var/www
sudo groupadd www-data
sudo useradd -d /var/www -g www-data -s /usr/sbin/nologin www-data
sudo chgrp www-data /var/www
sudo chmod 2770 /var/www
sudo gpasswd --add $USER www-data
su - $USER

# Installation
cd /var/www
git clone https://github.com/CoeJoder/Py-Stats-Webapp.git
cd Py-Stats-Webapp
virtualenv venv
./venv/bin/pip install -r requirements.txt
sudo ln -s /var/www/Py-Stats-Webapp/py-stats-webapp.service /etc/systemd/system/py-stats-webapp.service
sudo systemctl daemon-reload
```
## Management 
```shell
# Startup
sudo systemctl start py-stats-webapp.service

# Shutdown
sudo systemctl stop py-stats-webapp.service

# Restart
sudo systemctl restart py-stats-webapp.service

# Check status
sudo systemctl status py-stats-webapp.service
```

## Authors
Evan Raiewski  
Joe Nasca
