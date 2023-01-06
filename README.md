# iaroapp

## Setup

On MacOS

```
sh <(curl -L https://nixos.org/nix/install)
# Restart terminal after successfull installation
nix --extra-experimental-features "nix-command flakes" run git clone https://git.project-insanity.org/onny/iaroapp.git
cd iaroapp
nix --extra-experimental-features "nix-command flakes" develop
```

## Run local server


```
nix develop
python manage.py migrate
python manage.py runserver
```
