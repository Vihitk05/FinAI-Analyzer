from pdf2image import convert_from_path
import os
from config import TEMP_IMAGE_FOLDER

def pdf_to_images(pdf_path):
    images = convert_from_path(pdf_path, dpi=300)
    image_paths = []

    for i, img in enumerate(images):
        img_path = os.path.join(TEMP_IMAGE_FOLDER, f"page_{i}.png")
        img.save(img_path, "PNG")
        image_paths.append(img_path)

    return image_paths
