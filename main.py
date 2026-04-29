import imaplib
import email
import requests
import time
import os
import re
from bs4 import BeautifulSoup

EMAIL = os.getenv("EMAIL")
PASSWORD = os.getenv("PASSWORD")

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

processed_orders = set()


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


def extract_between(text, start, end):

    try:
        return text.split(start)[1].split(end)[0].strip()
    except:
        return "Unknown"


def parse_email(html):

    soup = BeautifulSoup(html, "html.parser")

    text = soup.get_text("\n")

    # Buyer name
    buyer = "Unknown"
    if "Order from" in text:
        buyer = extract_between(text, "Order from", "\n")

    # Transaction ID
    transaction = extract_between(text, "Transaction ID:", "\n")

    # Order total
    total = extract_between(text, "Order total:", "\n")

    # Shipping
    shipping = extract_between(text, "Shipping:", "\n")

    # Shipping address
    address = "Unknown"
    if "Ship to:" in text:
        address = extract_between(text, "Ship to:", "Order total")

    # Order link
    order_link = None
    for a in soup.find_all("a", href=True):

        if "etsy.com/your/orders" in a["href"]:
            order_link = a["href"]

    # Products
    products = []

    product_blocks = text.split("Quantity:")

    for block in product_blocks[1:]:

        name = block.split("\n")[0].strip()

        quantity = extract_between(block, "", "\n")

        price = "Unknown"
        if "Price:" in block:
            price = extract_between(block, "Price:", "\n")

        size = "Unknown"
        if "SIZE" in block:
            size = extract_between(block, "SIZE", "\n")

        products.append({
            "name": name,
            "quantity": quantity,
            "price": price,
            "size": size
        })

    # Image
    image = None
    img = soup.find("img")

    if img:
        image = img.get("src")

    return buyer, transaction, total, shipping, address, order_link, products, image


def check_orders():

    mail = imaplib.IMAP4_SSL("imap.gmail.com")

    mail.login(EMAIL, PASSWORD)

    mail.select("inbox")

    status, messages = mail.search(
        None,
        '(UNSEEN FROM "transaction@etsy.com")'
    )

    ids = messages[0].split()

    for num in ids:

        status, data = mail.fetch(num, "(RFC822)")

        raw = data[0][1]

        msg = email.message_from_bytes(raw)

        html = None

        if msg.is_multipart():

            for part in msg.walk():

                if part.get_content_type() == "text/html":

                    html = part.get_payload(decode=True).decode()

        else:

            html = msg.get_payload(decode=True).decode()

        if not html:
            continue

        buyer, transaction, total, shipping, address, order_link, products, image = parse_email(html)

        if transaction in processed_orders:
            continue

        processed_orders.add(transaction)

        product_text = ""

        for p in products:

            product_text += f"""
📦 <b>{p['name']}</b>
📏 Size: {p['size']}
📦 Qty: {p['quantity']}
💰 Price: {p['price']}

"""

        caption = f"""
🛒 <b>NEW ETSY ORDER</b>

👤 <b>Buyer</b>
{buyer}

📍 <b>Shipping Address</b>
{address}

{product_text}

🚚 <b>Shipping</b>
{shipping}

💵 <b>Order Total</b>
{total}

🆔 <b>Transaction</b>
{transaction}
"""

        if order_link:

            caption += f'\n🔗 <a href="{order_link}">Open Order</a>'

        if image:

            send_photo(image, caption)

        else:

            send_message(caption)

        mail.store(num, '+FLAGS', '\\Seen')

    mail.logout()


while True:

    try:

        check_orders()

        print("Checking Etsy orders...")

    except Exception as e:

        print("Error:", e)

    time.sleep(20)
