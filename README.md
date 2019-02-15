# Ski Stats Webapp
A web framework for generating single-page applications from a collection of data analysis scripts.  
Analysis scripts should be added to the `ski_stats.scripts` package and should
implement `get_html_form() : form` and `html_form_submitted(form) : image`.  

Uses: Python 2.7, NumPy, SciPy, Flask, WTForms.

## Example

![Sample image](/readme_form_example.png "Form example")

#### my_nonlinear_curve_fitter.py
```python
from flask_wtf import FlaskForm
from io import BytesIO
from ski_stats.forms.fields import (
    Title, BrowseSpreadsheetInput, MathEquation, RunButton, 
    ParamGroup, ParamInput, ParamBoundsGroup, ParamBoundsInput
)

def get_html_form():
    """Returns a FlaskForm."""
    
    class HtmlForm(FlaskForm):
        title = Title("Non-Linear Curve Fitting")
        spreadsheet = BrowseSpreadsheetInput(label="Select measurement data")
        equation = MathEquation(label="Curve equation", 
                                latex=r"y_1\sim h\cdot\cos\left(\frac{2\left(x_1+v\right)\pi}{p}\right)+b")
        initial_params = ParamGroup(label="Initial params guess", fields=[
            ParamInput(param="h", size=5, default=700),
            ParamInput(param="b", size=5, default=200),
            ParamInput(param="v", size=5, default=0),
            ParamInput(param="p", size=5, default=24),
        ])
        param_bounds = ParamBoundsGroup(label="Param bounds", fields=[
            ParamBoundsInput(param="h", size=5, default_min="-inf", default_max="inf"),
            ParamBoundsInput(param="b", size=5, default_min="-inf", default_max="inf"),
            ParamBoundsInput(param="v", size=5, default_min="-inf", default_max="inf"),
            ParamBoundsInput(param="p", size=5, default_min="-inf", default_max="inf"),
        ])
        do_curve_fit = RunButton(label="", button_text="Do curve fit")
        
    return HtmlForm()


def html_form_submitted(form):
    """Handles a submitted, validated FlaskForm. Returns an image stream."""
    
    time, data = form.spreadsheet.parse()
    initial_params = form.initial_params.data
    bounds = form.param_bounds.data

    # do calculation and generate a matplotlib figure...
    buf = BytesIO()
    fig.savefig(buf, format="png")
    buf.seek(0)
    return buf
```  

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
git clone https://github.com/CoeJoder/Ski-Stats-Webapp.git
cd Ski-Stats-Webapp
virtualenv venv
./venv/bin/pip install -r requirements.txt
sudo ln -s /var/www/Ski-Stats-Webapp/ski-stats-webapp.service /etc/systemd/system/ski-stats-webapp.service
sudo systemctl daemon-reload
```
## Management 
```shell
# Startup
sudo systemctl start ski-stats-webapp.service

# Shutdown
sudo systemctl stop ski-stats-webapp.service

# Restart
sudo systemctl restart ski-stats-webapp.service

# Check status
sudo systemctl status ski-stats-webapp.service
```

## Authors
Evan Raiewski  
Joe Nasca
