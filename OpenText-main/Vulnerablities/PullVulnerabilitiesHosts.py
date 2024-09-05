import requests
import json
import datetime
import os.path
import time
import csv
import configparser

def generate_Configuration():
    config_obj = configparser.ConfigParser()
    config_obj.read("configfile.ini")
    prismacloud = config_obj["prismacloud"]
    username = prismacloud["access_key"]
    password = prismacloud["secret_key"]

    return username,password

def auth():
    config_obj = configparser.ConfigParser()
    config_obj.read("configfile.ini")
    prismacloud = config_obj["prismacloud"]
    url = prismacloud["url"]+"/login"
    accesskey = prismacloud["access_key"]
    secretkey = prismacloud["secret_key"]
    
    payload = {
        "password": secretkey,
        "username": accesskey
    }
    headers = {
        "content-type": "application/json; charset=UTF-8"
    }
    response = requests.request("POST", url, json=payload, headers=headers)
    response_json = response.json()
    token = response_json.get('token')
    return token

def get_vul_Hosts(token,offset):
    print("Obtaining Host Vulnerabilities")
    config_obj = configparser.ConfigParser()
    config_obj.read("configfile.ini")
    prismacloud = config_obj["prismacloud"]
    url = prismacloud["twistlock_url"]+"/api/v1/hosts/download?offset="+str(offset)
    payload = {}
    headers = {
       "accept": "application/json, */*",
        "x-redlock-auth": token,
    }
    response = requests.request("GET", url, headers=headers, data=payload)

    if response.status_code == 200:
        image_data = response.content
        with open("hosts"+str(offset)+".csv", "wb") as f:
            f.write(image_data)
            print("Host downloaded successfully to hosts.csv")
        f.close
    else:
        print(f"Error downloading host: {response.status_code}")
        raise TypeError(f"Error downloading host: {response.status_code}")

def appendedOffsets(token,currentOffset,mapping_images,used):
    done=False
    position=currentOffset
    for offset in range(currentOffset,currentOffset+2):
        print("Pulling offsetData: " + str(offset))
        mapping_images_temp,usedTemp = getHostsData(token,offset,mapping_images,used)
        # if offset returns no data then exit loop
        if mapping_images_temp == None: 
            print("The offset: " + str(offset) + " contains no data. Exiting host pull")
            done=True
            break
        else:
            mapping_images=mapping_images_temp
            used=usedTemp
            position+=1
    return mapping_images,used,position,done

def get_accounts_by_collections_filtered(token,collectionSelected): 
    mapping_collections = {}
    dataCollections=get_collections(token)
    for singleCollection in dataCollections:
        collectionName=singleCollection["name"]
        #Non-onboarded cloud accounts has no accounts and produces an error if let alone
        if collectionName!="Non-onboarded cloud accounts"and collectionName in  collectionSelected:
            if collectionName in mapping_collections:
                accounts=singleCollection["accountIDs"]
                for account in accounts:
                    if account not in mapping_collections[collectionName]:
                        mapping_collections[collectionName].append(account)
            else:
                mapping_collections[collectionName]=[]
                accounts=singleCollection["accountIDs"]
                for account in accounts:
                    mapping_collections[collectionName].append(account)
    mapping_collections=doAccountsMappingALLCorrection(token,mapping_collections)
    return mapping_collections

def getFile (data, filename):
    file_name = filename + '.csv'
    
    with open(file_name,'wb') as csvFile:
        csvFile.write(data.content)

        csvFile.close()
    return file_name

def doAccountsMappingALLCorrection(token,mapping_collections):
    print("Getting discovery")
    allAccounts=[]
    data = get_discovery(token)   
    CloudFileName=getFile(data,'CloudDiscovery_')
    with open(CloudFileName,encoding="utf-8") as file_obj: 
        reader_obj = csv.reader(file_obj) 
        for row in reader_obj: 
           account=row[7]
           if account not in allAccounts and account!="Account ID":
                allAccounts.append(account)    
    file_obj.close()
    for collectionName, accounts in mapping_collections.items():
        if accounts[0]=="*":
            mapping_collections[collectionName]=allAccounts
    return mapping_collections

def getHostsData(token,offset,mapping_images,used):
    #Download the file for the current offset
    get_vul_Hosts(token,offset) 
    noData=False
    #Process the downloaded data and save the images mapped with the CVE's info, 
    #the used CVE's per host so it doesnt repeat itself, and check if there is 
    #no more data to iterate over
    mapping_images,used,noData=processDownloadHosts(offset,mapping_images,used)

    if noData:  
        return None, None
    return mapping_images,used

def runSet(offset,mapping_images,used,username, password):
    token = auth()
    done=False
    failed=False
    while not done and not failed:
        try:
            newMappingImages, newUsed,currentOffset,done=appendedOffsets(token, offset,mapping_images,used)
            mapping_images=newMappingImages
            used=newUsed
            offset=currentOffset
            print("executing:")
            print(not done)
        except TypeError:
             print("error at runSet")    
             writeNewCSV(mapping_images)
             failed=True 
    print("sale")  
    return done, mapping_images,used,offset

def get_collections(token):
    config_obj = configparser.ConfigParser()
    config_obj.read("configfile.ini")
    prismacloud = config_obj["prismacloud"]
    url = prismacloud["twistlock_url"]+"/api/v1/collections"
    headers = {
        'Accept': 'application/json; charset=UTF-8',
        'x-redlock-auth': token
    }
    response = requests.request("GET", url, headers=headers)
    getFile(response,'Collections')
    data = response.json()
    
    return data


