# 초상화 AI 처리를 위한 처리
import sys
import os
import torch
from PIL import Image

# subprocess 사용법: https://umbum.dev/382
import subprocess

from face_detector import FaceDetector
import slack_util
from redis_helper import RedisHelper
import config

class PortraitHelper:

    SVG_FOLDER = r"E:\GIT_AI\informative-drawings\output\svg"

    def __init__(self):
        self.redisHelper = RedisHelper(config)
        self.ani_model = torch.hub.load("bryandlee/animegan2-pytorch:main", "generator", pretrained="face_paint_512_v2")
        self.face2paint = torch.hub.load("bryandlee/animegan2-pytorch:main", "face2paint", size=512)
        self.faceDetector = FaceDetector("model/yolov8n-face.pt")

    def run(self, file_url, user_key, slack_channel, slack_ts):
        slack_util.add_reaction('ani_gear', slack_channel, slack_ts)

        self.redisHelper.set(user_key, "photo", file_url)

        # 0. slack 다운로드 및 얼굴 위치를 고려한 정사각형 crop
        img = slack_util.download_image(file_url, config.Slack.BOT_TOKEN)
        img_ext = file_url.split(".")[-1]
        print("img_ext:", img_ext)
        if len(img_ext) > 4:
            # 디폴트 확장자: jpg
            img_ext = "jpg"
        box_list = self.faceDetector.pedict(img)
        print("box_list:", box_list)
        square_img = self.faceDetector.get_square_image(img, box_list)
        print(square_img.size)
        print("len(box_list):", len(box_list))
        if len(box_list) == 1:
            # 1. 카툰화
            ani_img = self.run_anime_gan(square_img)
            ret = slack_util.upload_image(slack_channel, ani_img, "1. 카툰화", slack_ts)
            image_url = slack_util.get_download_url(ret)
            self.redisHelper.set(user_key, "anime", image_url)

        INPUT_PHOTO_NAME = f"1.{img_ext}"
        INPUT_ANIME_NAME = "2.png"
        OUTPUT_PHOTO_FILE = "1_out.png"
        OUTPUT_ANIME_FILE = "2_out.png"

        # 2. 드로잉(사진+카툰화)        
        INPUT_FOLDER = "temp/input"
        OUTPUT_FOLDER = "temp/output"
        square_img.save(os.path.join(INPUT_FOLDER, INPUT_PHOTO_NAME))
        if len(box_list) == 1:
            ani_img.save(os.path.join(INPUT_FOLDER, INPUT_ANIME_NAME))
        
        self.run_drawing(INPUT_FOLDER, OUTPUT_FOLDER)

        photo_drawing_path = os.path.join(OUTPUT_FOLDER, "anime_style", OUTPUT_PHOTO_FILE)
        ret = slack_util.upload_file(slack_channel, photo_drawing_path, "2. 드로잉(사진)", slack_ts)
        image_url = slack_util.get_download_url(ret)
        self.redisHelper.set(user_key, "drawing_photo", image_url)
        
        if len(box_list) == 1:
            anime_drawing_path = os.path.join(OUTPUT_FOLDER, "anime_style", OUTPUT_ANIME_FILE)
            ret = slack_util.upload_file(slack_channel, anime_drawing_path, "2. 드로잉(카툰)", slack_ts)
            image_url = slack_util.get_download_url(ret)
            self.redisHelper.set(user_key, "drawing_anime", image_url)

        PHOTO_BMP_FILE = "1_out.bmp"
        ANIME_BMP_FILE = "2_out.bmp"
                
        # 3. BMP
        photo_bmp_path = os.path.join(OUTPUT_FOLDER, "anime_style", PHOTO_BMP_FILE)
        self.convert_image_ext(photo_drawing_path, photo_bmp_path)
        if len(box_list) == 1:
            anime_bmp_path = os.path.join(OUTPUT_FOLDER, "anime_style", ANIME_BMP_FILE)
            self.convert_image_ext(anime_drawing_path, anime_bmp_path)

        # 4. SVG
        photo_svg_path = os.path.join(self.SVG_FOLDER, user_key + "_photo.svg")
        self.convert_svg(photo_bmp_path, photo_svg_path)
        if len(box_list) == 1:
            anime_svg_path = os.path.join(self.SVG_FOLDER, user_key + "_anime.svg")
            self.convert_svg(anime_bmp_path, anime_svg_path)

        ret = slack_util.upload_file(slack_channel, photo_svg_path, "3. SVG(사진)", slack_ts)
        image_url = slack_util.get_download_url(ret)
        self.redisHelper.set(user_key, "svg_photo", image_url)
        
        if len(box_list) == 1:
            ret = slack_util.upload_file(slack_channel, anime_svg_path, "3. SVG(카툰)", slack_ts)
            image_url = slack_util.get_download_url(ret)
            self.redisHelper.set(user_key, "svg_anime", image_url)

        # slack 이모티콘 처리
        slack_util.remove_reaction('ani_gear', slack_channel, slack_ts)
        slack_util.remove_reaction('listening', slack_channel, slack_ts)
        slack_util.add_reaction('white_check_mark', slack_channel, slack_ts)


    def run_anime_gan(self, img):
        # img = Image.open(file_path).convert("RGB")
        out_img = self.face2paint(self.ani_model, img)
        return out_img

    def run_drawing(self, input_folder, output_folder):
        # python test.py --name anime_style --size 512 --dataroot examples/1 --results_dir results
        commands = ['python', 'test.py', '--name', 'anime_style', '--size', '512', '--dataroot', input_folder, '--results_dir', output_folder]

        print(" ".join(commands))

        subprocess.run(commands, shell=True)

    def convert_image_ext(self, input_path, output_path):
        img = Image.open(input_path)
        img.save(output_path)

    def convert_svg(self, input_path, output_path):
        # C:\util\potrace-1.16.win64\potrace -s -k 0.65 -t 6 -o fd16b069557e5430623fb73821be5e52_out.svg fd16b069557e5430623fb73821be5e52_out.bmp
        commands = [r'D:\util\potrace-1.16.win64\potrace.exe', '-s', '-k', '0.8', '-t', '5', '-o', output_path, input_path]

        print(" ".join(commands))

        subprocess.run(commands, shell=True)



