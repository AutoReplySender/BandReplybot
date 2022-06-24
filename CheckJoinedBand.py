import requests
import json


with open("./config.json", "r", encoding="utf-8") as configJson:
    configDict = json.loads(configJson.read())["config"]
access_token = configDict["access_token"]


def get_bands(access_token_: str) -> list:
    url = "https://openapi.band.us/v2.1/bands"
    params = {
        "access_token": access_token_,
    }
    r = requests.get(url, params=params, timeout=20)
    result = json.loads(r.text)
    return result


bands = get_bands(access_token)
print(bands)
