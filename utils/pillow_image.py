from PIL import Image




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

