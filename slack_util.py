import io
import os
import time
import requests
from PIL import Image

from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

import config

import ssl
import certifi
ssl_context = ssl.create_default_context(cafile=certifi.where())
client = WebClient(token=config.Slack.BOT_TOKEN, ssl=ssl_context)

def message():
    try:
        response = client.chat_postMessage(channel='#test', text="Hello world!")
        assert response["message"]["text"] == "Hello world!"
    except SlackApiError as e:
        # You will get a SlackApiError if "ok" is False
        assert e.response["ok"] is False
        assert e.response["error"]  # str like 'invalid_auth', 'channel_not_found'
        print(f"Got an error: {e.response['error']}")

# message()
# exit()

# response 결과로부터 download_url 을 가져옴
def get_download_url(response):
    if response.get("ok") != True:
        return ""
    elif "file" not in response:
        return ""

    download_url = response["file"].get("url_private_download")
    return download_url


def add_reaction(name, channel, ts):
    # client.reactions_add(name="ani_gear", channel="C05TRJEUPF0", timestamp="1695832761.355159")
    try:
        client.reactions_add(name=name, channel=channel, timestamp=ts)
    except SlackApiError as e:
        if e.response["error"] == "already_reacted":
            pass
        else:
            raise e


def remove_reaction(name, channel, ts):
    # client.reactions_remove(name=name, channel=channel, timestamp=ts)
    try:
        client.reactions_remove(name=name, channel=channel, timestamp=ts)
    except SlackApiError as e:
        if e.response["error"] == "no_reaction":
            pass
        else:
            raise e

def post_thread():
    try:
        response = client.chat_postMessage(
            channel="#test",
            text="Here's a message for you!",
            # reply_broadcast=True,
            thread_ts="1695832761.355159"
        )
        assert response["message"]["text"] == "Here's a message for you!"
    except SlackApiError as e:
        # You will get a SlackApiError if "ok" is False
        assert e.response["ok"] is False
        assert e.response["error"]  # str like 'invalid_auth', 'channel_not_found'
        print(f"Got an error: {e.response['error']}")


def upload_file(channel_id, file_path, comment = "", thread_ts = ""):
    response = client.files_upload(
        channels=channel_id,
        file=file_path,
        thread_ts=thread_ts,
        initial_comment=comment
    )

    return response



# URL을 통해 이미지를 가져옴
def download_image(download_url, slack_token = False):
    headers = {}
    if slack_token:
        headers = {'Authorization': 'Bearer ' + slack_token}
    
    res = requests.get(download_url, headers=headers)
    
    try:
        if res.status_code == 200:
            image_bytes = bytearray(res.content)
            image = Image.open(io.BytesIO(image_bytes))
            return image

        else:
            # 파일이 존재하지 않을때(404)
            return None
    finally:
        del res


# PIL image -> bytes
def image_to_bytes(image):
    imgByteArr = io.BytesIO()
    image.save(imgByteArr, format='JPEG')
    imgByteArr = imgByteArr.getvalue()
    return imgByteArr

def upload_image(channel_id, image, comment = "", thread_ts = ""):

    image_bytes = image_to_bytes(image)
    ret = client.files_upload(
            channels=channel_id,
            initial_comment=comment,
            thread_ts=thread_ts,
            file=image_bytes,
        )
    
    return ret


def post_message_with_button(slack_client, channel_id):
    attach_json = [
        {
            "fallback": "신고문서를 만드시겠습니까?",
            "color": "#CC0000",
            "actions": [
                {
                    "type": "button",
                    "text": "신고문서 생성하기",
                    # "text": ":red_circle:   Complete Task: ",
                    "url": "https://roach.ngrok.io/workflow/",
                }
            ]
        }
    ]

    # Post the message to Slack, storing the result as `res`
    res = slack_client.chat_postMessage(
        channel=channel_id,
        text="신고문서를 만드시겠습니까?",
        attachments=attach_json
    )


if __name__ == "__main__":
    import image_util
    import slack.settings_slack as settings_slack
    from slack_sdk import WebClient
    
    channel_id = settings_slack.Slack.CHANNEL
    slack_client = WebClient(settings_slack.Slack.BOTUSER_TOKEN)
    
    post_message_with_button(slack_client, channel_id)

    exit()

    file_path = r"E:\DATA\@car3\@코드스테이츠_차종분류\0905 데이터 수정본\@train\test\랜드로버_SUV_디스커버리_2017-2020\SUV_디스커버리-43.jpg"
    image_np = image_util.imread(file_path)
    image_bytes = image_util.image_to_bytes(image_np)
    ret = upload_image(slack_client, channel_id, image_bytes, comment = "test")
    print(ret)