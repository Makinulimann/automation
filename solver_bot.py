import time
import pyautogui
import google.generativeai as genai
import requests
from PIL import Image

# ================= KONFIGURASI ================= #
GEMINI_API_KEY = "AIzaSyDKyLzeN3aYHURBaUH1DT_2e1eV_jwUmTM"

# Endpoint (Webhook) dari server lokal bot WhatsApp Anda (Node.js)
WA_BOT_WEBHOOK_URL = "http://localhost:3000/send-message" 

# Nomor target WhatsApp (biasanya berakhiran @c.us untuk user biasa)
WA_TARGET_NUMBER = "6288231033266@c.us" 

SCREENSHOT_FILENAME = "screenshot_soal.png"
PROMPT_GEMINI = "berikan penyelesaian/jawaban kode program dari case tersebut untuk soal yang ada di gambar ini."
# =============================================== #

# Konfigurasi Gemini AI
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-3.1-flash-lite')

def send_to_wa_bot(message):
    """
    Kirim pesan ke bot WA melalui API lokal.
    (Bot Node.js Anda perlu menambah fitur endpoint Express)
    """
    try:
        payload = {
            "number": WA_TARGET_NUMBER,
            "message": message
        }
        # Mengirim POST Request
        response = requests.post(WA_BOT_WEBHOOK_URL, json=payload, timeout=10)
        if response.status_code == 200:
            print("[BERHASIL] Pesan WhatsApp terkirim.")
        else:
            print(f"[GAGAL] Bot WA merespons dengan HTTP {response.status_code}: {response.text}")
    except Exception as e:
        print(f"[ERROR] Tidak dapat terhubung ke WA Bot Webhook. Pastikan bot Node.js berjalan: {e}")

def process_screenshot_and_solve():
    """
    Fungsi utama untuk mengambil screenshot, kirim ke Gemini, 
    dan kirim hasilnya ke WA.
    """
    print("\n--- Memulai proses penyelesaian soal ---")
    try:
        # 1. Ambil Screenshot Monitor
        print("[1] Mengambil screenshot layar...")
        screenshot = pyautogui.screenshot()
        screenshot.save(SCREENSHOT_FILENAME)
        
        # 2. Kirim ke Gemini API
        print("[2] Mengirim gambar ke Gemini AI...")
        img = Image.open(SCREENSHOT_FILENAME)
        
        response = model.generate_content([PROMPT_GEMINI, img])
        answer = response.text
        
        print("\n=== JAWABAN GEMINI ===")
        print(answer)
        print("======================\n")
        
        # 3. Kirim ke WhatsApp via Bot
        print("[3] Mengirimkan jawaban ke WhatsApp...")
        send_to_wa_bot(answer)

    except Exception as e:
         print(f"[ERROR] Kegagalan sistem: {e}")
    finally:
        print("--- Proses selesai ---")

def main():
    print("="*40)
    print("SISTEM AUTOMATION SCREENSHOT TO GEMINI")
    print("="*40)
    if GEMINI_API_KEY == "MASUKKAN_API_KEY_GEMINI_ANDA_DISINI":
         print("Peringatan: Harap ganti GEMINI_API_KEY di script dengan API key valid Anda.")
         
    print("Sistem berjalan... Tekan Ctrl+C untuk menghentikan.")
    
    try:
        while True:
            process_screenshot_and_solve()
            
            # Loop setiap 1 menit (60 detik)
            print("Menunggu 60 detik untuk cycle berikutnya...\n")
            time.sleep(60)
            
    except KeyboardInterrupt:
        print("\nSistem dihentikan oleh user.")

if __name__ == "__main__":
    main()
