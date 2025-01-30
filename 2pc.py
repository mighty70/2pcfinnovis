import time
import threading
from flask import Flask, request, jsonify

app = Flask(__name__)

# --- Глобальные переменные ---
pc_data = {}
current_game_state = "waiting"
final_result = None
start_time = None
game_history = []
REQUIRED_PCS = 2
lock = threading.Lock()

def reset_state():
    """Сбрасываем состояние через 10 секунд после первого ID"""
    global pc_data, current_game_state, start_time, final_result
    time.sleep(5)
    with lock:
        pc_data.clear()
        current_game_state = "waiting"
        start_time = None
        final_result = None

def check_all_and_reset():
    """Через 5 секунд выставляем accept/reject, через 10 сбрасываем"""
    global current_game_state, final_result
    time.sleep(5)
    with lock:
        if len(pc_data) < REQUIRED_PCS:
            final_result = "reject"
        else:
            all_lobby_ids = {data[0] for data in pc_data.values()}
            final_result = "accept" if len(all_lobby_ids) == 1 else "reject"
        current_game_state = final_result
        if final_result == "accept":
            game_history.insert(0, {
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "lobby_id": list(all_lobby_ids)[0],
                "status": "Game started"
            })
    elapsed = time.time() - start_time
    remain = 10 - elapsed
    if remain > 0:
        time.sleep(remain)
    reset_state()

@app.route("/send_lobby_id", methods=["POST"])
def send_lobby_id():
    """Приём лобби ID от ПК"""
    global start_time
    data = request.json
    if not data or "lobby_id" not in data or "pc" not in data:
        return jsonify({"error": "Invalid data"}), 400
    with lock:
        pc_data[data["pc"]] = (data["lobby_id"], time.time())
        if start_time is None:
            start_time = time.time()
            threading.Thread(target=check_all_and_reset).start()
    return jsonify({"status": "received"})

@app.route("/check_status", methods=["GET"])
def check_status():
    """ПК проверяет статус"""
    with lock:
        return jsonify({"status": final_result if final_result else "pending"})

@app.route("/game_history", methods=["GET"])
def get_game_history():
    """Получение истории игр"""
    return jsonify(game_history)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
