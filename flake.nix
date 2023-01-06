{
  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/master";
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
            ${pkgs.python3}/bin/python manage.py migrate
            ${pkgs.python3}/bin/python manage.py runserver
          '';
      in
      {
        devShell = pkgs.mkShell {
          packages = with pkgs; [
            python3Packages.django
            python3Packages.dj-database-url
            python3Packages.whitenoise
          ];
        };

        packages = { inherit start; };
        defaultPackage = start;
      });
}
