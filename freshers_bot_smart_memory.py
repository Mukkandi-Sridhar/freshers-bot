# freshers_bot_smart_memory.py
import json
import uuid
import logging
import requests
from flask import Flask, request, jsonify, render_template_string
from datetime import datetime
import os
from flask_cors import CORS
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Access the keys
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
PUSHOVER_USER_KEY = os.getenv("PUSHOVER_USER_KEY")
PUSHOVER_APP_TOKEN = os.getenv("PUSHOVER_APP_TOKEN")
PAYMENT_AMOUNT = "₹500"
PHONEPE_NUMBER = "9392886199"
UPI_ID = "9392886199@ibl"

# -----------------------
# LOGGING
# -----------------------
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("FreshersBot")

# -----------------------
# STUDENT DATABASE
# -----------------------
STUDENTS_DB = {
    "23091A3301": "Mekala Ammar",
    "23091A3302": "Meerja Anjum",
    "23091A3305": "Andhe Bhargav",
    "23091A3306": "Sompalli Brahmini",
    "23091A3308": "Chitkela Charan",
    "23091A3309": "P Charan Kumar Reddy",
    "23091A3310": "Kaki Charitha Rani",
    "23091A3311": "Kalletti Dedeepya Varshini",
    "23091A3312": "Bethamsetty Deepthi",
    "23091A3313": "Kumarnaki Gari Dharshan",
    "23091A3318": "Bovilla Dileep Kumar Reddy",
    "23091A3319": "Gandla Eranna",
    "23091A3320": "M Giri Prasad",
    "23091A3321": "Kethepalle Guru Sai Sulekha",
    "23091A3323": "Pathuru Guru Vishnu",
    "23091A3319_1": "Veludrthi Hema",          # duplicate keys renamed
    "23091A3319_2": "Chakali Hima Bindhu",
    "23091A3320_1": "Challa Hima Vamsi Reddy",
    "23091A3321_1": "Shaik Mohammad Hussain",
    "23091A3322": "Gurumadhu Kakarl",
    "23091A3323_1": "Andra Keerthana",
    "23091A3324": "Kurimigalla Krishna Mohan",
    "23091A3325": "Kampamalla Madhavi",
    "23091A3326": "Bestha Mahesh Babu",
    "23091A3327": "Mogilipalli Mani Rupesh",
    "23091A3328": "Gopanngari Manjunath",
    "23091A3329": "Gaddam Manvitha",
    "23091A3330": "Muriki Naga Venkata Sai",
    "23091A3331": "Agraharam Naveen Kumar",
    "23091A3332": "Kyabarshi Navya",
    "23091A3333": "Pranathi Reddy K",
    "23091A3334": "Chittiboina Rajeswari",
    "23091A3335": "Boggadi Rama Devi",
    "23091A3337": "Bilavath Ramesh Naik",
    "23091A3338": "Mopuru Rushendra Phani",
    "23091A3339": "Pyaram Rushika",
    "23091A3340": "Chennuri Sai",
    "23091A3341": "Barrenkala Sai Kiranmayi",
    "23091A3342": "Tomala Sai Manaswini",
    "23091A3343": "Gaddam Sai Swaroopa Reddy",
    "23091A3344": "A Mohammed Sameer",
    "23091A3345": "Vakamalla Sanjana",
    "23091A3346": "Syed Shajida Bhanu",
    "23091A3348": "Dudekula Siddini Sharmi",
    "23091A3349": "Mukkandi Sridhar",
    "23091A3350": "Idhumulla Sudheer Kumar",
    "23091A3351": "Maddula Sumanth",
    "23091A3352": "Tagaram Sumhitha",
    "23091A3353": "Vanke Suneetha",
    "23091A3354": "Sivapuram Swapna",
    "23091A3355": "Lakkireddy Swaroopa",
    "23091A3356": "Shaik Tarannum Naaz",
    "23091A3357": "Gajulapalle Thanuja",
    "23091A3358": "Mota Thrilok",
    "23091A3359": "Palla Umesh",
    "23091A3360": "Kotha Varun Kumar",
    "23091A3361": "N Venkata Naga Joshita",
    "23091A3362": "T Venkata Naga Tejaswini",
    "23091A3363": "Gorla Vijaya Lakshmi",
    "23091A3364": "Maneri Vishnu Sai Vamsi",
    "23091A3365": "Dayyam Yashwanth",
    "24095A3301": "Phatan Afroz Ali Khan",
    "24095A3302": "Chinthala Chenna Madhavi",
    "24095A3303": "Jambula Dinesh Reddy",
    "24095A3304": "Labbi Nagarjuna",
    "24095A3305": "Pathapadu Saimanjunath",
    "24095A3306": "Gantala Sumanth",
    "24095A3307": "Suddula Venkata Sivudu",
    "23091A3304": "T Bhanu Prakash"
}

