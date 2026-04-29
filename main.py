import imaplib
import email
import requests
import time
from bs4 import BeautifulSoup

EMAIL = "haanhtuanetsy@gmail.com"
PASSWORD = "slzzfsvttjqpjykt"

BOT_TOKEN = "8687189308:AAG0IKJPF84WnsXB6DxGKvcltu81222njzY"
CHAT_ID = "7242802148"


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

    if msg.is_multipart():

        for part in msg.walk():

            if part.get_content_type() == "text/html":

                return part.get_payload(decode=True).decode(errors="ignore")

    else:

        return msg.get_payload(decode=True).decode(errors="ignore")

    return None


def parse_etsy(html):

    soup = BeautifulSoup(html, "html.parser")

    text = soup.get_text("\n")

    buyer = "Unknown"
    total = "Unknown"
    shipping = "Unknown"
    title = "Unknown"
    personalization = "None"

    # ===== Buyer =====

    for line in text.split("\n"):

        if "Buyer" in line:

            buyer = line.replace("Buyer", "").strip()

    # ===== Total =====

        if "$" in line and "." in line and len(line) < 15:

            total = line.strip()

    # ===== Shipping =====

        if "United States" in line or "USA" in line:

            shipping = line.strip()

    # ===== Product Title =====

        if "SIZE" in line or "Sneaker" in line:

            title = line.strip()

    # ===== Personalization =====

        if "Personalization" in line:

            personalization = line.replace("Personalization", "").strip()

    # ===== Transaction =====

    transaction = None

    for link in soup.find_all("a"):

        href = link.get("href")

        if href and "transaction_id=" in href:

            transaction = href.split("transaction_id=")[1]

            break

    # ===== Image =====

    img = None

    for tag in soup.find_all("img"):

        src = tag.get("src")

        if src and "etsy" in src:

            img = src
            break

    return buyer, total, shipping, title, personalization, transaction, img


def check_orders():

    mail = imaplib.IMAP4_SSL("imap.gmail.com")

    mail.login(EMAIL, PASSWORD)

    mail.select("inbox")

    status, data = mail.search(None, '(UNSEEN SUBJECT "You made a sale on Etsy")')

    ids = data[0].split()

    for num in ids:

        status, msg_data = mail.fetch(num, "(RFC822)")

        raw = msg_data[0][1]

        msg = email.message_from_bytes(raw)

        html = get_html(msg)

        if not html:
            continue

        buyer, total, shipping, title, personalization, transaction, img = parse_etsy(html)

        order_link = f"https://www.etsy.com/your/orders/sold?transaction_id={transaction}"

        caption = f"""
🛒 <b>NEW ETSY ORDER</b>

🏪 Shop: Festifast

📦 Product:
{title}

✏️ Personalization:
{personalization}

👤 Buyer:
{buyer}

💰 Total:
{total}

🏠 Shipping:
{shipping}

🔢 Transaction:
{transaction}

🔗 Order:
{order_link}
"""

        if img:

            send_photo(img, caption)

    mail.logout()


while True:

    try:

        print("Checking Etsy orders...")

        check_orders()

    except Exception as e:

        print("Error:", e)

    time.sleep(60)
