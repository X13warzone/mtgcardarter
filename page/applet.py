#!/usr/bin/env python
"""Parses in a list of Magic the Gathering cards, using Scryfall's API for art.

Currently, it can handle text files in the format of:
amount card_name (set_code) collector_num
Which is the most common format, used for moxfield and other sites.

with a newline separating each new card. Set and collector number are optional.
"""
from io import BytesIO

import unicodedata
import time
from datetime import datetime

import json
from numpy import ceil
import os
from PIL import Image, ImageFont, ImageDraw
import re
import requests
import urllib


__name__ = "MtGCardArter"
__author__ = "X13warzone"
__version__ = "1.3.1"
__maintainer__ = "X13warzone"
# __email__ = "<EMAIL>"
__status__ = "Maintenance"


"""
Can change these
"""
OUT_DIR: str = "mtgcardout"
IN_DIR: str = "mtgcardin"

PAGE_TOP_MARGIN_MM: float = 5
PAGE_LEFT_MARGIN_MM: float = 5
PAGE_CARD_BETWEEN_MARGIN_MM: float = 1.5


PAGE_INCLUDE_EDGE_MARGIN: bool = False
""" Whether the printed page should include a margin around the edge. """

"""
DO NOT CHANGE THESE
"""
BASE_URL: str = "https://api.scryfall.com"
A4_SIZE_MM: tuple[int, int] = (210, 297)
CARD_SIZE_MM: tuple[int, int] = (63, 89)
CARD_SIZE_PX: tuple[int, int] = (745, 1040)
_px_per_mm: float = CARD_SIZE_PX[0] / CARD_SIZE_MM[0]


def get_valid_filename(s: str) -> str:
    s = str(s).strip().replace(" ", "_")
    return re.sub(r"(?u)[^-\w.]", '', s)


def scryfall_request(url: str, stream: bool=False):
    """
    Does 1 Scryfall fetch request. Automatically includes required headers.
    :param url: str representing full url to search (including the base).
    :param stream: Optional param
    :return:
    """
    with requests.get(url, headers={"User-Agent": f"{__name__}/{__version__}", "Accept": "*/*"}, stream=stream) as response:
        return response


def fetch_bulk():
    """
    Fetch bulk.
    :return: Bulk data as json.
    """
    url = f'{BASE_URL}/bulk-data'

    with scryfall_request(url) as response:
        if response.status_code == 200:
            data = response.json()
            return data
        else:
            print(f'Error could not fetch bulk: {response.status_code}')
    return None


def search_bulk(card_name: str, set_name=None, collector_num=None):
    pass


def save_bulk(bulk_data: dict):
    """
    Save bulk.
    :param bulk_data: Dictionary/json format of bulk data.
    :return:
    """
    pass


def query_cards(query_restrictions: str, out_file, page_count = 1):
    url = f"{BASE_URL}/cards/search?page={page_count}&q={query_restrictions}+f%3Acommander&unique=cards"

    with scryfall_request(url) as response:
        if response.status_code == 200:
            data = response.json()
            if data:
                print(f"Total cards: {data['total_cards']}")

                for card in data["data"]:
                    out_file.write(card['name'])
                    out_file.write("\n")
                if data["has_more"]:
                    query_cards(query_restrictions, out_file, page_count + 1)
        else:
            print(f'Error could not query cards: {response.status_code}')


def search_card(name: str, set_name: str =None, collector_num: str = None):
    # Scryfall API restriction. DO NOT go lower than 0.5 seconds
    time.sleep(0.6)

    url = f"{BASE_URL}/cards/search?q="
    if name is not None:
        url += f"{name}+"
    if set_name is not None:
        url += f"set%3A{set_name}+"
    if collector_num is not None:
        url += f"cn%3A{collector_num}+"
    url = url.strip("+")

    with scryfall_request(url) as response:
        if response.status_code == 200:
            data = response.json()
            return data
        else:
            print(f'Error could not search card [({name}) ({set_name}) ({collector_num})]: {response.status_code}')
            return None
    return None


def check_dir(dir_path):
    """
    Checks if a folder, directory or path exists. Creates a directory if it doesn't already exist.
    Use before saving any created files to ensure the save location is valid.
    :param dir_path: Filepath to the directory to check.
    :return: None
    """
    if not os.path.isdir(dir_path):
        os.makedirs(dir_path)


def save_image(img: Image, file_path=OUT_DIR, img_name=None):
    """
    :param img:
    :param file_path:
    :param img_name:
    :return:
    """
    i = 0
    if img_name is None:
        fp = file_path + "\\" + "mtgcardarted.png"
        while (os.path.isfile(fp)):
            i += 1
            fp = file_path + "\\" + f"mtgcardarted ({i}).png"
        img.save(fp, "PNG")
    else:
        fp = file_path + "\\" + img_name + ".png"
        while (os.path.isfile(fp)):
            i += 1
            fp = file_path + "\\" + img_name + f" ({i}).png"
        img.save(fp, "PNG")


