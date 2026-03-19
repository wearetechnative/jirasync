{
  description = "Jira synchronization tool for one-way sync from client boards to organization boards";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-25.11";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};

        pythonEnv = pkgs.python3.withPackages (ps: with ps; [
          requests
        ]);

        jirasync = pkgs.stdenv.mkDerivation {
          pname = "jirasync";
          version = "1.0.0";

          src = ./.;

          nativeBuildInputs = [ pkgs.makeWrapper ];

          installPhase = ''
            mkdir -p $out/bin $out/share/jirasync

            # Install the Python script
            cp jirasync.py $out/share/jirasync/
            chmod +x $out/share/jirasync/jirasync.py

            # Create wrapper
            makeWrapper ${pythonEnv}/bin/python3 $out/bin/jirasync \
              --add-flags "$out/share/jirasync/jirasync.py"
          '';

          meta = with pkgs.lib; {
            description = "One-way Jira synchronization tool";
            homepage = "https://github.com/wearetechnative/jirasync";
            license = licenses.mit;
            platforms = platforms.linux;
            maintainers = [ ];
          };
        };

      in {
        packages = {
          default = jirasync;
          jirasync = jirasync;
        };

        apps = {
          default = {
            type = "app";
            program = "${jirasync}/bin/jirasync";
          };
        };

        # For development
        devShells.default = pkgs.mkShell {
          buildInputs = [
            pythonEnv
          ];
        };
      }
    );
}
