import os
import time
import re
from collections import defaultdict
from flask import Flask, request, jsonify, send_from_directory

app = Flask(__name__, static_folder='static', static_url_path='/static')

# Mock databases
leads_db = []
orders_db = {
    "BM12345": {"order_id": "BM12345", "status": "paid", "customer": "Nguyen Van A", "total": "250,000 VND", "items": ["Nhà Giả Kim"], "shipping_address": "123 Nguyen Trai, Q.5, TP.HCM"},
    "BM67890": {"order_id": "BM67890", "status": "shipping", "customer": "Tran Thi B", "total": "420,000 VND", "items": ["Đắc Nhân Tâm", "Đọc Vị Bất Kỳ Ai"], "shipping_address": "456 Le Loi, Q.1, TP.HCM"},
    "BM11223": {"order_id": "BM11223", "status": "pending", "customer": "Le Van C", "total": "180,000 VND", "items": ["Sách Cho Người Mới Đi Làm"], "shipping_address": "789 CMT8, Q.10, TP.HCM"},
    "BM44556": {"order_id": "BM44556", "status": "delivered", "customer": "Pham Minh D", "total": "310,000 VND", "items": ["Đầu Tư Tài Chính"], "shipping_address": "321 Dien Bien Phu, Q. Bình Thạnh, TP.HCM"},
    "BM77889": {"order_id": "BM77889", "status": "cancelled", "customer": "Hoang Thi E", "total": "95,000 VND", "items": ["Đọc Vị Bất Kỳ Ai"], "shipping_address": "147 Ly Tu Trong, Q.1, TP.HCM"},
    "BM99001": {"order_id": "BM99001", "status": "refunded", "customer": "Vu Van F", "total": "86,000 VND", "items": ["Đắc Nhân Tâm"], "shipping_address": "963 Tran Hung Dao, Q.5, TP.HCM"},
    "BM22334": {"order_id": "BM22334", "status": "returning", "customer": "Ngo Thi G", "total": "158,000 VND", "items": ["Nhà Giả Kim", "Đắc Nhân Tâm"], "shipping_address": "159 Ba Thang Hai, Q.10, TP.HCM"},
}
products_db = [
    {"id": 1, "title": "Nhà Giả Kim", "author": "Paulo Coelho", "price": "79,000 VND", "category": "Kỹ năng sống", "description": "Một cuốn sách triết lý sâu sắc về việc theo đuổi ước mơ."},
    {"id": 2, "title": "Đắc Nhân Tâm", "author": "Dale Carnegie", "price": "86,000 VND", "category": "Phát triển bản thân", "description": "Sách gối đầu giường của mọi thời đại về nghệ thuật giao tiếp và thu phục lòng người."},
    {"id": 3, "title": "Đọc Vị Bất Kỳ Ai", "author": "David J. Lieberman", "price": "95,000 VND", "category": "Tâm lý học", "description": "Để không bị lừa dối và lợi dụng, hiểu thấu tâm lý người đối diện."},
    {"id": 4, "title": "Sách Cho Người Mới Đi Làm", "author": "Nhiều tác giả", "price": "120,000 VND", "category": "Kinh doanh", "description": "Kỹ năng làm việc hiệu quả, thích nghi nhanh với môi trường công sở."},
    {"id": 5, "title": "Đầu Tư Tài Chính", "author": "Zvi Bodie", "price": "350,000 VND", "category": "Tài chính", "description": "Kiến thức hàn lâm chuyên sâu về thị trường chứng khoán và quản lý danh mục đầu tư."},
]

escalations_db = []

# Rate limiter setup: 10 messages per 60 seconds per IP
rate_limit_records = defaultdict(list)
RATE_LIMIT_MAX = 10
RATE_LIMIT_WINDOW = 60 # seconds

def check_rate_limit(ip: str) -> bool:
    current_time = time.time()
    # Filter out requests older than 60 seconds
    rate_limit_records[ip] = [t for t in rate_limit_records[ip] if current_time - t < RATE_LIMIT_WINDOW]
    if len(rate_limit_records[ip]) >= RATE_LIMIT_MAX:
        return False
    rate_limit_records[ip].append(current_time)
    return True

# Serving index.html directly on root
@app.route("/")
def get_index():
    return send_from_directory('static', 'index.html')

