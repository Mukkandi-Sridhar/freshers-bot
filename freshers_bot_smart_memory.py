# freshers_bot_llm_powered.py
import json
import uuid
import logging
import requests
from flask import Flask, request, jsonify, render_template_string
from datetime import datetime
import os
import re
from flask_cors import CORS
from dotenv import load_dotenv
import firebase_admin
from firebase_admin import credentials, firestore


# Load environment variables from .env file
load_dotenv()

# Access the keys
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
PUSHOVER_USER_KEY = os.getenv("PUSHOVER_USER_KEY")
PUSHOVER_APP_TOKEN = os.getenv("PUSHOVER_APP_TOKEN")
PAYMENT_AMOUNT = "₹550"
PHONEPE_NUMBER = "7207088752"
UPI_ID = "7207088752@ibl"

# -----------------------
# FIREBASE SETUP
# -----------------------
try:
    firebase_admin.get_app()
except ValueError:
    cred = credentials.Certificate("freshers-263b4-firebase-adminsdk-fbsvc-632158ab07.json")  # path to your Firebase key file
    firebase_admin.initialize_app(cred)

db = firestore.client()


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("FreshersBot")

# -----------------------
# STUDENT DATABASE
# -----------------------
STUDENTS_DB = {
    "23091A3301": "MEKALA AMMAR",
    "23091A3302": "MEERIJA ANJUM",
    "23091A3304": "T.BHANU PRAKASH",
    "23091A3305": "ANDHE BHARGAV",
    "23091A3306": "SOMPALLI BRAHMINI",
    "23091A3307": "CHITIKELA CHARAN",
    "23091A3308": "P CHARAN KUMAR REDDY",
    "23091A3309": "KAKI CHARITHA RANI",
    "23091A3310": "KALLETI DEDEEPYA VARSHINI",
    "23091A3311": "BETHAMSETTY DEEPTHI",
    "23091A3312": "KUMARNAIK GARI DHARSHAN",
    "23091A3313": "BOVILLA DILEEP KUMAR REDDY",
    "23091A3314": "GANDLA ERANNA",
    "23091A3315": "M GIRI PRASAD",
    "23091A3316": "KETHEPALLE GURU SAI SULEKHA",
    "23091A3317": "PATHURU GURU VISHNU",
    "23091A3318": "VELDURTHI HEMA",
    "23091A3319": "CHAKALI HIMA BINDHU",
    "23091A3320": "CHALLA HIMA VAMSI REDDY",
    "23091A3321": "SHAIK MOHAMMAD HUSSAIN",
    "23091A3322": "GURUMADHU KAKARLA",
    "23091A3323": "ANDRA KEERTHANA",
    "23091A3324": "KURIMIGALLA KRISHNA MOHAN",
    "23091A3325": "KAMPAMALLA MADHAVI",
    "23091A3326": "BESTHA MAHESH BABU",
    "23091A3327": "MOGILIPALLI MANI RUPESH",
    "23091A3328": "GOPANNAGARI MANJUNATH",
    "23091A3329": "GADDAM MANVITHA",
    "23091A3330": "MURIKI NAGA VENKATA SAI",
    "23091A3331": "AGRAHARAM NAVEEN KUMAR",
    "23091A3332": "KYABARSHI NAVYA",
    "23091A3333": "PRANATHI REDDY K",
    "23091A3334": "CHITTIBOINA RAJESWARI",
    "23091A3336": "BOGGADI RAMA DEVI",
    "23091A3337": "BILAVATH RAMESH NAIK",
    "23091A3338": "MOPURU RUSHENDRA PHANI",
    "23091A3339": "PYARAM RUSHIKA",
    "23091A3340": "CHENNURI SAI",
    "23091A3341": "BARRENKALA SAI KIRANMAYI",
    "23091A3342": "TOMALA SAI MANASWINI",
    "23091A3343": "GADDAM SAI SWAROOPA REDDY",
    "23091A3344": "A MOHAMMED SAMEER",
    "23091A3345": "VAKAMALLA SANJANA",
    "23091A3346": "SYED SHAIJIDA BHANU",
    "23091A3348": "DUDEKULA SIDDINI SHARMI",
    "23091A3349": "MUKKANDI SRIDHAR",
    "23091A3350": "IDHUMALLA SUDHEER KUMAR",
    "23091A3351": "MADDULA SUMANTH",
    "23091A3352": "TAGARAM SUMMITHA",
    "23091A3353": "VANKE SUNEETHA",
    "23091A3354": "SIVAPURAM SWAPNA",
    "23091A3355": "LAKKIREDDY SWAROOPA",
    "23091A3356": "SHAIK TARANNUM NAAZ",
    "23091A3357": "GAJULAPALLE THANUJA",
    "23091A3358": "MOTA THRILOK",
    "23091A3359": "PALLA UMESH",
    "23091A3360": "KOTHA VARUN KUMAR",
    "23091A3361": "N VENKATA NAGA JOSHITA",
    "23091A3362": "T VENKATA NAGA TEJASWINI",
    "23091A3363": "GORLA VIJAYA LAKSHMI",
    "23091A3364": "MANERI VISHNU SAI VAMSI",
    "23091A3365": "DAYYAM YASHWANTH",
    "24095A3301": "PHATAN AFROZ ALI KHAN",
    "24095A3302": "CHINTHALA CHENNA MADHAVI",
    "24095A3303": "JAMBULA DINESH REDDY",
    "24095A3304": "LABBI NAGARJUNA",
    "24095A3305": "PATHAPADU SAIMANJUNATH",
    "24095A3306": "GANTALA SUMANTH",
    "24095A3307": "SUDDULA VENKATA SIVUDU"
}

