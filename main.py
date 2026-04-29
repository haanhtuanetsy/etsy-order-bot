import imaplib
import email
import requests
import time

EMAIL="haanhtuanetsy@gmail.com"
PASSWORD="unaciiagaapxsoux"

BOT_TOKEN="8687189308:AAG0IKJPF84WnsXB6DxGKvcltu81222njzY."
CHAT_ID="7242802148"


def send_telegram(msg):

    url=f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

    requests.post(
        url,
        data={
            "chat_id":CHAT_ID,
            "text":msg
        }
    )


def check_orders():

    mail=imaplib.IMAP4_SSL(
        "imap.gmail.com"
    )

    mail.login(
        EMAIL,
        PASSWORD
    )

    mail.select(
       "inbox"
    )

    status,messages=mail.search(
        None,
        'UNSEEN'
    )


    for num in messages[0].split():

        status,data=mail.fetch(
           num,
           "(RFC822)"
        )

        raw=data[0][1]

        msg=email.message_from_bytes(
            raw
        )

        subject=msg["Subject"]

        text=f"""
🛒 New Etsy Order

{subject}
"""

        send_telegram(
            text
        )

    mail.logout()



while True:

    try:
        check_orders()
        print("Checking...")

    except Exception as e:
        print(e)

    time.sleep(60)
