# Ski Slope Least-Squares
A simple website interface for a SciPy least-squares curve-fitting function.
Written in Python, using the Flask framework.

![Sample image](/sample_output.png "Sample output")

## Deployment (Ubuntu 18.04 + [Gunicorn](https://gunicorn.org/))
This is just one way to deploy the application; adjust as necessary.  The webapp will start automatically on boot with this configuration.
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
sudo chmod 775 /var/www
sudo gpasswd --add $USER www-data
su - $USER

# Installation
cd /var/www
git clone https://github.com/CoeJoder/Nonlinear-Least-Squares.git
cd Nonlinear-Least-Squares
virtualenv venv
source ./venv/bin/activate
pip install -r requirements.txt
sudo ln -s /var/www/Nonlinear-Least-Squares/nonlinear-least-squares.service /etc/systemd/system/nonlinear-least-squares.service
sudo chmod 755 nonlinear-least-squares.service
sudo systemctl daemon-reload
```
## Management 
```
# Startup
sudo systemctl start nonlinear-least-squares.service

# Shutdown
sudo systemctl stop nonlinear-least-squares.service

# Restart
sudo systemctl restart nonlinear-least-squares.service

# Check status
sudo systemctl status nonlinear-least-squares.service
```

## Authors
Evan Raiewski  
Joe Nasca
