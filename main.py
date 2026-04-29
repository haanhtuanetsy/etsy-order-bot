import imaplib
import email
import os
import time
import requests
from bs4 import BeautifulSoup

EMAIL = os.environ.get("haanhtuanetsy@gmail.com")
PASSWORD = os.environ.get("slzzfsvttjqpjykt")
BOT_TOKEN = os.environ.get("8687189308:AAG0IKJPF84WnsXB6DxGKvcltu81222njzY")
CHAT_ID = os.environ.get("7242802148")


def send_message(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

    requests.post(
        url,
        data={
            "chat_id": CHAT_ID,
            "text": text,
            "parse_mode": "HTML"
        }
    )


def send_photo(photo, caption):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"

    requests.post(
        url,
        data={
            "chat_id": CHAT_ID,
            "photo": photo,
            "caption": caption,
            "parse_mode": "HTML"
        }
    )


def get_html(msg):

    html = None

    if msg.is_multipart():

        for part in msg.walk():

            if part.get_content_type() == "text/html":

                html = part.get_payload(decode=True)

                if html:
                    return html.decode(errors="ignore")

    else:

        if msg.get_content_type() == "text/html":

            html = msg.get_payload(decode=True)

            if html:
                return html.decode(errors="ignore")

    return ""


def find_product(soup):

    # thử tìm product title trong h1/h2/h3
    for tag in soup.find_all(["h1", "h2", "h3"]):

        text = tag.get_text().strip()

        if len(text) > 6 and "etsy" not in text.lower():

            return text

    return "Unknown"


def find_total(lines):

    for l in lines:

        if "$" in l and "." in l and len(l) < 20:

            return l.strip()

    return "Unknown"


def find_personalization(lines):

    for l in lines:

        if "Personalization" in l:

            return l.replace("Personalization:", "").strip()

    return "None"


def find_shipping(lines):

    start = False
    addr = []

    for l in lines:

        if "Ship to" in l or "Shipping address" in l:

            start = True
            continue

        if start:

            if len(addr) < 6:

                addr.append(l)

            else:
                break

    if addr:

        return "\n".join(addr)

    return "Unknown"


def find_image(soup):

    for img in soup.find_all("img"):

        src = img.get("src")

        if not src:
            continue

        if "etsyimg.com" in src:

            return src

    return None


def parse_email(html):

    soup = BeautifulSoup(html, "html.parser")

    text = soup.get_text("\n")

    lines = [l.strip() for l in text.split("\n") if l.strip()]

    product = find_product(soup)

    total = find_total(lines)

    personalization = find_personalization(lines)

    shipping = find_shipping(lines)

    image = find_image(soup)

    return product, total, personalization, shipping, image


def check_orders():

    mail = imaplib.IMAP4_SSL("imap.gmail.com")

    mail.login(EMAIL, PASSWORD)

    mail.select("inbox")

    status, data = mail.search(None, '(UNSEEN FROM "etsy")')

    ids = data[0].split()

    for num in ids:

        status, msg_data = mail.fetch(num, "(RFC822)")

        raw_email = msg_data[0][1]

        msg = email.message_from_bytes(raw_email)

        html = get_html(msg)

        if not html:
            continue

        product, total, personalization, shipping, image = parse_email(html)

        caption = f"""
🛒 <b>NEW ETSY ORDER</b>

📦 Product:
{product}

✏️ Personalization:
{personalization}

💰 Total:
{total}

🏠 Shipping address:
{shipping}
"""

        try:

            if image:

                send_photo(image, caption)

            else:

                send_message(caption)

        except Exception as e:

            print("Send error:", e)

    mail.logout()


while True:

    try:

        print("Checking Etsy orders...")

        check_orders()

    except Exception as e:

        print("Error:", e)

    time.sleep(60)
