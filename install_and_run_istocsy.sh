#!/bin/sh -e

echo "=== Making Python3 environment ==="
python3 -m venv istocsy-env
source istocsy-env/bin/activate
echo "=== Upgrading pip ==="
python3 -m pip install --upgrade pip
echo "=== Installing ISTOCSY Python libraries ==="
pip install -r requirements.txt

echo "=== Launching app ==="
python pyIstocsy/runISTOCSY.py


