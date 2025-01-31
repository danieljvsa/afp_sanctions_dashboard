import requests
from config import parser_config
TOKEN = parser_config('notion_api_secret')
NOTION_API_URL = parser_config('notion_api_url')

headers = {
    "Authorization": "Bearer " + TOKEN, 
    "Notion-Version": "2022-06-28", 
    "Content-Type": "application/json" 
}

def get_results(database_id: str):
    url = NOTION_API_URL + "databases/" + database_id + "/query"
    print(url)

    status_code = 400
    results = []
    next_cursor = None
    error = None
    while True:
        # If there's a cursor, include it in the query
        data = {
            "start_cursor": next_cursor
        } if next_cursor else {}

        response = requests.post(url, json=data, headers=headers)
        status_code = response.status_code
        #response = requests.post(NOTION_API_URL.format(database_id=database_id), json=data, headers=headers)

        if response.status_code == 200:
            result = response.json()
            results.extend(result["results"])
            next_cursor = result.get('next_cursor', None)
            if not next_cursor:
                break
        else:
            error = response.json()
            print("Error 400: ", response.json())
            break

    if status_code == 200:
        data = {"success": True, "statusCode": response.status_code, "result": results}
    else:
        data = {"success": False, "statusCode": response.status_code, "result": None, "error": error}
    
    return data
          
    
    
def create_page(data: dict, database_id: str):
    url = NOTION_API_URL + "pages/"
    payload = {"parent": {"database_id": database_id}, "properties": data}

    print(url)
    response = requests.post(url, headers=headers, json=payload)

    if response.status_code == 200:
        result = response.json()
        data = {"success": True, "statusCode": response.status_code, "result": result}
        return data
    else:
        data = {"success": False, "statusCode": response.status_code, "result": None, "error": response.json()}
        print("Error: ", response.json())
        return data
    
def update_page(data: dict, page_id: str):
    url = NOTION_API_URL + "pages/" + page_id
    payload = {"properties": data}

    print(url)
    response = requests.patch(url, headers=headers, json=payload)

    if response.status_code == 200:
        result = response.json()
        data = {"success": True, "statusCode": response.status_code, "result": result}
        return data
    else:
        data = {"success": False, "statusCode": response.status_code, "result": None, "error": response.json()}
        print("Error: ", response.json())
        return data