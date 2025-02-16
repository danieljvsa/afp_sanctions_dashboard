from notion import get_results, create_page
import streamlit as st
import json
import uuid
import time

CLUBS_DATABASE = st.secrets['clubs_database_id']

def get_clubs(): 
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
        print(row["properties"]['Alias'])
        alias = row["properties"]['Alias']["rich_text"][0]['text']['content']
        club_id = row["properties"]['ClubId']["title"][0]['text']['content']
        clubs.append({"row_id": row_id, "name": name, "city": city, "url": url, "img_url": img_url, "alias": alias, "club_id": club_id})

    return {"response": clubs, "success": True}

get_clubs()