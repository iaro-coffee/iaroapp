# iaroapp

## Overview

What is already supported

- [x] Administration interface
- [x] Managing users and groups
- [x] Adding tasks (admin)
- [x] Adding items to the inventory list (admin)

## Setup

On MacOS

```
sh <(curl -L https://nixos.org/nix/install)
mkdir -p ~/.config/nix
echo 'experimental-features = nix-command flakes' >> ~/.config/nix/nix.conf
# Restart terminal after successfull installation
nix run git clone https://git.project-insanity.org/onny/iaroapp.git
```

## Run local server

Create admin user
```
python3 manage.py createsuperuser
```

```
cd iaroapp
nix develop
nix run
```

Open http://localhost:8000. To access the admin panel go to
http://localhost:8000/admin.
