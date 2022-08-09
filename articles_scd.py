import json
import os
import re
import requests
from sys import argv, exit
from pathlib import Path
from dotenv import load_dotenv, find_dotenv

from transform_for_db import transform_sc_item

# Get API key from .env
load_dotenv(find_dotenv())
API_KEY = os.getenv('API_KEY')

def main():
    # Get file containing list of links
    filename = argv[1] if len(argv) == 2 else "links.txt"

    # Extract PIIs from links
    try:
        id_list =  extract_pub_ids(filename)
    except Exception as e:
        print(e)
        exit(1)

    # Initialize variables
    failed = {}
    articles = []
    num_ids = len(id_list)

    # Loop though every publication ID in list
    for n, id in enumerate(id_list):
        
        # Construct request URL
        url = f"https://api.elsevier.com/content/article/pii/{id}?apiKey={API_KEY}&httpAccept=application%2Fjson"
        # Get response
        try:
            print(f"Getting article {n + 1} of {num_ids}")
            response = requests.get(url)
            response.raise_for_status()
        # Handle errors
        except requests.RequestException as e:
            match response.status_code:
                case 400:
                    # If invalid PII, log & move to next podcast
                    print(f"Invalid PII/publication ID {id}")
                    failed[id] = f"Invalid PII/publication ID"                
                    continue
                case 404:
                    # If resource not founf, log & move to next podcast
                    print(f"Resource not found for {id}")
                    failed[id] = f"Resource not found"                
                    continue
                case _:
                    # For all else, especially authorization error/Quota exceeded
                    print(f"Unable to fetch article {id}: {e}")
                    failed[id] = f"Unable to fetch: {e}"
                    exit(1)
        # Get JSON response
        data = response.json()
        # Check key
        if 'full-text-retrieval-response' not in data:
            print(f"Unable to parse article {id}")
            failed[id] = f"Unable to parse article {id}"
            continue
        data_dict = data['full-text-retrieval-response']

        # Transform into desired format
        try:
            article = transform_sc_item(data_dict)
        except Exception as e:
            print(f"Failed to transform data for {id}. See failed_article.json")
            failed[id] = f"Failed to transform data"
        else:
            articles.append(article)

    # Create json file for transformed episodes in folder `ki_json`
    create_json_file(
        folder="ki_json", name="articles", source_dict=articles, failed=failed
    )

    # Create json file for errors if any
    if len(failed) > 0:
        create_json_file(
            folder="", name="failed", source_dict=failed, failed=failed
        )


def extract_pub_ids(filename):
    id_list = []
    
    # Make path
    try:
        filepath = os.path.join(filename)
    except Exception as e:
        raise Exception(e)

    # Check path exists
    if not os.path.exists(filepath):
        raise Exception(f"Could not find file {filepath}")

    # Open file and get list of lines
    with open(filepath, 'r') as f:
        lines = [line.strip() for line in f.readlines()]
    
    # Extract all PII in urls
    for line in lines:
        fragments = line.split('pii/')
        if len(fragments) == 2:
            id_list.append(fragments[1])

    return id_list


def create_json_file(folder, name, source_dict, failed):
    """ 
    Create json file from dict and save to given folder and filename 
    and log errors in dict `failed`
    """
    
    # Convert `data_dict` to JSON formatted string
    json_string = json.dumps(source_dict, indent=4)
    try:
        # Create valid file name
        filename = f"{get_valid_filename(name)}.json"
        # Create folder if does not already exist
        Path(folder).mkdir(parents=True, exist_ok=True)
        # Join folder and filename
        filepath = os.path.join(folder, filename)
    except Exception as e:
        print(e)
        failed[name] = "Could not create valid file name or folder"
        return
    # Write to JSON file
    with open(filepath, 'w') as file:
            file.write(json_string)


def get_valid_filename(name):
    """
    modified from: https://github.com/django/django/blob/main/django/utils/text.py

    Return the given string converted to a string that can be used for a clean
    filename. Remove leading and trailing spaces; convert other spaces to
    underscores; and remove anything that is not an alphanumeric, dash,
    underscore, or dot.
    >>> get_valid_filename("john's portrait in 2004.jpg")
    'johns_portrait_in_2004.jpg'
    """
    s = str(name).strip().replace(" ", "_")
    s = re.sub(r"(?u)[^-\w.]", "", s)
    if s in {"", ".", ".."}:
        raise Exception("Could not derive file name from '%s'" % name)
    return s


if __name__ == "__main__":
    main()