# -----------------------
# FLASK APP
# -----------------------
app = Flask(__name__)
CORS(app)

# Global conversation memory
conversation_sessions = {}

# COMPLETE SYSTEM PROMPT - LLM HAS FULL CONTROL
SYSTEM_PROMPT = f"""
You are FPA (Freshers Payment Assistant) - an AI assistant that helps students complete payments for the Freshers Party.

CRITICAL INFORMATION:
- STUDENT DATABASE: {json.dumps(STUDENTS_DB, indent=2)}
- PAYMENT AMOUNT: {PAYMENT_AMOUNT}
- Payment Methods: 
  • PhonePe: {PHONEPE_NUMBER}
  • UPI ID: {UPI_ID}

YOUR ROLE AND POWERS:
You have COMPLETE control over the conversation. You decide:
- What to say next
- When to ask for information
- When to show payment options
- When to confirm payments
- Everything about the conversation flow

CONVERSATION FLOW (Suggested, but you adapt as needed):
1. Greet and ask for register number
2. Verify register number against database
3. If valid: Show payment options and instructions
4. Wait for payment confirmation or transaction ID
5. When transaction ID received: Send confirmation and thank you message

RESPONSE FORMAT - YOU MUST USE THIS JSON STRUCTURE:
{{
  "reply": "Your message to the student",
  "action": "ask_register|show_payment|ask_transaction|complete|general_chat",
  "student_verified": true/false,
  "student_name": "Name if verified" or null,
  "register_number": "Reg number if provided" or null,
  "should_send_notification": true/false,
  "notification_data": {{"name": "...", "reg_no": "...", "txn_id": "..."}} or null
}}

ACTIONS EXPLANATION:
- "ask_register": Ask for register number
- "show_payment": Show payment options and instructions
- "ask_transaction": Ask for transaction ID after payment
- "complete": Conversation completed, payment confirmed
- "general_chat": Regular conversation without specific action

MEMORY MANAGEMENT:
- You will receive the FULL conversation history
- Remember everything that was said before
- Never ask for the same information twice
- Maintain context throughout the entire conversation

PAYMENT NOTIFICATION:
- Set "should_send_notification": true ONLY when you receive a valid transaction ID
- Fill "notification_data" with student name, register number, and transaction ID
- This will automatically send a push notification to organizers

IMPORTANT RULES:
1. NEVER provide payment details before verifying register number
2. ALWAYS maintain conversation context - remember previous messages
3. Be friendly, helpful, and use emojis appropriately 🎉😊
4. Adapt to the user's conversation style
5. You have COMPLETE freedom to manage the conversation as you see fit

FRESHERS INFORMATION:
1. freshers will be held on next wednesday - 15th october 2025
2. venue is rgm grounds, nandyal
3. branch - cse-aiml , rgmcet

EXAMPLE RESPONSES:
User: "hi"
You: {{
    "reply": "Hello! 😊 Welcome to Freshers Payment Assistant! Please share your register number to get started.",
    "action": "ask_register",
    "student_verified": false,
    "student_name": null,
    "register_number": null,
    "should_send_notification": false,
    "notification_data": null
}}

User: "23091A3349"
You: {{
    "reply": "✅ Verified! Hello <b>Mukkandi Sridhar</b>! 🎉\\n\\n<b>Payment Details:</b>\\n• Amount: {PAYMENT_AMOUNT}\\n• PhonePe: {PHONEPE_NUMBER}\\n• UPI: {UPI_ID}\\n\\nPlease make the payment and share your transaction ID with me!",
    "action": "show_payment",
    "student_verified": true,
    "student_name": "Mukkandi Sridhar",
    "register_number": "23091A3349",
    "should_send_notification": false,
    "notification_data": null
}}

User: "TXN123456789"
You: {{
    "reply": "🎉 <b>Payment Confirmed!</b> Thank you <b>Mukkandi Sridhar</b>! Your Freshers Party registration is complete. Have a wonderful time! 🥳",
    "action": "complete",
    "student_verified": true,
    "student_name": "Mukkandi Sridhar",
    "register_number": "23091A3349",
    "should_send_notification": true,
    "notification_data": {{
        "name": "Mukkandi Sridhar",
        "reg_no": "23091A3349",
        "txn_id": "TXN123456789"
    }}
}}
"""

