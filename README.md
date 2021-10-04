# adblock-hosts-zip

## 1. Description
Will create flashable TWRP .zip file containing adblock hosts file. Its termux compatible able to run directly on phone.

## 2. Requirements
   ```
   pip install request
   ```

## 3. Running in termux
Install [Termux](https://termux.com/) from F-Droid

In termux:
```
termus-setup-storage
pgk install python
pip install request
python path/to/build-hosts.zip.py
```