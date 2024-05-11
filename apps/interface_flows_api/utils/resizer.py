from io import BytesIO

from django.core.files.uploadedfile import InMemoryUploadedFile
from PIL import Image


def resize_image(image: InMemoryUploadedFile) -> (BytesIO, str):
    img = Image.open(image)
    img_format = img.format.lower()

    min_dimension = min(img.width, img.height)

    left = (img.width - min_dimension) // 2
    top = (img.height - min_dimension) // 2
    right = (img.width + min_dimension) // 2
    bottom = (img.height + min_dimension) // 2

    img = img.crop((left, top, right, bottom))

    buffered = BytesIO()
    img.save(buffered, format=img_format)

    return buffered, img_format
