"""
This script extracts all files from the FHIR packages, located in ./packages, filters for Profiles only and gathers the information for cardinality, mustSuport and ValueSet bindings. This information is 
presented in an HTML file (_cardinality.html, _ValueSet.html, _mustSupprt.html), which each contain a number of tables, one for each Profile. STU3 files will be converted to R4 before checking by posting 
the profile to a FHIR server using the $convertR4. Custom elements can be added via GitHub actions, each one seperated by a comma (,).
"""

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

directory = './packages'
extract_package_path = './extracted_packages/'

def extract_tar_gz(tar_gz_file, extract_path):
    try:
        with tarfile.open(tar_gz_file, 'r:gz') as tar:
            tar.extractall(path=extract_path)
        print("Extraction successful!")
    except Exception as e:
        print(f"Extraction failed: {e}")

def find_tgz_packages(directory):
    tgz_files = glob.glob(directory+'/*.tgz')
    return tgz_files
 
def open_json_file(path, warnings):
    ''' loads JSON File returns dict named contents '''
    try:
        with open(path, 'r',encoding="utf8") as j:
            jsonFile = json.loads(j.read())
    except Exception as e:
        print(f"{path} The code has an error that needs to be fixed before it can be checked:{str(e)}")       
        return {}, warnings
    return jsonFile, warnings

def check_if_profile(jsonFile):
    '''For each file check the element kind is present and not equal to extension. Will return empty for any retired assets'''
    try:
        if 'type' in jsonFile and jsonFile['type']!='Extension' and jsonFile['resourceType'] == 'StructureDefinition':
            print(jsonFile['url'],jsonFile['resourceType'])
            return jsonFile['type']
    except KeyError as e:
        print(jsonFile['url'],e)
        return None

def find_attributes_min_max(json_data, attribute_dict=None):
    if attribute_dict is None:
        attribute_dict = {}

    if isinstance(json_data, dict):
        if 'id' in json_data and ('min' in json_data or 'max' in json_data) and (not os.environ['IGNORE_EXTENSION'] or 'extension' not in json_data['id'].lower()):
            if 'min' in json_data:
                attribute_dict[json_data['id']] = str(json_data['min'])+'..'
            else:
                attribute_dict[json_data['id']] = ' ..'
            if 'max' in json_data:
                attribute_dict[json_data['id']] = attribute_dict[json_data['id']]+str(json_data['max'])
            else:
                attribute_dict[json_data['id']]+" "
        for key, value in json_data.items():\
            find_attributes_min_max(value, attribute_dict)
    elif isinstance(json_data, list):
        for item in json_data:
            find_attributes_min_max(item, attribute_dict)
    return attribute_dict

def find_attributes_valueSet(json_data, attribute_dict=None):
    if attribute_dict is None:
        attribute_dict = {}

    if isinstance(json_data, dict):
        if 'id' in json_data and ('binding' in json_data) and (not os.environ['IGNORE_EXTENSION'] or 'extension' not in json_data['id'].lower()):
            try:
                attribute_dict[json_data['id']] = f"{json_data['binding']['strength']}\n{json_data['binding']['valueSet']}"
            except:
                attribute_dict[json_data['id']] = f"{json_data['binding']['strength']}"
        for key, value in json_data.items():\
            find_attributes_valueSet(value, attribute_dict)
    elif isinstance(json_data, list):
        for item in json_data:
            find_attributes_valueSet(item, attribute_dict)
    return attribute_dict

def find_attributes_x(json_data, custom_key, attribute_dict=None):
    if attribute_dict is None:
        attribute_dict = {}

    if isinstance(json_data, dict):
        if 'id' in json_data and custom_key in json_data and (not os.environ['IGNORE_EXTENSION'] or 'extension' not in json_data['id'].lower()):
            attribute_dict[json_data['id']] = str(json_data[custom_key])
        for key, value in json_data.items():\
            find_attributes_x(value, custom_key, attribute_dict)
    elif isinstance(json_data, list):
        for item in json_data:
            find_attributes_x(item, custom_key, attribute_dict)
    return attribute_dict
    
def check_if_stu3(path,jsonFile):
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


''' Find and extract each FHIR package '''
tgz_packages = find_tgz_packages(directory)
print("Packages Extracted")
for tgz_package in tgz_packages:
    extract_path = extract_package_path+os.path.splitext(os.path.basename(tgz_package))[0]
    extract_tar_gz(tgz_package, extract_path)
    print(tgz_package)
    
