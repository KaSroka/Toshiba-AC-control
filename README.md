# Toshiba AC control
This software allows to control Toshiba AC

## Instalation
1. Download or clone this repository to desired directory:

    `git clone https://github.com/KaSroka/Toshiba-AC-control.git`
2. Install toshiba-ac package:

    `pip3 install .`

    If you want to edit the code you can install package as editable:

    `pip3 install -e .`

## Sample script
Sample script was created to demonstrate usage of this package. It allows to turn on/off the AC and shows reported status updates.

It requires to provide env variables with AC information:

```
export TOSHIBA_DEVICE_ID=<DEVICE_ID>
export TOSHIBA_AC_ID=<AC_ID>
export TOSHIBA_SHARED_ACCESS_KEY=<SHARED_ACCESS_TOKEN>
```

where

- `DEVICE_ID` is string in format: `<USER_NAME>_<16_HEXADECIMAL_CHARACTERS>` i.e., `user_0011223344556677`

- `AC_ID` is string in format: `<8_HEXADECIMAL_CHARACTERS>-<4_HEXADECIMAL_CHARACTERS>-<4_HEXADECIMAL_CHARACTERS>-<4_HEXADECIMAL_CHARACTERS>-<12_HEXADECIMAL_CHARACTERS>` i.e., `00112233-4455-6677-8899-aabbccddeeff`

- `SHARED_ACCESS_TOKEN` is string in base64 format i.e., `dGVzdA==`

Please read this [Home Assistant forum thread](https://community.home-assistant.io/t/toshiba-home-ac-control/137698) for explanation how to obtain them.


 