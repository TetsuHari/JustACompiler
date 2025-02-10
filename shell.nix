# shell.nix
let
  # We pin to a specific nixpkgs commit for reproducibility.
  # Last updated: 2024-04-29. Check for new commits at https://status.nixos.org.
  pkgs = import (fetchTarball "https://github.com/NixOS/nixpkgs/archive/300081d0cc72df578b02d914df941b8ec62240e6.tar.gz") {};
in pkgs.mkShell {
  packages = [
    pkgs.poetry
    pkgs.python3
    ];
}