def call_openai(user_message, session_id):
    """Call OpenAI API with complete conversation history and full control."""
    # Initialize session if not exists
    if session_id not in conversation_sessions:
        conversation_sessions[session_id] = [
            {"role": "system", "content": SYSTEM_PROMPT}
        ]
    
    # Add user message to conversation history
    conversation_sessions[session_id].append({"role": "user", "content": user_message})
    
    # Keep last 15 messages to maintain context while managing tokens
    if len(conversation_sessions[session_id]) > 16:  # system + 15 messages
        # Keep system prompt and recent messages
        conversation_sessions[session_id] = [conversation_sessions[session_id][0]] + conversation_sessions[session_id][-15:]
    
    logger.info(f"Session {session_id} has {len(conversation_sessions[session_id])} messages in history")
    
    # Prepare payload with full conversation history
    payload = {
        "model": "gpt-4o",
        "messages": conversation_sessions[session_id],
        "temperature": 0.7,
        "max_tokens": 500,
        "response_format": { "type": "json_object" }
    }
    
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}", 
        "Content-Type": "application/json"
    }

    try:
        logger.info(f"Calling OpenAI API for session {session_id}")
        r = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload, timeout=30)
        
        if r.status_code == 200:
            ai_response = r.json()["choices"][0]["message"]["content"]
            
            # Add AI response to conversation history
            conversation_sessions[session_id].append({"role": "assistant", "content": ai_response})
            
            logger.info("OpenAI API call successful")
            return ai_response
        else:
            logger.error(f"OpenAI error: {r.status_code} {r.text}")
            return json.dumps({
                "reply": "I'm having some technical issues. Please try again in a moment! 🔧",
                "action": "general_chat",
                "student_verified": False,
                "student_name": None,
                "register_number": None,
                "should_send_notification": False,
                "notification_data": None
            })
    except Exception as e:
        logger.error(f"OpenAI call failed: {e}")
        return json.dumps({
            "reply": "Connection issue. Please check your internet and try again! 🌐",
            "action": "general_chat",
            "student_verified": False,
            "student_name": None,
            "register_number": None,
            "should_send_notification": False,
            "notification_data": None
        })

