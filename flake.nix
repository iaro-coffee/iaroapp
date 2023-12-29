{
  inputs = {
    nixpkgs.url = "nixpkgs/nixos-23.11";
    # Required for multi platform support
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = import nixpkgs { inherit system; };

        start =
          pkgs.writeShellScriptBin "start" ''
            set -e
            ${pkgs.python3}/bin/python manage.py makemigrations
            ${pkgs.python3}/bin/python manage.py migrate
            ${pkgs.python3}/bin/python manage.py runserver
          '';
      in
      {
        devShell = pkgs.mkShell {
          packages = with pkgs; with python3Packages; [
            python3
            django_5
            dj-database-url
            whitenoise
            django-widget-tweaks
            setuptools # Required by widget-tweaks
            django-login-required-middleware
            django_colorful
            django-crispy-forms
            django-crispy-bootstrap4
            django-import-export
            requests
            python-dotenv
            django-ckeditor
            dateutil
          ];
        };

        packages = { inherit start; };
        defaultPackage = start;
      });
}
