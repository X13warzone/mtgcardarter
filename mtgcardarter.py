#!/usr/bin/env python
"""Parses in a list of Magic the Gathering cards, using Scryfall's API for art.

Currently, it can handle text files in the format of:
amount card_name (set_code) collector_num
Which is the most common format, used for moxfield and other sites.

with a newline separating each new card. Set and collector number are optional.
"""

__author__ = "X13warzone"
__version__ = "1.2.0"
__maintainer__ = "X13warzone"
# __email__ = "<EMAIL>"
__status__ = "Development"

import time
from datetime import datetime
import tkinter as tk

import ijson
import json
from numpy import ceil
import os
from PIL import Image, ImageTk, ImageFont, ImageDraw
import re
import requests
import urllib


BASE_URL: str = "https://api.scryfall.com"
OUT_DIR: str = "mtgcardout"
IN_DIR: str = "mtgcardin"
A4_SIZE_MM: tuple[int, int] = (210, 297)
CARD_SIZE_MM: tuple[int, int] = (63, 89)
CARD_SIZE_PX: tuple[int, int] = (745, 1040)
PAGE_TOP_MARGIN_MM: float = 5
PAGE_LEFT_MARGIN_MM: float = 5
PAGE_CARD_BETWEEN_MARGIN_MM: float = 1.5
PAGE_INCLUDE_EDGE_MARGIN: bool = False

_px_per_mm: float = CARD_SIZE_PX[0] / CARD_SIZE_MM[0]


def get_valid_filename(s: str) -> str:
    s = str(s).strip().replace(" ", "_")
    return re.sub(r"(?u)[^-\w.]", '', s)


def fetch_bulk():
    url = f'{BASE_URL}/bulk-data'

    with requests.get(url) as response:
        if response.status_code == 200:
            data = response.json()
            return data
        else:
            print(f'Error could not fetch bulk: {response.status_code}')
    return None


def query_cards(query_restrictions: str, out_file, page_count = 1):
    url = f"{BASE_URL}/cards/search?page={page_count}&q={query_restrictions}+f%3Acommander&unique=cards"

    with requests.get(url) as response:
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


def search_card(name: str, set_name=None):
    if name is None:
        return None
    if set_name is not None:
        url = f"{BASE_URL}/cards/search?q={name}+e%3A{set_name}+unique%3Aprints"
    else:
        url = f"{BASE_URL}/cards/search?q={name}+unique%3Aprints"

    with requests.get(url) as response:
        if response.status_code == 200:
            data = response.json()
            return data
        else:
            print(f'Error could not search card {name}, {set_name}: {response.status_code}')
    return None


def check_dir(dir_path):
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


def _read_card_from_string(card_info: str):
    nd = card_info.split()
    d = {}

    for n in nd:
        if n == "":
            continue
        if n.isdecimal():
            if "amount" not in d and "name" not in d:
                d["amount"] = int(n)
            else:
                if "set" in d and "collector_number" not in d:
                    d["collector_number"] = n
        else:
            if "name" in d:
                if "set" in d:
                    d["collector_number"] = n.strip()
                else:
                    if n.strip().startswith("("):
                        d["set"] = n.strip(" ()")
                    else:
                        d["name"] += " " + n.strip()
            else:
                d["name"] = n
    if "amount" not in d:
        d["amount"] = 1
    return d


def read_cards_from_string(card_list: str):
    res = []
    for c in card_list.split("\n"):
        res.append(_read_card_from_string(c))
    print(res)
    return res


def read_cards_from_file(file_path):
    """
    Reads in card names from a valid text file, and saves their data in memory.
    A valid text file should be in the format of:

    - Each unique card is separated by a newline

    - AMOUNT CARD_NAME (SET_CODE) COLLECTOR_NUMBER

    Where (SET_CODE) and COLLECTOR_NUMBER are optional. If
    :param file_path: String representing the path to the text file.
    :return: list[dict[str, str]]
    """
    with open(file_path, "r") as f:
        fl = f.read().splitlines()
        res = []
        for line in fl:
            res.append(_read_card_from_string(line))
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
        img = Image.open(requests.get(url, stream=True).raw)
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


def queue_cards_to_save(cards):
    """
    Reads in a list of card arrays of the format [{"name": "", "set": "", "data": "", "collector_number": ""}, {}, {}]
    :param cards:
    :return:
    """
    image_uris = []
    for card in cards:
        newc = search_card(card.get("name", None), card.get("set", None))
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
        time.sleep(0.05)
    save_to_page([url_to_image(u) for u in image_uris] + read_cards_from_folder(IN_DIR))


def tk_trial():
    def close_window():
        root.destroy()

    def submit_decklist():
        after_read_list = decklist.get("1.0", "end")
        tk_cards = read_cards_from_string(after_read_list)
        queue_cards_to_save(tk_cards)

    root = tk.Tk()

    root.title("MTG Card Arter")
    root.configure(background="white")
    root.minsize(300, 250)
    root.maxsize(600, 600)
    root.geometry("300x300+100+100")

    tk.Label(root, text="MTG Card Proxy Sheet Maker.").pack()

    decklist = tk.Text(root, height=10, width=40)
    decklist.pack()

    submit_button = tk.Button(
        root,
        text = "Submit Decklist",
        command=submit_decklist,
        background="white",
        foreground="black",
        font=("Arial", 16),
    )
    submit_button.pack()

    exit_button = tk.Button(
        root,
        text="Quit",
        command=close_window,
        background="white",
        foreground="black",
        font=("Arial", 12),
    )
    exit_button.pack()

    root.mainloop()


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
tk_trial()

#new_art = read_card("mtgframes/1732383168025_1732383168026.png")
#create_card("white creature", new_art)

end_time = datetime.now()
print(f'Ending at {end_time}\nTime taken: {end_time - start_time}')

"""
spawn of thraxes
1 mana confluence (sld)
2 mountain
"""
