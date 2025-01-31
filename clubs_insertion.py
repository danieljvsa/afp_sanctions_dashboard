from database.notion import get_results, create_page
from config import parser_config
import json
import uuid
import time

CLUBS_DATABASE = parser_config('clubs_database_id')

def get_clubs(): 
    results = get_results(CLUBS_DATABASE)

    rows = results["result"]["results"]

    clubs = []
    for row in rows:
        row_id = row['id']
        city = row["properties"]['City']["rich_text"][0]['text']['content']
        name = row["properties"]['Name']["rich_text"][0]['text']['content']
        url = row["properties"]['Website Url']["rich_text"][0]['text']['content']
        img_url = row["properties"]['Image Url']["rich_text"][0]['text']['content']
        alias = row["properties"]['Alias']["rich_text"][0]['text']['content']
        club_id = row["properties"]['ClubId']["title"][0]['text']['content']
        clubs.append({"row_id": row_id, "name": name, "city": city, "url": url, "img_url": img_url, "alias": alias, "club_id": club_id})

    with open('clubs_db.json', 'w', encoding='utf8') as f:
        json.dump(clubs, f, ensure_ascii=False, indent=4)

def create_clubs():

    with open('clubs_raw.json', 'r') as file:
        clubs_rows = json.load(file)

    for club in clubs_rows:
        generated_uuid = uuid.uuid4().hex
        #print(club)

        data = {
            "ClubId": {"title": [{"text": {"content": generated_uuid}}]},
            "Name": {"rich_text": [{"text": {"content": club['name']}}]},
            "Website Url": {"rich_text": [{"text": {"content": club['url']}}]},
            "City": {"rich_text": [{"text": {"content": club['city']}}]},
            "Image Url": {"rich_text": [{"text": {"content": club['img_url']}}]},
            "Alias": {"rich_text": [{"text": {"content": ""}}]},
        }
        #print(data)
        response = create_page(data, CLUBS_DATABASE)
        print(club["name"] + "..." + str(response['statusCode']))
        if response['success'] == False:
            print("Error...")
            #print(response)
            break
        time.sleep(1)

#create_clubs()
get_clubs()