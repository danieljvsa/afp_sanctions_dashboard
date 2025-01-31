from database.notion import get_results, update_page, create_page
from config import parser_config
import json
import uuid
import time
import datetime

SANCTIONS_MANAGERS_DATABASE = parser_config('sanctions_managers_database_id')
CLUBS_ALIAS_DATABASE = parser_config('clubs_alias_database_id')

def get_sanctions():
    results = get_results(SANCTIONS_MANAGERS_DATABASE)
    
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
        #print("----sanction----")
        #print(sanction_id, date)
        #print("----------------")
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

    with open('sanctions_managers_db.json', 'w', encoding='utf8') as f:
        json.dump(sanctions, f, ensure_ascii=False, indent=4)
    

def update_sanctions():

    with open('sanctions_managers_db.json', 'r', encoding='utf8') as file:
        sanctions_rows = json.load(file)

    for sanction in sanctions_rows:
        print("sanction...")
        generated_uuid = uuid.uuid4().hex
        print(sanction)

        if sanction["sanction_id"] != "":
            continue

        data = {
            "SanctionId": {"title": [{"text": {"content": generated_uuid}}]}
        }

        print(data)
        response = update_page(data, sanction['page_id'])
        print(sanction["date"] + "..." + str(response['statusCode']))
        if response['success'] == False:
            print("Error...")
            print(response)
            break
        time.sleep(1)


def open_sanctions():
    with open('sanctions_managers_db.json', 'r') as file:
        sanctions_rows = json.load(file)

    print(sanctions_rows[0])


def get_clubs_alias():
    results = get_results(SANCTIONS_MANAGERS_DATABASE)

    rows = results["result"]["results"]

    clubs = []
    for row in rows: 
        club_group = row["properties"]['Club Group']["select"]['name']
        
        if club_group not in clubs:    
            clubs.append(club_group)
            

    with open("clubs_alias_db.txt", "w") as file:
        for item in clubs:
            file.write(item + "\n")

    with open('clubs_alias_db.json', 'w', encoding='utf8') as f:
        json.dump(clubs, f, ensure_ascii=False, indent=4)

def create_clubs_alias(): 

    with open("clubs_alias_db.txt", "r") as file:
        clubs_rows = [line.strip() for line in file]

    for club in clubs_rows:
        data = {
            "Club": {"title": [{"text": {"content": club}}]},
            
        }
        #print(data)
        response = create_page(data, CLUBS_ALIAS_DATABASE)
        print(club + "..." + str(response['statusCode']))
        if response['success'] == False:
            print("Error...")
            #print(response)
            break
        time.sleep(1)

def open_clubs():
    with open("clubs_alias_db.txt", "r") as file:
        clubs = [line.strip() for line in file]

    print(clubs)

get_sanctions()
#update_sanctions()
#open_sanctions()
#get_clubs_alias()
#create_clubs_alias()
#open_clubs()