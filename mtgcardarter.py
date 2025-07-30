#!/usr/bin/env python
"""Parses in a list of Magic the Gathering cards, using Scryfall's API for art.

Currently, it can handle text files in the format of:
amount card_name (set_code) collector_num

with a newline separating each new card. Set and collector number are optional.
"""

from datetime import datetime
from tkinter import Tk, ttk

import ijson
import json
from numpy import ceil
import os
from PIL import Image, ImageTk, ImageFont, ImageDraw
import re
import requests
import urllib


__author__ = "X13warzone"
__version__ = "1.0.0"
__maintainer__ = "X13warzone"
# __email__ = "<EMAIL>"
__status__ = "Development"

BASE_URL = "https://api.scryfall.com"
OUT_DIR = "mtgcardout"
IN_DIR = "mtgcardin"
A4_SIZE_MM: tuple[int, int] = (210, 297)
CARD_SIZE_MM: tuple[int, int] = (63, 89)
CARD_SIZE_PX: tuple[int, int] = (745, 1040)
PAGE_TOP_MARGIN_MM = 5
PAGE_LEFT_MARGIN_MM = 5
PAGE_CARD_BETWEEN_MARGIN_MM = 1.5
PAGE_INCLUDE_EDGE_MARGIN = False

_px_per_mm: float = CARD_SIZE_PX[0] / CARD_SIZE_MM[0]


def get_valid_filename(s: str):
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


def search_card(name, set_name=None):
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


def parse_bulk(card_list):
    bulk_data = fetch_bulk()
    f = urllib.request.urlopen(bulk_data["data"][3]["download_uri"])
    objects = ijson.items(f, "item")

    cards = (o for o in objects if
             (o["name"].lower() in [s["name"] for s in card_list])
             and o["set"]
             and o["lang"] == "en"
             )

    for card in cards:
        target_path = f"{OUT_DIR}" + "\\" + get_valid_filename(card["name"])
        if "image_uris" in card:
            file_path = target_path + "\\" + {card["set"]} + "_" + {card["collector_number"]} + ".png"
            save_image(card["image_uris"]["png"], file_path)


