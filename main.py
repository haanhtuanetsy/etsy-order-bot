import imaplib
import email
import requests
import time
import re

EMAIL="haanhtuanetsy@gmail.com"
PASSWORD="aucelfgaxefsfhoc"

BOT_TOKEN="8687189308:AAG0IKJPF84WnsXB6DxGKvcltu81222njzY"
CHAT_ID="7242802148"



def send_photo(image_bytes, caption):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"

    requests.post(
        url,
        data={
            "chat_id": CHAT_ID,
            "caption": caption
        },
        files={
            "photo": ("image.jpg", image_bytes)
        }
    )


def send_text(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

    requests.post(url, data={
        "chat_id": CHAT_ID,
        "text": text
    })


def extract_info(body):
    # ===== TITLE =====
    lines = body.strip().split("\n")
    product = lines[0] if lines else "Unknown product"

    # ===== SHOP =====
    shop = "N/A"
    m = re.search(r'Shop:\s*(.+)', body)
    if m:
        shop = m.group(1).strip()

    # ===== ORDER TOTAL =====
    total = "N/A"
    m = re.search(r'Order total:\s*([\d,\.đ$]+)', body)
    if m:
        total = m.group(1)

    # ===== PERSONALIZATION =====
    personalization = "N/A"
    m = re.search(r'Personalization:\s*(.+)', body)
    if m:
        personalization = m.group(1).strip()

    # ===== SHIPPING =====
    shipping = "N/A"
    m = re.search(r'Shipping.*?:\s*(.+)', body)
    if m:
        shipping = m.group(1).strip()

    return product, shop, total, personalization, shipping


def extract_image(msg):
    image_bytes = None
    biggest = 0

    if msg.is_multipart():
        for part in msg.walk():

            content_type = part.get_content_type()

            # chỉ cần là image là lấy
            if content_type.startswith("image/"):

                img = part.get_payload(decode=True)

                if img:
                    size = len(img)

                    print("Image size:", size)

                    # lọc ảnh nhỏ (icon)
                    if size > biggest and size > 5000:
                        biggest = size
                        image_bytes = img

    return image_bytes


def check_orders():

    mail = imaplib.IMAP4_SSL("imap.gmail.com")
    mail.login(EMAIL, PASSWORD)
    mail.select("inbox")

    status, messages = mail.search(
        None,
        '(UNSEEN SUBJECT "You made a sale on Etsy")'
    )

    for num in messages[0].split():

        status, data = mail.fetch(num, "(RFC822)")
        raw = data[0][1]

        msg = email.message_from_bytes(raw)

        body = ""

        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_type() == "text/plain":
                    body = part.get_payload(decode=True).decode(errors="ignore")
                    break
        else:
            body = msg.get_payload(decode=True).decode(errors="ignore")

        # ===== LẤY THÔNG TIN =====
        product, shop, total, personalization, shipping = extract_info(body)

        # ===== LẤY ẢNH =====
        image_bytes = extract_image(msg)

        # ===== FORMAT TEXT =====
        caption = f"""{product}

Shop: {shop}
Order total: {total}
Personalization: {personalization}
Shipping: {shipping}"""

        # ===== GỬI TELEGRAM =====
        if image_bytes:
            print("Sending PHOTO...")
            send_photo(image_bytes, caption)
        else:
            print("NO IMAGE → sending TEXT")
            send_text(caption)

    mail.logout()


while True:
    try:
        check_orders()
        print("Checking...")
    except Exception as e:
        print("ERROR:", e)

    time.sleep(120)
