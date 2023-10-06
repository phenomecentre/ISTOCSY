#!/bin/sh -ex

echo "=== Fetching ISTOCSY from Github ==="
git clone git@github.com:phenomecentre/ISTOCSY.git
cd ISTOCSY/
git checkout pyqt6
echo "=== Making Python3 environment ==="
python3 -m venv istocsy-env
source istocsy-env/bin/activate
echo "=== Upgrading pip ==="
python3 -m pip install --upgrade pip
echo "=== Installing ISTOCSY Python libraries ==="
pip install -r requirements.txt

echo "=== Launching app ==="
python pyIstocsy/runISTOCSY.py
#cd ..
#rm -rf ISTOCSY/
#deactivate

#conda create -n istocsy python=3.7.1 ipykernel # this creates istocsy environment
#onda activate istocsy # this activates the environment
#navigate to the folder which contains requirements.txt file and use cd to change directories, then run line 4
#pip install -r requirements.txt
#Once everything’s downloaded then navigate to the folder which contains runISTOCSY.py file and use cd to change directories, then run line 6
#python runISTOCSY.py # Runs ISTOCSY