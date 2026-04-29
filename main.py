import imaplib
import email
import requests
import time
import os
from bs4 import BeautifulSoup

EMAIL = os.environ.get("haanhtuanetsy@gmail.com")
PASSWORD = os.environ.get("slzzfsvttjqpjykt")
BOT_TOKEN = os.environ.get("8687189308:AAG0IKJPF84WnsXB6DxGKvcltu81222njzY")
CHAT_ID = os.environ.get("7242802148")


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


def get_html(msg):

    if msg.is_multipart():

        for part in msg.walk():

            if part.get_content_type() == "text/html":

                return part.get_payload(decode=True).decode(errors="ignore")

    else:

        if msg.get_content_type() == "text/html":

            return msg.get_payload(decode=True).decode(errors="ignore")

    return ""


def parse_email(html):

    soup = BeautifulSoup(html, "html.parser")

    text = soup.get_text("\n")

    lines = [l.strip() for l in text.split("\n") if l.strip()]

    product = "Unknown"
    total = "Unknown"
    shipping = "Unknown"
    personalization = "None"
    image = None

    # PRODUCT
    for tag in soup.find_all("h1"):
        t = tag.get_text().strip()

        if len(t) > 5 and "etsy" not in t.lower():
            product = t
            break

    # TOTAL
    for l in lines:

        if "$" in l and "." in l:

            total = l
            break

    # PERSONALIZATION
    for l in lines:

        if "Personalization" in l:

            personalization = l.replace("Personalization:", "").strip()

    # SHIPPING ADDRESS
    start = False
    addr = []

    for l in lines:

        if "Ship to" in l or "Shipping address" in l:
            start = True
            continue

        if start:

            if len(addr) < 6:
                addr.append(l)

    if addr:
        shipping = "\n".join(addr)

    # PRODUCT IMAGE (lọc đúng ảnh Etsy)
    for img in soup.find_all("img"):

        src = img.get("src")

        if not src:
            continue

        if "etsyimg.com" in src and "75x75" not in src:

            image = src
            break

    return product, total, shipping, personalization, image


def check_orders():

    mail = imaplib.IMAP4_SSL("imap.gmail.com")

    mail.login(EMAIL, PASSWORD)

    mail.select("inbox")

    status, data = mail.search(None, '(UNSEEN FROM "etsy")')

    ids = data[0].split()

    for num in ids:

        status, msg_data = mail.fetch(num, "(RFC822)")

        raw = msg_data[0][1]

        msg = email.message_from_bytes(raw)

        html = get_html(msg)

        if not html:
            continue

        product, total, shipping, personalization, image = parse_email(html)

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

        if image:

            send_photo(image, caption)

        else:

            send_message(caption)

    mail.logout()


while True:

    try:

        print("Checking Etsy orders...")

        check_orders()

    except Exception as e:

        print("Error:", e)

    time.sleep(60)
