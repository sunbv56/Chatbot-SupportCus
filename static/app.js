// Bookmedi AI Assistant Client Controller
document.addEventListener("DOMContentLoaded", () => {
    // DOM Elements
    const chatTrigger = document.getElementById("chatTrigger");
    const chatPanel = document.getElementById("chatPanel");
    const minimizeChat = document.getElementById("minimizeChat");
    const clearChat = document.getElementById("clearChat");
    const chatMessages = document.getElementById("chatMessages");
    const messageInput = document.getElementById("messageInput");
    const sendBtn = document.getElementById("sendBtn");
    const quickOptions = document.getElementById("quickOptions");
    const leadFormOverlay = document.getElementById("leadFormOverlay");
    const leadForm = document.getElementById("leadForm");
    const closeLeadForm = document.getElementById("closeLeadForm");
    const rateLimitOverlay = document.getElementById("rateLimitOverlay");
    const rateLimitProgress = document.getElementById("rateLimitProgress");
    const rateLimitMessage = document.getElementById("rateLimitMessage");
    const demoChatBtn = document.getElementById("demoChatBtn");

    const API_BASE = window.location.origin;

    // Chat Session ID & User Data
    let sessionId = localStorage.getItem("bookmedi_chat_session");
    if (!sessionId) {
        sessionId = "sess_" + Math.random().toString(36).substring(2, 15);
        localStorage.setItem("bookmedi_chat_session", sessionId);
    }
    
    let isLeadSubmitted = localStorage.getItem("bookmedi_lead_submitted") === "true";
    let userData = JSON.parse(localStorage.getItem("bookmedi_user_data") || "null");

    // Toggle Chat Widget Open/Close
    function toggleChat(forceState = null) {
        const isOpen = forceState !== null ? forceState : !chatPanel.classList.contains("open");
        
        if (isOpen) {
            chatPanel.classList.add("open");
            document.querySelector(".trigger-open-icon").classList.add("hidden");
            document.querySelector(".trigger-close-icon").classList.remove("hidden");
            document.querySelector(".notification-badge").classList.add("hidden");
            
            // Check if lead capture is required
            if (!isLeadSubmitted) {
                leadFormOverlay.classList.remove("hidden");
            } else {
                messageInput.focus();
            }
        } else {
            chatPanel.classList.remove("open");
            document.querySelector(".trigger-open-icon").classList.remove("hidden");
            document.querySelector(".trigger-close-icon").classList.add("hidden");
        }
    }

    chatTrigger.addEventListener("click", () => toggleChat());
    minimizeChat.addEventListener("click", () => toggleChat(false));
    demoChatBtn.addEventListener("click", () => toggleChat(true));

    // Handle inputs changes
    messageInput.addEventListener("input", () => {
        sendBtn.disabled = messageInput.value.trim() === "";
    });

    // Clear Chat History
    clearChat.addEventListener("click", () => {
        if (confirm("Bạn có chắc chắn muốn xoá toàn bộ lịch sử trò chuyện không?")) {
            // Clear DOM
            chatMessages.innerHTML = `
                <div class="message system-message">
                    Lịch sử chat đã được làm sạch.
                </div>
                <div class="message bot-message">
                    <div class="message-content">
                        Tôi có thể hỗ trợ gì khác cho bạn không?
                    </div>
                    <span class="message-time">${getCurrentTime()}</span>
                </div>
            `;
            // Reset Session
            sessionId = "sess_" + Math.random().toString(36).substring(2, 15);
            localStorage.setItem("bookmedi_chat_session", sessionId);
        }
    });

    // Lead Form Handlers
    closeLeadForm.addEventListener("click", () => {
        leadFormOverlay.classList.add("hidden");
        isLeadSubmitted = true; // Temporary bypass for guest session
        messageInput.focus();
    });

    leadForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        const name = document.getElementById("leadName").value.trim();
        const email = document.getElementById("leadEmail").value.trim();
        const phone = document.getElementById("leadPhone").value.trim();

        // Regex Validations
        const emailRegex = /^[\w.+-]+@[\w-]+\.[a-z]{2,}$/i;
        const phoneRegex = /^(0|\+84)[0-9]{9}$/;

        if (!emailRegex.test(email)) {
            alert("Email không đúng định dạng.");
            return;
        }
        if (!phoneRegex.test(phone)) {
            alert("Số điện thoại không đúng định dạng (VD: 0901234567).");
            return;
        }

        try {
            const response = await fetch(`${API_BASE}/api/leads`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ name, email, phone })
            });

            const result = await response.json();
            
            if (response.ok) {
                isLeadSubmitted = true;
                userData = { name, email, phone };
                localStorage.setItem("bookmedi_lead_submitted", "true");
                localStorage.setItem("bookmedi_user_data", JSON.stringify(userData));
                
                leadFormOverlay.classList.add("hidden");
                
                // Add a welcome bot message for the user
                appendMessage("bot", `Cảm ơn anh/chị **${name}** đã cung cấp thông tin. Em đã sẵn sàng hỗ trợ anh/chị rồi ạ!`);
                messageInput.focus();
            } else {
                alert(result.detail || "Đã xảy ra lỗi khi gửi thông tin.");
            }
        } catch (error) {
            console.error("Error submitting lead:", error);
            alert("Không thể kết nối đến server backend.");
        }
    });

    // Message Rendering Helpers
    function getCurrentTime() {
        const now = new Date();
        return now.getHours().toString().padStart(2, '0') + ":" + now.getMinutes().toString().padStart(2, '0');
    }

    function appendMessage(sender, text, customElement = null) {
        const messageDiv = document.createElement("div");
        messageDiv.classList.add("message", sender === "user" ? "user-message" : "bot-message");

        const contentDiv = document.createElement("div");
        contentDiv.classList.add("message-content");
        
        // Simple bold markdown replacement
        let formattedText = text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
        formattedText = formattedText.replace(/\n/g, '<br>');
        contentDiv.innerHTML = formattedText;

        messageDiv.appendChild(contentDiv);

        if (customElement) {
            messageDiv.appendChild(customElement);
        }

        const timeSpan = document.createElement("span");
        timeSpan.classList.add("message-time");
        timeSpan.innerText = getCurrentTime();
        messageDiv.appendChild(timeSpan);

        chatMessages.appendChild(messageDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    // Typing Indicator
    let typingIndicatorElement = null;
    function showTypingIndicator() {
        if (typingIndicatorElement) return;

        typingIndicatorElement = document.createElement("div");
        typingIndicatorElement.classList.add("typing-indicator", "message", "bot-message");
        typingIndicatorElement.innerHTML = `
            <div class="typing-dot"></div>
            <div class="typing-dot"></div>
            <div class="typing-dot"></div>
        `;
        chatMessages.appendChild(typingIndicatorElement);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    function removeTypingIndicator() {
        if (typingIndicatorElement) {
            typingIndicatorElement.remove();
            typingIndicatorElement = null;
        }
    }

    // Rate Limiter Visual Counter
    function triggerRateLimit(seconds = 60) {
        rateLimitOverlay.classList.remove("hidden");
        rateLimitProgress.style.width = "0%";
        
        let remaining = seconds;
        rateLimitMessage.innerText = `Bạn đã đạt giới hạn 10 tin nhắn/phút. Vui lòng đợi ${remaining} giây...`;
        
        const interval = setInterval(() => {
            remaining--;
            if (remaining <= 0) {
                clearInterval(interval);
                rateLimitOverlay.classList.add("hidden");
            } else {
                rateLimitMessage.innerText = `Bạn đã đạt giới hạn 10 tin nhắn/phút. Vui lòng đợi ${remaining} giây...`;
                const percentage = ((seconds - remaining) / seconds) * 100;
                rateLimitProgress.style.width = `${percentage}%`;
            }
        }, 1000);
    }

    // Send message to Backend
    async function sendMessage(text) {
        if (!text.trim()) return;

        appendMessage("user", text);
        messageInput.value = "";
        sendBtn.disabled = true;

        showTypingIndicator();

        try {
            const response = await fetch(`${API_BASE}/api/chat/message`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    session_id: sessionId,
                    message: text,
                    user_name: userData ? userData.name : null
                })
            });

            removeTypingIndicator();

            if (response.status === 429) {
                // Rate limited
                triggerRateLimit(60);
                return;
            }

            const data = await response.json();
            
            if (response.ok) {
                let customElement = null;

                // Handle order structured card
                if (text.toUpperCase().includes("BM") && data.reply.includes("Mã đơn hàng:")) {
                    // It returned simulated order info, let's render standard order card!
                    // Extract properties
                    const lines = data.reply.split("\n");
                    const orderId = lines[0].split(": ")[1] || "BM";
                    const status = lines[1].split(": ")[1] || "pending";
                    const customer = lines[2].split(": ")[1] || "";
                    const books = lines[3].split(": ")[1] || "";
                    const address = lines[4].split(": ")[1] || "";
                    const total = lines[5].split(": ")[1] || "";

                    let statusClass = "pending";
                    const statusLower = status.toLowerCase();
                    if (statusLower.includes("paid")) statusClass = "paid";
                    else if (statusLower.includes("shipping")) statusClass = "shipping";
                    else if (statusLower.includes("delivered")) statusClass = "delivered";
                    else if (statusLower.includes("cancelled")) statusClass = "cancelled";
                    else if (statusLower.includes("refunded")) statusClass = "refunded";
                    else if (statusLower.includes("returning")) statusClass = "returning";

                    customElement = document.createElement("div");
                    customElement.classList.add("order-card");
                    customElement.innerHTML = `
                        <div class="order-card-header">
                            <h4>Đơn hàng ${orderId}</h4>
                            <span class="order-badge ${statusClass}">${status}</span>
                        </div>
                        <div class="order-card-body">
                            <p>Khách hàng: <strong>${customer}</strong></p>
                            <p>Sản phẩm: <strong>${books}</strong></p>
                            <p>Tổng: <strong>${total}</strong></p>
                            <p>Địa chỉ: <strong>${address}</strong></p>
                        </div>
                    `;
                    appendMessage("bot", "Thông tin chi tiết đơn hàng của anh/chị:", customElement);
                } else {
                    appendMessage("bot", data.reply);
                }

                // If buttons are provided
                if (data.buttons && data.buttons.length > 0) {
                    renderButtons(data.buttons);
                }
            } else {
                appendMessage("bot", `Lỗi: ${data.detail || "Không thể xử lý yêu cầu."}`);
            }
        } catch (error) {
            removeTypingIndicator();
            console.error("Message send error:", error);
            appendMessage("bot", "Hệ thống gặp sự cố kết nối. Vui lòng kiểm tra lại localhost server.");
        }
    }

    // Render quick action options/buttons inside chat stream
    function renderButtons(buttons) {
        const btnContainer = document.createElement("div");
        btnContainer.style.display = "flex";
        btnContainer.style.gap = "0.5rem";
        btnContainer.style.marginTop = "0.5rem";
        btnContainer.style.flexWrap = "wrap";

        buttons.forEach(btn => {
            const b = document.createElement("button");
            b.classList.add("quick-btn");
            b.innerText = btn.label;
            b.addEventListener("click", () => {
                handleQuickAction(btn.value);
            });
            btnContainer.appendChild(b);
        });

        chatMessages.appendChild(btnContainer);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    // Handle Quick Action Actions
    function handleQuickAction(action) {
        if (action === "check_order") {
            appendMessage("bot", "Vui lòng nhập mã đơn hàng của bạn để tra cứu (Ví dụ: **BM12345**):");
        } else if (action === "search_books") {
            appendMessage("bot", "Bạn đang muốn tìm sách thể loại gì? (Ví dụ: **đầu tư tài chính**, **kỹ năng sống**, **tâm lý học**...)");
        } else if (action === "escalate") {
            sendMessage("Tôi muốn gặp nhân viên hỗ trợ trực tiếp.");
        }
    }

    // Event listeners for message input
    sendBtn.addEventListener("click", () => {
        sendMessage(messageInput.value);
    });

    messageInput.addEventListener("keydown", (e) => {
        if (e.key === "Enter" && messageInput.value.trim() !== "") {
            sendMessage(messageInput.value);
        }
    });

    // Quick option panel buttons click
    quickOptions.addEventListener("click", (e) => {
        const btn = e.target.closest(".quick-btn");
        if (!btn) return;
        const val = btn.dataset.value;
        handleQuickAction(val);
    });
});
