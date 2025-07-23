{ pkgs ? import <nixpkgs> {} }:

let
  py = pkgs.python311;
  pyPkgs = py.withPackages (ps: with ps; [
    pip setuptools wheel
    numpy scipy scikit-learn tqdm pillow
  ]);
in
pkgs.mkShell {
  name = "arcface-env";

  buildInputs = [
    pyPkgs
    pkgs.cmake pkgs.pkg-config pkgs.gcc pkgs.gfortran pkgs.openblas
    pkgs.boost pkgs.eigen
    pkgs.curl pkgs.openssl pkgs.git
  ];

  shellHook = ''
    echo "✅ Nix-miljö laddad."

    if [ ! -d .venv ]; then
      python3 -m venv .venv
    fi
    source .venv/bin/activate

    pip install --upgrade pip
    pip install --no-cache-dir onnxruntime insightface opencv-python-headless==4.12.0.88

    echo "✅ Virtuell miljö aktiv. Kör: python face_arc_pipeline.py --mode both"
  '';
}