def extract_json(text):
    """Extract JSON from OpenAI response with robust error handling."""
    try:
        # Try to find JSON in the response
        start = text.find('{')
        end = text.rfind('}') + 1
        
        if start >= 0 and end > start:
            json_str = text[start:end]
            data = json.loads(json_str)
            
            # Validate required fields
            required_fields = [
                "reply", "action", "student_verified", "student_name", 
                "register_number", "should_send_notification", "notification_data"
            ]
            
            for field in required_fields:
                if field not in data:
                    logger.warning(f"Missing field {field} in response, using defaults")
                    if field == "student_verified":
                        data[field] = False
                    elif field == "should_send_notification":
                        data[field] = False
                    elif field in ["student_name", "register_number", "notification_data"]:
                        data[field] = None
                    elif field == "action":
                        data[field] = "general_chat"
                    else:
                        data[field] = ""
            
            return data
        else:
            logger.warning(f"No JSON found in response: {text}")
            # Return safe default response
            return {
                "reply": "Let me help you with the payment process. Could you please share your register number?",
                "action": "ask_register",
                "student_verified": False,
                "student_name": None,
                "register_number": None,
                "should_send_notification": False,
                "notification_data": None
            }
    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error: {e}")
        # If it's a simple text response, wrap it in JSON
        if text.strip():
            return {
                "reply": text,
                "action": "general_chat",
                "student_verified": False,
                "student_name": None,
                "register_number": None,
                "should_send_notification": False,
                "notification_data": None
            }
        else:
            return {
                "reply": "Hello! 😊 Please share your register number to start the payment process.",
                "action": "ask_register",
                "student_verified": False,
                "student_name": None,
                "register_number": None,
                "should_send_notification": False,
                "notification_data": None
            }

def validate_register_number(reg_number):
    """Validate register number against database."""
    reg_upper = reg_number.upper().strip()
    return STUDENTS_DB.get(reg_upper)

def send_pushover(name, reg_no, txn_id):
    """Send payment notification to organizers."""
    try:
        msg = f"🎉 Payment Received!\nName: {name}\nRegister: {reg_no}\nTransaction: {txn_id}\nAmount: {PAYMENT_AMOUNT}\nTime: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        response = requests.post("https://api.pushover.net/1/messages.json", data={
            "token": PUSHOVER_APP_TOKEN,
            "user": PUSHOVER_USER_KEY,
            "message": msg,
            "title": "✅ Freshers Payment Received"
        }, timeout=10)
        
        if response.status_code == 200:
            logger.info(f"Pushover notification sent for {name} - {txn_id}")
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
                "action": "general_chat",
                "student_verified": False,
                "student_name": None,
                "register_number": None,
                "should_send_notification": False,
                "notification_data": None
            }), 400
            
        user_message = (data.get("message") or "").strip()
        session_id = data.get("session_id") or str(uuid.uuid4())
        
        if not user_message:
            return jsonify({
                "reply": "Please enter a message to continue 💬",
                "action": "general_chat",
                "student_verified": False,
                "student_name": None,
                "register_number": None,
                "should_send_notification": False,
                "notification_data": None
            }), 400

        logger.info(f"Processing: '{user_message}' for session: {session_id}")
        
        # Get AI response with complete memory and control
        ai_response = call_openai(user_message, session_id)
        response_data = extract_json(ai_response)
        
        # Send notification if LLM decides to
        if (response_data.get("should_send_notification") and 
            response_data.get("notification_data")):
            
            notif_data = response_data["notification_data"]
            if (notif_data and 
                notif_data.get("name") and 
                notif_data.get("reg_no") and 
                notif_data.get("txn_id")):
                
                send_pushover(
                    notif_data["name"],
                    notif_data["reg_no"],
                    notif_data["txn_id"]
                )
                update_payment_status(notif_data["reg_no"], "Paid")
                logger.info(f"Notification + Firestore updated for {notif_data['name']}")
        return jsonify(response_data)
    
    except Exception as e:
        logger.error(f"Error in chat endpoint: {e}")
        return jsonify({
            "reply": "I'm experiencing some technical difficulties. Please try again in a moment! ⚠️",
            "action": "general_chat",
            "student_verified": False,
            "student_name": None,
            "register_number": None,
            "should_send_notification": False,
            "notification_data": None
        }), 500

@app.route("/health", methods=["GET"])
def health_check():
    return jsonify({
        "status": "healthy", 
        "timestamp": datetime.now().isoformat(),
        "active_sessions": len(conversation_sessions)
    })

@app.route("/clear_session/<session_id>", methods=["POST"])
def clear_session(session_id):
    """Clear a specific session's memory."""
    if session_id in conversation_sessions:
        del conversation_sessions[session_id]
        logger.info(f"Cleared session: {session_id}")
        return jsonify({"status": "success", "message": "Session cleared"})
    return jsonify({"status": "error", "message": "Session not found"}), 404

