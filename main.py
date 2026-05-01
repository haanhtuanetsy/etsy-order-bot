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

    requests.post(url, data={
        "chat_id":CHAT_ID,
        "text":text
    })


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

        html=""
        body=""

        image_map={}  # lưu cid -> ảnh

        if msg.is_multipart():

            for part in msg.walk():

                content_type=part.get_content_type()

                # ===== lấy HTML =====
                if content_type=="text/html":
                    html=part.get_payload(decode=True).decode(errors="ignore")

                # ===== lấy text =====
                if content_type=="text/plain" and not body:
                    body=part.get_payload(decode=True).decode(errors="ignore")

                # ===== lấy ảnh CID =====
                if content_type.startswith("image/"):

                    cid=part.get("Content-ID")

                    if cid:
                        cid=cid.replace("<","").replace(">","")

                        image_map[cid]=part.get_payload(decode=True)

        else:
            body=msg.get_payload(decode=True).decode(errors="ignore")

        # ===== TITLE =====
        product=body.strip().split("\n")[0]

        # ===== SHOP =====
        shop="Unknown"
        shop_match=re.search(r'Shop:\s*(.+)', body)
        if shop_match:
            shop=shop_match.group(1).strip()

        # ===== TOTAL =====
        total="N/A"
        total_match=re.search(r'Order total:\s*([\d,\.đ$]+)', body)
        if total_match:
            total=total_match.group(1)

        # ===== PERSONALIZATION =====
        personalization="N/A"
        p_match=re.search(r'Personalization:\s*(.+)', body)
        if p_match:
            personalization=p_match.group(1).strip()

        # ===== SHIPPING =====
        shipping="N/A"
        ship_match=re.search(r'Shipping.*?:\s*(.+)', body)
        if ship_match:
            shipping=ship_match.group(1).strip()

        # ===== TÌM ẢNH TRONG HTML =====
        image_bytes=None

        # tìm cid trong html
        cid_match=re.search(r'cid:(.*?)"', html)

        if cid_match:
            cid=cid_match.group(1)

            if cid in image_map:
                image_bytes=image_map[cid]

        # fallback: lấy ảnh lớn nhất nếu không match cid
        if not image_bytes:

            biggest=0

            for cid,img in image_map.items():

                if img and len(img) > biggest:
                    biggest=len(img)
                    image_bytes=img

        # ===== MESSAGE =====
        caption=f"""{product}

Shop: {shop}
Order total: {total}
Personalization: {personalization}
Shipping: {shipping}"""

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
