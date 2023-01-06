# iaroapp

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


```
cd iaroapp
nix develop
nix run
```
