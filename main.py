"""
--- Библиотеки ---

termcolor                  # Для цветных надписей
subprocess                 # Для поиска локальных устройств и т. д.
os                         # Для выполнения системных команд или получения данных о системе
requests                   # Для чата по локальной сети
time
threading                  # Для сканирований или процессов в фоне
socket

from tkinter.messagebox import showerror, showinfo, showwarning     # Для уведомлений 

"""

import os
import time
import socket
import threading
import random
import webbrowser
import logging
import sys

from tkinter.messagebox import showerror, showinfo, showwarning, askyesno     # Для уведомлений 

# --------------------- Настройки ---------------------

LocalNetworkScanEnabled = True          # Есть ли доступ к поиску по локальной сети  =  есть ли ограничения?
DISCOVERY_PORT = 43782                  # Порт обнаружения и передачи данных в локальной сети (не обязательно менять, менять если конфликт портов)
BUFFER_SIZE = 1024                      # Максимальное количество байт данных, которое программа может принять или отправить за один раз (не обязательно менять)
LOCK_PORT = 45678

# -----------------------------------------------------



# Предефайн переменных
global lastActivated
lastActivated = None

global debug
debug = False

global ip_list
ip_list = []

global attempt
attempt = 0

global messages
messages = {
    "global": {
        "Info": {
            "Name": "Локальный чат",
            "Description": "Чат со всеми пользователями, обнаруженные в локальной сети",
            "Users": "all",
            "AvalibleMessages": {
                
            }
        }
    }
}

global lastMessage
if debug:
    lastMessage = "[INFO] Включен режим разработчика"
else:
    lastMessage = ""

discovery_thread = None
discovery_running = False
discovery_socket = None

# Функции для дебага
def warn(msg):
    if debug:
        global lastMessage

        lastMessage = f"[WARN] {msg}"

def error(msg):
    if debug:
        global lastMessage

        lastMessage = f"[ERROR] {msg}"

def info(msg):
    if debug:
        global lastMessage
        lastMessage = f"[INFO] {msg}"

def msg(msg):
    global lastMessage
    lastMessage = f"{msg}"

# Поиск по локальной сети
def start_local_discovery():
    global discovery_thread, discovery_running, discovery_socket

    if discovery_running:
        return

    discovery_running = True

    def listen():
        global discovery_socket
        discovery_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        discovery_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            discovery_socket.bind(('', DISCOVERY_PORT))
            msg(f"Обнаружение вашего устройства запущено на порту {DISCOVERY_PORT}")

            while True:
                try:
                    discovery_socket.settimeout(1.0)
                    data, addr = discovery_socket.recvfrom(BUFFER_SIZE)
                    message = data.decode()
                    info(f"Получено сообщение от {addr}: {message}")
                except socket.timeout:
                    if not discovery_running:
                        break
                    continue
                except OSError as e:
                    if e.errno == 10038:
                        break
                    else:
                        error(f"Неизвестная ошибка: {e}")
                        break
                except Exception as e:
                    error(f"Ошибка: {e}")
                    break
        finally:
            if discovery_socket:
                discovery_socket.close()
            msg("Обнаружение вашего устройства отключено")

    discovery_thread = threading.Thread(target=listen)
    discovery_thread.start()

def stop_local_discovery():
    global discovery_running, discovery_thread, discovery_socket
    if not discovery_running:
        warn("Обнаружение не запущено.")
        return
    discovery_running = False
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.sendto(b'', ('127.0.0.1', DISCOVERY_PORT))
    except Exception:
        pass
    if discovery_thread is not None:
        discovery_socket.close()

# Функции

def random_id():
    return random.randint(111111, 9999999)

def censor_text(text):
    return text

def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    ip = s.getsockname()[0]
    s.close()

    return ip

def scan_network(network_cidr, port=43782, max_workers=50):
    global ip_list

    my_ip = get_local_ip()

    ip_list.clear()
    ips = [str(ip) for ip in ipaddress.IPv4Network(network_cidr)]
    def check_ip(ip):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(0.5)
        try:
            result = sock.connect_ex((ip, port))
            if result == 0:
                if my_ip != ip:
                    ip_list.append(ip)
            return ip, result == 0
        except:
            return ip, False
        finally:
            sock.close()

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(check_ip, ip) for ip in ips]
        for future in as_completed(futures):
            pass

def send_to(ip, message, sender, channel):
    if ip != str(get_local_ip()):
        try:
            result = requests.post(
                f"http://{str(ip)}:{DISCOVERY_PORT}/receive",
                json={"message": message, "sender": sender, "channel": str(channel)}
            )
            response_json = result.json()
        except Exception as e:
            error(f"Ошибка отправки сообщения: {e}")
            return
        status = response_json.get("status")
        if str(status) == "ok":
            return 200
        else:
            error(f"Ошибка отправки, код ошибки: {str(status)}")

def open_web():
    time.sleep(4)
    webbrowser.open_new_tab("http://127.0.0.1:43782")

def check_if_started():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind(("127.0.0.1", LOCK_PORT))
    except socket.error:
        from tkinter.messagebox import showerror
        showerror("Ошибка", "Программа уже запущена!")
        webbrowser.open_new_tab("http://127.0.0.1:43782")
        sys.exit()
    return s

# Проверка настроек 

