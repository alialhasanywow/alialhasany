import threading
import time
from uuid import uuid4
import random
import requests
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput
from kivy.clock import Clock
from kivy.core.window import Window

class InstaCheckerApp(App):
    def build(self):
        # إعدادات النافذة
        Window.clearcolor = (0.95, 0.95, 0.95, 1)  # لون خلفية النافذة (رمادي فاتح)
        self.layout = BoxLayout(orientation='vertical', padding=20, spacing=15)

        # عنوان التطبيق
        self.title_label = Label(
            text="🔍 Instagram Username Checker",
            font_size=28,
            bold=True,
            color=(0.2, 0.2, 0.2, 1)  # لون النص (رمادي غامق)
        )
        self.layout.add_widget(self.title_label)

        # إدخال التوكن (Token)
        self.token_input = TextInput(
            hint_text="أدخل التوكن (Token)",
            multiline=False,
            font_size=18,
            size_hint_y=None,
            height=50,
            background_color=(1, 1, 1, 1),  # لون خلفية مربع النص (أبيض)
            foreground_color=(0.2, 0.2, 0.2, 1)  # لون النص (رمادي غامق)
        )
        self.layout.add_widget(self.token_input)

        # إدخال معرف الدردشة (Chat ID)
        self.chat_id_input = TextInput(
            hint_text="أدخل معرف الدردشة (Chat ID)",
            multiline=False,
            font_size=18,
            size_hint_y=None,
            height=50,
            background_color=(1, 1, 1, 1),  # لون خلفية مربع النص (أبيض)
            foreground_color=(0.2, 0.2, 0.2, 1)  # لون النص (رمادي غامق)
        )
        self.layout.add_widget(self.chat_id_input)

        # إدخال عدد الخيوط (Threads)
        self.thread_input = TextInput(
            hint_text="أدخل عدد الخيوط (بين 5 و 50)",
            multiline=False,
            font_size=18,
            size_hint_y=None,
            height=50,
            background_color=(1, 1, 1, 1),  # لون خلفية مربع النص (أبيض)
            foreground_color=(0.2, 0.2, 0.2, 1)  # لون النص (رمادي غامق)
        )
        self.layout.add_widget(self.thread_input)

        # زر بدء الفحص
        self.start_button = Button(
            text="ابدأ الفحص",
            on_press=self.start_checking,
            font_size=20,
            bold=True,
            size_hint_y=None,
            height=60,
            background_color=(0.3, 0.6, 0.9, 1),  # لون الزر (أزرق)
            color=(1, 1, 1, 1)  # لون النص (أبيض)
        )
        self.layout.add_widget(self.start_button)

        # منطقة عرض النتائج
        self.result_area = ScrollView(size_hint=(1, None), size=(Window.width, Window.height * 0.5))
        self.result_label = Label(
            text="",
            font_size=18,
            size_hint_y=None,
            valign="top",
            color=(0.2, 0.2, 0.2, 1),  # لون النص (رمادي غامق)
            markup=True
        )
        self.result_label.bind(texture_size=self.result_label.setter('size'))
        self.result_area.add_widget(self.result_label)
        self.layout.add_widget(self.result_area)

        return self.layout

    def start_checking(self, instance):
        try:
            # الحصول على التوكن ومعرف الدردشة وعدد الخيوط من المستخدم
            token = self.token_input.text.strip()
            chat_id = self.chat_id_input.text.strip()
            thread_count = int(self.thread_input.text.strip())

            if not token or not chat_id:
                self.result_label.text = "[color=ff0000]⚠️ الرجاء إدخال التوكن ومعرف الدردشة[/color]"
                return

            if 5 <= thread_count <= 50:
                self.result_label.text = "[b]جاري الفحص...[/b]"
                threading.Thread(target=self.run_checker, args=(token, chat_id, thread_count), daemon=True).start()
            else:
                self.result_label.text = "[color=ff0000]⚠️ يجب إدخال عدد خيوط بين 5 و 50[/color]"
        except ValueError:
            self.result_label.text = "[color=ff0000]⚠️ الرجاء إدخال رقم صحيح لعدد الخيوط[/color]"

    def run_checker(self, token, chat_id, thread_count):
        good_count, bad_count = 0, 0
        valid_usernames = []
        start_time = time.time()

        url = 'https://i.instagram.com/api/v1/accounts/create/'
        headers = {
            'User-Agent': 'Instagram 6.12.1 Android',
            'Content-Type': 'application/x-www-form-urlencoded'
        }

        lowercase_chars = 'qwertyuioplkjhgfdsazxcvbnm'
        all_chars = lowercase_chars + '0123456789'

        def generate_username():
            return "_" + random.choice(lowercase_chars) + "_" + random.choice(all_chars) + random.choice(lowercase_chars)

        def check_username():
            nonlocal good_count, bad_count
            while True:
                username = generate_username()
                data = {
                    "email": f"user{random.randint(1000, 9999)}@gmail.com",
                    "username": username,
                    "password": f"Pass{random.randint(100, 999)}{username}",
                    "device_id": f"android-{uuid4()}",
                    "guid": str(uuid4()),
                }
                try:
                    response = requests.post(url, headers=headers, data=data).text
                    if '"email_is_taken"' in response:
                        good_count += 1
                        valid_usernames.append(username)
                        message = f"✅ Username found: {username}"
                        requests.post(f'https://api.telegram.org/bot{token}/sendMessage',
                                      data={'chat_id': chat_id, 'text': message})
                    else:
                        bad_count += 1
                    total = good_count + bad_count
                    elapsed_time = int(time.time() - start_time)
                    Clock.schedule_once(lambda dt: self.update_results(total, good_count, bad_count, valid_usernames, elapsed_time), 0)
                except Exception as e:
                    Clock.schedule_once(lambda dt: self.update_results(0, 0, 0, [], 0, error=str(e)), 0)
                    time.sleep(2)

        # تشغيل الخيوط
        for _ in range(thread_count):
            threading.Thread(target=check_username, daemon=True).start()

    def update_results(self, total, good, bad, valid_usernames, elapsed_time, error=None):
        if error:
            self.result_label.text = f"[color=ff0000]⚠️ خطأ: {error}[/color]"
            return

        hours, minutes, seconds = elapsed_time // 3600, (elapsed_time % 3600) // 60, elapsed_time % 60
        result_text = f"""
[b]📊 الإحصائيات:[/b]
✅ [color=00aa00]صالح: {good}[/color]
❌ [color=ff0000]غير صالح: {bad}[/color]
📌 [color=0000ff]الإجمالي: {total}[/color]
⏳ [color=555555]الوقت المنقضي: {hours:02d}:{minutes:02d}:{seconds:02d}[/color]
        """

        if valid_usernames:
            result_text += "\n[b]🔹 أسماء المستخدمين الصالحة:[/b]\n" + "\n".join(valid_usernames[-5:])

        self.result_label.text = result_text

if __name__ == '__main__':
    InstaCheckerApp().run()