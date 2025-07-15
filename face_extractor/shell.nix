{ pkgs ? import <nixpkgs> {} }:

let
  python = pkgs.python311;
  python-with-packages = python.withPackages (ps: with ps; [
    pip
    setuptools
    wheel
    numpy
    face_recognition
    opencv-python
  ]);
in

pkgs.mkShell {
  name = "face-extractor-env";

  buildInputs = [
    python-with-packages

    # Systemberoenden
    pkgs.cmake
    pkgs.boost
    pkgs.boost.dev
    pkgs.libjpeg
    pkgs.zlib
    pkgs.xz
    pkgs.libpng
    pkgs.ffmpeg
    pkgs.pkg-config
    pkgs.openblas
    pkgs.opencv
  ];

  shellHook = ''
    echo "✅ Miljö redo. Kör: python face_extractor.py"
  '';
}