def create_card(card_frame: str, card_art, card_name = "Nobody", card_cost = "{0}", card_set: str = "sld", card_artist: str="X13warzone", card_num = "1/500", card_layout: str="normal", card_power: str=None, card_toughness=None):
    """
    Creates a new card with the given card art, name, cost, P/T (IA), type, border, etc.
    :param card_frame: A string out of a selection of options.
    :param card_art: A Pillow Image object. The art should have the same ratio as a card (63 x 89), else it may be stretched/cropped.
    :param card_name: A string representing the name of the card.
    :param card_cost: A string representing the cost of the card, in the format of {n}{m}{p}. Each n, m, or p may be a number (for colorless), X, one of WUBRG with an optional p before it (for phyrexian mana), or two of WUBRG (for split mana).
    :param card_layout: A string representing the layout of the card. Examples are: normal; transform; saga; adventure etc.
    :param card_power: Strings representing the power/toughness of the card. Can also be set to *, or *+1 or similar.
    :return: PIL.Image
    """
    img = Image.new("RGBA", CARD_SIZE_PX, (255, 255, 255, 0))

    # For now, this is just the center. Todo: Add functionality for a translation shift
    if card_art.size[0] / card_art.size[1] < CARD_SIZE_PX[0] / CARD_SIZE_PX[1]:
        # Crop the top and bottom
        temp_num = card_art.size[0] * CARD_SIZE_PX[1] // CARD_SIZE_PX[0]
        cropped_art = card_art.crop((
            0,
            (card_art.size[1] - temp_num) // 2,
            card_art.size[0],
            (card_art.size[1] + temp_num) // 2
        ))
    else:
        # Crop left and right
        temp_num = card_art.size[1] * CARD_SIZE_PX[0] // CARD_SIZE_PX[1]
        cropped_art = card_art.crop((
            (card_art.size[0] - temp_num) // 2,
            0,
            (card_art.size[0] + temp_num) // 2,
            card_art.size[1]
        ))
    cropped_art = cropped_art.resize(CARD_SIZE_PX)

    match card_frame:
        case "white creature":
            new_frame = read_card("mtgframes/white creature frame.png")
    stretched_frame = new_frame.resize(CARD_SIZE_PX)

    stretched_art = card_art.resize(CARD_SIZE_PX)

    img.paste(cropped_art, (0, 0))
    img.paste(stretched_frame, (0, 0), mask=stretched_frame)

    save_image(stretched_frame)

    # Name of card
    font = ImageFont.truetype("mtgfont/typeface-beleren-bold-master/Beleren2016-Bold.ttf", 30)
    text = ImageDraw.Draw(img)
    text.text((64, 64), card_name, font=font, fill=(0, 0, 0, 255))

    

    # Insert other stuff here. Final step is make the corners transparent again.
    # Top side. For loop x then y means we do each column, going down, then go to the next col and go all the way down.
    for x in range(stretched_art.size[0]):
        for y in range(stretched_art.size[1]):
            # If it's transparent, it should be put as transparent
            # If it's not transparent, check if it's black. If it's black, break
            # If it's not black, put as transparent
            frame_px = stretched_frame.getpixel((x, y))
            if frame_px[3] != 0:
                if frame_px[0:3] == (0, 0, 0) and frame_px[3] == 255 and stretched_frame.getpixel((x, y + 2))[0:3] == (0, 0, 0):
                    break
            img.putpixel((x, y), (0, 0, 0, frame_px[3]))

        # Bottom side
        for y in range(stretched_art.size[1] - 1, -1, -1):
            frame_px = stretched_frame.getpixel((x, y))
            if frame_px[3] != 0:
                if frame_px[0:3] == (0, 0, 0) and frame_px[3] == 255 and stretched_frame.getpixel((x, y - 2))[0:3] == (0, 0, 0):
                    break
            img.putpixel((x, y), (0, 0, 0, 0))

    save_image(img)


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
            nd = re.split(r' \(|\)|\*F\*', line)
            d = {}
            if nd[0].startswith("//"):
                continue

            for n in nd:
                if n == "":
                    continue
                if "name" in d:
                    if "set" in d:
                        d["collector_number"] = n.strip()
                    else:
                        if len(n) > 3 and n.startswith(("p", "P")):
                            d["promo"] = True
                        d["set"] = n
                else:
                    count = 0
                    new_name = ""
                    for i, ch in enumerate(n):
                        if ch.isspace():
                            new_name = n[i+1:len(n)]
                            break
                        elif ch.isdigit():
                            count *= 10
                            count += ord(ch) - ord('0')
                        else:
                            count = 1
                            break

                    d["name"] = new_name
                    d["amount"] = max(count, 1)
            res.append(d)
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
    print(len(imgs))

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
        if not os.path.isfile(file_path):
            final_image.save(file_path, "PNG")


def queue_cards_to_save(cards):
    for card in cards:
        newc = None
        if "set" in card:
            newc = search_card(card["name"], card["set"])
        else:
            newc = search_card(card["name"])
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
    save_to_page([url_to_image(u) for u in image_uris] + read_cards_from_folder(IN_DIR))


def tk_trial():
    root = Tk()
    frm = ttk.Frame(root, padding=10)
    frm.grid()
    ImageTk.PhotoImage()
    ttk.Label(frm, text="Hello world!").grid(column=0, row=0)
    ttk.Button(frm, text="Quit", command=root.destroy).grid(column=1, row=0)
    root.mainloop()


start_time = datetime.now()
print(f'Starting at {start_time}')
# =====================================
# Main
# =====================================
"""
Editable list! Can handle card names, flavor names (alt prints),
sets, collector numbers
"""
my_cards = read_cards_from_file("mtgc.txt")
"""my_cards = [
    {"name": "underworld breach", "set": "spg"},
    {"name": "esper sentinel"},
    {"name": "chatterfang"},
    {"name": "volcanic island"},
    {"name": "sink into stup"},
    {"name": "etali, primal conq"},
    {"name": "arcee"}
]"""


# =====================================
# End of main
# =====================================
check_dir(OUT_DIR)
image_uris = []

queue_cards_to_save(my_cards)

#tk_trial()

#new_art = read_card("mtgframes/1732383168025_1732383168026.png")
#create_card("white creature", new_art)

end_time = datetime.now()
print(f'Ending at {end_time}\nTime taken: {end_time - start_time}')
