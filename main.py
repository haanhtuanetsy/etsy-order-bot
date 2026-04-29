import imaplib
import email
import requests
import time
import re

EMAIL = "haanhtuanetsy@gmail.com"
PASSWORD = "unaciiagaapxsouxD"

BOT_TOKEN = "8687189308:AAG0IKJPF84WnsXB6DxGKvcltu81222njzY"
CHAT_ID = "7242802148"


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


def send_photo(photo_url, caption):

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"

    requests.post(
        url,
        data={
            "chat_id": CHAT_ID,
            "photo": photo_url,
            "caption": caption,
            "parse_mode": "HTML"
        }
    )


def extract(pattern, text):

    match = re.search(pattern, text)

    if match:
        return match.group(1).strip()

    return "Unknown"


def parse_products(text):

    products = []

    matches = re.findall(r"Transaction ID:\s*(\d+)", text)

    for m in matches:
        products.append(m)

    return products


def find_image(text):

    match = re.search(r'(https://i\.etsystatic\.com/[^\s"]+)', text)

    if match:
        return match.group(1)

    return None


def check_orders():

    mail = imaplib.IMAP4_SSL("imap.gmail.com")

    mail.login(EMAIL, PASSWORD)

    mail.select("inbox")

    status, messages = mail.search(
        None,
        '(UNSEEN SUBJECT "You made a sale on Etsy")'
    )

    mail_ids = messages[0].split()

    for num in mail_ids:

        status, data = mail.fetch(num, "(RFC822)")

        raw_email = data[0][1]

        msg = email.message_from_bytes(raw_email)

        html = ""

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

        if html == "":
            continue

        buyer = extract(r'Buyer:\s*</strong>\s*(.*?)<', html)

        total = extract(r'Order total:\s*</strong>\s*\$?(.*?)<', html)

        transaction = extract(r'Transaction ID:\s*(\d+)', html)

        address = extract(r'Ship to:\s*</strong>\s*(.*?)<', html)

        products = parse_products(html)

        image = find_image(html)

        order_link = f"https://www.etsy.com/your/orders/sold?transaction_id={transaction}"

        text = f"""
🛒 <b>NEW ETSY ORDER</b>

👤 Buyer: {buyer}

📦 Transaction:
{transaction}

💰 Total:
${total}

🏠 Shipping:
{address}

🔗 Order:
{order_link}
"""

        if image:

            send_photo(image, text)

        else:

            send_message(text)

    mail.logout()


while True:

    try:

        print("Checking Etsy orders...")

        check_orders()

    except Exception as e:

        print("Error:", e)

    time.sleep(60)
