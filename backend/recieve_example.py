from flask import Flask, request, jsonify
from flask_cors import CORS

#behör cors!!!!
app = Flask(__name__)
CORS(app)  # <- lägger till CORS-stöd

@app.route('/recieve', methods=['POST'])
def receive_json():
    data = request.get_json()
    print("📥 JSON-mottaget från frontend:")
    print(data)
    return jsonify({"status": "OK", "received": data}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5173, debug=True)
