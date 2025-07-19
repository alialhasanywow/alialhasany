import subprocess
import sys

def install_packages():
    required_packages = [
        "telethon",
        "pytz",
        "sqlite3",
        "logging"
    ]
    
    for package in required_packages:
        try:
            # استخدم pip لتنزيل المكتبات
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])
            print(f"تم تثبيت {package} بنجاح")
        except subprocess.CalledProcessError:
            print(f"فشل في تثبيت {package}")

if __name__ == "__main__":
    print("جاري تثبيت المكتبات المطلوبة...")
    install_packages()
    print("اكتمل تثبيت جميع المكتبات!")