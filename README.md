# AutoFunkt

```
       d8888          888            8888888888                888      888          
      d88888          888            888                       888      888          
     d88P888          888            888                       888      888          
    d88P 888 888  888 888888 .d  b.  8888888 888  888 88888b.  888  888 888888       
   d88P  888 888  888 888   d88  88b 888     888  888 888 "88b 888 .88P 888          
  d88P   888 888  888 888            888     888  888 888  888 888888K  888          
 d8888888888 Y88b 888 Y88b. Y88  88P 888     Y88b 888 888  888 888 "88b Y88b.        
d88P     888  "Y88888  "Y888 "Y  P"  888      "Y88888 888  888 888  888  "Y888   

    			malleable c2 => serverless cloud functions
```

## Acknowledgements

- Thank you to [Brett Fitzpatrick](https://twitter.com/_brettfitz) for the excellent [pyMalleableProfileParser](https://github.com/brett-fitz/pyMalleableProfileParser) library. 
- Many thanks to my colleagues @ [FortyNorthSecurity](https://github.com/FortyNorthSecurity), especially [Chris Truncer](https://github.com/ChrisTruncer), [Joe Leon](https://github.com/joeleonjr), and [Grimm1e](https://github.com/Gr1mmie)

## Prerequisites

- Python 3.9 or higher
- Google Cloud Functions CLI
- Azure Functions Core Tools
- 

## Usage

1. Clone the repo: `git clone https://github.com/calebstewart/malleable2func.git`
2. Navigate to the `malleable2func` directory.
3. Install requirements: `pip3 install -r requirements.txt`
4. Generate Google Cloud Functions: `python3 malleable2func.py -p /path/to/profile -t https://teamserver.url -o /path/to/output/directory -g`
5. Generate Azure Functions: `python3 malleable2func.py -p /path/to/profile -t https://teamserver.url -o /path/to/output/directory -a -s <azure-subdomain> -r <route-prefix>`

## Command Line Arguments

- `-p, --profile_path`: Path to Malleable C2 profile (required)
- `-t, --teamserver_url`: Teamserver URL (required)
- `-o, --output-dir`: Output directory (required)
- `-g, --google`: Generate Google Cloud Functions (optional, default: False)
- `-a, --azure`: Generate Azure Functions (optional, default: False)
- `-s, --azure-subdomain`: Azure subdomain (required for Azure)
- `-r, --route-prefix`: Azure custom route prefix (optional, default: None)

### Notes

- The `teamserver_url` must end with a `/` (slash).
- The `uri` value in the `http-get` and `http-post` blocks of the Malleable C2 profile must contain only one URI string.
- For Google Cloud Functions, the program creates a directory for each URI value and generates a `main.py` and `requirements.txt` file in each directory.
- For Azure Functions, the program creates an `azure` directory and generates a `main.py`, `host.json`, `proxies.json`, and `requirements.txt` file in it.

