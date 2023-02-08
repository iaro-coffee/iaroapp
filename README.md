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

On Synology

Requirements
* Setup user home directories, see [here](https://asciich.ch/wordpress/synology-home-directory-fur-benutzer-festlegen/)
* Add Synocommunity Repo, see [here](https://synocommunity.com)
* Install `git` via Synology Software Center

```
cd /usr/share
sudo git clone https://git.project-insanity.org/onny/iaroapp.git
python3 -m ensurepip
python3 -m pip install -r requirements.txt
python3 manage.py runserver 0.0.0.0:8000
```

## Configure

Create admin user
```
cd iaroapp
nix develop
python3 manage.py createsuperuser
```

## Run

```
cd iaroapp
nix develop
nix run
```

Open http://localhost:8000. To access the admin panel go to
http://localhost:8000/admin.
