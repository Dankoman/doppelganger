{ pkgs ? import <nixpkgs> {} }:
pkgs.mkShell {
  packages = with pkgs; [
    python311
    python311Packages.scrapy

    gtk3 pango cairo gdk-pixbuf glib fontconfig freetype dbus alsa-lib atk
    xorg.libX11 xorg.libXext xorg.libXrender xorg.libXrandr
    xorg.libXcomposite xorg.libXfixes xorg.libXdamage xorg.libXcursor
    xorg.libXi xorg.libxcb
  ];

  shellHook = ''
    export PLAYWRIGHT_BROWSERS_PATH="$PWD/.pw-browsers"
    export PLAYWRIGHT_SKIP_VALIDATE_HOST_REQUIREMENTS=1

    if [ ! -d .venv ]; then python -m venv .venv; fi
    source .venv/bin/activate
  '';
}
