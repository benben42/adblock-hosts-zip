# adblock-hosts-zip

## 1. Description
Will create flashable TWRP .zip file containing adblock hosts file. Its termux compatible able to run directly on phone.
Gathering hosts is based on [adBlock Hosts File Generator](https://github.com/bornova/adblock-hosts) by [Bornova](https://github.com/bornova)

## 2. Running in termux
Install [Termux](https://termux.com/) from F-Droid

In termux:
```
termus-setup-storage
pgk install python
download all the files & adjust them as needed
python path/to/android-adblock-hosts.py
```