import imaplib
import email
import requests
import time
from bs4 import BeautifulSoup

EMAIL="haanhtuanetsy@gmail.com"
PASSWORD="slzzfsvttjqpjykt"

BOT_TOKEN="8687189308:AAG0IKJPF84WnsXB6DxGKvcltu81222njzYN"
CHAT_ID="7242802148"


def send_photo(photo, caption):

    url=f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"

    requests.post(
        url,
        data={
            "chat_id":CHAT_ID,
            "photo":photo,
            "caption":caption,
            "parse_mode":"HTML"
        }
    )


def get_html(msg):

    if msg.is_multipart():

        for part in msg.walk():

            if part.get_content_type()=="text/html":

                return part.get_payload(decode=True).decode(errors="ignore")

    else:

        return msg.get_payload(decode=True).decode(errors="ignore")

    return ""


def parse_email(html):

    soup=BeautifulSoup(html,"html.parser")

    text=soup.get_text("\n")

    lines=[i.strip() for i in text.split("\n") if i.strip()]

    shop="Unknown"
    product="Unknown"
    total="Unknown"
    buyer_address="Unknown"
    personalization="None"

    # SHOP
    for l in lines:
        if "from" in l.lower() and "shop" in l.lower():
            shop=l.replace("Shop","").replace("from","").strip()

    # TOTAL
    for l in lines:
        if "$" in l and "." in l and len(l)<20:
            total=l
            break

    # PRODUCT
    for tag in soup.find_all(["h1","h2","h3"]):
        t=tag.get_text().strip()
        if len(t)>5 and "etsy" not in t.lower():
            product=t
            break

    # PERSONALIZATION
    for l in lines:
        if "Personalization" in l:
            personalization=l.replace("Personalization","").strip()

    # BUYER + ADDRESS
    start=False
    addr=[]

    for l in lines:

        if "Ship to" in l or "Shipping address" in l:
            start=True
            continue

        if start:

            if len(addr)<5:
                addr.append(l)

            else:
                break

    if addr:
        buyer_address="\n".join(addr)

    # IMAGE
    img=None

    for tag in soup.find_all("img"):

        src=tag.get("src") or tag.get("data-src")

        if src and "etsy" in src:

            img=src
            break

    return shop,product,total,buyer_address,personalization,img


def check_orders():

    mail=imaplib.IMAP4_SSL("imap.gmail.com")

    mail.login(EMAIL,PASSWORD)

    mail.select("inbox")

    status,data=mail.search(None,'(UNSEEN FROM "etsy")')

    ids=data[0].split()

    for num in ids:

        status,msg_data=mail.fetch(num,"(RFC822)")

        raw=msg_data[0][1]

        msg=email.message_from_bytes(raw)

        html=get_html(msg)

        if not html:
            continue

        shop,product,total,buyer_address,personalization,img=parse_email(html)

        caption=f"""
🛒 <b>NEW ETSY ORDER</b>

🏪 Shop:
{shop}

📦 Product:
{product}

✏️ Personalization:
{personalization}

💰 Total:
{total}

🏠 Shipping:
{buyer_address}
"""

        if img:

            send_photo(img,caption)

        else:

            url=f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

            requests.post(
                url,
                data={
                    "chat_id":CHAT_ID,
                    "text":caption,
                    "parse_mode":"HTML"
                }
            )

    mail.logout()



while True:

    try:

        print("Checking orders...")

        check_orders()

    except Exception as e:

        print(e)

    time.sleep(60)
