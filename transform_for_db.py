from datetime import datetime
from dateutil.parser import parse
import json

DEFAULT_VALUES = {
    'thumbnail': None,
    'permission': "Global",
    'mediaType': "article",
    'tags': "research",
    'type': "ki",
    'transcript': "",
    'createdBy': None,
    'updated': "",
    'isDeleted': False,
}

def main():
    with open("test.json", "r") as file:
        data = json.load(file)
    
    article = transform_sc_item(data)
    with open('ki_test.json', 'w', encoding='utf-8') as f:
        json.dump(article, f, ensure_ascii=False, indent=4)


def standard_date(pub_date):
    if pub_date:
        try:
            date = parse(pub_date)
            pub_date = date.strftime("%Y-%m-%d")
        except ValueError:
            return None
    
    return pub_date


def standard_duration(audio_length):
    if audio_length:
        try:
            time = datetime.strptime(audio_length, "%H:%M:%S")
        except ValueError:
            try:
                time = datetime.strptime(audio_length, "%M:%S")
            except ValueError:
                return None

        audio_length = time.strftime("%H:%M:%S")
    
    return audio_length
    

def timestamp_ms():
    utc_time = datetime.utcnow()
    return int(utc_time.timestamp() * 1000)


def transform_sc_item(article):
    coredata = article['coredata']    
    
    url = None
    for link in coredata.get("link", []):
        if link['@rel'] == "scidir":
            url = link['@href']


    try:
        db_item = {
            'title': coredata.get('dc:title'), 
            'thumbnail': DEFAULT_VALUES['thumbnail'], 
            'description': coredata.get('dc:description'), 
            'permission': DEFAULT_VALUES['permission'], 
            'authors': [creator["$"] for creator in coredata.get('dc:creator', [])],
            'mediaType': DEFAULT_VALUES['mediaType'], 
            'tags': DEFAULT_VALUES['tags'], 
            'type': DEFAULT_VALUES['type'], 
            'metadata': {
                'url': url,
                }, 
            'created': {
                '$date': {
                    '$numberLong': str(timestamp_ms())
                    }
                }, 
            'createdBy': DEFAULT_VALUES['createdBy'],
            'updated': DEFAULT_VALUES['updated'],
            'isDeleted': DEFAULT_VALUES['isDeleted'],
            'original': [article], 
            'publishedDate': standard_date(coredata.get('prism:coverDate'))
        }
    except KeyError as e:
        print(e)
        # Convert `episode` dict to JSON formatted string
        json_string = json.dumps(article, indent=4)
        # Write to JSON file
        with open('failed_article.json', 'w') as file:
            file.write(json_string)
        raise Exception("Key Error")

    return db_item


if __name__ == "__main__":
    main()