{ pkgs ? import <nixpkgs> {} }:

let
  py = pkgs.python311;
  pyPkgs = py.withPackages (ps: with ps; [
    pip setuptools wheel
    numpy
    scipy              # behövs av scikit-learn
    scikit-learn
    tqdm
    # valfritt: joblib threadpoolctl (dras normalt in av sklearn)
  ]);
in
pkgs.mkShell {
  name = "face-extractor-env";

  buildInputs = [
    pyPkgs

    # Byggberoenden för dlib/opencv
    pkgs.cmake
    pkgs.pkg-config
    pkgs.gcc
    pkgs.gfortran          # SciPy/BLAS
    pkgs.openblas          # BLAS/LAPACK
    pkgs.boost
    pkgs.eigen
    pkgs.dlib              # slippa kompilera via pip (om du vill)

    # Bild-/video-codecs och headers som cv2/Pillow kan behöva
    pkgs.libjpeg
    pkgs.libtiff
    pkgs.libpng
    pkgs.libwebp
    pkgs.zlib
    pkgs.bzip2
    pkgs.xz

    # OpenCV + X/GL beroenden
    pkgs.opencv
    pkgs.libglvnd
    pkgs.mesa
    pkgs.xorg.libX11
    pkgs.xorg.libXext
    pkgs.xorg.libXrender
    pkgs.xorg.libxcb
    pkgs.xorg.libXau
    pkgs.fontconfig
    pkgs.freetype

    # För pip/HTTPS
    pkgs.curl
    pkgs.openssl
    pkgs.git
  ];

  shellHook = ''
    echo "✅ Nix-miljö laddad."

    # Skapa/aktivera venv för pip-paket som saknas i nixpkgs
    if [ ! -d .venv ]; then
      python3 -m venv .venv
    fi
    source .venv/bin/activate

    # Uppgradera pip & installera bara det som inte redan finns i nix
    pip install --upgrade pip

    # face_recognition + ev. opencv-python om du föredrar pip-versionen
    pip install --no-cache-dir face_recognition

    # (Valfritt) om du INTE vill använda pkgs.opencv:
    # pip install opencv-python

    echo "✅ Virtuell miljö aktiv. Kör ditt skript."
  '';
}
