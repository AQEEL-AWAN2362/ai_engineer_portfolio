import streamlit as st
import requests
import uuid
import logging
from datetime import datetime
import json
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
API_URL = "http://127.0.0.1:8000/agent/chat"
API_TIMEOUT = 30  # seconds
REQUEST_RETRIES = 2
CHAT_HISTORY_DIR = Path("chat_histories")
USERS_FILE = Path("users.json")

# Create directories if they don't exist
CHAT_HISTORY_DIR.mkdir(exist_ok=True)

st.set_page_config(
    page_title="Dr. AQEEL SkinCare Clinic",
    page_icon="🩺",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for modern chat interface
st.markdown("""
<style>
    .stChatMessage {
        border-radius: 15px;
        padding: 12px 16px;
        margin-bottom: 8px;
    }
    .stChatMessage.user {
        background-color: #dcf8c6;
        margin-left: 50px;
        border-radius: 18px 18px 4px 18px;
    }
    .stChatMessage.assistant {
        background-color: #ffffff;
        border: 1px solid #e0e0e0;
        margin-right: 50px;
        border-radius: 18px 18px 18px 4px;
    }
    .sidebar-chat-item {
        padding: 8px;
        margin: 5px 0;
        border-radius: 8px;
        cursor: pointer;
        border-left: 3px solid #1f77b4;
    }
    .sidebar-chat-item:hover {
        background-color: #f0f0f0;
    }
    .sidebar-chat-item.active {
        background-color: #dcf8c6;
        border-left: 3px solid #2ecc71;
    }
</style>
""", unsafe_allow_html=True)

# ============================================
# USER AUTHENTICATION FUNCTIONS
# ============================================

def load_users():
    """Load registered users from file"""
    if USERS_FILE.exists():
        with open(USERS_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_users(users):
    """Save users to file"""
    with open(USERS_FILE, 'w') as f:
        json.dump(users, f, indent=2)

def hash_password(password):
    """Simple password hashing (in production, use bcrypt)"""
    import hashlib
    return hashlib.sha256(password.encode()).hexdigest()

def register_user(email, password, name):
    """Register a new user"""
    users = load_users()
    if email in users:
        return False, "Email already registered"
    
    users[email] = {
        "name": name,
        "password": hash_password(password),
        "created_at": datetime.now().isoformat()
    }
    save_users(users)
    return True, "Registration successful!"

def login_user(email, password):
    """Validate user login"""
    users = load_users()
    if email not in users:
        return False, "Email not found"
    
    if users[email]["password"] != hash_password(password):
        return False, "Invalid password"
    
    return True, users[email]

def get_user_chat_histories(email):
    """Get all chat histories for a user"""
    user_dir = CHAT_HISTORY_DIR / email
    if not user_dir.exists():
        return []
    
    histories = []
    for file in sorted(user_dir.glob("*.json"), reverse=True):
        with open(file, 'r') as f:
            data = json.load(f)
            histories.append({
                "filename": file.name,
                "title": data.get("title", "Untitled"),
                "created_at": data.get("created_at", ""),
                "message_count": len(data.get("messages", []))
            })
    return histories

def save_chat_history(email, session_id, messages, title=""):
    """Save chat history to file"""
    user_dir = CHAT_HISTORY_DIR / email
    user_dir.mkdir(exist_ok=True)
    
    if not title:
        title = f"Chat {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    
    history_file = user_dir / f"{session_id}.json"
    
    chat_data = {
        "session_id": session_id,
        "title": title,
        "created_at": datetime.now().isoformat(),
        "messages": messages
    }
    
    with open(history_file, 'w') as f:
        json.dump(chat_data, f, indent=2)
    
    logger.info(f"Chat history saved: {history_file}")

def load_chat_history(email, filename):
    """Load a specific chat history"""
    history_file = CHAT_HISTORY_DIR / email / filename
    if history_file.exists():
        with open(history_file, 'r') as f:
            return json.load(f)
    return None

def delete_chat_history(email, filename):
    """Delete a chat history"""
    history_file = CHAT_HISTORY_DIR / email / filename
    if history_file.exists():
        history_file.unlink()
        return True
    return False

# ============================================
# INITIALIZE SESSION STATE
# ============================================

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
    st.session_state.user_email = None
    st.session_state.user_name = None

if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
    logger.info(f"New session created: {st.session_state.session_id}")
    
if "messages" not in st.session_state:
    st.session_state.messages = []
    st.session_state.chat_title = "New Conversation"

if "booking_complete" not in st.session_state:
    st.session_state.booking_complete = False

if "pending_booking_details" not in st.session_state:
    st.session_state.pending_booking_details = None

if "current_chat_file" not in st.session_state:
    st.session_state.current_chat_file = None

# ============================================
# AUTHENTICATION PAGE
# ============================================

if not st.session_state.authenticated:
    st.markdown("""
    <div style='text-align: center;'>
        <h1>🩺 Dr. AQEEL SkinCare Clinic</h1>
        <h3>AI Appointment Booking System</h3>
    </div>
    """, unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["🔓 Login", "📝 Sign Up"])
    
    # ============ LOGIN TAB ============
    with tab1:
        st.subheader("Welcome Back!")
        login_email = st.text_input("Email", key="login_email", placeholder="you@example.com")
        login_password = st.text_input("Password", type="password", key="login_password", placeholder="Enter your password")
        
        if st.button("🔓 Login", use_container_width=True, key="login_btn"):
            if not login_email or not login_password:
                st.error("❌ Please enter both email and password")
            else:
                success, user_data = login_user(login_email, login_password)
                if success:
                    st.session_state.authenticated = True
                    st.session_state.user_email = login_email
                    st.session_state.user_name = user_data["name"]
                    st.session_state.messages = []
                    st.success(f"✅ Welcome back, {user_data['name']}!")
                    st.rerun()
                else:
                    st.error(f"❌ {user_data}")
    
    # ============ SIGNUP TAB ============
    with tab2:
        st.subheader("Create Your Account")
        signup_name = st.text_input("Full Name", key="signup_name", placeholder="Your name")
        signup_email = st.text_input("Email", key="signup_email", placeholder="you@example.com")
        signup_password = st.text_input("Password", type="password", key="signup_password", placeholder="Create a password")
        signup_confirm = st.text_input("Confirm Password", type="password", key="signup_confirm", placeholder="Confirm password")
        
        if st.button("📝 Sign Up", use_container_width=True, key="signup_btn"):
            if not signup_name or not signup_email or not signup_password:
                st.error("❌ Please fill in all fields")
            elif signup_password != signup_confirm:
                st.error("❌ Passwords do not match")
            elif len(signup_password) < 6:
                st.error("❌ Password must be at least 6 characters")
            else:
                success, message = register_user(signup_email, signup_password, signup_name)
                if success:
                    st.success(f"✅ {message} You can now login!")
                else:
                    st.error(f"❌ {message}")

# ============================================
# MAIN CHAT INTERFACE (AUTHENTICATED)
# ============================================

else:
    # Header with user info and logout
    col1, col2, col3 = st.columns([1, 2, 1])
    with col1:
        st.markdown(f"### 👤 {st.session_state.user_name}")
    with col3:
        if st.button("🚪 Logout", use_container_width=True):
            # Save current chat before logout
            if st.session_state.messages and len(st.session_state.messages) > 0:
                save_chat_history(
                    st.session_state.user_email,
                    st.session_state.session_id,
                    st.session_state.messages,
                    st.session_state.chat_title
                )
            st.session_state.authenticated = False
            st.session_state.user_email = None
            st.session_state.user_name = None
            st.session_state.messages = []
            st.rerun()
    
    st.divider()
    
    # Sidebar for chat management
    with st.sidebar:
        st.markdown("### 💬 Conversations")
        
        # New Chat Button
        if st.button("➕ New Conversation", use_container_width=True, key="new_chat"):
            # Save current chat if it has messages
            if st.session_state.messages and len(st.session_state.messages) > 0:
                save_chat_history(
                    st.session_state.user_email,
                    st.session_state.session_id,
                    st.session_state.messages,
                    st.session_state.chat_title
                )
            
            # Reset for new chat
            st.session_state.session_id = str(uuid.uuid4())
            st.session_state.messages = []
            st.session_state.chat_title = f"Chat {datetime.now().strftime('%H:%M')}"
            st.session_state.current_chat_file = None
            st.rerun()
        
        st.divider()
        
        # Chat History
        st.markdown("#### 📚 Your Chats")
        histories = get_user_chat_histories(st.session_state.user_email)
        
        if histories:
            for history in histories:
                cols = st.columns([3, 1])
                with cols[0]:
                    # Click to load chat
                    if st.button(
                        f"💬 {history['title']}\n_{history['message_count']} messages_",
                        use_container_width=True,
                        key=f"load_chat_{history['filename']}"
                    ):
                        # Save current chat first
                        if st.session_state.messages and len(st.session_state.messages) > 0:
                            save_chat_history(
                                st.session_state.user_email,
                                st.session_state.session_id,
                                st.session_state.messages,
                                st.session_state.chat_title
                            )
                        
                        # Load selected chat
                        chat_data = load_chat_history(st.session_state.user_email, history['filename'])
                        if chat_data:
                            st.session_state.messages = chat_data['messages']
                            st.session_state.chat_title = chat_data['title']
                            st.session_state.session_id = chat_data['session_id']
                            st.session_state.current_chat_file = history['filename']
                            st.rerun()
                
                with cols[1]:
                    # Delete button
                    if st.button("🗑️", key=f"delete_{history['filename']}", help="Delete this chat"):
                        delete_chat_history(st.session_state.user_email, history['filename'])
                        st.success("Chat deleted!")
                        st.rerun()
        else:
            st.info("📭 No chat history yet. Start a new conversation!")
    
    # Main chat area
    st.markdown(f"## 🩺 Dr. AQEEL SkinCare Clinic")
    st.markdown(f"### {st.session_state.chat_title}")
    
    # Display Chat Messages
    if not st.session_state.messages:
        # Initial greeting for new chat
        st.session_state.messages = [{
            "role": "assistant",
            "content": "Hello! 👋 I'm Dr. AQEEL's AI appointment booking assistant. How can I help you today?"
        }]
    
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
    
    # Chat Input
    if prompt := st.chat_input("Type your message...", key=f"chat_input_{st.session_state.session_id}"):
        # Add user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Check if user is confirming a booking
        user_confirming = any(word in prompt.lower() for word in ['yes', 'confirm', 'book it', 'proceed', 'ok', 'sure'])
        message_to_send = prompt
        
        # Call API
        with st.spinner("🔄 Processing..."):
            try:
                for attempt in range(REQUEST_RETRIES):
                    try:
                        payload = {
                            "message": message_to_send,
                            "session_id": st.session_state.session_id
                        }
                        
                        if user_confirming and st.session_state.pending_booking_details:
                            payload["booking_details"] = st.session_state.pending_booking_details
                        
                        response = requests.post(
                            API_URL,
                            json=payload,
                            timeout=API_TIMEOUT
                        )
                        response.raise_for_status()
                        data = response.json()
                        agent_response = data.get("response", "I apologize, but I didn't receive a proper response.")
                        break
                    except requests.exceptions.Timeout:
                        if attempt < REQUEST_RETRIES - 1:
                            continue
                        agent_response = "⏱️ Server timeout. Please try again."
                    except requests.exceptions.ConnectionError:
                        agent_response = "❌ Cannot connect to API. Is the server running on http://127.0.0.1:8000?"
                        break
                    except requests.exceptions.HTTPError as e:
                        agent_response = f"⚠️ Server error ({e.response.status_code}). Please try again."
                        break
                
                # Add response
                st.session_state.messages.append({"role": "assistant", "content": agent_response})
                
                # Extract booking details if present
                if "Appointment Summary:" in agent_response:
                    import re
                    details = {
                        'name': re.search(r'Name: (\w+)', agent_response),
                        'phone': re.search(r'Phone: ([\d]+)', agent_response),
                        'email': re.search(r'Email: ([\w.@]+)', agent_response),
                        'concern': re.search(r'Concern: ([^\n]+)', agent_response),
                        'date': re.search(r'Date: (\d{4}-\d{2}-\d{2})', agent_response),
                        'time': re.search(r'Time: (\d{2}:\d{2})', agent_response),
                    }
                    st.session_state.pending_booking_details = {
                        'name': details['name'].group(1) if details['name'] else None,
                        'phone': details['phone'].group(1) if details['phone'] else None,
                        'email': details['email'].group(1) if details['email'] else None,
                        'concern': details['concern'].group(1).strip() if details['concern'] else None,
                        'date': details['date'].group(1) if details['date'] else None,
                        'time': details['time'].group(1) if details['time'] else None,
                    }
                
                # Check if booking confirmed
                if "APPOINTMENT CONFIRMED" in agent_response:
                    st.session_state.booking_complete = True
                    st.session_state.pending_booking_details = None
                
                with st.chat_message("assistant"):
                    st.markdown(agent_response)
                
                # Auto-save chat after each message
                save_chat_history(
                    st.session_state.user_email,
                    st.session_state.session_id,
                    st.session_state.messages,
                    st.session_state.chat_title
                )
                st.rerun()
                    
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
                logger.error(f"Unexpected error: {e}", exc_info=True)
    
    # Footer
    st.divider()
    col1, col2, col3 = st.columns(3)
    with col1:
        st.caption(f"📱 Session: {st.session_state.session_id[:8]}...")
    with col2:
        st.caption(f"💬 Messages: {len(st.session_state.messages)}")
    with col3:
        st.caption("🩺 Dr. AQEEL Clinic")

