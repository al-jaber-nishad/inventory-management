import requests
from celery import shared_task

@shared_task
def send_balance_alert_message():
    url = "https://api.rtcom.xyz/balance"
    payload = {
        "acode": "30000222",
        "api_key": "58b073b1876e88e855a03eb303270aabf7eeb2bd"
    }
    headers = {
        "Content-Type": "application/json"
    }
    try:
        response = requests.post(url, json=payload, headers=headers)
        data = response.json()

        if data.get("response", {}).get("code") == 200:
            balance = data.get("info", {}).get("balance", "N/A")
            print(f"✅ Balance: {balance}")
        else:
            print(f"❌ Error: {data.get('response', {}).get('message', 'Unknown error')}")

    except Exception as e:
        print(f"❌ Request failed: {e}")



    if float(balance) <= 6000:
        mobile = "8801861650206 8801896296159"
        message = "Your balance is low in RT Communication. Please recharge your account."
        url = f"https://sms.bluebayit.com/api/sendsms?api_key=q_X4VWQ9H8qhv2as8QzCcrcLd0SGESuvKsQENBi_-vU&type=text&phone={mobile}&senderid=YOUR_SENDER_ID&message={message}"

        res = requests.get(url)
        print("Balance alert SMS sent successfully.")

