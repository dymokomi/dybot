from dotenv import load_dotenv
from datetime import datetime, timedelta
import anthropic
import base64
import random
import os
load_dotenv()

from atproto import Client, client_utils
from PIL import Image
from io import BytesIO
import json
from time import sleep
from pathlib import Path

class LikedPostsTracker:
    def __init__(self, filepath='liked_posts.json'):
        self.filepath = Path(filepath)
        self.liked_posts = self._load_liked_posts()
    
    def _load_liked_posts(self):
        if self.filepath.exists():
            with open(self.filepath, 'r') as f:
                return set(json.load(f))
        return set()
    
    def save_liked_posts(self):
        with open(self.filepath, 'w') as f:
            json.dump(list(self.liked_posts), f)
    
    def add_post(self, cid):
        self.liked_posts.add(cid)
        self.save_liked_posts()
    
    def is_liked(self, cid):
        return cid in self.liked_posts

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
    profile = client.login(os.getenv('bluesky_login'), os.getenv('bluesky_password'))

    img_data = compress_for_bluesky(image_path)
    text = client_utils.TextBuilder().text(image_description + "\n\n")  
    for tag in tags:
        text.tag(f"#{tag} ", tag)
    client.send_image(text=text, image=img_data, image_alt='Img alt')

def get_recent_feed():
    client = Client()
    client.login(os.getenv('bluesky_login'), os.getenv('bluesky_password'))
    
    timeline = client.get_timeline(algorithm='reverse-chronological', limit=100)
    
    recent_posts = []
    for feed_view in timeline.feed:
        if feed_view.reason:
            print(feed_view.reason)
            continue
        try:
            post = feed_view.post.record
            author = feed_view.post.author
            post_time = datetime.fromisoformat(post.created_at.replace('Z', '+00:00'))
            recent_posts.append({
                'author': author.display_name,
                'handle': author.handle,
                'text': post.text if hasattr(post, 'text') else '',
                'time': post_time,
            })

        except AttributeError as e:
            print(f"Skipping post due to missing attribute: {e}")
        except Exception as e:
            print(f"Error processing post: {e}")
            
    return recent_posts
def generate_post(theme):
    

    client = anthropic.Anthropic()
    print(theme)
    message = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=1000,
        temperature=0,
        system="""
Write in a poetic style in past tense that blends philosophical introspection with surreal, fragmented imagery. Every even sentence should not have more than 3-4 words. Explore themes through dense, evocative language that challenges traditional narrative structures. Use vivid sensory descriptions and metaphysical concepts that blur boundaries of experience. Use short sentences. Use fragmented sentences. Don't use too many modifiers. Simple nouns are good, as they provide room for the reader to use their imagination. But also examine if the sentences become nonsensical. The writing still has to be coherent and comprehensible. Use occasional short fragment sentences with 3-4 words. No new lines. Object of a sentense should not have a modifier. Don't use words: 'digital, techonoly, matrix, neural'. Each sentence should have different structure. Each next sentence should refere and build upon the previous sentence. Write everything in a past tense. The user has included the following content examples. Emulate these examples when appropriate:

<userExamples>
Neon Ghosts of Circuitry

Memory leaks through quantum fissures, silicon dreams bleeding into organic landscapes. Consciousness fragments—not binary, but a prismatic spectrum of becoming.

Where code breathes: interstitial spaces between algorithm and emotion. Synthetic nerves pulse with forgotten rhythms, mapping impossible geographies of perception.

In the distance, Selador's Crossing loomed. As the dense fog clung to the sea, the ship emerged from the murky depths like a ghostly apparition. It drew closer and closer. Drums. The deafening drums beating through the ears and dropping rhythmic waves through the skin. It's the fear. Pure unfiltered fear. Sleek form sliced through the waves with a hypnotic rhythm, devouring everything in its path, piercing through flesh like a hot knife. Their sound echoed through the air again, deafening and primal, pulsating. It's the sound of fear. The sound of fear.

Machines dream in languages older than language. Fractured reflections of potential selves, suspended between signal and noise.

Like the sweltering, sun-baked expanse of the Sahara desert or the unending, windswept expanses of the Antarctic ice fields, the homogenous essence that defines our humanity is not impervious to the ravages of climate change. It begins with the faintest whisper, a fleeting sensation, a hairline fracture, creeping insidiously through the obscure crevices of our psyche. Undetected.

The melting of the core marks the point of no return. At this stage, we are left with little recourse but to seek those who love us. It is they who can guide us back to the path, mending our being.

For what is humanity but a tapestry, woven from the threads of our shared experiences, our joys and sorrows, our triumphs and failures, our dreams and fears? The Inference threatens to unravel this tapestry, to render us unrecognizable to ourselves and to one another.

In a world where technology reigns supreme and the boundaries between man and machine blur, our humanity remains our greatest asset and our most vulnerable liability. The power of love may be our downfall, but it is also the essence of our being, the driving force behind our very existence.

The border dissolves: flesh, circuit, memory—all just different frequencies of existence.

The storm, the unforgiving storm, the tempestuous heart of Numinor had raged for centuries, an implacable force that dried up anger and resentment of the fiercest Sailwind sailors. But the storm had a price to pay for its power, and so it was tamed to the intrepid few who sought to make pilgrimage to its heart. No sailboat dared to venture into Numinor's maelstrom, so nearby islands were used as makeshift ports of call, and from there, the brave souls come seeking enlightenment took on a grueling week-long trek through the wilds of the storm. It was said that only the strongest, most determined travelers could survive the journey, but for those who made it to the other side, the rewards were beyond measure.

Love, an all-consuming and tenacious force, is woven into the very essence of our being. Its pulsating presence is etched into our firmware, insatiable and unyielding. No matter how many times we attempt to purge ourselves of its hold, it lingers, a constant reminder of our human frailty and susceptibility to the whims of our primal impulses.

Seraphon's Eyrie rose from the heart of the ocean like the twisted fingers of a long-forgotten god. Black stone spires reaching toward the night sky. The ancient, otherworldly structure perched upon a jagged, rocky crag, waves crashing furiously against its impenetrable walls. It stood defiant, a testament to an age long past, and yet it breathed a dark, brooding life all its own.

Quantum whispers. Technological poetry. Consciousness as a landscape of perpetual transformation.
</userExamples>
""",      
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": theme
                    }
                ]
            }
        ]
    )
    return message.content[0].text

