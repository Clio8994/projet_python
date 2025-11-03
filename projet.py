import os
import re
import requests
import pandas as pd
from scrapy import Selector
import argparse

url = "https://books.toscrape.com/"

def create_output_dirs():
    OUTPUT_DIR = os.path.join(".", "output")
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    RESULT_DIR = os.path.join(OUTPUT_DIR, "csv")
    IMAGES_DIR = os.path.join(OUTPUT_DIR, "images")

    os.makedirs(RESULT_DIR, exist_ok=True)
    os.makedirs(IMAGES_DIR, exist_ok=True)
    
    return IMAGES_DIR

def boucle_scrap(categories, cat_name, images_dir):
   for idx, n in enumerate(categories):
    cat = cat_name[idx]
    url_cat = url + n
    page_url = url_cat
    data = []
    cat_img_dir = os.path.join(images_dir, cat.replace(" ", "_"))
    os.makedirs(cat_img_dir, exist_ok=True)

    while True:
        response = requests.get(page_url)
        sel_page = Selector(text=response.text)
        get_all_book = sel_page.css("h3 a::attr(href)").getall()

        for i in get_all_book:
            url_book = url + i.replace("../../../", "catalogue/")
            resp_book = requests.get(url_book)
            sel = Selector(text=resp_book.text)
            price = sel.css("p.price_color::text").get()
            titre = sel.css("h1::text").get()
            stock = sel.css("p.instock.availability::text").getall()[1].strip()
            note = sel.css("p.star-rating::attr(class)").get().split()[-1]
            upc = sel.css("table td::text").getall()[0]
            img_path = sel.css("img::attr(src)").get()
            img_path = url + img_path.replace("../../", "")
            rep_img = requests.get(img_path)
            cat_clean = cat.replace(" ", "_")
            titre_propre = re.sub(r'[<>:"/\\|?*]', "", titre).replace(" ", "_")
            with open(f"{images_dir}/{cat_clean}/{titre_propre}.jpg", "wb") as f:
                f.write(rep_img.content)
            data.append(
                {
                    "title": titre,
                    "price": price,
                    "stock": stock,
                    "note": note,
                    "upc": upc,
                    "image_url": img_path,
                    "category": cat_clean,
                }
            )
        next_href = sel_page.css("li.next a::attr(href)").get()
        if next_href:
            page_url = page_url.rsplit("/", 1)[0] + "/" + next_href
        else:
            break

    df = pd.DataFrame(data)
    safe_name = cat.replace(" ", "_")
    csv_path = f"output/csv/{safe_name}.csv"
    df.to_csv(csv_path, index=False, sep=";")

def scrap_all(images_dir):
    response = requests.get(url)
    sel = Selector(text=response.text)
    categories = sel.css("ul.nav li a::attr(href)").getall()[1:]
    cat_name_raw = sel.css("ul.nav li a::text").getall()[1:]
    cat_name = [s.strip() for s in cat_name_raw if s.strip()]

    boucle_scrap(categories, cat_name, images_dir)

def scrap_category(category, images_dir):
    response = requests.get(url)
    sel = Selector(text=response.text)
    categories = sel.css("ul.nav li a::attr(href)").getall()[1:]
    cat_name_raw = sel.css("ul.nav li a::text").getall()[1:]
    cat_name = [s.strip() for s in cat_name_raw if s.strip()]
    
    if category not in cat_name:
        print(f"Catégorie '{category}' introuvable!")
        return
        
    idx = cat_name.index(category)
    boucle_scrap([categories[idx]], [category], images_dir)


def main():
    parser = argparse.ArgumentParser(description="scraper livre")
    parser.add_argument("--categories", nargs="+", help="Donner une categorie ou all si vous souhaitez tout scrapper") 
    parser.add_argument("--output", default="output")
    args = parser.parse_args()

    images_dir = create_output_dirs()

    if args.categories is None or "all" in args.categories:
        scrap_all(images_dir)
    else:
        for category in args.categories:
            scrap_category(category, images_dir)

if __name__ == "__main__":
    main()