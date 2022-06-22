import requests
import pickle
import json
import backoff
import time
import os
import sys
from random import randint

keywords_list = []
replies_list = []
with open("./autoreply.json", "r", encoding="utf-8") as autoReplyJson:
    autoReplyDict = json.loads(autoReplyJson.read())
for item in autoReplyDict["autoreply"]:
    keywords_list.append(item["keywords"])
    replies_list.append(item["replies"])

with open("./config.json", "r", encoding="utf-8") as configJson:
    configDict = json.loads(configJson.read())["config"]
access_token = configDict["access_token"]
band_key_to_check = configDict["band_key_to_check"]
max_comment_try_times = configDict["max_comment_try_times"]
max_trigger_times_by_single_post = configDict["max_trigger_times_by_single_post"]


class ReplySenderBaseException(Exception):
    def __init__(self, msg="Reply sender error."):
        super().__init__(msg)


class GetPostsException(ReplySenderBaseException):
    def __init__(self, error_code, error_message):
        super().__init__(f"Get posts error. {error_code}: {error_message}")


@backoff.on_exception(backoff.expo,
                      requests.exceptions.RequestException,
                      max_time=60,
                      max_tries=5)
def getPosts(access_token: str, band_key: str, locale: str) -> list:
    url = "https://openapi.band.us/v2/band/posts"
    params = {
        "access_token": access_token,
        "band_key": band_key,
        "locale": locale,
    }
    r = requests.get(url, params=params)
    result = json.loads(r.text)
    if result["result_code"] != 1:
        raise GetPostsException(
            result["result_code"], result["result_data"]["message"])
    return result["result_data"]["items"]


@backoff.on_exception(backoff.expo,
                      requests.exceptions.RequestException,
                      max_time=60,
                      max_tries=5)
def writeComment(access_token: str, band_key: str, post_key: str, body: str) -> bool:
    url = "https://openapi.band.us/v2/band/post/comment/create"
    suffixed_body = body + "\n\nI am a bot, and this action was performed automatically. Please contact 织女小e if you have any questions or concerns."
    params = {
        "access_token": access_token,
        "band_key": band_key,
        "post_key": post_key,
        "body": suffixed_body
    }
    r = requests.post(url, params=params)
    result = json.loads(r.text)
    if result["result_code"] == 1:
        return True
    return False


def containPictures(photos):
    for photo in photos:
        if photo["is_video_thumbnail"] == False:
            return True
    return False


def checkKeywords(keywords: list, content: str) -> bool:
    for keyword in keywords:
        if keyword in content:
            return True
    return False


def chooseReply(replies: list) -> str:
    chosen_index = randint(0, len(replies) - 1)
    return replies[chosen_index]


class ReplySenderState:
    def __init__(self):
        self.loop_times = 0
        self.bands = {}
        self.reminded_author = {}


def main_loop(state):
    print(f"Begin loop: {state.loop_times}")
    for key in state.bands.keys():
        print("Begin post check.")
        current_timestamp = state.bands[key]["checked_timestamp"]
        max_timestamp = current_timestamp
        posts = getPosts(access_token, key, "zh_CN")
        for post in posts:
            trigger_times = 0
            if post["created_at"] > current_timestamp:
                if post["created_at"] > max_timestamp:
                    max_timestamp = post["created_at"]
                author_key = post["author"]["user_key"]
                for (keywords, replies) in zip(keywords_list, replies_list):
                    content = post["content"]
                    if checkKeywords(keywords, content) and trigger_times < max_trigger_times_by_single_post:
                        chosen_reply = chooseReply(replies)
                        result = writeComment(
                            access_token, key, post["post_key"], chosen_reply)
                        if result:
                            print(f"{chosen_reply} added.")
                            trigger_times += 1
                        else:
                            print(f"{chosen_reply} failed.")
                        for t in range(10):
                            time.sleep(1)
                if author_key not in state.reminded_author.keys():
                    if containPictures(post["photos"]):
                        for i in range(max_comment_try_times):
                            result = writeComment(
                                access_token, key, post["post_key"], "您好，这是我首次检测到您的账号发布图片贴，请注意BAND不会自动删除图片的EXIF信息，参见 https://band.us/band/87834662/post/2657\n如果您发布了自己拍摄的照片，建议立即删除贴子。注意：勾选禁止下载无法阻止EXIF信息泄露！")
                            for t in range(10):
                                time.sleep(1)
                            if result:
                                print("EXIF reminder added.")
                                break
                if author_key not in state.reminded_author.keys():
                    state.reminded_author[author_key] = post["author"]["name"]
        state.bands[key]["checked_timestamp"] = max_timestamp
    print("Posts checked.")
    for t in range(2 * 60):
        time.sleep(1)


def main():
    pickle_path = "./ReplySenderState.pickle"
    old_pickle_path = "./ReplySenderState.pickle.archive"
    state = ReplySenderState()
    if os.path.exists(pickle_path):
        with open(pickle_path, "rb") as pickleFile:
            state = pickle.load(pickleFile)
    for band_key in band_key_to_check:
        if band_key not in state.bands.keys():
            state.bands[band_key] = {}
            state.bands[band_key]["checked_timestamp"] = 0
    for key in list(state.bands.keys()):
        if key not in band_key_to_check:
            del state.bands[key]
    try:
        while True:
            main_loop(state)
            state.loop_times += 1
    except BaseException as e:
        print(e)
        print("Saving the state...")
        if os.path.exists(pickle_path):
            os.replace(pickle_path, old_pickle_path)
        with open(pickle_path, "wb") as pickleFile:
            pickle.dump(state, pickleFile)
        print("Completed.")
        sys.exit()


if __name__ == "__main__":
    main()
