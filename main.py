import imaplib
import email
import requests
import time
import re
from bs4 import BeautifulSoup

# ===== CONFIG =====

EMAIL = "haanhtuanetsy@gmail.com"
PASSWORD = "slzzfsvttjqpjykt"

BOT_TOKEN = "8687189308:AAG0IKJPF84WnsXB6DxGKvcltu81222njzY"
CHAT_ID = "7242802148"


# ===== TELEGRAM SEND PHOTO =====

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


# ===== REGEX HELPER =====

def extract(regex, text):

    match = re.search(regex, text, re.I)

    if match:
        return match.group(1).strip()

    return "Unknown"


# ===== GET HTML EMAIL =====

def get_html(msg):

    html = None

    if msg.is_multipart():

        for part in msg.walk():

            if part.get_content_type() == "text/html":

                payload = part.get_payload(decode=True)

                if payload:
                    html = payload.decode(errors="ignore")

    else:

        payload = msg.get_payload(decode=True)

        if payload:
            html = payload.decode(errors="ignore")

    return html


# ===== PARSE ETSY EMAIL =====

def parse_etsy(html):

    soup = BeautifulSoup(html, "html.parser")

    text = soup.get_text(" ")

    # Buyer
    buyer = extract(r"Buyer\s*:\s*(.*?)\s", text)

    # Total
    total = extract(r"Order total\s*\$?([\d\.,]+)", text)

    # Shipping
    shipping = extract(r"Ship to\s*(.*?)\s", text)

    # Transaction
    transaction = extract(r"Transaction ID:\s*(\d+)", text)

    # Shop name
    shop = extract(r"Shop\s*:\s*(.*?)\s", text)

    # Product title
    title = extract(r"Item\s*:\s*(.*?)\s", text)

    # PERSONALIZATION
    personalization = extract(r"Personalization\s*:\s*(.*?)\s{2,}", text)

    if personalization == "Unknown":
        personalization = extract(r"Personalization\s*(.*?)\s{2,}", text)

    # IMAGE HD
    img = None

    for i in soup.find_all("img"):

        src = i.get("src")

        if src and "etsy" in src:

            img = src.replace("il_75x75", "il_570xN")

            break

    return buyer, total, shipping, transaction, shop, title, img, personalization


# ===== CHECK ETSY ORDERS =====

def check_orders():

    mail = imaplib.IMAP4_SSL("imap.gmail.com")

    mail.login(EMAIL, PASSWORD)

    mail.select("inbox")

    status, data = mail.search(
        None,
        '(UNSEEN SUBJECT "You made a sale on Etsy")'
    )

    ids = data[0].split()

    for num in ids:

        status, msg_data = mail.fetch(num, "(RFC822)")

        raw = msg_data[0][1]

        msg = email.message_from_bytes(raw)

        html = get_html(msg)

        if not html:
            continue

        buyer, total, shipping, transaction, shop, title, img, personalization = parse_etsy(html)

        order_link = f"https://www.etsy.com/your/orders/sold?transaction_id={transaction}"

        caption = f"""
🛒 <b>NEW ETSY ORDER</b>

🏪 <b>Shop:</b>
{shop}

📦 <b>Product:</b>
{title}

✏️ <b>Personalization:</b>
{personalization}

👤 <b>Buyer:</b>
{buyer}

💰 <b>Total:</b>
${total}

🏠 <b>Shipping:</b>
{shipping}

🔢 <b>Transaction:</b>
{transaction}

🔗 <b>Order Link:</b>
{order_link}
"""

        if img:
            send_photo(img, caption)

    mail.logout()


# ===== LOOP =====

while True:

    try:

        print("Checking Etsy orders...")

        check_orders()

    except Exception as e:

        print("Error:", e)

    time.sleep(60)