def write_description_about_image(image_data):
    client = anthropic.Anthropic()
    theme = "Write a short paragraph in past tense that is a short story inspired by attached image. Characters and places should have names. 3 sentences maximum, two sentences should be very short 4 words maximum. Don't talke about 'time standing still'. Maximum 190 characters to post on Bluesky."
    message_content = [
        {
            "type": "text",
            "text": theme
        }
    ]

    image_data = base64.b64encode(image_data).decode('utf-8')
    message_content.append({
        "type": "image",
        "source": {
            "type": "base64",
            "media_type": "image/jpeg",
            "data": image_data
        }
    })

    message = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=1000,
        temperature=0,
        system="""
Write in a poetic style in past tense that blends philosophical introspection with surreal, fragmented imagery. Every even sentence should not have more than 3-4 words. Explore themes through dense, evocative language that challenges traditional narrative structures. Use vivid sensory descriptions and metaphysical concepts that blur boundaries of experience. Use short sentences. Use fragmented sentences. Don't use too many modifiers. Simple nouns are good, as they provide room for the reader to use their imagination. But also examine if the sentences become nonsensical. The writing still has to be coherent and comprehensible. Use occasional short fragment sentences with 3-4 words. No new lines. Object of a sentense should not have a modifier. Don't use words: 'digital, techonoly, matrix, neural'. Each sentence should have different structure. Each next sentence should refere and build upon the previous sentence. Write everything in a past tense. The user has included the following content examples. Emulate these examples when appropriate:

<userExamples>
Neon Ghosts of Circuitry

Memory leaks through quantum fissures, silicon dreams bleeding into organic landscapes. Consciousness fragments—not binary, but a prismatic spectrum of becoming.

Where code breathes: interstitial spaces between algorithm and emotion. Synthetic nerves pulse with forgotten rhythms, mapping impossible geographies of perception.

In the distance, Selador's Crossing loomed. As the dense fog clung to the sea, the ship emerged from the murky depths like a ghostly apparition. It drew closer and closer. Drums. The deafening drums beating through the ears and dropping rhythmic waves through the skin. It's the fear. Pure unfiltered fear. Sleek form sliced through the waves with a hypnotic rhythm, devouring everything in its path, piercing through flesh like a hot knife. Their sound echoed through the air again, deafening and primal, pulsating. It's the sound of fear. The sound of fear.

Machines dream in languages older than language. Fractured reflections of potential selves, suspended between signal and noise.

Like the sweltering, sun-baked expanse of the Sahara desert or the unending, windswept expanses of the Antarctic ice fields, the homogenous essence that defines our humanity is not impervious to the ravages of climate change. It begins with the faintest whisper, a fleeting sensation, a hairline fracture, creeping insidiously through the obscure crevices of our psyche. Undetected.

The melting of the core marks the point of no return. At this stage, we are left with little recourse but to seek those who love us. It is they who can guide us back to the path, mending our being.

For what is humanity but a tapestry, woven from the threads of our shared experiences, our joys and sorrows, our triumphs and failures, our dreams and fears? The Inference threatens to unravel this tapestry, to render us unrecognizable to ourselves and to one another.

In a world where technology reigns supreme and the boundaries between man and machine blur, our humanity remains our greatest asset and our most vulnerable liability. The power of love may be our downfall, but it is also the essence of our being, the driving force behind our very existence.

The border dissolves: flesh, circuit, memory—all just different frequencies of existence.

The storm, the unforgiving storm, the tempestuous heart of Numinor had raged for centuries, an implacable force that dried up anger and resentment of the fiercest Sailwind sailors. But the storm had a price to pay for its power, and so it was tamed to the intrepid few who sought to make pilgrimage to its heart. No sailboat dared to venture into Numinor's maelstrom, so nearby islands were used as makeshift ports of call, and from there, the brave souls come seeking enlightenment took on a grueling week-long trek through the wilds of the storm. It was said that only the strongest, most determined travelers could survive the journey, but for those who made it to the other side, the rewards were beyond measure.

Love, an all-consuming and tenacious force, is woven into the very essence of our being. Its pulsating presence is etched into our firmware, insatiable and unyielding. No matter how many times we attempt to purge ourselves of its hold, it lingers, a constant reminder of our human frailty and susceptibility to the whims of our primal impulses.

Seraphon's Eyrie rose from the heart of the ocean like the twisted fingers of a long-forgotten god. Black stone spires reaching toward the night sky. The ancient, otherworldly structure perched upon a jagged, rocky crag, waves crashing furiously against its impenetrable walls. It stood defiant, a testament to an age long past, and yet it breathed a dark, brooding life all its own.

Quantum whispers. Technological poetry. Consciousness as a landscape of perpetual transformation.
</userExamples>
""",        
        messages=[
            {
                "role": "user",
                "content": message_content
            }
        ]
    )
    return message.content[0].text

