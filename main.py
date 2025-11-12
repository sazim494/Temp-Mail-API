import os
import asyncio
import logging
from fbchat_async import Client, MessageEvent, ThreadType
import openai

# --- কনফিগারেশন ---
# Replit Secrets (পরিবেশগত ভেরিয়েবল) থেকে জরুরি তথ্য লোড করা
FB_EMAIL = os.getenv("FB_EMAIL")
FB_PASSWORD = os.getenv("FB_PASSWORD")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
TARGET_GROUP_NAME = os.getenv("GROUP_NAME") # আপনার টার্গেট করা গ্রুপের সঠিক নাম
BOT_NAME_TAG = f"@{os.getenv('BOT_NAME')}" # গ্রুপে বটকে যেভাবে ট্যাগ করা হবে, যেমন: "@BotName"

# OpenAI ক্লায়েন্ট কনফিগার করা
if OPENAI_API_KEY:
    openai.api_key = OPENAI_API_KEY
else:
    print("সতর্কবার্তা: OPENAI_API_KEY সেট করা নেই। AI উত্তর দেওয়ার ফিচারটি বন্ধ থাকবে।")

# লগিং কনফিগার করা, যাতে আপনি ইভেন্ট ও ত্রুটি দেখতে পারেন
logging.basicConfig(level=logging.INFO)

# --- AI দ্বারা উত্তর তৈরি করার ফাংশন ---
async def get_ai_response(prompt: str) -> str:
    """
    OpenAI-এর GPT মডেল থেকে উত্তর সংগ্রহ করে।
    """
    if not OPENAI_API_KEY:
        return "দুঃখিত, AI ফিচারটি সঠিকভাবে কনফিগার করা হয়নি।"

    try:
        # OpenAI API-কে একটি চ্যাট অনুরোধ পাঠানো হচ্ছে
        response = await openai.ChatCompletion.acreate(
            model="gpt-3.5-turbo",  # আপনার অ্যাক্সেস থাকলে "gpt-4" ব্যবহার করতে পারেন
            messages=[
                {
                    "role": "system",
                    "content": "তুমি একজন বন্ধুত্বপূর্ণ এবং সহায়ক AI অ্যাসিস্ট্যান্ট, যা একটি ফেসবুক মেসেঞ্জার গ্রুপ চ্যাটে কাজ করে। তোমার উত্তরগুলো সহজ ও সংক্ষিপ্ত রাখবে।"
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.7, # এটি উত্তরের মধ্যে বৈচিত্র্য আনে
            max_tokens=250, # উত্তরের সর্বোচ্চ শব্দ সংখ্যা
        )
        # উত্তরটি এক্সট্র্যাক্ট করা
        ai_reply = response.choices[0].message.content.strip()
        return ai_reply
    except Exception as e:
        logging.error(f"AI থেকে উত্তর আনতে সমস্যা: {e}")
        return "আমার ভাবতে একটু সমস্যা হচ্ছে। অনুগ্রহ করে কিছুক্ষণ পর আবার চেষ্টা করুন।"

# --- ফেসবুক বট ক্লায়েন্ট ---
class AIBot(Client):
    def __init__(self, email, password):
        super().__init__(email, password)
        self.target_group_id = None
        self.bot_user_id = None

    async def on_ready(self):
        """
        বট সফলভাবে লগইন করলে এই ফাংশনটি কাজ করে।
        এটি শোনার জন্য টার্গেট গ্রুপের আইডি খুঁজে বের করে।
        """
        print(f"বট লগইন করেছে: {self.user.id}")
        self.bot_user_id = self.user.id
        try:
            # গ্রুপের নাম দিয়ে সার্চ করা
            groups = await self.fetch_threads(thread_type=ThreadType.GROUP, limit=20)
            for group in groups:
                if group.name == TARGET_GROUP_NAME:
                    self.target_group_id = group.id
                    print(f"সফলভাবে '{TARGET_GROUP_NAME}' গ্রুপটি খুঁজে পাওয়া গেছে, আইডি: {self.target_group_id}")
                    break
            if not self.target_group_id:
                print(f"ত্রুটি: '{TARGET_GROUP_NAME}' নামে কোনো গ্রুপ খুঁজে পাওয়া যায়নি। নামটি সঠিক কিনা তা নিশ্চিত করুন।")
        except Exception as e:
            logging.error(f"গ্রুপ খুঁজতে সমস্যা: {e}")

    async def on_message(self, event: MessageEvent):
        """
        যখনই কোনো মেসেজ আসে, এই ফাংশনটি কাজ করে।
        """
        # ১. বট নিজের পাঠানো মেসেজ উপেক্ষা করবে
        if event.author.id == self.bot_user_id:
            return

        # ২. মেসেজটি আমাদের টার্গেট গ্রুপ থেকে এসেছে কিনা তা পরীক্ষা করবে
        if event.thread.id != self.target_group_id:
            return

        # ৩. মেসেজে বটকে ট্যাগ করা হয়েছে কিনা তা পরীক্ষা করবে
        if event.message.text and BOT_NAME_TAG in event.message.text:
            print(f"গ্রুপ {self.target_group_id}-এ {event.author.id} বটকে ট্যাগ করেছে")

            # আসল প্রশ্নটি পাওয়ার জন্য ট্যাগটি মেসেজ থেকে সরিয়ে ফেলা হচ্ছে
            user_prompt = event.message.text.replace(BOT_NAME_TAG, "").strip()

            if not user_prompt:
                await self.send_text("হ্যালো! আমি আপনাকে কীভাবে সাহায্য করতে পারি?", thread_id=self.target_group_id)
                return
            
            # বট যে টাইপ করছে, তা দেখানো হচ্ছে
            await self.set_typing_status(is_typing=True, thread_id=self.target_group_id)

            # ৪. AI দ্বারা তৈরি উত্তর সংগ্রহ করা
            ai_reply = await get_ai_response(user_prompt)
            
            # ৫. উত্তরটি গ্রুপে পাঠানো
            await self.send_text(ai_reply, thread_id=self.target_group_id)
            
            # টাইপিং স্ট্যাটাস বন্ধ করা
            await self.set_typing_status(is_typing=False, thread_id=self.target_group_id)


# --- বটকে সচল রাখার সার্ভার ---
from keep_alive import keep_alive

# --- মূল কোড চালানো ---
if __name__ == "__main__":
    if not FB_EMAIL or not FB_PASSWORD:
        print("ত্রুটি: FB_EMAIL এবং FB_PASSWORD অবশ্যই Replit Secrets-এ সেট করতে হবে।")
    else:
        # বটকে সচল রাখতে ওয়েব সার্ভার চালু করা
        keep_alive()
        
        # বট ক্লায়েন্ট তৈরি এবং চালানো
        client = AIBot(FB_EMAIL, FB_PASSWORD)
        asyncio.run(client.run())
