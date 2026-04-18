VERBOSE = False
VISUAL = True

import re
from bs4 import BeautifulSoup

if VISUAL:
    import folium #For Map Vis
    import requests
    import os
    import json
    CACHE_FILE = "geocode_cache.json"
    API_KEY = "AIzaSyDJCW0w1rWCz9h-n5aIc_b4-bwxyyOYtGc"
    colors = {
        "$4.99":  "darkgreen",   # best deal
        "$5.99":  "darkgreen",
        "$6.99":  "darkgreen",
        "$7.99":  "darkgreen",
        "$8.99":  "green",
        "$9.99":  "green",
        "$10.99": "green",
        "$11.99": "green",
        "$12.99": "lightgreen",
        "$13.99": "lightgreen",
        "$14.99": "lightblue",
        "$15.99": "lightblue",
        "$16.99": "cadetblue",
        "$17.99": "cadetblue",
        "$18.99": "darkblue"          # worst deal (relative)
    }

    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "r") as f:
            GEOCACHE = json.load(f)
    else:
        GEOCACHE = {}

URL = "https://coupons-2save.com/"
patt = r"Valid at Great Clips (.*?) Not valid"
headers = {"User-Agent": "Mozilla/5.0"}

##################################################################
# INFO:   Obtains Great Clips offers from Sketchy Site           #
# INPUT:  NONE                                                   #
# RETURN: Array of Tuples [(price, offer_url, location), ...]    #
##################################################################
def getGC():
    coupons = []

    amount = []
    soup = BeautifulSoup(requests.get(URL+"greatclips", headers=headers).text, "html.parser")
    urls = [a["href"] for a in soup.select("a.greatclips-getbutton[href]")]
    
    for u in urls:
        match = re.search(r"\$[\d]+-[\d]+", u)
        if match:
            amount.append(match.group(0).replace("-", "."))
    
    gc_urls = []
    for url_ext in urls:
        block_coup = []
        meta_soup = BeautifulSoup(requests.get(URL+"/"+url_ext, headers=headers).text,"html.parser")
        elements = meta_soup.find_all(class_='rtl', attrs={'value': lambda v: v}) #meta_soup.select(".rtl[value]") DIDNT CONSIDER EMPTY RTL INPUTS
        for el in elements:
            block_coup.append(el.get("value"))
        gc_urls.append(block_coup)

    for val in range(len(gc_urls)-1):
        for indv in range(len(gc_urls[val])-1):
            ind_soup = BeautifulSoup(requests.get(gc_urls[val][indv], headers=headers).text,"html.parser")
            valid = ind_soup.find(id="redeem-now")
            if valid:
                el = ind_soup.find_all("p", id="terms_and_conditions")
                match = re.search(patt, el[0].text)
            if match:
                address = match.group(1)
                coupons.append((amount[val], gc_urls[val][indv], address))
            else:
                coupons.append((amount[val], gc_urls[val][indv], "National Locations"))

    return coupons

def save_geocache():
    with open(CACHE_FILE, "w") as f:
        json.dump(GEOCACHE, f)

def geocode(address):
    if address == "National Locations":
        print("National Deal")
        return 0, 0
    # Look in cache
    if address in GEOCACHE:
        res = GEOCACHE[address]
    
    #If unable to locate, query API
    else:
        url = "https://maps.googleapis.com/maps/api/geocode/json"
        params = {"address": address, "key": API_KEY}
        res = requests.get(url, params=params).json()

        #Update cache
        GEOCACHE[address] = res
        save_geocache()

    #Extract lat/long
    lat_long = res["results"][0]["geometry"]["location"]
    return lat_long["lat"], lat_long["lng"]

def vis(coupons):
    m = folium.Map(location=(32.779167, -96.808891))

    for c in coupons:
        lat, long = geocode(c[2])

        #Check for national deal Currently go to 0,0
        #if lat ==0 and long == 0:
        #    ""
        #else:

        folium.Marker(
            location=[lat, long],
            tooltip= "Great Clips:" + c[0],
            popup="<a href="+c[1]+">"+c[1]+"</a>",
            icon=folium.Icon(icon="map-pin", color=colors[c[0]]),
        ).add_to(m)

    m.save("index.html")

def main():
    coupons = getGC()
    if VISUAL:
        #coupons = [("14.99", "https://TEST.com", "Inspirada Marketplace at 2345 Via Inspirada in Henderson, NV.")]
        vis(coupons)
    if VERBOSE:
        for i in coupons:
            print(i[0], " ", i[1], " ", i[2])

main()