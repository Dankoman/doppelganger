{ pkgs ? import <nixpkgs> {} }:
pkgs.mkShell {
  packages = with pkgs; [
    python311
    python311Packages.scrapy
    playwright-driver
    nodejs
    patchelf
    
    gtk3 pango cairo gdk-pixbuf glib fontconfig freetype dbus alsa-lib atk
    xorg.libX11 xorg.libXext xorg.libXrender xorg.libXrandr
    xorg.libXcomposite xorg.libXfixes xorg.libXdamage xorg.libXcursor
    xorg.libXi xorg.libxcb
    libdrm mesa nss nspr expat libxkbcommon
    swi-prolog
  ];

  shellHook = ''
    export PLAYWRIGHT_BROWSERS_PATH="$PWD/.pw-browsers"
    export PLAYWRIGHT_NODEJS_PATH="${pkgs.nodejs}/bin/node"
    export PLAYWRIGHT_SKIP_VALIDATE_HOST_REQUIREMENTS=1
    
    # Robust LD_LIBRARY_PATH for NixOS to run unpatched browser binaries
    export LD_LIBRARY_PATH="${pkgs.lib.makeLibraryPath [
      pkgs.stdenv.cc.cc
      pkgs.zlib
      pkgs.glib
      pkgs.dbus
      pkgs.atk
      pkgs.pango
      pkgs.gtk3
      pkgs.libdrm
      pkgs.mesa
      pkgs.alsa-lib
      pkgs.nss
      pkgs.nspr
      pkgs.expat
      pkgs.libxkbcommon
      pkgs.xorg.libX11
      pkgs.xorg.libXcomposite
      pkgs.xorg.libXdamage
      pkgs.xorg.libXext
      pkgs.xorg.libXfixes
      pkgs.xorg.libXrandr
      pkgs.xorg.libxcb
      pkgs.swi-prolog
    ]}:''${LD_LIBRARY_PATH:-}"

    # nix-ld support
    export NIX_LD="${pkgs.stdenv.cc.libc}/lib/ld-linux-x86-64.so.2"
    export NIX_LD_LIBRARY_PATH="$LD_LIBRARY_PATH"

    # Fallback: Patch camoufox-bin if needed
    CAMOUFOX_BIN="$HOME/.cache/camoufox/camoufox-bin"
    if [ -f "$CAMOUFOX_BIN" ]; then
        INTERP=$(cat ${pkgs.stdenv.cc}/nix-support/dynamic-linker)
        if [ "$(patchelf --print-interpreter $CAMOUFOX_BIN 2>/dev/null)" != "$INTERP" ]; then
            echo "🔧 Patching camoufox-bin for NixOS..."
            patchelf --set-interpreter "$INTERP" "$CAMOUFOX_BIN"
        fi
    fi

    if [ ! -d .venv ]; then python -m venv .venv; fi
    source .venv/bin/activate
  '';
}
