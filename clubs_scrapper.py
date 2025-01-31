from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import json
import time

URL = 'https://afporto.pt/instituicao/clubes/page/'

def getClubs(html):
    html = driver.page_source
    soup = BeautifulSoup(html, 'html.parser')
    #table = soup.find('div', class_='row')
    #print("table", table)
    rawRows = soup.find_all('article', class_='col-12 col-lg-3 mb-sameaspaddingx2')
    #print("rawRows", rawRows)
    rows = []
    for tr in rawRows:
        #print("row", tr)
        url = tr.find('a', class_='d-block').get('href')
        name = tr.find('p', class_='grid-clube-name mb-2').get_text().strip()
        img_url = tr.find('img', class_='attachment- size- wp-post-image').get('src') if tr.find('img', class_='attachment- size- wp-post-image') else ''
        city = tr.find('p', class_='grid-clube-city').get_text().strip()
        rows.append({"name": name, "url": url, "city": city, "img_url": img_url})
        print("data", {"name": name, "url": url, "city": city, "img_url": img_url})
    return rows

def saveData(rows):
    with open('clubs_raw.json', 'w') as f: 
        json.dump(rows, f, indent=4)

if __name__ == "__main__":
    options = Options()
    options.headless = True 
    driver = webdriver.Chrome(options=options)
    data = []
    for page in range(1,27) : 
        driver.get(URL + str(page))
        time.sleep(3)
        html = driver.page_source
        rows = getClubs(html)
        data.extend(rows)
    driver.quit()

    saveData(data)
    