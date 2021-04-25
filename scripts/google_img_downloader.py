
import os
import io
import time
import asyncio
import hashlib
import requests

from PIL import Image
from selenium import webdriver

DRIVER_PATH = '/home/vitor/git/screenshot-project/chromedriver'


async def fetch_image_urls(query: str, max_links_to_fetch: int, wd: webdriver, sleep_between_interactions: int = 1):
    def scroll_to_end(windows_down):
        windows_down.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(sleep_between_interactions)

    search_url = "https://www.google.com/search?safe=off&site=&tbm=isch&source=hp&q={q}&oq={q}&gs_l=img"

    wd.get(search_url.format(q=query))

    image_urls = set()
    image_count = 0
    results_start = 0
    while image_count < max_links_to_fetch:
        scroll_to_end(wd)
        thumbnail_results = wd.find_elements_by_css_selector("img.Q4LuWd")
        number_results = len(thumbnail_results)

        print(f"Found: {number_results} search results. Extracting links from {results_start}:{number_results}")

        for img in thumbnail_results[results_start:number_results]:
            # try to click every thumbnail such that we can get the real image behind it
            try:
                img.click()
                time.sleep(sleep_between_interactions)
            except Exception as error:
                print(error)
                continue

            # extract image urls
            actual_images = wd.find_elements_by_css_selector('img.n3VNCb')
            for actual_image in actual_images:
                if actual_image.get_attribute('src') and 'http' in actual_image.get_attribute('src'):
                    image_urls.add(actual_image.get_attribute('src'))

            image_count = len(image_urls)

            if len(image_urls) >= max_links_to_fetch:
                print(f"Found: {len(image_urls)} image links, done!")
                break
        else:
            print("Found:", len(image_urls), "image links, looking for more ...")
            time.sleep(30)
            load_more_button = wd.find_element_by_css_selector(".mye4qd")
            if load_more_button:
                wd.execute_script("document.querySelector('.mye4qd').click();")

        results_start = len(thumbnail_results)

    return image_urls


async def persist_image(folder_path: str, file_name: str, url: str):
    image_content = None
    try:
        image_content = requests.get(url).content

    except Exception as e:
        print(f"ERROR - Could not download {url} - {e}")

    try:
        if image_content:
            image_file = io.BytesIO(image_content)
            image = Image.open(image_file).convert('RGB')
            folder_path = os.path.join(folder_path, file_name)
            if os.path.exists(folder_path):
                file_path = os.path.join(folder_path, hashlib.sha1(image_content).hexdigest()[:10] + '.jpg')
            else:
                os.mkdir(folder_path)
                file_path = os.path.join(folder_path, hashlib.sha1(image_content).hexdigest()[:10] + '.jpg')
            with open(file_path, 'wb') as f:
                image.save(f, "JPEG", quality=85)
            print(f"SUCCESS - saved {url} - as {file_path}")
    except Exception as error:
        print(f"ERROR - Could not save {url} - {error}")


async def start():
    max_links_to_fetch = 20
    sleep_seconds = 2

    images_path = '/home/vitor/git/test'

    wd = webdriver.Chrome(executable_path=DRIVER_PATH)
    queries = ["walmart phishing"]
    for query in queries:
        print(f" Searching ... {query}")
        wd.get('https://google.com')
        search_box = wd.find_element_by_css_selector('input.gLFyf')
        search_box.send_keys(query)
        links = await fetch_image_urls(query, max_links_to_fetch, wd, sleep_between_interactions=sleep_seconds)

        for i in links:
            await persist_image(images_path, query, i)
    wd.quit()

if __name__ == '__main__':
    asyncio.run(start())