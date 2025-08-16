from PIL import Image
import os
import base64
from django.conf import settings
from django.utils.safestring import mark_safe

def resizeImage(w, h, img):
    width = w
    height = h
    image = img
    print('image: ', image)
    name = str(image).split('.')[0]
    print('image name: ', name)
    image_obj = Image.open(image)
    print('original_image_size: ', image_obj.size)
    try:
        resized_image = image_obj.resize((850, 1100))
        print('resized_image_size: ', resized_image.size)
        final_image = resized_image.save(str(name) +'.png')
        image_obj.close()
        return final_image
    except OSError:
        image_obj.close()
        return image



def img_base64(img_path):
    image_path = os.path.join(settings.BASE_DIR, 'static', img_path)
    with open(image_path, 'rb') as image_file:
        base64_string = base64.b64encode(image_file.read()).decode('utf-8')
        return mark_safe(f'data:image/png;base64,{base64_string}')
    