Policy Enable Guide:

This script is for Opentext Only.  It is designed for there Tenant and no one else.

PolicyEnable.py:
This script uses the config.ini file to pull the username, password, and API URL for prisma Cloud.  You need to have the config.ini filed out before using the PolicyEnable.py Script.

This script uses the Prisma Cloud API to pull All policies that are in the Opentext Standard for {CSP} Compliance Standard.  It will save a .json file for each respected Cloud Service Provider (CSP).  Then it will import the .json data into an excel document called policies.xlsx and make sheets for each respected CSP.  From there it will remove the .json files and then proceed to load the xlsx file and find all policies that are not enabled in Column I and send a payload to Prisma Cloud to enable those polices that are not enabled.

Requirements:
pip3 install:
    - requests
    - jsonlib
    - openpyxl
    - os-sys
    - configparser

This script is preferred to be run locally as you will only need to do it one time.

Run the Script:

python3 ./PolicyEnable.py