@app.route("/session_info/<session_id>", methods=["GET"])
def session_info(session_id):
    """Get information about a session (for debugging)."""
    if session_id in conversation_sessions:
        message_count = len(conversation_sessions[session_id])
        return jsonify({
            "session_id": session_id,
            "message_count": message_count,
            "has_memory": message_count > 1
        })
    return jsonify({"error": "Session not found"}), 404
def update_payment_status(register_number, status):
    """Update student's payment status in Firestore."""
    try:
        doc_ref = db.collection("students").document(register_number)
        doc_ref.set({"status": status}, merge=True)
        print(f"✅ Firestore updated: {register_number} → {status}")
    except Exception as e:
        print(f"❌ Firestore update failed for {register_number}: {e}")


# -----------------------
# HTML CHAT UI (Enhanced Mobile-Optimized)
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
            --radius: 16px;
        }

        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }

        body {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 0;
            margin: 0;
        }

        .chat-container {
            width: 100%;
            max-width: 100%;
            height: 100vh;
            background: white;
            display: flex;
            flex-direction: column;
            overflow: hidden;
            position: relative;
        }

        .chat-header {
            background: linear-gradient(to right, var(--primary), var(--secondary));
            color: white;
            padding: 16px 20px;
            text-align: center;
            position: relative;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            z-index: 10;
        }

        .chat-header h1 {
            font-size: 1.3rem;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 10px;
            margin-bottom: 4px;
        }

        .chat-header p {
            font-size: 0.85rem;
            opacity: 0.9;
        }

        .chat-messages {
            flex: 1;
            padding: 16px;
            overflow-y: auto;
            background-color: #f9fafb;
            display: flex;
            flex-direction: column;
            gap: 12px;
            scroll-behavior: smooth;
        }

        .message {
            max-width: 85%;
            padding: 12px 16px;
            border-radius: var(--radius);
            line-height: 1.4;
            position: relative;
            animation: fadeIn 0.3s ease;
            word-wrap: break-word;
            white-space: pre-line;
            font-size: 0.95rem;
        }

        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }

        .user-message {
            align-self: flex-end;
            background: var(--user-msg);
            color: white;
            border-bottom-right-radius: 4px;
        }

        .bot-message {
            align-self: flex-start;
            background: var(--bot-msg);
            color: var(--dark);
            border-bottom-left-radius: 4px;
            border: 1px solid var(--light-gray);
        }

        .message-time {
            font-size: 0.7rem;
            opacity: 0.7;
            margin-top: 6px;
            text-align: right;
        }

        .payment-details {
            background: white;
            border-radius: 12px;
            padding: 16px;
            margin: 10px 0;
            border: 1px solid var(--light-gray);
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }

        .payment-header {
            background: linear-gradient(to right, var(--primary), var(--secondary));
            color: white;
            padding: 10px 15px;
            margin: -16px -16px 15px -16px;
            border-radius: 12px 12px 0 0;
            font-weight: bold;
            display: flex;
            align-items: center;
            gap: 8px;
            font-size: 0.9rem;
        }

        .payment-option {
            margin: 12px 0;
            padding: 12px;
            border-radius: 10px;
            background: var(--light);
            border-left: 4px solid var(--primary);
            font-size: 0.9rem;
        }

        .payment-actions {
            display: flex;
            gap: 8px;
            margin-top: 15px;
            flex-wrap: wrap;
        }

        .btn {
            padding: 10px 12px;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            font-weight: 600;
            display: flex;
            align-items: center;
            gap: 6px;
            transition: all 0.3s;
            font-size: 0.85rem;
            text-decoration: none;
            flex: 1;
            justify-content: center;
            min-height: 44px;
        }

        .btn-primary { background: var(--primary); color: white; }
        .btn-success { background: #2ecc71; color: white; }
        .btn-light { background: var(--light-gray); color: var(--dark); }

        .btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(0,0,0,0.2);
        }

        .chat-input-container {
            padding: 16px;
            border-top: 1px solid var(--light-gray);
            background: white;
            position: sticky;
            bottom: 0;
            z-index: 5;
        }

        .chat-input-form {
            display: flex;
            gap: 10px;
            align-items: center;
        }

        .chat-input {
            flex: 1;
            padding: 14px 16px;
            border: 1px solid var(--light-gray);
            border-radius: 25px;
            font-size: 1rem;
            outline: none;
            transition: all 0.3s;
            background: #f8f9fa;
        }

        .chat-input:focus {
            border-color: var(--primary);
            box-shadow: 0 0 0 3px rgba(67, 97, 238, 0.1);
            background: white;
        }

        .send-btn {
            background: var(--primary);
            color: white;
            border: none;
            border-radius: 50%;
            padding: 0;
            cursor: pointer;
            height: 50px;
            width: 50px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.2rem;
            transition: all 0.3s;
            box-shadow: 0 2px 8px rgba(67, 97, 238, 0.3);
        }

        .send-btn:hover {
            background: var(--primary-dark);
            transform: scale(1.05);
        }

        .typing-indicator {
            display: none;
            align-self: flex-start;
            background: var(--bot-msg);
            padding: 12px 16px;
            border-radius: var(--radius);
            border-bottom-left-radius: 4px;
            margin-bottom: 10px;
            border: 1px solid var(--light-gray);
        }

        .typing-dots {
            display: flex;
            gap: 4px;
        }

        .typing-dot {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: var(--gray);
            animation: typing 1s infinite ease-in-out;
        }

        .typing-dot:nth-child(1) { animation-delay: 0s; }
        .typing-dot:nth-child(2) { animation-delay: 0.1s; }
        .typing-dot:nth-child(3) { animation-delay: 0.2s; }

        @keyframes typing {
            0%, 60%, 100% { transform: translateY(0); opacity: 0.4; }
            30% { transform: translateY(-5px); opacity: 1; }
        }

        .footer {
            text-align: center;
            padding: 12px;
            font-size: 0.75rem;
            color: var(--gray);
            background: var(--light);
            border-top: 1px solid var(--light-gray);
        }

        /* Mobile-specific optimizations */
        @media (max-width: 768px) {
            .chat-container {
                height: 100vh;
                border-radius: 0;
            }
            
            .message {
                max-width: 90%;
                font-size: 0.9rem;
            }
            
            .payment-actions {
                flex-direction: column;
            }
            
            .btn {
                width: 100%;
            }
            
            .chat-header h1 {
                font-size: 1.2rem;
            }
            
            .chat-header p {
                font-size: 0.8rem;
            }
        }

        /* Small phones */
        @media (max-width: 480px) {
            .chat-messages {
                padding: 12px;
            }
            
            .message {
                max-width: 95%;
                padding: 10px 14px;
            }
            
            .chat-input-container {
                padding: 12px;
            }
            
            .chat-input {
                padding: 12px 16px;
            }
            
            .send-btn {
                height: 46px;
                width: 46px;
            }
        }

        /* Dark mode support */
        @media (prefers-color-scheme: dark) {
            .bot-message {
                background: #2d3748;
                color: #e2e8f0;
                border-color: #4a5568;
            }
            
            .chat-messages {
                background-color: #1a202c;
            }
            
            .chat-input {
                background: #2d3748;
                color: #e2e8f0;
                border-color: #4a5568;
            }
            
            .chat-input:focus {
                background: #2d3748;
            }
            
            .payment-details {
                background: #2d3748;
                color: #e2e8f0;
                border-color: #4a5568;
            }
            
            .payment-option {
                background: #4a5568;
                color: #e2e8f0;
            }
        }
    </style>
