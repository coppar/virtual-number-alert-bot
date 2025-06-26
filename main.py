# main.py

import cloudscraper
from bs4 import BeautifulSoup
from telegram import Bot
import asyncio
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = int(os.getenv('TELEGRAM_CHAT_ID'))

bot = Bot(token=TELEGRAM_BOT_TOKEN)
seen_numbers = set()
scraper = cloudscraper.create_scraper()

BASE_URL = 'https://temp-number.com/countries/'
COUNTRY_PATHS = [
    'United-Kingdom',
    'United-States',
    'Finland',
    'Netherlands',
    'Sweden',
]

def fetch_all_countries_numbers():
    all_numbers = []

    for country_path in COUNTRY_PATHS:
        url = f"{BASE_URL}{country_path}"
        try:
            response = scraper.get(url)
            response.raise_for_status()
        except Exception as e:
            print(f"[Error] Failed to fetch {url}: {e}")
            continue

        soup = BeautifulSoup(response.text, 'html.parser')

        # Find boxes marked "NEW" with recent timestamps
        new_boxes = []
        for box in soup.select('div.country-box'):
            if not box.select_one('.ribbon-green'):
                continue  # Skip if not marked NEW

            time_tag = box.select_one('.add_time-top')
            time_text = time_tag.text.strip().lower() if time_tag else ''
            if 'second' in time_text or 'just now' in time_text:
                new_boxes.append(box)

        # Limit to top 3 most recent per country
        new_boxes = new_boxes[:3]

        for box in new_boxes:
            number_tag = box.select_one('h4.card-title')
            number = number_tag.text.strip() if number_tag else 'N/A'

            flag_span = box.select_one('span.flag-icon')
            country_code = 'N/A'
            if flag_span and 'class' in flag_span.attrs:
                classes = flag_span['class']
                for c in classes:
                    if c.startswith('flag-icon-'):
                        country_code = c.split('flag-icon-')[-1].upper()
                        break

            link_tag = box.select_one('a.country-link')
            link = link_tag['href'] if link_tag and 'href' in link_tag.attrs else ''
            full_link = f'https://temp-number.com{link}' if link else url

            all_numbers.append((number, country_code, 'temp-number.com', full_link))

    return all_numbers

async def monitor():
    global seen_numbers
    print("Starting monitor loop...")
    while True:
        try:
            new_numbers = fetch_all_countries_numbers()
            print(f"Checked all countries, found {len(new_numbers)} new seconds-ago numbers")
            for num, country, source, link in new_numbers:
                if num not in seen_numbers:
                    seen_numbers.add(num)
                    msg = f"📞 {num} ({country})\n🌐 {source}\n🔗 {link}"
                    print(f"Sending alert for: {num}")
                    await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=msg)
        except Exception as e:
            print(f"[Error] {e}")
        await asyncio.sleep(60)

if __name__ == '__main__':
    asyncio.run(monitor())
