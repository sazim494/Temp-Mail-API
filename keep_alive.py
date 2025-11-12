#### `keep_alive.py` (এই ফাইলটি Replit-এ বটকে ২৪/৭ সচল রাখবে)

python
from flask import Flask
from threading import Thread

# একটি সাধারণ Flask ওয়েব সার্ভার তৈরি করা
app = Flask('')

@app.route('/')
def home():
    # UptimeRobot এই পেজটি ভিজিট করবে
    return "Bot is alive!"

def run():
    # সার্ভারটি একটি আলাদা থ্রেডে চালানো হচ্ছে
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    # সার্ভার থ্রেডটি শুরু করা
    t = Thread(target=run)
    t.start()