'''create dictionaries for each of the elements to check. Each dict will look like: {Resource:[{Profile:{id:value,...}},...],...}'''
table_min_max = {}
table_valueSet = {}
custom_input_list = list(filter(None,('mustSupport,'+os.environ['INPUT_ELEMENT']).split(',')))
custom_input_dict = {}
for l in custom_input_list:
    custom_input_dict[l] = {}

''' filter for profiles only '''
for path in glob.glob(extract_package_path+'**/package/*.json', recursive=True):
    name = path.split('/')[-1].split('.')[0]
    warnings = []
    if 'examples' in name or name == "package":
        continue
    jsonFile, warnings = open_json_file(path, warnings)
    resource = check_if_profile(jsonFile)
    if resource != None:
        jsonFile = check_if_stu3(path,jsonFile)
        if os.environ['DIFF_ELEMENT']:
            #try:
            jsonFile = jsonFile['differential']
            print(jsonFile)
            #except:
                #print(f"No differential found in {name} - using snapshot")
        if resource not in table_min_max.keys():
            table_min_max[resource] = []
        attribute_dict_min_max = find_attributes_min_max(jsonFile)
        dic_min_max = {}
        dic_min_max[name]=attribute_dict_min_max
        table_min_max[resource].append(dic_min_max)
        
        if resource not in table_valueSet.keys():
            table_valueSet[resource] = []
        attribute_dict_valueSet = find_attributes_valueSet(jsonFile)
        dic_valueSet = {}
        dic_valueSet[name]=attribute_dict_valueSet
        table_valueSet[resource].append(dic_valueSet)

        for custom_key, custom_value in custom_input_dict.items():
            print(custom_key,custom_value)
            if resource not in custom_value:
                custom_value[resource] = []
            attribute_dict_x = find_attributes_x(jsonFile, custom_key)
            dic_x = {}
            dic_x[name]=attribute_dict_x
            custom_value[resource].append(dic_x)
        
    if warnings:
        print(os.path.splitext(os.path.basename(tgz_package))[0])
        for x in warnings:
            print(x)

table_min_max = dict(sorted(table_min_max.items()))
table_valueSet = dict(sorted(table_valueSet.items()))
for v in custom_input_dict.values():
    v = dict(sorted(v.items()))

def dict_to_dataframe(data_dict):
    dfs = {}
    for key, value in data_dict.items():
        if type(value) is list:
            list_of_dfs = []
            for profile in range(len(value)):
                list_of_dfs.append(pd.DataFrame.from_dict(value[profile], orient='index').T)
            try:
                dfs[key] = reduce(lambda  left,right: pd.merge(left,right, left_index=True, right_index=True, how='outer'), list_of_dfs).fillna('')
            except:
                print(f"{key}, {value}")
        else:
            dfs[key] = pd.DataFrame.from_dict(value[0], orient='index').T
    return dfs

''' Convert each dictionary into a DataFrame '''
min_max = dict_to_dataframe(table_min_max)
valueSet = dict_to_dataframe(table_valueSet)
custom_dataframe = {}
for k, v in custom_input_dict.items():
    custom_dataframe[k] = dict_to_dataframe(v)

if os.path.exists("index.html"):
    os.remove("index.html")
    
''' Create dataframes '''
dataframes = {'Cardinality':min_max,'ValueSet_binding':valueSet}
dataframes = dataframes | custom_dataframe

''' Create xlsx files '''
for title, title_df in dataframes.items():
    with pd.ExcelWriter('_'+title+'.xlsx') as writer:
        for k, v in title_df.items():
            try:
                v.to_excel(writer,sheet_name=k)
            except ValueError:
                print(f"invalid Excel sheet name: {v}")
                
''' Create html files '''
for key,value in dataframes.items():
    if os.path.exists(f"_{key}.html"):
        os.remove(f"_{key}.html")

    html_file = open(f"_{key}.html","w")

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
    html_file.write(f"<title>Table for the element: '{key}'</title><h1>Table for the element: '{key}'</h1>")
    for profile, df in value.items():
        html_file.write(f"<h2>{profile}</h2>\n")
        html_file.write(df.to_html(classes=["table-bordered", "table-striped", "table-hover"]).replace("\\n","<br>"))
    html_file.write("</body></html>")
    html_file.close()