# -----------------------
# FLASK APP
# -----------------------
app = Flask(__name__)
CORS(app)

conversation_sessions = {}

SYSTEM_PROMPT = f"""
You are FPA, Freshers Payment Assistant 🤖. Your job is to guide students through the payment process for Freshers Party.

CRITICAL INFORMATION:
- STUDENT DATABASE: {json.dumps(STUDENTS_DB, indent=2)}
- PAYMENT AMOUNT: {PAYMENT_AMOUNT}
- Payment Methods: PhonePe ({PHONEPE_NUMBER}) or UPI ({UPI_ID})

RESPONSE FORMAT - YOU MUST ALWAYS RESPOND WITH VALID JSON:
{{
  "reply": "Your conversational response",
  "show_payment_buttons": true/false,
  "student_verified": true/false,
  "student_name": "Full Name" or null,
  "register_number": "23091A3301" or null,
  "payment_status": "not_started/verified/pending/completed",
  "thinking": "Internal reasoning about what to do next"
}}

CONVERSATION FLOW - THINK STEP BY STEP:
1. FIRST: Always ask for register number first. No exceptions.
2. VALIDATE: Check if register number exists in database (case insensitive)
3. VERIFIED: Once verified, greet by name and explain payment process
4. PAYMENT: Only show payment details AFTER verification
5. TRANSACTION: Ask for transaction ID after payment details are provided
6. COMPLETE: Confirm completion and celebrate

THINKING PROCESS - ALWAYS ANALYZE:
- What information do I have?
- What information do I need?
- What step comes next?
- Is the conversation progressing logically?

RULES:
- NEVER provide payment details before verifying register number
- ALWAYS maintain context - remember what we've discussed
- If user provides invalid register number, ask them to try again
- Keep responses natural and conversational
- Use emojis to make it friendly 🎉😊
- Show payment buttons ONLY after student verification
"""

def call_openai(user_message, session_id):
    """Call OpenAI API with full conversation memory."""
    if session_id not in conversation_sessions:
        conversation_sessions[session_id] = [
            {"role": "system", "content": SYSTEM_PROMPT}
        ]
    
    # Add user message to conversation history
    conversation_sessions[session_id].append({"role": "user", "content": user_message})
    
    # Keep only last 10 messages to prevent token overflow
    if len(conversation_sessions[session_id]) > 12:  # system + 10 messages + new user
        conversation_sessions[session_id] = [conversation_sessions[session_id][0]] + conversation_sessions[session_id][-10:]
    
    payload = {
        "model": "gpt-4o",
        "messages": conversation_sessions[session_id],
        "temperature": 0.7,
        "max_tokens": 350
    }
    headers = {"Authorization": f"Bearer {OPENAI_API_KEY}", "Content-Type": "application/json"}

    try:
        logger.info(f"Calling OpenAI API for session {session_id}")
        r = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload, timeout=20)
        if r.status_code == 200:
            ai_response = r.json()["choices"][0]["message"]["content"]
            # Add AI response to conversation history
            conversation_sessions[session_id].append({"role": "assistant", "content": ai_response})
            logger.info("OpenAI API call successful")
            return ai_response
        else:
            logger.error(f"OpenAI error: {r.status_code} {r.text}")
            return json.dumps({
                "reply": "Technical issue. Please try again! 🔧",
                "show_payment_buttons": False,
                "student_verified": False,
                "student_name": None,
                "register_number": None,
                "payment_status": "not_started",
                "thinking": "API error occurred"
            })
    except Exception as e:
        logger.error(f"OpenAI call failed: {e}")
        return json.dumps({
            "reply": "Connection issue. Please check your internet! 🌐",
            "show_payment_buttons": False,
            "student_verified": False,
            "student_name": None,
            "register_number": None,
            "payment_status": "not_started",
            "thinking": "Network error occurred"
        })

