import imaplib
import email
import requests
import time
import re

EMAIL="haanhtuanetsy@gmail.com"
PASSWORD="aucelfgaxefsfhoc"

BOT_TOKEN="8687189308:AAG0IKJPF84WnsXB6DxGKvcltu81222njzY"
CHAT_ID="7242802148"


def send_photo_file(image_bytes, caption):

    url=f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"

    files={
        "photo":("image.jpg", image_bytes)
    }

    requests.post(
        url,
        data={"chat_id":CHAT_ID, "caption":caption},
        files=files
    )


def send_text(text):

    url=f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

    requests.post(
        url,
        data={
            "chat_id":CHAT_ID,
            "text":text
        }
    )


def check_orders():

    mail=imaplib.IMAP4_SSL("imap.gmail.com")
    mail.login(EMAIL, PASSWORD)
    mail.select("inbox")

    status,messages=mail.search(
        None,
        '(UNSEEN SUBJECT "You made a sale on Etsy")'
    )

    for num in messages[0].split():

        status,data=mail.fetch(num,"(RFC822)")
        raw=data[0][1]

        msg=email.message_from_bytes(raw)

        body=""

        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_type()=="text/plain":
                    body=part.get_payload(decode=True).decode(errors="ignore")
                    break
        else:
            body=msg.get_payload(decode=True).decode(errors="ignore")

        # ===== PRODUCT TITLE =====
        product=body.strip().split("\n")[0]

        # ===== SHOP NAME =====
        shop="Unknown"
        shop_match=re.search(r'Shop:\s*(.+)', body)
        if shop_match:
            shop=shop_match.group(1).strip()

        # ===== ORDER TOTAL =====
        total="N/A"
        total_match=re.search(r'Order total:\s*([\d,\.đ]+)', body)
        if total_match:
            total=total_match.group(1)

        # ===== LẤY ẢNH NHÚNG =====
        image_bytes=None

        if msg.is_multipart():
            for part in msg.walk():

                content_type=part.get_content_type()

                if content_type.startswith("image/"):

                    img=part.get_payload(decode=True)

                    if img and len(img) > 20000:  # lọc ảnh nhỏ (logo)

                        image_bytes=img
                        break

        # ===== FORMAT TELEGRAM =====
        caption=f"""{product[:80]}

🏪 {shop}
💰 {total}"""

        # ===== SEND =====
        if image_bytes:
            send_photo_file(image_bytes, caption)
        else:
            send_text(caption)

    mail.logout()


while True:
    try:
        check_orders()
        print("Checking...")
    except Exception as e:
        print(e)

    time.sleep(120)