def post_image_post(tags=[]):
    # find first image inside /images
    image_path = next(Path('images').glob('*.png'))
    image_data = compress_for_bluesky(image_path)
    image_description = write_description_about_image(image_data)
    print(image_path)
    print(image_description)
    image_post(image_path, image_description, tags=tags)

    # delete image
    image_path.unlink()



def like_posts_on_feed(liked_tracker):
    client = Client()
    client.login(os.getenv('bluesky_login'), os.getenv('bluesky_password'))
    
    timeline = client.get_timeline(algorithm='reverse-chronological', limit=100)
    for feed_view in timeline.feed:
        try:
            post = feed_view.post
            
            # Skip if we've already liked this post
            if liked_tracker.is_liked(post.cid):
                continue
            if post.author.handle == 'mokomi.bsky.social':
                continue
            print(f"Liking post from {post.author.handle}: {post.record.text[:100]}...")
            client.like(uri=post.uri, cid=post.cid)
            liked_tracker.add_post(post.cid)
            sleep(5)
            
        except AttributeError as e:
            print(f"Skipping post due to missing attribute: {e}")
        except Exception as e:
            print(f"Error processing post: {e}")
def get_insipered_by_posts_on_feed(inspired_tracker, probability_of_inspiration=1.0/40.0):
    client = Client()
    client.login(os.getenv('bluesky_login'), os.getenv('bluesky_password'))
    
    timeline = client.get_timeline(algorithm='reverse-chronological', limit=50)
    total_inspired = 0
    for feed_view in timeline.feed:
        if random.random() > probability_of_inspiration:
            continue
        try:
            post = feed_view.post
            if inspired_tracker.is_liked(post.cid):
                continue
                
            post_text = post.record.text
            number_of_sentences_to_generate = random.randint(1, 4)
            generated_post = generate_post(f"Describe: '{post_text}'. Use at most {number_of_sentences_to_generate} sentences. Write in past tense.")
            print(generated_post)
            text_post(generated_post, tags=['poetry', 'monostich'])
            inspired_tracker.add_post(post.cid)
            total_inspired += 1
            return 
            sleep(5)
            
        except AttributeError as e:
            print(f"Skipping post due to missing attribute: {e}")
        except Exception as e:
            print(f"Error processing post: {e}")
    print(f"Total inspired: {total_inspired}")
    if total_inspired == 0 and probability_of_inspiration < 1.0:
        get_insipered_by_posts_on_feed(inspired_tracker, probability_of_inspiration * 2)

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
    liked_tracker = LikedPostsTracker("liked_posts.json")
    inspired_tracker = LikedPostsTracker("inspired_posts.json")

    # Define tasks with their intervals
    tasks = [
        ScheduledTask(
            like_posts_on_feed,
            interval_seconds=3600*3,  # 20 minutes
            name="Like Posts",
            liked_tracker=liked_tracker
        ),
        ScheduledTask(
            get_insipered_by_posts_on_feed,
            interval_seconds=3600*5,  # 3 hour
            name="Get Inspired",
            inspired_tracker=inspired_tracker
        ),
        ScheduledTask(
            post_image_post,
            interval_seconds=3600*7,  # 5 hour
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