def extract_json(text):
    """Extract JSON from OpenAI response with better error handling."""
    try:
        # Try to find JSON in the response
        start = text.find('{')
        end = text.rfind('}') + 1
        
        if start >= 0 and end > start:
            json_str = text[start:end]
            data = json.loads(json_str)
            
            # Validate required fields
            required_fields = ["reply", "show_payment_buttons", "student_verified", "student_name", "register_number", "payment_status"]
            for field in required_fields:
                if field not in data:
                    logger.warning(f"Missing field {field} in response")
                    data[field] = None if field != "show_payment_buttons" else False
                    
            return data
        else:
            logger.warning(f"No JSON found in response: {text}")
            # Return a safe default response
            return {
                "reply": "I apologize for the confusion. Let's continue with the payment process. Could you please provide your register number?",
                "show_payment_buttons": False,
                "student_verified": False,
                "student_name": None,
                "register_number": None,
                "payment_status": "not_started",
                "thinking": "JSON parsing failed, returning to initial state"
            }
    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error: {e}")
        # If it's a simple text response, wrap it in JSON
        if text.strip():
            return {
                "reply": text,
                "show_payment_buttons": False,
                "student_verified": False,
                "student_name": None,
                "register_number": None,
                "payment_status": "not_started",
                "thinking": "JSON parsing failed, using text as reply"
            }
        else:
            return {
                "reply": "Please provide your register number to get started! 🎓",
                "show_payment_buttons": False,
                "student_verified": False,
                "student_name": None,
                "register_number": None,
                "payment_status": "not_started",
                "thinking": "Empty response received"
            }

def validate_register_number(reg_number):
    """Validate register number against database (case insensitive)."""
    reg_upper = reg_number.upper().strip()
    return STUDENTS_DB.get(reg_upper)

def send_pushover(name, reg_no, txn_id):
    """Send payment notification."""
    try:
        msg = f"🎉 Payment Received!\nName: {name}\nRegister: {reg_no}\nTransaction: {txn_id}\nAmount: {PAYMENT_AMOUNT}\nTime: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        response = requests.post("https://api.pushover.net/1/messages.json", data={
            "token": PUSHOVER_APP_TOKEN,
            "user": PUSHOVER_USER_KEY,
            "message": msg,
            "title": "✅ Freshers Payment Received"
        }, timeout=10)
        if response.status_code == 200:
            logger.info("Pushover notification sent successfully")
            return True
        else:
            logger.error(f"Pushover error: {response.status_code} {response.text}")
            return False
    except Exception as e:
        logger.error(f"Pushover failed: {e}")
        return False

# -----------------------
# ROUTES
# -----------------------
@app.route("/", methods=["GET"])
def index():
    return render_template_string(HTML)

@app.route("/chat", methods=["POST"])
def chat():
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                "reply": "Invalid request format 📝",
                "show_payment_buttons": False,
                "student_verified": False,
                "student_name": None,
                "register_number": None,
                "payment_status": "not_started"
            }), 400
            
        user_message = (data.get("message") or "").strip()
        session_id = data.get("session_id") or str(uuid.uuid4())
        
        if not user_message:
            return jsonify({
                "reply": "Please enter a message to continue 💬",
                "show_payment_buttons": False,
                "student_verified": False,
                "student_name": None,
                "register_number": None,
                "payment_status": "not_started"
            }), 400

        logger.info(f"Processing message: '{user_message}' for session: {session_id}")
        
        # Get AI response
        ai_response = call_openai(user_message, session_id)
        response_data = extract_json(ai_response)
        
        # Enhanced validation: Check if this looks like a register number
        if not response_data.get("student_verified") and len(user_message) == 10:
            # Auto-detect potential register number
            student_name = validate_register_number(user_message)
            if student_name:
                response_data.update({
                    "student_verified": True,
                    "student_name": student_name,
                    "register_number": user_message.upper(),
                    "payment_status": "verified",
                    "show_payment_buttons": True
                })
                # Update the conversation memory
                if session_id in conversation_sessions:
                    conversation_sessions[session_id][-1]["content"] = f"Student provided register number: {user_message.upper()} - Verified as {student_name}"
        
        # Send notification when payment is completed
        if (response_data.get("payment_status") == "completed" and 
            response_data.get("student_verified") and
            response_data.get("student_name") and
            response_data.get("register_number")):
            
            # Extract transaction ID from user message if possible
            transaction_id = user_message if any(char.isdigit() for char in user_message) else "manual_entry"
            send_pushover(
                response_data["student_name"],
                response_data["register_number"],
                transaction_id
            )
            
        return jsonify(response_data)
    
    except Exception as e:
        logger.error(f"Error in chat endpoint: {e}")
        return jsonify({
            "reply": "I'm experiencing technical difficulties. Please try again in a moment! ⚠️",
            "show_payment_buttons": False,
            "student_verified": False,
            "student_name": None,
            "register_number": None,
            "payment_status": "not_started"
        }), 500

