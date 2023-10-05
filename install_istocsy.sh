#!/bin/sh -ex

git clone git@github.com:phenomecentre/ISTOCSY.git
cd ISTOCSY/
git checkout pyqt6

python3 -m venv istocsy-env
source istocsy-env/bin/activate
python3 -m pip install --upgrade pip
pip install -r requirements.txt