def main(): 
    username,password=generate_Configuration()
    offset=0
    mapping_images = {}
    used = {}
    done=False
    while not done:
        done, new_mapping_images,newUsed,offset=runSet(offset,mapping_images,used,username, password)
        mapping_images=new_mapping_images
        used=newUsed
        print("Saving processed information")
        writeNewCSV(mapping_images)
        print("script entering sleep mode for 10 seconds")
        time.sleep(10) 

def processDownloadHosts(offset, mapping_images,used):
    
    print("Processing offsetData: "+str(offset))
    count=0
    noData=False
    if noData == False:
        #Opening file just created
        with open("hosts"+str(offset)+".csv",encoding="utf-8") as file_obj: 
            reader_obj = csv.reader(file_obj) 
            for row in reader_obj: 
                #Check If there is not data, in that case stop the process and return noData=True
                if row[0]=="no data":
                    noData=True
                    file_obj.close()
                    break
                #Taking the individual data that is needed 
                id=row[0]
                distro=row[1]
                CVE=row[2]
                compliance=row[3]
                typeH=row[4]
                severity=row[5]
                packageH=row[6]
                sourcePackage=row[7]
                packageV=row[8]
                packageLicense=row[9]
                packagePath=row[10]
                CVSS=row[11]
                status=row[12]
                vulnTags=row[13]
                description=row[14]
                cause=row[15]
                Published=row[16]
                services=row[17]
                cluster=row[18]
                vulnLink=row[19]
                agentless=row[20]
                provider=row[21]
                accountId=row[22]
                region=row[23]
                resourceId=row[24]
                Discovered=row[25]
                #Collections=row[30]
                #Only work the data if its not the row with the column names and if it has a discovery date
                if Discovered!="" and Discovered!="Discovered":
                    cveData=[distro,CVE, compliance,typeH,severity,packageH,sourcePackage,packageV,packageLicense,packagePath,CVSS,status,vulnTags,description,cause,Published,services,cluster,vulnLink,agentless,provider,accountId,region,resourceId,Discovered]
                    #Check if the id of the host already is in use, if it is continue as normal
                    #if it is not, add it and initialice it to avoid error
                    if id in used:
                        #Check if the CVE was already mapped to the id if not, map it
                        if cveData[1] not in used[id]:
                            used[id].append(cveData[1])
                            mapping_images[id].append(cveData)
                            count+=1
                    else:
                        mapping_images[id]=[]
                        mapping_images[id].append(cveData)
                        used[id]=[cveData[1]]
                        count+=1
                                
                                
                                    
        file_obj.close()
    print("There are "+str(count)+" new found vulns")
    return mapping_images,used,noData
   
def writeNewCSV(mapping_images):
    with open('vulnerabilities_Hosts.csv','w+',newline='') as csvFile:                          
        fieldnames = ["HostName","Distro","CVE-ID","Compliance","Type","Severity","Packages","Source Package","Package version","Package license","Package path","CVSS","Fix Status","Vulnerability Tags","Description","Cause","Published","Services","Cluster","Vulnerability Link","Agentless","Provider","Account ID","Region", "Resource ID", "Discovered"]
        writer = csv.DictWriter(csvFile, fieldnames=fieldnames)
        writer.writeheader()
        for id, cveData in mapping_images.items():
            for case in cveData:
                if type(case)!=type(list()):
                    print(type(case))
                if type(case)==type(list()):         
                    distro=case[0]
                    CVE=case[1]
                    compliance=case[2]
                    typeH=case[3]
                    severity=case[4]
                    packageH=case[5]
                    sourcePackage=case[6]
                    packageV=case[7]
                    packageLicense=case[8]
                    packagePath=case[9]
                    CVSS=case[10]
                    status=case[11]
                    vulnTags=case[12]
                    description=case[13]
                    cause=case[14]
                    Published=case[15]
                    services=case[16]
                    cluster=case[17]
                    vulnLink=case[18]
                    agentless=case[19]
                    provider=case[20]
                    accountId=case[21]
                    region=case[22]
                    resourceId=case[23]
                    Discovered=case[24]
                    writer.writerow({'HostName':id,'Distro':distro,'CVE-ID':CVE,'Compliance':compliance,'Type':typeH,'Severity':severity,'Packages':packageH,'Source Package':sourcePackage,'Package version':packageV,'Package license':packageLicense,'Package path':packagePath,'CVSS':CVSS,'Fix Status':status,'Vulnerability Tags':vulnTags,'Description':description,'Cause':cause,'Published':Published,'Services':services,'Cluster':cluster,'Vulnerability Link':vulnLink,'Agentless':agentless,'Provider':provider,'Account ID':accountId,'Region':region, 'Resource ID':resourceId, 'Discovered':Discovered})
    csvFile.close()
   
def get_discovery(token):
    config_obj = configparser.ConfigParser()
    config_obj.read("configfile.ini")
    prismacloud = config_obj["prismacloud"]
    url = prismacloud["twistlock_url"]+"/api/v1/cloud/discovery/download"
    headers = {
        "accept": "application/json, text/plain, */*",
        'x-redlock-auth': token
    }
    response = requests.request("GET", url, headers=headers)
    #data = response.json()
    
    return response
if __name__ == "__main__":
    main()
