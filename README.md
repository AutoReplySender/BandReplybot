# BandReplybot

用于 BAND 的自动回复 bot。`autoreply.json` 中是要检测的关键词和检测到对应关键词时的回复（若同一条目设置多项回复，bot 会随机选择一项）。`config.json` 是程序的配置文件，其中`max_trigger_times_by_single_post` 表示单个贴子最多触发几条回复。由于 BAND 只有回复贴子的 API，没有回复回复的 API，本程序只对主题贴一楼的内容进行检测。

bot 会对首次检测到发布图片贴的用户进行提醒，让其注意图片的 [EXIF 信息](https://en.wikipedia.org/wiki/Exif)。如不需要提醒，请注释或删去以下代码行：

```python
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
```

## 使用方式

要使用本 bot，请：

**一、获取 Access Token：**

在 [BAND Developers](https://developers.band.us/develop/myapps/list) 上注册应用。"Redirect URI" 可以随便填，例如 http://localhost:8080/ 。 注册完成后点开 "App Name"，连接账户即可获得 Access Token。

BAND 要求用户验证手机号后才能注册 APP，可以使用 [textfree](https://messages.textfree.us/) 等在线短信服务接码作为代替。

**二、填写 Access Token：**

在 `config.json` 的 `access_token` 一项中填入你的 Access Token。`band_key_to_check` 一项可以暂时留空。

**三、运行 `CheckJoinedBand.py`：**

运行 `CheckJoinedBand.py`，其会输出你目前加入的 BAND 的信息。将你想要 bot 检查的 BAND 的 `band_key` 复制下来保存。

**四、填写 Band Keys：**

在 `config.json` 的 `and_key_to_check` 一项中填入上一步复制的 band key。如果有好几个 band keys，请用逗号分隔，例如`["A_band_key", "B band Key"]`。

**五、运行 `AutoReplySender.py`：**

⚠警告⚠：BAND 有隐藏的每日 API 调用配额限制。如果设置程序在多个 BAND 上运行，或是调整设置使 bot 更频繁地检查贴子，可能会超出配额限制。可以考虑注册多个账号来为每个 BAND 设置 bot。

要为 bot 设置代理请参考[如何为 Python 的 Requests 模块设置代理](https://stackoverflow.com/questions/8287628/proxies-with-python-requests-module)。
