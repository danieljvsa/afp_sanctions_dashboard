from database.notion import get_results, create_page
import streamlit as st
import json
import uuid
import time

CLUBS_DATABASE = st.secrets['clubs_database_id']
CLUBS_ALIAS_DATABASE = st.secrets['clubs_alias_database_id']

def get_clubs_contacts(): 
    results = get_results(CLUBS_DATABASE)

    if results["success"] == False: 
        return {"response": [], "success": False}

    rows = results["result"]

    clubs = []
    for row in rows:
        row_id = row['id']
        city = row["properties"]['City']["rich_text"][0]['text']['content']
        name = row["properties"]['Name']["rich_text"][0]['text']['content']
        url = row["properties"]['Website Url']["rich_text"][0]['text']['content']
        img_url = row["properties"]['Image Url']["rich_text"][0]['text']['content']
        alias_id = row["properties"]['Alias']['relation'][0]['id'] if len(row["properties"]['Alias']['relation']) > 0 else ""
        club_id = row["properties"]['ClubId']["title"][0]['text']['content']
        clubs.append({"row_id": row_id, "name": name, "city": city, "url": url, "img_url": img_url, "alias_id": alias_id, "club_id": club_id})

    return {"response": clubs, "success": True}

def get_clubs_alias(): 
    results = get_results(CLUBS_ALIAS_DATABASE)

    if results["success"] == False: 
        return {"response": [], "success": False}

    rows = results["result"]

    clubs = []
    for row in rows:
        alias_id = row['id']
        club = row["properties"]['Club']["title"][0]['text']['content']
        clubs.append({"alias_id": alias_id, "club": club})
        # print({"alias_id": alias_id, "club": club})

    return {"response": clubs, "success": True}

def get_clubs_info():
    club_ref = {}
    clubs_contacts = get_clubs_contacts()
    clubs_alias = get_clubs_alias()

    if clubs_alias['success']:
        for club in clubs_alias['response']:
            club_ref[club['alias_id']] = club['club']
    else:
        return {"response": [], "success": False}

    if clubs_contacts['success']:
        for club in clubs_contacts['response']:
            if 'alias_id' in club and club['alias_id'] != None and club['alias_id'] != "": 
                club['alias'] = club_ref[club['alias_id']]
            else:
                club["alias"] = ""
                club["alias_id"] = ""

    else:
        return {"response": [], "success": False}

    return {"response": clubs_contacts["response"], "success": True}

# get_clubs_contacts()
# get_clubs_alias()
