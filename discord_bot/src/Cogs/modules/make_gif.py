import os
from PIL import Image, ImageOps
import math
import sys


def path_to_list(path):
    if(path[-1] != '/'):
        path += '/'
    list = [path+i for i in os.listdir(path)]    
    return list


def get_filename_from_path(path):
    path_list = path.split("/")
    return path_list[-1]


'''画像読み込み＆前処理'''
def Load_images(images_path, is_transparency):
    images = []
    if is_transparency:
        for image_path in images_path:
            img = Image.open(image_path)
            images.append(img)
    else:
        for image_path in images_path:
            img = Image.open(image_path)
            img = img.convert('RGB')
            img = img.quantize(colors=256,method=0)
            images.append(img)
    return images


def Scaling_images(images, scale):
    scaled_images = []
    for image in images:
        scaled_images.append(image.resize((int(image.width*scale),int(image.height*scale))))
        
    return scaled_images


def Generate_reverse_loop(images):
    reverse_images = images[::-1].copy()
    return images + reverse_images[1:-1]


'''透過処理'''
def Generate_mask(images):
    masked_images = []
    for image in images:
        alpha = image.split()[3]
        image = image.convert('RGB').convert('P', palette=Image.ADAPTIVE, colors=256)
        mask = Image.eval(alpha, lambda alpha: 255 if alpha <= 100 else 0)
        image.paste(255, mask=mask)
        
        masked_images.append(image)
    return masked_images


'''GIFアニメ生成＆保存'''
def Generate_GIF(images, is_transparency, save_path ,duration=30):
    if is_transparency:
        images[0].save(save_path,
                       save_all=True,
                       append_images=images[1:],
                       interlace = False,
                       disposal = 2,
                       optimize = False,
                       version = 'GIF89a',
                       transparency=255,
                       loop = 0,   #無限ループ=0
                       duration = duration #time[ms]
                      )
    else:
        images[0].save(save_path,
                   save_all=True,
                   append_images=images[1:],
                   include_color_table = False,
                   interlace = False,
                   disposal = 0,
                   optimize = False,
                   version = 'GIF89a',
                   loop = 0,   #無限ループ=0
                   duration = duration #time[ms]
                  )


def Generate_Adaptive_size_Gif(images_path, is_transparency=True, max_size=256, save_path='./output/out.gif', duration=30, is_loop=False):
    
    images = Load_images(images_path, is_transparency)
    if is_transparency:
        masked_images =  Generate_mask(images)
    else:
        masked_images = images
    
    if is_loop:
        masked_images = Generate_reverse_loop(masked_images)
    
    riprocal_scale_list = [x/100 for x in range(100, 5000, 1)]
    low = 0
    high = len(riprocal_scale_list)
    mid = int((low+high) / 2)
    while True:
        scaled_images = Scaling_images(images=masked_images, scale=1/riprocal_scale_list[mid])
        Generate_GIF(scaled_images, is_transparency, save_path, duration=duration)
        size = os.path.getsize(save_path)/(1e+3)

        print(low, mid, high)
        if (size > max_size):
            low = mid   
        elif (size <= max_size):
            if (high - low) <= 1:
                break
            high = mid
           
        mid = math.ceil((low+high) / 2)
        
    return save_path