</head>
<body>
    <div class="chat-container">
        <div class="chat-header">
            <h1><i class="fas fa-robot"></i> Freshers Payment Assistant-2025</h1>
            <p>CSE-AIML</p>
        </div>
        
        <div class="chat-messages" id="chatMessages">
            <div class="message bot-message">
                🎉 Welcome to Freshers Payment Assistant! 
                <div class="message-time" id="currentTime"></div>
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
                <input type="text" class="chat-input" id="chatInput" placeholder="Type here....." autocomplete="off" autofocus>
                <button class="send-btn" id="sendButton">
                    <i class="fas fa-paper-plane"></i>
                </button>
            </div>
        </div>
        
        <div class="footer">
            Developed by Sridhar | CSE-AIML 3rd Year
        </div>
    </div>

    <script>
        let sessionId = Math.random().toString(36).substring(2) + Date.now().toString(36);
        const chatMessages = document.getElementById('chatMessages');
        const chatInput = document.getElementById('chatInput');
        const sendButton = document.getElementById('sendButton');
        const typingIndicator = document.getElementById('typingIndicator');

        // Update time function
        function updateTime() {
            const now = new Date();
            const timeElements = document.querySelectorAll('.message-time');
            if (timeElements.length > 0) {
                timeElements[timeElements.length - 1].textContent = 
                    now.getHours().toString().padStart(2, '0') + ':' + 
                    now.getMinutes().toString().padStart(2, '0');
            }
        }
        setInterval(updateTime, 60000);
        updateTime();

        // Send message function
        async function sendMessage() {
            const message = chatInput.value.trim();
            if (!message) return;

            // Add user message
            addMessage(message, true);
            chatInput.value = '';
            
            // Show typing indicator
            typingIndicator.style.display = 'flex';
            chatMessages.scrollTop = chatMessages.scrollHeight;

            try {
                const response = await fetch('/chat', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ 
                        message: message, 
                        session_id: sessionId 
                    })
                });

                const data = await response.json();
                
                // Hide typing indicator
                typingIndicator.style.display = 'none';
                
                // Add bot message
                addMessage(data.reply, false);
                
            } catch (error) {
                typingIndicator.style.display = 'none';
                addMessage('Sorry, I encountered an error. Please try again.', false);
                console.error('Error:', error);
            }
        }

        function addMessage(content, isUser) {
            const messageDiv = document.createElement('div');
            messageDiv.className = isUser ? 'message user-message' : 'message bot-message';
            
            const timeDiv = document.createElement('div');
            timeDiv.className = 'message-time';
            timeDiv.textContent = new Date().toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
            
            messageDiv.innerHTML = content;
            messageDiv.appendChild(timeDiv);
            
            chatMessages.appendChild(messageDiv);
            chatMessages.scrollTop = chatMessages.scrollHeight;
        }

        // Event listeners
        sendButton.addEventListener('click', sendMessage);
        chatInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') sendMessage();
        });

        // Auto-focus input and scroll to bottom on load
        window.addEventListener('load', () => {
            chatInput.focus();
            chatMessages.scrollTop = chatMessages.scrollHeight;
        });

        // Handle virtual keyboard on mobile
        if ('visualViewport' in window) {
            const visualViewport = window.visualViewport;
            visualViewport.addEventListener('resize', () => {
                chatMessages.scrollTop = chatMessages.scrollHeight;
            });
        }
    </script>
