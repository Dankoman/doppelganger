{ pkgs ? import <nixpkgs> {} }:

pkgs.mkShell {
  buildInputs = with pkgs; [
    python311
    python311Packages.rich
    stdenv.cc.cc.lib
    zlib
    swi-prolog
    nodejs
  ];

  shellHook = ''
    export LD_LIBRARY_PATH="${pkgs.lib.makeLibraryPath [
      pkgs.stdenv.cc.cc
      pkgs.zlib
      pkgs.swi-prolog
      pkgs.gtk3
      pkgs.glib
      pkgs.dbus
      pkgs.atk
      pkgs.pango
      pkgs.alsa-lib
      pkgs.nss
      pkgs.xorg.libX11
      pkgs.xorg.libXcomposite
      pkgs.xorg.libXdamage
      pkgs.xorg.libXrandr
      pkgs.xorg.libxcb
    ]}:''${LD_LIBRARY_PATH:-}"
    
    # nix-ld support for Playwright/Node and Camoufox/Firefox
    export NIX_LD="${pkgs.stdenv.cc.libc}/lib/ld-linux-x86-64.so.2"
    export NIX_LD_LIBRARY_PATH="$LD_LIBRARY_PATH"

    # Tell Playwright to use the system nodejs
    export PLAYWRIGHT_NODEJS_PATH="${pkgs.nodejs}/bin/node"

    # Aktivera virtual environment automatiskt om den finns
    if [ -d .venv ]; then
      source .venv/bin/activate
    fi
  '';
}