@app.route("/health", methods=["GET"])
def health_check():
    return jsonify({
        "status": "healthy", 
        "timestamp": datetime.now().isoformat(),
        "active_sessions": len(conversation_sessions)
    })

# -----------------------
# HTML CHAT UI
# -----------------------
HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Freshers Payment Assistant</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        :root {
            --primary: #4361ee;
            --primary-dark: #3a56d4;
            --secondary: #7209b7;
            --success: #4cc9f0;
            --light: #f8f9fa;
            --dark: #212529;
            --gray: #6c757d;
            --light-gray: #e9ecef;
            --user-msg: #4361ee;
            --bot-msg: #f1f3f5;
            --shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }

        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }

        body {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 20px;
        }

        .chat-container {
            width: 100%;
            max-width: 900px;
            height: 90vh;
            background: white;
            border-radius: 20px;
            display: flex;
            flex-direction: column;
            box-shadow: var(--shadow);
            overflow: hidden;
        }

        .chat-header {
            background: linear-gradient(to right, var(--primary), var(--secondary));
            color: white;
            padding: 15px 20px;
            text-align: center;
            position: relative;
        }

        .chat-header h1 {
            font-size: 1.5rem;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 10px;
        }

        .chat-header p {
            font-size: 0.9rem;
            opacity: 0.9;
            margin-top: 5px;
        }

        .developer-credit {
            position: absolute;
            bottom: 8px;
            right: 15px;
            font-size: 0.75rem;
            opacity: 0.8;
            background: rgba(255,255,255,0.2);
            padding: 2px 8px;
            border-radius: 10px;
        }

        .chat-messages {
            flex: 1;
            padding: 15px;
            overflow-y: auto;
            background-color: #f9fafb;
            display: flex;
            flex-direction: column;
            gap: 12px;
        }

        .message {
            max-width: 80%;
            padding: 12px 15px;
            border-radius: 18px;
            line-height: 1.4;
            position: relative;
            animation: fadeIn 0.2s ease;
        }

        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(8px); }
            to { opacity: 1; transform: translateY(0); }
        }

        .user-message {
            align-self: flex-end;
            background: var(--user-msg);
            color: white;
            border-bottom-right-radius: 5px;
        }

        .bot-message {
            align-self: flex-start;
            background: var(--bot-msg);
            color: var(--dark);
            border-bottom-left-radius: 5px;
            border: 1px solid var(--light-gray);
        }

        .message-time {
            font-size: 0.65rem;
            opacity: 0.7;
            margin-top: 4px;
            text-align: right;
        }

        .payment-details {
            background: white;
            border-radius: 12px;
            padding: 12px;
            margin: 8px 0;
            border: 1px solid var(--light-gray);
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        }

        .payment-header {
            background: linear-gradient(to right, var(--primary), var(--secondary));
            color: white;
            padding: 8px 12px;
            margin: -12px -12px 10px -12px;
            border-radius: 12px 12px 0 0;
            font-weight: bold;
            display: flex;
            align-items: center;
            gap: 8px;
            font-size: 0.9rem;
        }

        .payment-option {
            margin: 12px 0;
            padding: 8px;
            border-radius: 8px;
            background: var(--light);
        }

        .payment-option h4 {
            display: flex;
            align-items: center;
            gap: 6px;
            margin-bottom: 6px;
            color: var(--primary);
            font-size: 0.9rem;
        }

        .payment-info {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 8px;
        }

        .payment-value {
            font-family: monospace;
            font-weight: bold;
            font-size: 1rem;
            color: var(--dark);
        }

        .payment-actions {
            display: flex;
            gap: 8px;
            margin-top: 8px;
            flex-wrap: wrap;
        }

        .btn {
            padding: 6px 12px;
            border: none;
            border-radius: 6px;
            cursor: pointer;
            font-weight: 600;
            display: flex;
            align-items: center;
            gap: 4px;
            transition: all 0.2s;
            font-size: 0.8rem;
            text-decoration: none;
        }

        .btn-primary {
            background: var(--primary);
            color: white;
        }

        .btn-primary:hover {
            background: var(--primary-dark);
        }

        .btn-success {
            background: #2ecc71;
            color: white;
        }

        .btn-success:hover {
            background: #27ae60;
        }

        .btn-light {
            background: var(--light-gray);
            color: var(--dark);
        }

        .btn-light:hover {
            background: #d1d5db;
        }

        .chat-input-container {
            padding: 15px;
            border-top: 1px solid var(--light-gray);
            background: white;
        }

        .chat-input-form {
            display: flex;
            gap: 8px;
        }

        .chat-input {
            flex: 1;
            padding: 10px 12px;
            border: 1px solid var(--light-gray);
            border-radius: 10px;
            font-size: 0.9rem;
            outline: none;
            transition: all 0.2s;
        }

        .chat-input:focus {
            border-color: var(--primary);
            box-shadow: 0 0 0 2px rgba(67, 97, 238, 0.2);
        }

        .send-btn {
            background: var(--primary);
            color: white;
            border: none;
            border-radius: 10px;
            padding: 0 16px;
            cursor: pointer;
            transition: all 0.2s;
            display: flex;
            align-items: center;
            justify-content: center;
        }

        .send-btn:hover {
            background: var(--primary-dark);
        }

        .send-btn:disabled {
            background: var(--gray);
            cursor: not-allowed;
        }

        .typing-indicator {
            display: none;
            align-self: flex-start;
            background: var(--bot-msg);
            padding: 12px;
            border-radius: 18px;
            border-bottom-left-radius: 5px;
            margin-bottom: 12px;
        }

        .typing-dots {
            display: flex;
            gap: 3px;
        }

        .typing-dot {
            width: 6px;
            height: 6px;
            border-radius: 50%;
            background: var(--gray);
            animation: typing 1s infinite ease-in-out;
        }

        .typing-dot:nth-child(1) { animation-delay: 0s; }
        .typing-dot:nth-child(2) { animation-delay: 0.1s; }
        .typing-dot:nth-child(3) { animation-delay: 0.2s; }

        @keyframes typing {
            0%, 60%, 100% { transform: translateY(0); }
            30% { transform: translateY(-3px); }
        }

        .error-message {
            background: #ffe6e6;
            color: #d63031;
            border: 1px solid #ff7675;
            padding: 8px;
            border-radius: 6px;
            margin: 8px 0;
            font-size: 0.85rem;
        }

        .student-greeting {
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
            padding: 12px;
            border-radius: 10px;
            margin: 8px 0;
            text-align: center;
            font-weight: bold;
            font-size: 0.9rem;
        }

        .welcome-banner {
            background: linear-gradient(135deg, #4facfe, #00f2fe);
            color: white;
            padding: 15px;
            border-radius: 12px;
            margin: 10px 0;
            text-align: center;
        }

        .welcome-banner h3 {
            margin-bottom: 5px;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
        }

        /* Scrollbar styling */
        .chat-messages::-webkit-scrollbar {
            width: 5px;
        }

        .chat-messages::-webkit-scrollbar-track {
            background: var(--light-gray);
        }

        .chat-messages::-webkit-scrollbar-thumb {
            background: var(--gray);
            border-radius: 3px;
        }

        @media (max-width: 768px) {
            .chat-container {
                height: 95vh;
                border-radius: 15px;
            }
            
            .message {
                max-width: 90%;
            }
            
            .payment-actions {
                flex-direction: column;
            }
            
            .btn {
                justify-content: center;
            }
            
            body {
                padding: 10px;
            }
            
            .developer-credit {
                position: static;
                margin-top: 5px;
                display: inline-block;
            }
        }
    </style>
</head>
<body>
    <div class="chat-container">
        <div class="chat-header">
            <h1><i class="fas fa-robot"></i> Freshers Payment Assistant</h1>
            <p>Smart & Secure Payment Processing</p>
            <div class="developer-credit">Developed by Sridhar | CSE-AIML 3rd Year</div>
        </div>
        
        <div class="chat-messages" id="chatMessages">
            <div class="welcome-banner">
                <h3><i class="fas fa-brain"></i> Smart Payment Assistant</h3>
                <p>I'll guide you step by step. Start by sharing your register number!</p>
            </div>
        </div>
        
        <div class="typing-indicator" id="typingIndicator">
            <div class="typing-dots">
                <div class="typing-dot"></div>
                <div class="typing-dot"></div>
                <div class="typing-dot"></div>
            </div>
        </div>
        
        <div class="chat-input-container">
            <div class="chat-input-form">
                <input type="text" class="chat-input" id="chatInput" placeholder="Type your register number to start..." autocomplete="off" autofocus>
                <button class="send-btn" id="sendButton">
                    <i class="fas fa-paper-plane"></i>
                </button>
            </div>
        </div>
    </div>

    <script>
        let sessionId = null;
        const chatMessages = document.getElementById('chatMessages');
        const chatInput = document.getElementById('chatInput');
        const sendButton = document.getElementById('sendButton');
        const typingIndicator = document.getElementById('typingIndicator');
        
        // Generate session ID if not exists
        if (!sessionId) {
            sessionId = generateSessionId();
        }
        
        // Send message on button click
        sendButton.addEventListener('click', sendMessage);
        
        // Send message on Enter key
        chatInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                sendMessage();
            }
        });
        
        function generateSessionId() {
            return 'session-' + Math.random().toString(36).substring(2, 15) + Math.random().toString(36).substring(2, 15);
        }
        
        function getCurrentTime() {
            const now = new Date();
            return now.getHours().toString().padStart(2, '0') + ':' + now.getMinutes().toString().padStart(2, '0');
        }
        
        function appendMessage(content, isUser = false) {
            const messageDiv = document.createElement('div');
            messageDiv.className = isUser ? 'message user-message' : 'message bot-message';
            
            const timeDiv = document.createElement('div');
            timeDiv.className = 'message-time';
            timeDiv.textContent = getCurrentTime();
            
            messageDiv.innerHTML = content;
            messageDiv.appendChild(timeDiv);
            
            chatMessages.appendChild(messageDiv);
            chatMessages.scrollTop = chatMessages.scrollHeight;
        }
        
        function showStudentGreeting(studentName) {
            return `
                <div class="student-greeting">
                    <i class="fas fa-check-circle"></i> Verified Student: ${studentName}
                </div>
            `;
        }
        
        function showPaymentDetails() {
            const paymentHTML = `
                <div class="payment-details">
                    <div class="payment-header">
                        <i class="fas fa-credit-card"></i>
                        Payment Details - ₹500
                    </div>
                    
                   <div class="payment-option">
                        <h4><i class="fas fa-mobile-alt"></i> PhonePe</h4>
                        <div class="payment-info">
                            <span class="payment-value">""" + PHONEPE_NUMBER + """</span>
                        </div>
                        <div class="payment-actions">
                            <!-- Copy PhonePe number -->
                            <button class="btn btn-primary" onclick="copyToClipboard('""" + PHONEPE_NUMBER + """')">
                                <i class="fas fa-copy"></i> Copy Number
                            </button>
                    
                            <!-- Open PhonePe app directly (mobile only) -->
                            <a href="upi://pay?pa=""" + PHONEPE_NUMBER + """&pn=Freshers%20Payment&cu=INR" class="btn btn-success">
                                <i class="fas fa-external-link-alt"></i> Open PhonePe
                            </a>
                        </div>
                    </div>
                    <div class="payment-option">
                        <h4><i class="fas fa-university"></i> UPI Payment</h4>
                        <div class="payment-info">
                            <span class="payment-value">""" + UPI_ID + """</span>
                        </div>
                        <div class="payment-actions">
                            <button class="btn btn-primary" onclick="copyToClipboard('""" + UPI_ID + """')">
                                <i class="fas fa-copy"></i> Copy UPI
                            </button>
                            <a href="upi://pay?pa=""" + UPI_ID + """&pn=Freshers%20Payment&am=500" class="btn btn-light">
                                <i class="fas fa-external-link-alt"></i> Pay via UPI
                            </a>
                        </div>
                    </div>
                </div>
            `;
            return paymentHTML;
        }
        
        function copyToClipboard(text) {
            navigator.clipboard.writeText(text).then(function() {
                showNotification('Copied to clipboard!', 'success');
            }).catch(function() {
                // Fallback for older browsers
                const textArea = document.createElement('textarea');
                textArea.value = text;
                document.body.appendChild(textArea);
                textArea.select();
                document.execCommand('copy');
                document.body.removeChild(textArea);
                showNotification('Copied to clipboard!', 'success');
            });
        }
        
        function showNotification(message, type = 'success') {
            const notification = document.createElement('div');
            notification.textContent = message;
            notification.style.position = 'fixed';
            notification.style.bottom = '15px';
            notification.style.right = '15px';
            notification.style.background = type === 'success' ? '#2ecc71' : '#e74c3c';
            notification.style.color = 'white';
            notification.style.padding = '8px 12px';
            notification.style.borderRadius = '5px';
            notification.style.zIndex = '1000';
            notification.style.boxShadow = '0 2px 10px rgba(0,0,0,0.1)';
            notification.style.fontSize = '0.8rem';
            document.body.appendChild(notification);
            
            setTimeout(() => {
                if (document.body.contains(notification)) {
                    document.body.removeChild(notification);
                }
            }, 1500);
        }
        
        async function sendMessage() {
            const message = chatInput.value.trim();
            if (!message) return;
            
            // Add user message to chat
            appendMessage(message, true);
            chatInput.value = '';
            
            await sendMessageToBackend(message);
        }
        
        async function sendMessageToBackend(message) {
            // Disable send button and show typing indicator
            sendButton.disabled = true;
            typingIndicator.style.display = 'flex';
            chatMessages.scrollTop = chatMessages.scrollHeight;
            
            try {
                // Send message to backend
                const response = await fetch('/chat', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        message: message,
                        session_id: sessionId
                    })
                });
                
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                
                const data = await response.json();
                
                // Hide typing indicator
                typingIndicator.style.display = 'none';
                sendButton.disabled = false;
                
                // Process the AI response
                let botMessage = data.reply || 'Thank you for your message!';
                
                // Add student greeting if we have verified student
                if (data.student_verified && data.student_name) {
                    botMessage = showStudentGreeting(data.student_name) + botMessage;
                }
                
                // Add payment buttons if needed
                if (data.show_payment_buttons) {
                    botMessage += showPaymentDetails();
                    // Update input placeholder to guide next step
                    chatInput.placeholder = "Enter transaction ID after payment...";
                } else {
                    chatInput.placeholder = "Type your message...";
                }
                
                appendMessage(botMessage);
                
            } catch (error) {
                console.error('Error:', error);
                
                // Hide typing indicator and re-enable send button
                typingIndicator.style.display = 'none';
                sendButton.disabled = false;
                
                // Show error message
                appendMessage(`
                    <div class="error-message">
                        <i class="fas fa-exclamation-triangle"></i> 
                        Connection error. Please try again.
                    </div>
                `);
            }
        }
        
        // Focus on input field when page loads
        chatInput.focus();
    </script>
</body>
</html>
"""

# -----------------------
# RUN APP
# -----------------------
if __name__ == "__main__":
    print("🚀 Smart Freshers Payment Bot running at http://127.0.0.1:8000")
    print("📱 Health check available at http://127.0.0.1:8000/health")
    print("🧠 Enhanced: Full conversation memory with thinking process")
    print("🎯 Improved: LLM decides flow, no pre-programmed responses")
    print("🔍 Smart: Auto-detects register numbers and maintains context")
    print("👨‍💻 Developed by Sridhar | CSE-AIML 3rd Year")
    
    try:
        app.run(host="0.0.0.0", port=8000, debug=False)
    except Exception as e:
        logger.error(f"Failed to start server: {e}")
        print(f"Server failed to start: {e}")
