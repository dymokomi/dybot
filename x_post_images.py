from dotenv import load_dotenv
from pathlib import Path
from PIL import Image
from io import BytesIO
import os, json, random
from scheduler import ScheduledTask
from time import sleep
import tweepy
from claude import Claude
load_dotenv()

BEARER_TOKEN = os.getenv('X_BEARER_TOKEN')
API_KEY = os.getenv('X_API_KEY')
API_SECRET = os.getenv('X_API_KEY_SECRET')
ACCESS_TOKEN = os.getenv('X_ACCESS_TOKEN')
ACCESS_TOKEN_SECRET = os.getenv('X_ACCESS_TOKEN_SECRET')


def compress_for_x(image_path, max_size_mb=0.68, max_dimension=4096):
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
            # Save compressed image to a temporary file
            temp_path = Path('temp_compressed.jpg')
            with open(temp_path, 'wb') as f:
                f.write(output.getvalue())
            print(f"Saved compressed image to: {temp_path.absolute()}")
            return temp_path.absolute()
        
        quality -= 5
        if quality < 5:
            raise ValueError("Cannot compress image enough to meet size requirements")  
def post_text_to_twitter(tweet_text):
    # Authenticate with Twitter
    client = tweepy.Client(
        bearer_token=BEARER_TOKEN,
        consumer_key=API_KEY, 
        consumer_secret=API_SECRET,
        access_token=ACCESS_TOKEN, 
        access_token_secret=ACCESS_TOKEN_SECRET
    )

    print(f"Posting tweet to X")
    client.create_tweet(text=tweet_text)
    
    print("Tweet posted successfully!")
def post_image_to_twitter(image_path, tweet_text):

    # Authenticate with Twitter
    client = tweepy.Client(
        bearer_token=BEARER_TOKEN,
        consumer_key=API_KEY, 
        consumer_secret=API_SECRET,
        access_token=ACCESS_TOKEN, 
        access_token_secret=ACCESS_TOKEN_SECRET
    )
    
    # Create API v1.1 object for media upload (still required for v2)
    auth = tweepy.OAuth1UserHandler(
        API_KEY, 
        API_SECRET, 
        ACCESS_TOKEN, 
        ACCESS_TOKEN_SECRET
    )
    api = tweepy.API(auth)
    
    # Upload the image
    print(f"Compressing image for X")
    compressed_image_path = compress_for_x(image_path)
    print(f"Uploading image to X")
    media = api.media_upload(filename=compressed_image_path)
    
    # Post tweet with media
    print(f"Posting tweet to X")
    client.create_tweet(text=tweet_text, media_ids=[media.media_id])
    
    print("Tweet posted successfully!")



def post_image_on_x():
    try:
        print("Trying to post image to X")
        image_path = next(Path('image_x').glob('*.png'))
        image_path_stem = image_path.stem
        json_description_path = Path(f'image_x/{image_path_stem}.json')
        with open(json_description_path, 'r') as f:
            image_description = json.load(f)['image_description']
        print(f"Posting image to X: {image_path}")
        post_image_to_twitter(image_path, image_description)

        # delete the image
        image_path.unlink()
        json_description_path.unlink()

    except Exception as e:
        print(f"Error posting image: {str(e)}")

# Example usage
if __name__ == "__main__":
    tasks = [
        ScheduledTask(
            post_image_on_x,
            interval_seconds=3600*7,  # Once every 7 hours
            name="Post image on X"
        ),

    ]
    print("Starting X scheduler...")
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
