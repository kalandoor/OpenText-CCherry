This Document is to explain how to use the CVEfinder.py script.

Requirements:
    1) Python 3.9
    2) pip3 install --no-cache-dir requests jsonlib-python3 openpyxl configparser
    3) Make sure to have the config.ini file in the same folder as the python script.

Config.ini Setup:
    1) username is the access_key_id from your Access Key in Prisma Cloud
    2) password is the secret_key from your Access Key in Prisma Cloud
    3) api_url is the Api end point for your tenant.
    4) console_url is the Runtime Security Console API Endpoint found in System > Utilities > Path to Console

When you run the python script it will prompt you to put in a CVE ID.  This ID should start with CVE-***-*****.
Put in a Valid CVE ID and the script will pull all the impacted resources for that CVE from Runtime Security.
Next it will pull the Image IDs from the impacted Resources and get the Image Data.
Finally we parse through the Image Data to get the required info need to put into the Excel File.

Note: When pulling the Image data the script will possilbe make a lot of image_data{i}.json files.  This is part of the process for CVE that have a huge impact and are found on many images.  This is so we dont go over the max URL length when getting the image data.

At the end of the script the script will remove the files that it saved when pulling data.  If you which to keep the data then please comment out lin 202-210 in the script.