import requests
from bs4 import BeautifulSoup
from datetime import datetime
import json


class Parser:
    def __init__(self, base_url):
        self.base_url = base_url
        self.data = []

    def fetch_page(self, url):
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.text

    def get_shop_links(self):
        html = self.fetch_page(self.base_url + "/hypermarkte/")
        soup = BeautifulSoup(html, "html.parser")
        return [(li.get_text(strip=True), self.base_url + li.select_one("a")["href"])
                for li in soup.select("ul.categories li") if li.select_one("a")]

    def parse_shop_page(self, shop_name, shop_url):
        soup = BeautifulSoup(self.fetch_page(shop_url), "html.parser")
        div_name = soup.select_one("div.letaky-grid")
        if not div_name:
            return

        for item in div_name.select("div.brochure-thumb"):
            picture_tag = item.select_one("div.img-container picture img")
            img_src = picture_tag.get("src") or picture_tag.get("data-src", None) if picture_tag else None

            title = item.select_one("p.grid-item-content strong").get_text(strip=True)
            date_text = item.select_one("p.grid-item-content small.hidden-sm").get_text(strip=True)
            valid_from, valid_to = self.parse_dates(date_text)

            # if the leaflet is currently active
            if valid_from and valid_to and valid_from <= datetime.today().date() <= valid_to:
                self.data.append({
                    "title": title,
                    "thumbnail": img_src,
                    "shop_name": shop_name,
                    "valid_from": valid_from.strftime("%Y-%m-%d"),
                    "valid_to": valid_to.strftime("%Y-%m-%d"),
                    "parsed_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                })

    def parse_dates(self, date_text):
        try:
            date_parts = date_text.split(" - ")
            if len(date_parts) == 2:
                valid_from, valid_to = map(lambda x: datetime.strptime(x.strip(), "%d.%m.%Y").date(), date_parts)
            else:               # for example: " von Freitag *date* "
                valid_from = "-"
                valid_to = datetime.strptime(date_parts[0].strip(), "%d.%m.%Y").date()
            return valid_from, valid_to
        except ValueError:
            return None, None

    def save_to_json(self, filename="output.json"):
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(self.data, f, ensure_ascii=False, indent=4)


if __name__ == "__main__":

    parser = Parser("https://www.prospektmaschine.de")

    for shop_name, shop_link in parser.get_shop_links():
        parser.parse_shop_page(shop_name, shop_link)

    parser.save_to_json("leaflets.json")
