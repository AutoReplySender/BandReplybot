import requests
import json


with open("./config.json", "r", encoding="utf-8") as configJson:
    configDict = json.loads(configJson.read())["config"]
access_token = configDict["access_token"]


def getBands(access_token: str) -> list:
    url = "https://openapi.band.us/v2.1/bands"
    params = {
        "access_token": access_token,
    }
    r = requests.get(url, params=params)
    result = json.loads(r.text)
    return result


bands = getBands(access_token)
print(bands)