def read_card_from_string(card_info: str):
    """
    Parses a single line of a Moxfield-like string into card name, set, and collector number (if applicable).
    :param card_info: A single line of a Magic the Gathering card in Moxfield format.
    :return: dict() with keys ["amount", "name", "set", "collector_number"]
    """
    if card_info is None:
        return None

    # Remove foiling
    nd = card_info.removesuffix(" *F*")
    nd = nd.split()
    d = {}
    # Used to track if a card is double-sided. The back face name will be removed before parsing to Scryfall.
    # Note: Although the term "mdfc" is used here, "mdfc" within this function will refer to any double-sided card,
    # even if it's not actually an MDFC. This means transforming cards, battles, etc. are included as well.
    mdfc = False

    mdfc_pattern = r"(\d*) ?([^\(]+) ?\/ ?(.+) ?(\([A-z0-9]+\)) ?(\d*)"
    base_pattern = r"(\d*) ?([^\(]+) ?(\([A-Z0-9]+\))? ?(\d*)"

    m = re.match(mdfc_pattern, card_info)
    if m:
        m = re.split(mdfc_pattern, card_info)
        mdfc = True
    else:
        m = re.match(base_pattern, card_info)
        if m:
            m = re.split(base_pattern, card_info)
        else:
            print(f"Could not read card from string: {card_info=}!")
            return None

    for group in m:
        # If empty
        if not group:
            continue

        group = group.strip()
        group = unicodedata.normalize("NFKD", group)

        if "amount" not in d:
            if group.isnumeric():
                d["amount"] = int(group)
                continue
        if "name" not in d:
            d["name"] = group
            continue
        if mdfc:
            # MDFC or special case. Ignore second string
            mdfc = False
            continue
        if "set" not in d:
            d["set"] = group.strip(" ()")
            continue
        if "collector_number" not in d:
            d["collector_number"] = group
            continue
        print(f"Weird value in read_card_from_string: {card_info=} {group=}")
    return d


def read_cards_from_string(card_list: str):
    """
    Parses a string of cards into distinct card dictionaries.
    A valid card should be in the format of:

    - Each unique card is separated by a newline

    - AMOUNT CARD_NAME (SET_CODE) COLLECTOR_NUMBER

    Where (SET_CODE) and COLLECTOR_NUMBER are optional. If
    :param card_list: string representing a card. Different cards should be delimited by \n.
    :param progress_bar: (DEPRECATED) ttk.Progressbar to use to display progress bar
    :return: list[dict[str, str]]
    """
    res = []
    cl = card_list.split("\n")
    n = len(cl)
    for i, c in enumerate(cl):
        c = c.strip()
        if c:
            r = read_card_from_string(c)
            if r:
                res.append(r)
    return res


def read_cards_from_folder(folder_path):
    """
    Reads in all valid image files (png and jpg) from a folder, and opens them in memory.
    :param folder_path: String representing the folder path.
    :return: list[Image]
    """
    ret = []
    for f in os.listdir(folder_path):
        if f.endswith((".png", ".jpg", ".jpeg")):
            try:
                img = Image.open(folder_path + "\\" + f, 'r')
                img = img.resize(CARD_SIZE_PX)
                ret.append(img)
            except Exception as e:
                print(f"Error opening image from folder: {folder_path}/{f}\nError: {e}")
    return ret


def read_card(file_path):
    """
    Reads in a single card with the provided path and name. If the card doesn't exist, then None will be returned.
    :param file_path: File path to the image.
    :return: PIL.Image
    """
    try:
        img = Image.open(file_path, 'r')
        return img
    except Exception as e:
        print(f"Error opening single image with file path: {file_path}\nError: {e}")
        return None


def url_to_image(url):
    """
    Reads in a single url and tries to open that image.
    :param url: A string that represents a URL to an image.
    :return: Image
    """
    try:
        img = Image.open(BytesIO(scryfall_request(url).content))
        return img
    except Exception as e:
        print(f'Error loading image: {url}\nException: {e}')
    return None


