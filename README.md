# iaroapp

## Overview

What is already supported

- [x] Administration interface
- [x] Managing users and groups
- [x] Adding tasks (admin)
- [x] Adding items to the inventory list (admin)

## Install

On MacOS

```
sh <(curl -L https://nixos.org/nix/install)
mkdir -p ~/.config/nix
echo 'experimental-features = nix-command flakes' >> ~/.config/nix/nix.conf
# Restart terminal after successfull installation
nix run nixpkgs#git clone https://git.project-insanity.org/onny/iaroapp.git
```

On Debian

```
sudo apt install git python3 npm
cd /usr/share
sudo git clone https://git.project-insanity.org/onny/iaroapp.git
chown -R http:http iaroapp
cd iaroapp
sudo -u http python3 -m venv .venv
sudo -u http .venv/bin/pip3 install -r requirements.txt
cp dist/iaroapp.service /etc/systemd/system/
cp dist/app.iaro.co.conf /etc/nginx/sites-enabled/
systemctl enable iaroapp
systemctl start iaroapp
systemctl reload nginx
```

## Configure

Create admin user
```
cd iaroapp
nix develop
python3 manage.py createsuperuser
```

Create `.env` file in the project root folder and add the Planday credentials
```
CLIENT_ID=
REFRESH_TOKEN=
``` 

## Build

```
cd iaroapp
nix develop
make
```

## Run

```
cd iaroapp
nix develop
nix run
```

Open http://localhost:8000. To access the admin panel go to
http://localhost:8000/admin.

## Documentation

### Where are the template files stored?

