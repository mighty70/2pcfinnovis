import time
import threading
from flask import Flask, request, jsonify

app = Flask(__name__)

# --- Глобальные переменные ---
pc_data = {}
current_game_state = "waiting"
final_result = None
start_time = None
REQUIRED_PCS = 2
lock = threading.Lock()
response_queue = []  # Очередь ПК, которым нужно отправить ответ

def process_lobby():
    """Обрабатываем запросы и отправляем ответы по очереди"""
    global current_game_state, final_result
    time.sleep(5)
    with lock:
        if len(pc_data) < REQUIRED_PCS:
            final_result = "reject"
        else:
            all_lobby_ids = {data[0] for data in pc_data.values()}
            final_result = "accept" if len(all_lobby_ids) == 1 else "reject"
        current_game_state = final_result
        response_queue.extend(pc_data.keys())  # Добавляем ПК в очередь на ответ
        if final_result == "reject":
            pc_data.clear()
            current_game_state = "waiting"

@app.route("/send_lobby_id", methods=["POST"])
def send_lobby_id():
    """Приём лобби ID от ПК"""
    global start_time
    data = request.json
    if not data or "lobby_id" not in data or "pc" not in data:
        return jsonify({"error": "Invalid data"}), 400
    with lock:
        if not pc_data:  # Ждем первого ПК
            start_time = time.time()
            threading.Thread(target=process_lobby).start()
        pc_data[data["pc"]] = (data["lobby_id"], time.time())
    return jsonify({"status": "received"})

@app.route("/check_status", methods=["GET"])
def check_status():
    """ПК проверяет статус"""
    pc_name = request.args.get("pc")
    with lock:
        if pc_name in response_queue:
            response_queue.remove(pc_name)  # Отправляем ответ только 1 раз
            return jsonify({"status": final_result})
        return jsonify({"status": "pending"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
