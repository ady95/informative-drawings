# Ultralytics YOLO 🚀, GPL-3.0 license

from pathlib import Path

import cv2
import torch
from PIL import Image

from ultralytics import YOLO
# from ultralytics.yolo.utils import ROOT, SETTINGS



class FaceDetector:

    def __init__(self, model_path):
        self.model = YOLO(model_path)

    # 얼굴 인식 결과를 이용해서 정사각형 이미지 리턴
    def get_square_image(self, img, box_list = None):
        w, h = img.size

        if w == h:
            # 이미 정사각형일떄는 bypass
            return img

        elif w > h:
            # 가로모드일때
            x1 = (w-h)/2
            y1 = 0
            x2 = (w+h)/2
            y2 = h

            return img.crop((x1, y1, x2, y2))

        h1 = (h - w) /2
        h2 = (h + w) /2

        face_h_min = -1
        face_h_max = -1

        if box_list == None:
            box_list = self.pedict(img)

        for box in box_list:
            y1 = int(box[1])
            y2 = int(box[3])
            if face_h_min == -1 or face_h_min > y1:
                face_h_min = y1
            if face_h_max == -1 or face_h_max < y2:
                face_h_max = y2

        face_h_min2 = face_h_min - int((face_h_max - face_h_min) /2)
        if face_h_min2 < 0: face_h_min2 = 0
        # print(face_h_min2, face_h_min, face_h_max)

        c1 = h1
        c2 = h2
        if h1 > face_h_min2:
            c1 = face_h_min2
            c2 = face_h_min2 + w

        return img.crop((0, c1, w, c2))


    def pedict(self, img):        
        
        # output = model.predict(source=img, stream=False, verbose=True)  # PIL
        output = self.model(source=img, save=False, verbose=False)  # PIL
        
        box_list = output[0].boxes.data.cpu().tolist()

        return box_list
        # for box in box_list:
        #     x = int(box[0])
        #     y = int(box[1])
        #     x2 = int(box[2])
        #     y2 = int(box[3])
        #     print(x, y, x2, y2)


if __name__ == "__main__":

    MODEL = "model/yolov8n-face.pt"

    # SOURCE = 'examples/ady95_crop.jpg'
    SOURCE = 'examples/1/hyunjun-1.jpg'
    # SOURCE = 'examples/IMG_7574.jpg'
    # SOURCE = 'examples/1/ady95_1.jpg'
    img = Image.open(str(SOURCE))

    face = FaceDetector(MODEL)
    box_list = face.pedict(img)
    print(type(box_list))
    print(len(box_list))
    print(box_list)

    exit()

    crop_img = face.get_square_image(img)
    crop_img.save("results/square.jpg")
