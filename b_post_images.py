from dotenv import load_dotenv
from datetime import datetime, timedelta
import anthropic
import base64
import random
import os
import uuid
load_dotenv()

from atproto import Client, client_utils
from PIL import Image
from io import BytesIO
import json
from time import sleep
from pathlib import Path

def text_post(text_to_post, tags=[]):
    client = Client()
    profile = client.login(os.getenv('bluesky_login'), os.getenv('bluesky_password'))

    print('Welcome,', profile.display_name)

    text = client_utils.TextBuilder().text(text_to_post + "\n\n")
    for tag in tags:
        text.tag(f"#{tag} ", tag)
    post = client.send_post(text)

def compress_for_bluesky(image_path, max_size_mb=1, max_dimension=4096):
    # Open the image
    img = Image.open(image_path)
    
    # Convert to RGB if necessary
    if img.mode in ('RGBA', 'LA') or (img.mode == 'P' and 'transparency' in img.info):
        bg = Image.new('RGB', img.size, 'WHITE')
        bg.paste(img, mask=img.getchannel('A') if img.mode == 'RGBA' else img)
        img = bg
    
    # Resize if larger than max dimension while maintaining aspect ratio
    if max(img.size) > max_dimension:
        ratio = min(max_dimension/img.size[0], max_dimension/img.size[1])
        new_size = (int(img.size[0] * ratio), int(img.size[1] * ratio))
        img = img.resize(new_size, Image.Resampling.LANCZOS)
    
    # Start with quality 95 and decrease until file size is under limit
    quality = 95
    while True:
        output = BytesIO()
        img.save(output, format='JPEG', quality=quality)
        file_size = output.tell()
        
        if file_size <= max_size_mb * 1000 * 1000:  # Convert MB to bytes
            print(f"Final image size: {file_size/1024/1024:.2f}MB with quality {quality}")
            return output.getvalue()
        
        quality -= 5
        if quality < 5:
            raise ValueError("Cannot compress image enough to meet size requirements")     
         
def image_post(image_path, image_description, tags=[]):
    client = Client()
    client.login(os.getenv('bluesky_login'), os.getenv('bluesky_password'))

    img_data = compress_for_bluesky(image_path)
    text = client_utils.TextBuilder().text(image_description + "\n\n")  
    for tag in tags:
        text.tag(f"#{tag} ", tag)
    client.send_image(text=text, image=img_data, image_alt='Img alt')


def post_image_post(tags=[]):
    # find first image inside /images
    image_path = next(Path('image_b').glob('*.png'))
    image_path_stem = image_path.stem
    json_description_path = Path(f'image_b/{image_path_stem}.json')
    with open(json_description_path, 'r') as f:
        image_description = json.load(f)['image_description']

    print(image_path)
    print(image_description)
    image_post(image_path, image_description, tags=tags)

    # delete image
    image_path.unlink()
    json_description_path.unlink()


class ScheduledTask:
    def __init__(self, func, interval_seconds, name=None, *args, **kwargs):
        self.func = func
        self.interval = interval_seconds
        self.last_run = datetime.min
        self.name = name or func.__name__
        self.args = args
        self.kwargs = kwargs

    def should_run(self):
        return datetime.now() - self.last_run > timedelta(seconds=self.interval)

    def run(self):
        try:
            print(f"\nRunning task: {self.name}")
            self.func(*self.args, **self.kwargs)
            self.last_run = datetime.now()
        except Exception as e:
            print(f"Error in task {self.name}: {e}")
            self.last_run = datetime.now()

def main():
    # Define tasks with their intervals
    tasks = [
        ScheduledTask(
            post_image_post,
            interval_seconds=3600*7,  # 7 hour
            name="Post Image",
            tags=['aiart', 'generativeart']
        ),
    ]

    print("Starting Bluesky scheduler...")
    while True:
        try:
            for task in tasks:
                if task.should_run():
                    task.run()
            sleep(10)
            
        except KeyboardInterrupt:
            print("\nStopping scheduler...")
            break
        except Exception as e:
            print(f"Encountered error in main loop: {e}")
            print("Waiting 60 seconds before retry...")
            sleep(60)

if __name__ == '__main__':
    main()