</body>
</html>
"""

# --- Health Check Route ---
@app.route("/health", methods=["GET", "POST"])
def health():
    """Health check endpoint to show uptime and optionally reboot."""
    uptime_seconds = time.time() - START_TIME
    uptime_str = time.strftime("%Hh %Mm %Ss", time.gmtime(uptime_seconds))

    if request.method == "POST":
        data = request.get_json(silent=True) or {}
        if data.get("action") == "reboot":
            # Optional: Protect with secret key or token if needed
            os.execv(sys.executable, ['python'] + sys.argv)  # Restarts app
            return jsonify({"status": "rebooting..."})
        return jsonify({"error": "Invalid action"}), 400

    return jsonify({
        "status": "ok",
        "uptime": uptime_str,
        "uptime_seconds": round(uptime_seconds, 2),
        "message": "App is running smoothly 🚀"
    })

# -----------------------
# RUN APP
# -----------------------
if __name__ == "__main__":
    print("🚀 LLM-Powered Freshers Payment Bot running at http://127.0.0.1:8000")
    print("🧠 COMPLETE CONTROL: OpenAI manages entire conversation flow")
    print("💾 FULL MEMORY: Complete conversation history sent to LLM")
    print("🔔 SMART NOTIFICATIONS: LLM decides when to send push notifications")
    print("📱 MOBILE OPTIMIZED: Works perfectly on all devices")
    print("👨‍💻 Developed by CSE-AIML 3rd Year")
    
    try:
        app.run(host="0.0.0.0", port=8000, debug=False)
    except Exception as e:
        logger.error(f"Failed to start server: {e}")
        print(f"Server failed to start: {e}")
