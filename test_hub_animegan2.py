import torch
from PIL import Image

model = torch.hub.load("bryandlee/animegan2-pytorch:main", "generator", pretrained="face_paint_512_v2")
face2paint = torch.hub.load("bryandlee/animegan2-pytorch:main", "face2paint", size=512)

image_path = r"E:\GIT_AI\informative-drawings\examples\1\ady95_1.jpg"

img = Image.open(image_path).convert("RGB")
out = face2paint(model, img)

out.save("output/ady95_1.jpg")