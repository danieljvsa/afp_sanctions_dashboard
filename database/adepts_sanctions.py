from database.notion import get_results, update_page, create_page
from config import parser_config
import streamlit as st
import json
import uuid
import time
import datetime

SANCTIONS_ADEPTS_DATABASE = st.secrets['sanctions_adepts_database_id']

def get_sanctions():
    results = get_results(SANCTIONS_ADEPTS_DATABASE)
    
    if results["success"] == False: 
        return {"response": [], "success": False}

    rows = results["result"]
    #print(rows)

    sanctions = []

    for row in rows: 
        page_id = row['id']
        sanction_id = row["properties"]['SanctionId']["title"][0]['text']['content'] if len(row["properties"]['SanctionId']["title"]) > 0 else ""
        club_group = row["properties"]['Club Group']["select"]['name']
        quantity = row["properties"]['Quantity']["number"]
        suspension_days = row["properties"]['Suspension Days']["number"]
        formation = row["properties"]['Formation']["select"]['name']
        fines = row["properties"]['Fines']["number"]
        date = row["properties"]['Date']['date']["start"]
        date = datetime.date.fromisoformat(date)
        date = datetime.date.isoformat(date)
        sanctions.append({
            "page_id": page_id,
            "sanction_id": sanction_id,
            "club_group": club_group,
            "quantity": quantity ,
            "suspension_days": suspension_days ,
            "formation": formation ,
            "fines": fines ,
            "date": date 
        })

    return {"response": sanctions, "success": True}
    