# CORS Header helper (since flask_cors is not installed to keep dependencies minimal)
@app.after_request
def add_cors_headers(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type,Authorization'
    response.headers['Access-Control-Allow-Methods'] = 'GET,PUT,POST,DELETE,OPTIONS'
    return response

# Handle preflight options requests
@app.route("/api/<path:path>", methods=["OPTIONS"])
def handle_options(path):
    return "", 200

# API Endpoints
@app.route("/api/leads", methods=["POST"])
def create_lead():
    data = request.get_json() or {}
    name = data.get("name", "").strip()
    email = data.get("email", "").strip()
    phone = data.get("phone", "").strip()
    
    if not name or not email or not phone:
        return jsonify({"detail": "Vui lòng nhập đầy đủ Tên, Email và Số điện thoại."}), 400
        
    # Email check
    if not re.match(r"^[\w.+-]+@[\w-]+\.[a-z]{2,}$", email, re.IGNORECASE):
        return jsonify({"detail": "Định dạng email không hợp lệ."}), 400
        
    # Phone check
    if not re.match(r"^(0|\+84)[0-9]{9}$", phone):
        return jsonify({"detail": "Định dạng số điện thoại không hợp lệ (cần 10 chữ số bắt đầu bằng 0 hoặc +84)."}), 400
        
    lead = {"name": name, "email": email, "phone": phone}
    leads_db.append(lead)
    print(f"[Lead Gen] New lead recorded: {lead}")
    return jsonify({"status": "success", "message": "Thông tin liên hệ của bạn đã được ghi nhận."})

@app.route("/api/orders/<order_id>", methods=["GET"])
def get_order(order_id):
    order = orders_db.get(order_id.upper().strip())
    if not order:
        return jsonify({"detail": "Không tìm thấy mã đơn hàng này. Vui lòng kiểm tra lại."}), 404
    return jsonify(order)

@app.route("/api/products/search", methods=["GET"])
def search_products():
    q = request.args.get("q", "").strip()
    query = q.lower()
    results = []
    for product in products_db:
        if query in product["title"].lower() or query in product["description"].lower() or query in product["category"].lower():
            results.append(product)
    return jsonify(results)

@app.route("/api/chat/escalate", methods=["POST"])
def escalate_chat():
    data = request.get_json() or {}
    session_id = data.get("session_id", "default_session")
    escalations_db.append({"session_id": session_id, "timestamp": time.time(), "status": "pending"})
    print(f"[Escalation] Session {session_id} escalated to human agent.")
    return jsonify({"status": "success", "message": "Đã chuyển phiên chat cho nhân viên hỗ trợ."})

# Load environment variabless
from dotenv import load_dotenv
import httpx

load_dotenv()
N8N_WEBHOOK_URL = os.getenv("N8N_WEBHOOK_URL", "https://sunbv56.app.n8n.cloud/webhook-test/bookmedi-webhook")
N8N_USERNAME = os.getenv("N8N_USERNAME")
N8N_PASSWORD = os.getenv("N8N_PASSWORD")

@app.route("/api/chat/message", methods=["POST"])
def send_message():
    # Rate limit check
    client_ip = request.remote_addr
    if not check_rate_limit(client_ip):
        return jsonify({"detail": "Bạn đã gửi quá nhiều tin nhắn. Vui lòng thử lại sau 1 phút (Tối đa 10 tin nhắn/phút)."}), 429
        
    data = request.get_json() or {}
    message = data.get("message")
    message = str(message).strip() if message is not None else ""
    session_id = data.get("session_id")
    session_id = str(session_id).strip() if session_id is not None else ""
    user_name = data.get("user_name")
    user_name = str(user_name).strip() if user_name is not None else ""
    
    msg = message.lower()
    
    # Try forwarding to production n8n webhook first
    if N8N_WEBHOOK_URL:
        try:
            print(f"[Proxy] Forwarding to n8n: {N8N_WEBHOOK_URL} (Auth: {'Yes' if N8N_USERNAME else 'No'})")
            # Construct multipart/form-data format matching the Postman screenshot
            files = {
                "message": (None, message),
                "session_id": (None, session_id),
                "user_name": (None, user_name),
                "chatId": (None, session_id),
            }
            
            auth = (N8N_USERNAME, N8N_PASSWORD) if N8N_USERNAME and N8N_PASSWORD else None
            
            # Send sync POST with timeout as multipart/form-data
            response = httpx.post(N8N_WEBHOOK_URL, files=files, auth=auth, timeout=20.0)
            
            if response.status_code in [200, 201]:
                n8n_data = response.json()
                print(f"[Proxy] n8n response: {n8n_data}")
                
                # n8n lastNode returns could be a list or direct dict
                reply_text = ""
                buttons = []
                escalated = False
                
                if isinstance(n8n_data, list) and len(n8n_data) > 0:
                    item = n8n_data[0]
                else:
                    item = n8n_data
                
                # Extract text output from AI Agent or standard nodes
                if isinstance(item, dict):
                    reply_text = item.get("output") or item.get("text") or item.get("reply") or ""
                    buttons = item.get("buttons", [])
                    escalated = item.get("escalated", False)
                elif isinstance(item, str):
                    reply_text = item
                
                if not reply_text:
                    # Fallback text if n8n returned empty output properties but succeeded
                    reply_text = str(item)
                
                return jsonify({
                    "reply": reply_text,
                    "buttons": buttons,
                    "escalated": escalated
                })
            else:
                print(f"[Proxy Warning] n8n responded with status {response.status_code}: {response.text}")
                return jsonify({
                    "reply": f"⚠️ **Lỗi n8n workflow (HTTP {response.status_code})**: {response.text}\nVui lòng kiểm tra mục **Executions** (Lịch sử chạy) trên giao diện n8n cloud để xem chi tiết node nào bị lỗi."
                })
        except Exception as e:
            print(f"[Proxy Error] Failed to connect to n8n webhook: {str(e)}")
            return jsonify({
                "reply": f"⚠️ **Lỗi kết nối đến n8n**: {str(e)}\nKhông thể gọi webhook {N8N_WEBHOOK_URL}. Vui lòng kiểm tra cấu hình trong file `.env`."
            })
            # Fall back to rule-based mock for testing if n8n is offline or building

    # Rule-based fallback replies for local testing / when n8n webhook is not activated
    if "đơn hàng" in msg or "giao hàng" in msg:
        return jsonify({
            "reply": "Để tra cứu đơn hàng, vui lòng nhập mã đơn hàng của bạn (Ví dụ: BM12345) hoặc click nút 'Vận chuyển & Giao hàng' bên dưới.",
            "buttons": [{"label": "Vận chuyển & Giao hàng", "value": "check_order"}]
        })
    elif "sách" in msg or "tìm sách" in msg:
        return jsonify({
            "reply": "Tôi có thể giúp bạn tìm các sách phù hợp. Bạn muốn tìm sách thể loại gì? (Ví dụ: kỹ năng sống, kinh doanh...)",
            "buttons": [{"label": "Tìm kiếm sách", "value": "search_books"}]
        })
    elif "hỗ trợ" in msg or "nhân viên" in msg or "gặp người" in msg:
        escalations_db.append({"session_id": session_id, "timestamp": time.time(), "status": "pending"})
        return jsonify({
            "reply": "Tôi đang chuyển bạn gặp nhân viên hỗ trợ. Vui lòng đợi trong giây lát... 🕒",
            "escalated": True
        })
    
    # Check if this matches a order search directly
    match = re.search(r"BM\d{5}", message, re.IGNORECASE)
    if match:
        order_id = match.group(0).upper()
        order = orders_db.get(order_id)
        if order:
            status_vn = {
                "paid": "Đã thanh toán (Paid)",
                "shipping": "Đang giao hàng (Shipping)",
                "pending": "Chưa thanh toán (Pending)",
                "delivered": "Đã giao hàng thành công (Delivered)",
                "cancelled": "Đã hủy đơn (Cancelled)",
                "refunded": "Đã hoàn tiền (Refunded)",
                "returning": "Đang chuyển hoàn (Returning)"
            }.get(order['status'], order['status'])
            
            return jsonify({
                "reply": f"Mã đơn hàng: {order['order_id']}\nTrạng thái: {status_vn}\nKhách hàng: {order['customer']}\nSách: {', '.join(order['items'])}\nĐịa chỉ: {order['shipping_address']}\nTổng thanh toán: {order['total']}"
            })
    
    return jsonify({
        "reply": f"Chào {user_name or 'bạn'}! Tôi là AI Sales Assistant của Bookmedi. Tôi đã nhận được tin nhắn: '{message}'. (Lưu ý: n8n webhook tại cloud đang ngoại tuyến hoặc chưa kích hoạt, đây là phản hồi tự động từ Localhost)."
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
