@echo off
REM First download and unzip ISTOCSY code from Git:

REM https://github.com/phenomecentre/ISTOCSY/archive/refs/heads/pyqt6.zip
REM then in a PowerShell terminal window, cd to the unzipped directory and run this batch file.

echo "=== Making Python3 environment ==="
python3 "-m" "venv" "istocsy-env"
call istocsy-env\Scripts\activate.bat

echo "=== Installing ISTOCSY Python libraries ==="
pip "install" "-r" "requirements.txt"
echo "=== Launching app ==="
python "pyIstocsy\runISTOCSY.py"

REM using Conda:
REM conda create -n istocsy python=3.7.1 ipykernel # this creates istocsy environment
REM conda activate istocsy # this activates the environment
REM navigate to the folder which contains requirements.txt file and use cd to change directories, then run line 4
REM pip install -r requirements.txt
REM Once everything’s downloaded then navigate to the folder which contains runISTOCSY.py file and use cd to change directories, then run line 6
REM python runISTOCSY.py # Runs ISTOCSY