if __name__ == "__main__":
    helper = PortraitHelper()

    slack_ts = "1695832761.355159"
    slack_channel = "C05TRJEUPF0"
    user_key = "01090014461"
    file_url = "https://files.slack.com/files-pri/T05TH4T3WMD-F05TS025GHM/download/_______crop.jpg"
    ret = helper.run(file_url, user_key, slack_channel, slack_ts)
    # ret = slack_util.get_download_url(ret)
    # print("download_url:", ret)
    exit()

    # input_path = r"E:\GIT_AI\informative-drawings\examples\1\ady95_1.jpg"
    file_url = "https://files.slack.com/files-pri/T05TH4T3WMD-F05TN9F0C07/download/_________2.png"
    svg_path = r"E:\GIT_AI\informative-drawings\output\svg\2.svg"
    helper.run(file_url, svg_path)

    exit()

    input_path = r"E:\GIT_AI\informative-drawings\temp\output\anime_style\1_out.png"
    output_path = r"E:\GIT_AI\informative-drawings\temp\output\anime_style\1_out.bmp"

    helper.convert_image_ext(input_path, output_path)

    exit()

    input_path = r"E:\GIT_AI\informative-drawings\temp\output\anime_style\1_out.bmp"
    output_path = r"E:\GIT_AI\informative-drawings\output\svg\1_out.svg"

    helper.convert_svg(input_path, output_path)

    exit()

    input_folder = "temp/input"
    output_folder = "temp/output"

    
    helper.run_drawing(input_folder, output_folder)

    print("done")

    exit()

    image_path = r"E:\GIT_AI\informative-drawings\examples\1\ady95_1.jpg"

    ret = helper.run_anime_gan(image_path)
    print(ret)