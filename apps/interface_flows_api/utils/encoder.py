from io import BytesIO

import numpy as np
from PIL import Image


def numpy_array_to_io(image_np: np.array, img_format="JPEG") -> BytesIO:
    # convert BGR to RGB
    image_np = image_np[:, :, ::-1]
    # create a file from correct array
    image = Image.fromarray(image_np.astype(np.uint8))
    buffered = BytesIO()
    image.save(buffered, format=img_format)
    return buffered
