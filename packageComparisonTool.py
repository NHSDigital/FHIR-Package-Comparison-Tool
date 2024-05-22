import tarfile
import os
import requests
import glob
import json
import pandas as pd
import numpy as np
from functools import reduce
from IPython.display import HTML
import pathlib

def extract_tar_gz(tar_gz_file, extract_path):
    try:
        # Open the tar.gz file
        with tarfile.open(tar_gz_file, 'r:gz') as tar:
            # Extract all contents
            tar.extractall(path=extract_path)
        print("Extraction successful!")
    except Exception as e:
        print(f"Extraction failed: {e}")

directory = './packages'
extract_package_path = './extracted_packages/'

def find_tgz_packages(directory):
    tgz_files = glob.glob(directory+'/*.tgz')
    return tgz_files

tgz_packages = find_tgz_packages(directory)

# Extract each .tgz package
print("Packages Extracted")
for tgz_package in tgz_packages:
    extract_path = extract_package_path+os.path.splitext(os.path.basename(tgz_package))[0]
    extract_tar_gz(tgz_package, extract_path)
    print(tgz_package)
    
    ''' open each file '''
def openJSONFile(path, warnings):
    ''' loads JSON File returns dict named contents '''
    try:
        with open(path, 'r',encoding="utf8") as j:
            jsonFile = json.loads(j.read())
    except Exception as e:
        print(f"{path} The code has an error that needs to be fixed before it can be checked:{str(e)}")       
        return {}, warnings
    return jsonFile, warnings

'''For each file check the element kind is present and not equal to extension'''
def checkIfProfile(jsonFile):
    '''Will return empty for any retired assets'''
    try:
        if 'type' in jsonFile and jsonFile['type']!='Extension' and jsonFile['resourceType'] == 'StructureDefinition':
            print(jsonFile['url'],jsonFile['resourceType'])
            return jsonFile['type']
    except KeyError as e:
        print(jsonFile['url'],e)
        return None

'''Finds all values with key not equal to 0 (also add *??) '''
def find_attributes(json_data, Type, attribute, attribute_dict=None, parent_keys=""):
    if attribute == 'min':
        ignore = 0
    elif attribute == 'max':
        ignore = '*'
    else:
        ignore = ''
    if attribute_dict is None:
        attribute_dict = {}

    if isinstance(json_data, dict):
        element = ''
        for key, value in json_data.items():
            if key == 'id' and Type in value:
                element = value
            elif key == attribute and value !=ignore:
                attribute_path = f"{parent_keys}.{key}" if parent_keys else key
                attribute_dict[element] = str(value)
            elif isinstance(value, (dict, list)):
                if parent_keys:
                    find_attributes(value, Type, attribute, attribute_dict, f"{parent_keys}.{key}")
                else:
                    find_attributes(value, Type, attribute, attribute_dict, key)
    elif isinstance(json_data, list):
        for index, item in enumerate(json_data):
            if parent_keys:
                find_attributes(item, Type, attribute, attribute_dict, f"{parent_keys}[{index}]")
            else:
                find_attributes(item, Type, attribute, attribute_dict, f"[{index}]")

    return attribute_dict
    
def checkIfSTU3(path,jsonFile):
    url = 'https://3cdzg7kbj4.execute-api.eu-west-2.amazonaws.com/poc/Conformance/FHIR/STU3/$convertR4'

    headers = {
        'accept': 'application/fhir+json',
        'Content-Type': 'application/fhir+json'
    }

    if '3' in jsonFile['fhirVersion']:
        with open(path, 'rb') as stu3_data:
            stu3_file = stu3_data.read()
        response = requests.post(url, headers=headers, data=stu3_file)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"STU3-R4 Conversion Error: {response.status_code} - {response.reason}")
    return jsonFile

table = {}
attribute = os.environ['INPUT_ELEMENT']
for path in glob.glob(extract_package_path+'**/package/*.json', recursive=True):
    name = path.split('/')[-1].split('.')[0]
    warnings = []
    if 'examples' in name or name == "package":
        continue
    jsonFile, warnings = openJSONFile(path, warnings)
    Type = checkIfProfile(jsonFile)
    if Type != None:
        jsonFile = checkIfSTU3(path,jsonFile)
        if Type not in table.keys():
            table[Type] = []
        ''' add filename to dict '''
        attribute_dict = find_attributes(jsonFile, Type, attribute)
        dic = {}
        dic[name]=attribute_dict
        table[Type].append(dic) 
    if warnings:
        print(os.path.splitext(os.path.basename(tgz_package))[0])
        for x in warnings:
            print(x)

def dict_to_dataframe(data_dict):
    dfs = {}
    for key, value in data_dict.items():
        if type(value) is list:
            list_of_dfs = []
            for profile in range(len(value)):
                list_of_dfs.append(pd.DataFrame.from_dict(value[profile], orient='index').T)
            #dfs[key] = pd.concat(list_of_dfs).replace([np.nan, -np.inf], "")
            try:
                dfs[key] = reduce(lambda  left,right: pd.merge(left,right, left_index=True, right_index=True, how='outer'), list_of_dfs).fillna('')
            except:
                print(f"{key}, {value}")
        else:
            dfs[key] = pd.DataFrame.from_dict(value[0], orient='index').T
    return dfs

# Convert each dictionary into a DataFrame
dataframes = dict_to_dataframe(table)

if os.path.exists("index.html"):
    os.remove("index.html")
    
''' HTML FILE CREATION '''
html_file = open("index.html","w")

#HTML(dataframes.to_html(classes='table table-stripped'))
html_file.write('''
<html>
<head>
<style>

    h2 {
        text-align: center;
        font-family: Helvetica, Arial, sans-serif;
    }
    table { 
        margin-left: auto;
        margin-right: auto;
    }
    table, th, td {
        border: 1px solid black;
        border-collapse: collapse;
    }
    th, td {
        padding: 5px;
        text-align: center;
        font-family: Helvetica, Arial, sans-serif;
        font-size: 90%;
    }
    table tbody tr:hover {
        background-color: #dddddd;
    }
    .wide {
        width: 90%; 
    }

</style>
</head>
<body>
<h1></h1>
''')
html_file.write(f"<title>Table for the element: '{attribute}'</title><h1>Table for the element: '{attribute}'</h1>")
for key, df in dataframes.items():
    
    html_file.write(f"<h2>{key}</h2>\n")
    html_file.write(df.to_html(classes=["table-bordered", "table-striped", "table-hover"]))
html_file.write("</body></html>")
html_file.close()
