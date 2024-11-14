import os
from PIL import Image
from moviepy.editor import VideoFileClip
import requests

def create_and_upload_thumbnail(video_path):
    clip = VideoFileClip(video_path)
    
    frame = clip.get_frame(1.0)  # Primeiro segundo do clipe
    
    image = Image.fromarray(frame)
    image_path = "thumbnail.jpg"
    
    # Salvar o thumbnail
    image.save(image_path)

    # Fechar explicitamente o arquivo para evitar problemas de "arquivo em uso"
    image.close()
    
    # Garantir que o arquivo foi liberado antes de prosseguir
    try:
        with open(image_path, 'rb') as file:
            files = {'files[]': file}
            response = requests.post('https://up1.fileditch.com/upload.php', files=files)

        if response.status_code == 200:
            json_response = response.json()
            image_url = json_response['files'][0]['url']
            os.remove(image_path)  # Deletar o arquivo após o upload
            return image_url
        else:
            raise Exception("Failed to upload thumbnail. Status code: " + str(response.status_code))
    except Exception as e:
        os.remove(image_path)  # Garantir que o arquivo seja deletado em caso de erro
        raise e  

def get_video_info_and_shortlink(video_url, filepath):
    info_url = "https://autocompressor.net/videoinfo"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
        "Accept": "*/*",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate, br",
        "Content-Type": "application/json; charset=UTF-8",
        "X-Requested-With": "XMLHttpRequest",
        "Origin": "https://autocompressor.net",
        "Connection": "keep-alive",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin"
    }
    data = {"url": video_url}
    response = requests.post(info_url, headers=headers, json=data)
    info_json = response.json()

    width = info_json["info"]["width"]
    height = info_json["info"]["height"]

    shortlink_url = "https://autocompressor.net/av1/mkshortlink"
    data["w"] = width
    data["h"] = height
    data["v"] = video_url

    try:
        # Gerar o thumbnail e obter a URL
        thumbnail_url = create_and_upload_thumbnail(filepath)
        if thumbnail_url:
            data["i"] = thumbnail_url
    except Exception as e:
        print("Error creating and uploading thumbnail:", e)

    response = requests.post(shortlink_url, headers=headers, json=data)
    shortlink_json = response.json()

    return "https://autocompressor.net/av1?s=" + shortlink_json["shortLink"]