if __name__ == "__main__":
    if debug:print("Инициализация библиотек и проверка данных...")
    lock_socket = check_if_started()

    try:                  # Установить библиотеки если не установлены
        import termcolor
        import subprocess 
        
        import requests
        from flask_cors import CORS
        import ipaddress
        from concurrent.futures import ThreadPoolExecutor, as_completed
        from flask import Flask, jsonify, request, render_template
    except Exception as e:
        if askyesno("Не удалось запустить программу", "Не удалось найти некоторые библиотеки, вы хотите установить их сейчас?"):
            showinfo("Установка библиотек", "Установка последних версий... \n\nПрограмма будет автоматически перезапущена")
            os.system("pip install requests termcolor flask flask_cors")
        else:
            showerror("Критическая ошибка", "Не удалось корректно запустить программу, пожалуйста установите библиотеки самостоятельно")
            os.abort()
    time.sleep(2)
    try:
        import termcolor
        import subprocess 
        import ipaddress
        from flask_cors import CORS
        from concurrent.futures import ThreadPoolExecutor, as_completed
        
        import requests
        from flask import Flask, jsonify, request, render_template
    except Exception as e:
        showerror("Ошибка", "Не удалось установить библиотеки, установите библиотеки самостоятельно.")
        os.abort()

    if DISCOVERY_PORT == "" or DISCOVERY_PORT == None:
        error("Порт не выбран")
        os.abort()
    elif DISCOVERY_PORT < 500:
        error("Порт не доступен. Используйте порт от 500 до 50000")
        os.abort()
    elif DISCOVERY_PORT > 50000:
        error("Порт не доступен. Используйте порт от 500 до 50000")
        os.abort()

    if BUFFER_SIZE == None:
        error("BUFFER_SIZE - неверное значение.")
        os.abort()
    termcolor.cprint("Получение текущего IP...", "blue")
    local_ip = get_local_ip()
    network_cidr = '.'.join(local_ip.split('.')[:-1]) + '.0/24'

    ip_list = []
    termcolor.cprint("Сканирование сети...", "blue")
    scan_network(network_cidr)

    termcolor.cprint("Инициализация завершена!", "green", end="")
    termcolor.cprint("\nЗапуск веб-сервера...", "blue")

app = Flask(__name__)
CORS(app)

# API

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/send_message', methods=['POST'])
def send_message():
    global ip_list, messages

    try:
        data = request.get_json(force=True)
        from_ip = data.get('IP', 'unknown')
        message_text = data.get('Message', '').strip()
        to_ip = data.get('To')

        if not message_text:
            return jsonify({'result': 'empty'}), 400
        if not to_ip:
            return jsonify({'result': 'error', 'message': 'No target channel specified'}), 400

        msg_id = str(random_id())
        timestamp = int(time.time())

        if to_ip not in messages:
            messages[to_ip] = {"Info": {"Name": to_ip, "Description": "", "Users": "", "AvalibleMessages": {}}}

        messages[to_ip]["Info"]["AvalibleMessages"][msg_id] = {
            "text": message_text,
            "user": from_ip,
            "timestamp": timestamp }

        if to_ip == "global":
            local_ip = get_local_ip()
            network_cidr = '.'.join(local_ip.split('.')[:-1]) + '.0/24'

            ip_list.clear()
            scan_network(network_cidr)

            for target in ip_list:
                try:
                    if target != get_local_ip():
                        send_to(target, message_text, from_ip, to_ip)
                except Exception as e:
                    warn(f"Не удалось отправить сообщение {msg_id} на {target}: {e}")

    except Exception as e:
        error(f"Ошибка: {e}")
        return jsonify({'result': 'error', 'message': str(e)}), 500

    info(f"Сообщение {msg_id} отправлено в канал {to_ip}: {message_text}")
    return jsonify({'result': 'ok', 'id': msg_id}), 200


@app.route('/get_messages', methods=['POST', 'GET'])
def get_messages():
    try:
        if request.method == 'GET':
            Channel = request.args.get('Channel')
        else:
            data = request.get_json()
            if not data:
                return jsonify({'result': 'error', 'message': 'No JSON data received'}), 400
            Channel = data.get('Channel')

        if not Channel:
            return jsonify({'result': 'error', 'message': 'Channel parameter missing'}), 400

        if Channel not in messages:
            return jsonify({'result': 'error', 'message': 'Channel not found'}), 404

        return jsonify(messages[Channel]["Info"]["AvalibleMessages"]), 200

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'result': 'error', 'message': str(e)}), 500

@app.route("/receive", methods=['POST'])
def receive_msg():
    data = request.get_json()
    channel = data['channel']
    msg_id = str(random_id())

    if channel not in messages:
        messages[channel] = {
            "Info": {"Name": channel, "Description": "", "Users": "", "AvalibleMessages": {}}
        }

    messages[channel]["Info"]["AvalibleMessages"][msg_id] = {"text": data['message'], "user": data['sender'], "timestamp": int(time.time())}
    return '', 200

@app.route("/request-ip", methods=['GET'])
def get_ip():
    ip = str(get_local_ip())
    return jsonify({"IP": ip})

@app.route("/shutdown", methods=['GET'])
def exit():
    os.abort()

@app.route("/members", methods=['GET', 'POST'])
def get_members():
    count = len(ip_list) + 1
    return jsonify({"members": str(count)})

@app.route('/status', methods=['GET', 'POST'])
def status():
    return jsonify({'lastMessage': str(lastMessage)}), 200

if __name__ == '__main__':
    threading.Thread(target=open_web(), daemon=True)

    log = logging.getLogger('werkzeug')
    log.setLevel(logging.ERROR)

    app.run(debug=False, port=43782, host='0.0.0.0')