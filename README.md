[![Github Release](https://img.shields.io/github/release/KaSroka/Toshiba-AC-control.svg)](https://github.com/KaSroka/Toshiba-AC-control/releases)
[![Github Commit since](https://img.shields.io/github/commits-since/KaSroka/Toshiba-AC-control/latest?sort=semver)](https://github.com/KaSroka/Toshiba-AC-control/releases)
[![Github Open Issues](https://img.shields.io/github/issues/KaSroka/Toshiba-AC-control.svg)](https://github.com/KaSroka/Toshiba-AC-control/issues)
[![Github Open Pull Requests](https://img.shields.io/github/issues-pr/KaSroka/Toshiba-AC-control.svg)](https://github.com/KaSroka/Toshiba-AC-control/pulls)

# Toshiba AC control
This software allows to control Toshiba AC

## Installation
### Typical installation
Download using pip
`pip3 install toshiba-ac`
### Installation for development
1. Download or clone this repository to desired directory:

    `git clone https://github.com/KaSroka/Toshiba-AC-control.git`
2. Install toshiba-ac package:

    `pip3 install .`

    If you want to edit the code you can install the package as editable:

    `pip3 install -e .`

## Sample script
Sample GUI application `toshiba_ac_gui.py` was created to demonstrate usage of this package. It allows to switch basic functionalities of the AC and shows current status.

It requires to provide env variables with login information:
```
TOSHIBA_USER=<USER_NAME> TOSHIBA_PASS=<PASSWORD> python3 toshiba_ac_gui.py
```
or
```
export TOSHIBA_USER=<USER_NAME>
export TOSHIBA_PASS=<PASSWORD>
python3 toshiba_ac_gui.py
```
