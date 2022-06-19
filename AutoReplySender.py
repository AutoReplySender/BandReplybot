import requests
import pickle
import json
import backoff
import time
import os
import sys
from random import randint

# access_token 需要在 https://developers.band.us/develop/myapps/list 注册获取
# access_token = 【你的token】
max_comment_try_times = 3
max_trigger_times_by_single_post = 2
keywords_list = [["原神", "原批"], ["三次元"], [
    "求个种", "求种"], ["撸"], ["牛子"], ["晚安", "好梦"], ["小e"], ["鼠人", "本鼠", "鼠鼠"], ["test", "测试"], ["集美", "织女"], ["大的来了", "大的來了", "大的来了", "大的要来了", "大的要來了"], ["新家在哪", "新家圈我"]]
replies_list = [["原神可以不玩，原批不可不艹", "运气用完了，妈妈也走了。最后还是没抽到甘雨，一大遗憾。"], ["三次元？狗都不看！"], ["同求，裤子都脱了，急"], ["多撸我只能说", "一起撸"], [
    "牛子在哪，我找了半天没找到", "我的牛子是渗氮钢材料的，延展性好"], ["晚安，睡大觉了zzz"], ["单词天天背，功力日日深🤘⭕🙆🙏"], ["弘扬手冲文化，传承鼠人精神"], ["理你一下"], ["我求求你们别舔集美了可以吗？像个小学生一样，舔又舔不到，只能无能狂怒了，没有集美活不下去了是吧，那么喜欢集美能直接去开个小号和集美玩吗"], ["《大的来了》是荒诞戏剧的代表作。以几个鼠人苦等“大的”，而“大的”不来的情节，喻示人生是一场无尽无望的等待，表达了世界荒诞、人生痛苦的存在主义思想。它发生的时间地点都是模糊的，布景也是一片荒凉，他们一边等，一边用各种无意义的手段打发时光。他们经常显得头脑一片混乱，缺乏思维能力，尤其是极度地惧怕孤独。当有人询问“大的代表什么”时，鼠人们说：“我要是知道，早就说出来了。”"], ["新家来：红迪手冲TV。鼠人最后的根据地，永不陷落的堡垒。"]]


class ReplySenderBaseException(Exception):
    def __init__(self, msg="Reply sender error."):
        super().__init__(msg)


class GetBandsException(ReplySenderBaseException):
    def __init__(self):
        super().__init__("Get bands error.")


class GetPostsException(ReplySenderBaseException):
    def __init__(self):
        super().__init__("Get posts error.")


class CheckPermissionsException(ReplySenderBaseException):
    def __init__(self):
        super().__init__("Check permissions error.")


@backoff.on_exception(backoff.expo,
                      (requests.exceptions.RequestException,
                       ReplySenderBaseException),
                      max_time=60,
                      max_tries=5)
def getBands(access_token: str) -> list:
    url = "https://openapi.band.us/v2.1/bands"
    params = {
        "access_token": access_token,
    }
    r = requests.get(url, params=params)
    result = json.loads(r.text)
    if result["result_code"] != 1:
        raise GetBandsException
    return result["result_data"]["bands"]


@backoff.on_exception(backoff.expo,
                      (requests.exceptions.RequestException,
                       ReplySenderBaseException),
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
        raise GetPostsException
    return result["result_data"]["items"]


@backoff.on_exception(backoff.expo,
                      (requests.exceptions.RequestException,
                       ReplySenderBaseException),
                      max_time=60,
                      max_tries=5)
def checkPermissions(access_token: str, band_key: str, permissions="posting,commenting,contents_deletion") -> list:
    url = "https://openapi.band.us/v2/band/permissions"
    params = {
        "access_token": access_token,
        "band_key": band_key,
        "permissions": permissions,
    }
    r = requests.get(url, params=params)
    result = json.loads(r.text)
    if result["result_code"] != 1:
        raise CheckPermissionsException
    return result["result_data"]["permissions"]


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
    print(f"开始循环：{state.loop_times}")
    bands = getBands(access_token)
    tmp_band_list = []
    for band in bands:
        band_key = band["band_key"]
        tmp_band_list.append(band_key)
        if band_key not in state.bands.keys():
            state.bands[band_key] = {}
            state.bands[band_key]["checked_timestamp"] = 0
        state.bands[band_key]["name"] = band["name"]
        state.bands[band_key]["member_count"] = band["member_count"]
        permissions = checkPermissions(access_token, band_key)
        state.bands[band_key]["permissions"] = permissions
    for key in list(state.bands.keys()):
        if key not in tmp_band_list:
            del state.bands[key]
    print("bands saved.")
    for key in state.bands.keys():
        if 'commenting' in state.bands[key]["permissions"]:
            print("begin post check.")
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
    print("posts checked.")
    for t in range(60):
        time.sleep(1)


def main():
    pickle_path = "./ReplySenderState.pickle"
    old_pickle_path = "./ReplySenderState.pickle.archive"
    state = ReplySenderState()
    if os.path.exists(pickle_path):
        with open(pickle_path, "rb") as pickleFile:
            state = pickle.load(pickleFile)
    try:
        while True:
            main_loop(state)
            state.loop_times += 1
    except BaseException as e:
        print(e)
        print("正在保存状态……")
        if os.path.exists(pickle_path):
            os.replace(pickle_path, old_pickle_path)
        with open(pickle_path, "wb") as pickleFile:
            pickle.dump(state, pickleFile)
        print("保存完成。")
        sys.exit()


if __name__ == "__main__":
    main()