def save_to_page(imgs):
    """
    Reads in a string array of image urls, and saves it to a printable image file.
    Default printing options are A4 sized paper, 5mm edge margins, and 5mm margin between cards
    :param imgs: An array of Pillow Images.
    :return: void
    """
    print(f"Saving: {len(imgs)} images received.")

    if PAGE_INCLUDE_EDGE_MARGIN:
        w = round(A4_SIZE_MM[0] * _px_per_mm)
        h = round(A4_SIZE_MM[1] * _px_per_mm)
    else:
        w = round((A4_SIZE_MM[0] - PAGE_LEFT_MARGIN_MM * 2) * _px_per_mm)
        h = round((A4_SIZE_MM[1] - PAGE_TOP_MARGIN_MM * 2) * _px_per_mm)

    """Assume center alignment to page
    Find how much space is left:
    Start with w, subtract margins, then subtract a card x, then subtract a card x and between margin until it would go negative
    """
    num_across = 1
    num_down = 1
    w_across = w - CARD_SIZE_PX[0]
    while True:
        check_next = w_across - CARD_SIZE_PX[0] - ceil(PAGE_CARD_BETWEEN_MARGIN_MM * _px_per_mm).astype(int)
        if check_next < 0:
            break
        w_across = check_next
        num_across += 1
    h_down = h - CARD_SIZE_PX[1]
    while True:
        check_next = h_down - CARD_SIZE_PX[1] - ceil(PAGE_CARD_BETWEEN_MARGIN_MM * _px_per_mm).astype(int)
        if check_next < 0:
            break
        h_down = check_next
        num_down += 1
    reset_left = w_across // 2
    reset_top = h_down // 2

    final_image = Image.new('RGBA', (w, h), color=(255, 255, 255, 0))

    # Use numpy.ceil here, since we don't want to risk having less margin, such as for printing.
    # Note that (x, y) refers to the top left corner of where the next image should be pasted
    x: int = reset_left
    y: int = reset_top
    sheet_count = 1
    temp_across = 0
    temp_down = 0

    for img in imgs:
        final_image.paste(img, (x, y))

        x += ceil(PAGE_CARD_BETWEEN_MARGIN_MM * _px_per_mm).astype(int) + CARD_SIZE_PX[0]
        temp_across += 1

        if temp_across >= num_across:
            x = reset_left
            y += ceil(PAGE_CARD_BETWEEN_MARGIN_MM * _px_per_mm).astype(int) + CARD_SIZE_PX[1]
            temp_across = 0
            temp_down += 1

            if temp_down >= num_down:
                file_path = OUT_DIR + "\\" + f"print_sheet{sheet_count}.png"
                while os.path.isfile(file_path):
                    sheet_count += 1
                    file_path = OUT_DIR + "\\" + f"print_sheet{sheet_count}.png"
                if not os.path.isfile(file_path):
                    final_image.save(file_path, "PNG")
                    sheet_count += 1
                    y = reset_top
                    temp_down = 0
                    final_image = Image.new('RGBA', (w, h), color=(255, 255, 255, 0))

    # If we have "leftover" cards that don't fill up a page, we should save what we have
    if temp_across != 0 or temp_down != 0:
        file_path = OUT_DIR + "\\" + f"print_sheet{sheet_count}.png"
        while os.path.isfile(file_path):
            sheet_count += 1
            file_path = OUT_DIR + "\\" + f"print_sheet{sheet_count}.png"
        if not os.path.isfile(file_path):
            final_image.save(file_path, "PNG")


def cards_to_images(cards):
    """
    Reads in a list of card arrays of the format [{"name": "", "set": "", "data": "", "collector_number": ""}, {}, {}]
    :param cards:
    :return:
    """
    image_uris = []
    for card in cards:
        newc = search_card(card.get("name", None), card.get("set", None), card.get("collector_number", None))
        if newc is not None:
            for c in newc["data"]:
                if "collector_number" in card and card["collector_number"] != c["collector_number"]:
                    continue
                if "promo" in card and card["promo"] != c["promo"]:
                    continue
                if "image_uris" in c:
                    for i in range(card["amount"]):
                        image_uris.append(c["image_uris"]["png"])
                    break
                elif "card_faces" in c:
                    for i in range(card["amount"]):
                        for face in c["card_faces"]:
                            image_uris.append(face["image_uris"]["png"])
                    break
                else:
                    print(f"Couldn't find a strange card: {c}")
    return [url_to_image(u) for u in image_uris] + read_cards_from_folder(IN_DIR)


def save_images(images):
    save_to_page(images)


def check_card_list(cards: list) -> bool:
    """
    Checks a list of pre-formatted cards for validity.
    Returns true if all cards searched had at least one positive result.
    Returns false if one or more cards searched had a negative result.
    :param cards: [{"amount": 0, "name": "", "set": "", "collector_number": ""}, {}, {}]
    :param progress_val: ttk.Progressbar
    :return: bool
    """
    n = len(cards)
    for i, c in enumerate(cards):
        if search_card(c.get("name", None), c.get("set", None), c.get("collector_num", None)) is None:
            return False

    return True


def process(image_bytes, text):
    check_card_list(read_cards_from_string(text))
    cards = read_cards_from_string(text)
    ims = cards_to_images(cards)
    return ims


start_time = datetime.now()
print(f'Starting at {start_time}')
# =====================================
# Main
# =====================================
# Search based on oracle text/restrictions. Comment/Uncomment based on usage.
# Change this `search_query` line by copying the scryfall link for everything after `search?q=`
#search_query = "o%3A%22token%22+o%3A%22artifact%22+c%3C%3Dtemur+legal%3Acommander"
#out_file = open(f"{OUT_DIR}/out_file.txt", "a")
#query_cards(search_query, out_file)

check_dir(OUT_DIR)

#my_cards = read_cards_from_file("mtgc.txt")
#queue_cards_to_save(my_cards)

# =====================================
# End of main
# =====================================

#new_art = read_card("mtgframes/1732383168025_1732383168026.png")
#create_card("white creature", new_art)

end_time = datetime.now()
print(f'Ending at {end_time}\nTime taken: {end_time - start_time}')
