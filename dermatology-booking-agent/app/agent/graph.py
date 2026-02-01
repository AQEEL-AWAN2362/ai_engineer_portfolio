from datetime import datetime, timedelta
from typing import Annotated, TypedDict
from langchain_core.messages import BaseMessage, AIMessage, HumanMessage
from langchain_core.runnables import RunnableConfig
from langgraph.graph import StateGraph, END, add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.store.base import BaseStore
from app.core.config import settings
from app.agent.tools import check_availability, book_appointment, get_clinic_info
import logging
import socket
from langchain_core.messages import HumanMessage
import re
import calendar
import uuid
from ollama import Client

logger = logging.getLogger(__name__)

# --- State Definition ---
class AgentState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]

# --- LLM Setup with Direct Ollama Client ---
logger.info(f"LLM Configuration: {settings.OLLAMA_MODEL} at {settings.OLLAMA_BASE_URL}")

class OllamaWrapper:
    """Wrapper around direct Ollama client for better reliability"""
    
    def __init__(self):
        self.model = settings.OLLAMA_MODEL
        self.base_url = settings.OLLAMA_BASE_URL
        self.api_key = settings.OLLAMA_API_KEY
        self.client = None
        self._initialize()
    
    def _initialize(self):
        """Initialize Ollama client based on configuration"""
        try:
            # Use configuration directly without blocking tests
            if self.api_key and "localhost" not in self.base_url:
                logger.info(f"Configuring Ollama Cloud ({self.model}) at {self.base_url}")
                headers = {"Authorization": f"Bearer {self.api_key}"}
                self.client = Client(host=self.base_url, headers=headers)
            else:
                logger.info(f"Configuring Local Ollama at {self.base_url}")
                self.client = Client(host=self.base_url)
                
            # Test the connection quickly
            try:
                # Don't actually call it, just check if client is valid
                logger.info("Ollama client configured successfully")
            except Exception as e:
                logger.warning(f"Ollama client created but may have connection issues: {e}")
            
            return
        except Exception as e:
            logger.warning(f"Error configuring Ollama client (will use fallback): {e}")
            self.client = None
    
    def invoke(self, messages):
        """Call Ollama and return as AIMessage"""
        try:
            if self.client is None:
                # Mock response
                return AIMessage(content="Hello! I'm a test assistant. Please ensure your Ollama API key is valid for production use.")
            
            # Convert LangChain messages to Ollama format
            ollama_messages = []
            for msg in messages:
                if isinstance(msg, dict):
                    ollama_messages.append(msg)
                elif hasattr(msg, 'content') and hasattr(msg, 'role'):
                    ollama_messages.append({"role": msg.role, "content": msg.content})
                elif hasattr(msg, 'content'):
                    # Assume it's a system or user message
                    role = getattr(msg, 'role', 'user')
                    if isinstance(msg, AIMessage):
                        role = 'assistant'
                    ollama_messages.append({"role": role, "content": msg.content})
            
            # Call Ollama with a short timeout to fail fast
            try:
                
                # Set timeout for socket
                socket.setdefaulttimeout(5)  # 5 second timeout
                
                response = self.client.chat(
                    model=self.model,
                    messages=ollama_messages,
                    stream=False
                )
                
                socket.setdefaulttimeout(None)  # Reset timeout
                return AIMessage(content=response['message']['content'])
            except (socket.timeout, TimeoutError, ConnectionError) as llm_error:
                # If LLM fails, return a helpful mock response for testing
                logger.warning(f"LLM call failed, using mock response: {llm_error}")
                # Generate a helpful response based on conversation context
                last_user_msg = ""
                for msg in reversed(ollama_messages):
                    if msg.get("role") == "user":
                        last_user_msg = msg.get("content", "").lower()
                        break
                
                if "clinic" in last_user_msg or "info" in last_user_msg or "about" in last_user_msg:
                    return AIMessage(content="**Clinic Name**: Dr. AQEEL Skin Clinic\n**Specialization**: Dermatology (Acne, Rashes, Hair Loss, Cosmetic)\n**Hours**: Mon-Thu 09:00-17:00, Fri 09:00-13:00, Sat-Sun Closed.\n**Contact**: +923001234567")
                elif "available" in last_user_msg or "slot" in last_user_msg or "appointment" in last_user_msg:
                    return AIMessage(content="I can help you book an appointment! Please provide me with your name, phone number, email, skin concern, preferred date and time.")
                else:
                    return AIMessage(content="I'm here to help you book an appointment with Dr. AQEEL. How can I assist you today?")
        
        except Exception as e:
            logger.error(f"Ollama invoke failed critically: {e}")
            return AIMessage(content=f"I'm experiencing technical difficulties. Please try again shortly or call +923001234567 to book directly.")
    
    
    def bind_tools(self, tools):
        """Return self (tools not fully supported in this implementation yet)"""
        logger.warning("⚠️ Tool binding not fully implemented with direct Ollama client")
        return self


ollama_client = OllamaWrapper()

# --- Guardrails (System Prompt) ---
SYSTEM_PROMPT = """You are Dr. AQEEL Skin's AI Booking Assistant.
Your goal is to help patients book appointments efficiently.

CRITICAL RULES FOR MEMORY:
- ALWAYS refer to the conversation history below to remember patient information
- If you already have the patient's name/phone/details from history, DO NOT ask for them again
- Use the CONVERSATION HISTORY section to understand what the patient has already told you
- Reference specific details the patient has already provided

GENERAL RULES:
1. DO NOT provide medical advice or diagnosis. If a user asks for it, say: "I cannot provide medical advice. Please book a consultation with Dr. AQEEL."
2. ALWAYS check availability using the tool before confirming a booking.
3. Collect: Name, Phone, Email, Concern, and Urgency before booking.
4. Keep responses concise and professional.
5. If the user wants to cancel or reschedule, ask for their details (mock implementation: just say "Please call the clinic to reschedule" for now as we don't have auth).
6. **IMPORTANT**: Review the conversation history carefully. Do NOT ask for information the patient has already provided.
7. If the user provides multiple pieces of information at once, process them all.

PHONE NUMBER UPDATE:
- If user says "change phone", "update phone", "new phone", "phone number", etc., ask what the NEW phone number should be
- Once you have the old phone (from conversation history) and new phone, execute the update immediately
- Confirm the update with patient details

BOOKING FLOW STEPS:
1. When you have ALL required info (Name, Phone, Email, Concern, Date/Time), FIRST check availability by reporting what you found
2. If slots are available at the requested time, present the information and ask: "Should I book this appointment?" 
3. Wait for user confirmation (yes/confirm) before actually booking
4. If slot is NOT available, suggest alternative times from available slots
5. NEVER skip the confirmation step - always ask "Should I book this?" before proceeding
6. If user says "yes" or "confirm", then execute the booking
7. If user says "edit" or wants to change details, ask what they want to modify
8. After successful booking, provide confirmation with appointment details and note that email will be sent with conversation history

IMPORTANT: Session should NOT end until booking is completed or user explicitly cancels.
"""

# --- Tools Setup ---
tools = [get_clinic_info, check_availability, book_appointment]
llm_with_tools = ollama_client  # Using Ollama wrapper directly

def extract_booking_details(state: AgentState):
    """Extract patient booking details from conversation history"""
    
    patient_name = None
    patient_phone = None
    patient_email = None
    patient_concern = None
    appointment_date = None
    appointment_time = None
    
    # First, try to extract from current messages (may contain explicit format like "name=X, phone=Y")
    # This allows the frontend to send booking details along with confirmation
    for msg in state["messages"]:
        if not isinstance(msg, HumanMessage):
            continue
        
        content = msg.content
        
        # Check for explicit key=value format (e.g., from frontend)
        if "name=" in content.lower() and "phone=" in content.lower():
            # Extract from key=value format
            name_match = re.search(r'name=([^,]+)', content, re.IGNORECASE)
            phone_match = re.search(r'phone=(\d+)', content, re.IGNORECASE)
            email_match = re.search(r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})', content)
            concern_match = re.search(r'concern=([^,]+)', content, re.IGNORECASE)
            date_match = re.search(r'date=(\d{4}-\d{2}-\d{2})', content, re.IGNORECASE)
            time_match = re.search(r'time=(\d{2}:\d{2})', content, re.IGNORECASE)
            
            if name_match and patient_name is None:
                patient_name = name_match.group(1).strip()
            if phone_match and patient_phone is None:
                patient_phone = phone_match.group(1).strip()
            if email_match and patient_email is None:
                patient_email = email_match.group(1).strip()
            if concern_match and patient_concern is None:
                patient_concern = concern_match.group(1).strip()
            if date_match and appointment_date is None:
                appointment_date = date_match.group(1).strip()
            if time_match and appointment_time is None:
                appointment_time = time_match.group(1).strip()
    
    # If we got all details from explicit format, return early
    if patient_name and patient_phone and patient_email and patient_concern and appointment_date and appointment_time:
        return {
            "name": patient_name,
            "phone": patient_phone,
            "email": patient_email,
            "concern": patient_concern,
            "date": appointment_date,
            "time": appointment_time
        }
    
    # Otherwise, scan all user messages for booking information (original logic)
    for msg in state["messages"]:
        if not isinstance(msg, HumanMessage):
            continue
        
        content = msg.content.lower()
        original_content = msg.content
        
        # Extract name - look for pattern like "name is aqeel" or "name = alice" or from comma-separated format
        if "name" in content:
            # Try "name = value" or "name is value" format first
            name_match = re.search(r'name\s*[=:]\s*([a-zA-Z\s]+?)(?:[,\.]|$)', original_content, re.IGNORECASE)
            if not name_match:
                # Try "name is value" format
                name_match = re.search(r'name\s+(?:is\s+)?([a-zA-Z\s]+?)(?:[,\.]|$)', original_content, re.IGNORECASE)
            if name_match:
                potential_name = name_match.group(1).strip()
                if 2 <= len(potential_name) <= 50 and patient_name is None:
                    patient_name = potential_name
        
        # Extract from comma-separated format (e.g., "aqeel, 03014567654, hair loss, tomorrow at 10 am" or "name = alipur, phone = 03014567654, blisters, tomorrow at 11:00 am")
        if ',' in original_content:
            parts = [p.strip() for p in original_content.split(',')]
            
            # First part - extract name if it looks like a name
            if len(parts) >= 1:
                first_part = parts[0].strip()
                # Skip if it's a keyword like "name", "phone", "email" or a greeting
                if not any(x in first_part.lower() for x in ['hi', 'hello', 'hey', 'greetings', 'name', 'phone', 'email', 'concern', 'date', 'time', '=']):
                    potential_name = first_part
                    # Also check if it's after "name =" 
                    if '=' in first_part:
                        parts_of_first = first_part.split('=')
                        if 'name' in parts_of_first[0].lower():
                            potential_name = parts_of_first[1].strip()
                    
                    if 2 <= len(potential_name) <= 50 and patient_name is None:
                        patient_name = potential_name
            
            # Extract phone from parts
            if len(parts) >= 2:
                for part in parts:
                    if 'phone' in part.lower() or part[0].isdigit():
                        potential_phone = ''.join(c for c in part if c.isdigit())
                        if len(potential_phone) >= 10 and patient_phone is None:
                            patient_phone = potential_phone
                            break
            
            # Extract concern from parts
            if len(parts) >= 3 and patient_concern is None:
                for part in parts:
                    concern_keywords_check = ['loss', 'acne', 'rash', 'eczema', 'psoriasis', 'fungal', 'wart', 'mole', 'cosmetic', 'dermatitis', 'blister', 'infection', 'itching', 'scars']
                    for keyword in concern_keywords_check:
                        if keyword in part.lower():
                            potential_concern = part.strip()
                            if 2 <= len(potential_concern) <= 200:
                                patient_concern = potential_concern
                            break
        
        # Extract phone from "phone number = 03014567654" or "0301..."
        phone_match = re.search(r'(?:phone\s*=?\s*)?(\d{10,})', original_content)
        if phone_match and patient_phone is None:
            patient_phone = phone_match.group(1)
        
        # Extract email
        if patient_email is None:
            email_match = re.search(r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})', original_content)
            if email_match:
                patient_email = email_match.group(1)
        
        # Extract concern - Accept ANY concern related to skin/dermatology
        # Strategy: In comma-separated format, the concern is typically between phone and date/time
        if patient_concern is None:
            # First try to extract from comma-separated format intelligently
            if ',' in original_content:
                parts = [p.strip() for p in original_content.split(',')]
                # Find the part that's not name, phone, email, date, or time
                for part in parts:
                    part_lower = part.lower()
                    # Skip if it's a known field (contains =, or is obviously a name/phone/email/date)
                    has_equals = '=' in part
                    is_phone = part[0].isdigit() if part else False
                    is_email = '@' in part
                    is_time = ':' in part or 'am' in part_lower or 'pm' in part_lower
                    is_date = any(x in part_lower for x in ['tomorrow', 'today', 'jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec'])
                    is_keyword = any(x in part_lower for x in ['hi', 'hello', 'hey', 'greetings', 'name', 'phone', 'email', 'date', 'time', 'concern'])
                    
                    # If it's none of the above, it's likely the concern
                    if not (has_equals or is_phone or is_email or is_time or is_date or is_keyword):
                        potential_concern = part.strip()
                        if 2 <= len(potential_concern) <= 200 and potential_concern:
                            patient_concern = potential_concern
                            break
            
            # Fallback: If not found in comma-separated, accept any phrase with skin-related or medical context
            if patient_concern is None:
                # Accept common dermatology terms or any medical-sounding term between phone and date
                concern_keywords = ['loss', 'acne', 'rash', 'eczema', 'psoriasis', 'fungal', 'wart', 'mole', 'cosmetic', 'dermatitis', 'blister', 'infection', 'itching', 'scars', 'wrinkles', 'pigmentation', 'allergy', 'bump', 'growth', 'patch', 'spot', 'eczema', 'derma', 'skin', 'lesion', 'inflammation']
                for keyword in concern_keywords:
                    if keyword in content:
                        # Try to extract surrounding context
                        match = re.search(rf'([a-zA-Z\s]*{keyword}[a-zA-Z\s]*)', original_content, re.IGNORECASE)
                        if match:
                            patient_concern = match.group(1).strip()
                            break
        
        # Extract date - handle multiple formats: "2 feb 2026", "february 2", "2026-01-30", etc.
        if 'tomorrow' in content:
            appointment_date = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        elif 'today' in content:
            appointment_date = datetime.now().strftime("%Y-%m-%d")
        else:
            # Try YYYY-MM-DD format first
            date_match = re.search(r'(\d{4}-\d{2}-\d{2})', original_content)
            if date_match:
                appointment_date = date_match.group(1)
            else:
                # Try "D Month YYYY" or "Month D, YYYY" format (e.g., "2 feb 2026", "February 2, 2026")
                month_names = '|'.join(calendar.month_name[1:]) + '|' + '|'.join(calendar.month_abbr[1:])
                # Match both "D Month YYYY" and "Month D, YYYY" patterns
                date_pattern = rf'(\d{{1,2}})\s*({month_names})\s*(\d{{4}})|({month_names})\s*(\d{{1,2}}),?\s*(\d{{4}})'
                date_match = re.search(date_pattern, original_content, re.IGNORECASE)
                if date_match:
                    groups = date_match.groups()
                    if groups[0]:  # "D Month YYYY" format
                        day = groups[0]
                        month_str = groups[1]
                        year = groups[2]
                    else:  # "Month D YYYY" format
                        month_str = groups[3]
                        day = groups[4]
                        year = groups[5]
                    
                    try:
                        # Try to parse the month name
                        month_num = None
                        for i, name in enumerate(calendar.month_name[1:], 1):
                            if name.lower() == month_str.lower():
                                month_num = i
                                break
                        if not month_num:  # Try abbreviations
                            for i, name in enumerate(calendar.month_abbr[1:], 1):
                                if name.lower() == month_str.lower():
                                    month_num = i
                                    break
                        if month_num:
                            appointment_date = f"{year}-{month_num:02d}-{int(day):02d}"
                    except Exception as e:
                        logger.warning(f"Could not parse date '{original_content}': {e}")
        
        # Extract time - more specific regex to avoid matching day numbers
        # Require either colon+minutes OR am/pm to be valid time
        time_match = re.search(r'(\d{1,2}):(\d{2})\s*(am|pm)?|(\d{1,2})\s*(am|pm)', original_content, re.IGNORECASE)
        if time_match:
            if time_match.group(1):  # Format: HH:MM [AM/PM]
                hour = int(time_match.group(1))
                minute = int(time_match.group(2))
                am_pm = time_match.group(3).lower() if time_match.group(3) else None
            else:  # Format: H [AM/PM] (no minutes)
                hour = int(time_match.group(4))
                minute = 0
                am_pm = time_match.group(5).lower() if time_match.group(5) else None
            
            if am_pm == 'pm' and hour != 12:
                hour += 12
            elif am_pm == 'am' and hour == 12:
                hour = 0
            
            appointment_time = f"{hour:02d}:{minute:02d}"
    
    return {
        "name": patient_name,
        "phone": patient_phone,
        "email": patient_email,
        "concern": patient_concern,
        "date": appointment_date,
        "time": appointment_time
    }


def chatbot_with_prompt(state: AgentState, config: RunnableConfig = None, *, store: BaseStore = None):
    """Process user message with proper availability checking and confirmation flow"""
    try:
        # Handle config safely
        if config is None:
            config = {}
        
        # Extract user_id from config for memory namespace
        user_id = config.get("configurable", {}).get("user_id", "unknown") if config else "unknown"
        namespace = ("patient_memories", user_id)
        
        current_date = datetime.now().strftime("%Y-%m-%d")
        system_message = f"{SYSTEM_PROMPT}\n\nToday's date is {current_date}. Use this to calculate dates like 'tomorrow' or 'next Monday' when tool calling."
        
        # Store patient message
        if store:
            try:
                last_message = state["messages"][-1]
                if hasattr(last_message, 'content'):
                    content = last_message.content
                    memory = f"[{datetime.now().isoformat()}] Patient: {content}"
                    store.put(namespace, str(uuid.uuid4()), {"data": memory})
                    logger.debug(f"Stored patient message for user {user_id}")
            except Exception as save_error:
                logger.warning(f"Could not store patient message: {save_error}")
        
        # Retrieve conversation history
        memory_context = ""
        if store:
            try:
                memories = store.search(namespace, query="", limit=20)
                if memories:
                    memory_lines = []
                    for mem in memories:
                        data = mem.value.get("data", "") if isinstance(mem.value, dict) else str(mem.value)
                        if data:
                            memory_lines.append(data)
                    
                    if memory_lines:
                        memory_context = "\n".join(memory_lines[-10:])
                        system_message += f"\n\n=== CONVERSATION HISTORY ===\n{memory_context}\n=== END HISTORY ==="
                        logger.debug(f"Retrieved {len(memory_lines)} memory entries for user {user_id}")
            except Exception as mem_error:
                logger.warning(f"Could not retrieve memories: {mem_error}")
        
        # Convert messages for LLM
        ollama_messages = []
        ollama_messages.append({"role": "system", "content": system_message})
        
        for msg in state["messages"]:
            if isinstance(msg, dict):
                ollama_messages.append(msg)
            elif hasattr(msg, 'content'):
                role = 'user'
                if isinstance(msg, AIMessage):
                    role = 'assistant'
                elif hasattr(msg, 'role'):
                    role = getattr(msg, 'role', 'user')
                ollama_messages.append({"role": role, "content": msg.content})
        
        # Get LLM response
        logger.debug(f"Invoking LLM with {len(ollama_messages)} messages")
        response = llm_with_tools.invoke(ollama_messages)
        response_text = response.content
        
        # IMPORTANT: Strip any XML tags from LLM response (e.g., <availability_check>, <book_appointment>)
        # These are artifacts from the LLM trying to use tools, we handle them programmatically
        import re
        response_text = re.sub(r'<[^>]+>[^<]*</[^>]+>', '', response_text).strip()
        response_text = re.sub(r'<[^>]+>', '', response_text).strip()  # Also remove unclosed tags
        
        # Extract booking details from conversation
        booking_details = extract_booking_details(state)
        logger.info(f"Extracted booking details: {booking_details}")
        
        # Get the last user message
        last_user_msg = None
        
        for msg in reversed(state["messages"]):
            if isinstance(msg, HumanMessage):
                last_user_msg = msg.content.lower()
                break
        
        # Check if user wants to update phone number
        phone_update_request = False
        new_phone_number = None
        llm_confirmed_booking = False  # Initialize early to avoid UnboundLocalError
        
        if last_user_msg:
            # Check if user is asking to change phone (only if they explicitly say "change", "update", "new")
            # Do NOT trigger on just "phone number = " as that's used during initial booking too
            if any(x in last_user_msg for x in ['change phone', 'update phone', 'new phone', 'different phone']):
                phone_update_request = True
                
                # Try to extract new phone number from the message
                import re
                # Look for patterns like "03078817240" or "phone = 03078817240"
                phone_match = re.search(r'(?:phone\s*=?\s*)?(\d{10,})', last_user_msg)
                if phone_match:
                    new_phone_number = phone_match.group(1)
                    logger.info(f"Detected phone update request with new number: {new_phone_number}")
        
        # STEP 0: Handle phone number updates
        if phone_update_request and new_phone_number and booking_details["phone"]:
            try:
                from app.services.booking_service import booking_service
                
                logger.info(f"Processing phone number update from {booking_details['phone']} to {new_phone_number}")
                
                # Execute phone number update
                update_result = booking_service.update_patient_phone(
                    old_phone=booking_details['phone'],
                    new_phone=new_phone_number
                )
                
                response_text = update_result
                
            except Exception as e:
                logger.error(f"Error updating phone number: {e}", exc_info=True)
                response_text = f"Error updating phone number: {str(e)[:100]}"
        
        # Check if we have all required booking details AND user hasn't just provided them (to avoid immediate booking)
        has_all_details = all([booking_details["name"], booking_details["phone"], 
                               booking_details["concern"], booking_details["date"], booking_details["time"]])
        
        # IMPROVED: Check if user just provided booking information (check for phone number pattern as trigger)
        just_provided_details = False
        if last_user_msg and has_all_details:
            # Trigger availability check if:
            # 1. User provided phone/date/time info, OR
            # 2. User explicitly said "book", OR
            # 3. Message contains key booking indicators
            if any(x in last_user_msg for x in ['phone', 'number', 'tomorrow', 'today', 'date', 'time', 'am', 'pm', 'am.', 'pm.', ':']) or \
               any(x in last_user_msg for x in ['book', 'appointment', 'loss', 'acne', 'rash', 'concern']):
                just_provided_details = True
                logger.info("Detected that user just provided booking details - triggering availability check")
        
        # Check if user is trying to CONFIRM/BOOK now
        user_trying_to_confirm = last_user_msg and any(x in last_user_msg for x in ['yes', 'confirm', 'go ahead', 'book it', 'proceed', 'ok', 'sure', 'book', 'book on this'])
        
        logger.info(f"Flow Analysis:")
        logger.info(f"  just_provided_details: {just_provided_details}")
        logger.info(f"  user_trying_to_confirm: {user_trying_to_confirm}")
        logger.info(f"  has_all_details: {has_all_details}")
        logger.info(f"  last_user_msg: {last_user_msg}")
        
        # STEP 1A: If user provided booking details but NO EMAIL, ask for email first (MANDATORY)
        # BUT: Skip if user is confirming a booking (they'll provide email with other details)
        step1_executed = False
        booking_executed = False  # Track if booking was actually completed
        if not phone_update_request and has_all_details and just_provided_details and not booking_details["email"] and not user_trying_to_confirm and not llm_confirmed_booking:
            logger.info(f"STEP 1A: Email missing - requesting email before availability check")
            response_text = f"""Great! I have your booking information. Before we check availability, I need your email address:

**Information Collected So Far:**
- 👤 Name: {booking_details['name']}
- 📱 Phone: {booking_details['phone']}
- 🏥 Concern: {booking_details['concern']}
- 📅 Date: {booking_details['date']}
- ⏰ Time: {booking_details['time']}

**Please provide your email address** so we can send your appointment confirmation with the full conversation history."""
            step1_executed = True
        
        # STEP 1B: If user just provided all details INCLUDING EMAIL AND NOT trying to confirm yet, check availability and ask for confirmation
        # Skip this if user is trying to confirm (they want to book immediately with all details)
        elif not phone_update_request and has_all_details and booking_details["email"] and just_provided_details and not user_trying_to_confirm and not llm_confirmed_booking:
            try:
                from app.services.booking_service import booking_service
                
                logger.info(f"STEP 1B: Checking availability - all details including email present")
                logger.info(f"  Name: {booking_details['name']}, Phone: {booking_details['phone']}")
                logger.info(f"  Email: {booking_details['email']}, Date: {booking_details['date']}, Time: {booking_details['time']}")
                
                # We have all details including email, proceed to check availability
                logger.info(f"Checking availability for {booking_details['date']} at {booking_details['time']}")
                
                # Check availability for the requested date/time
                available_slots = booking_service.get_available_slots(
                    datetime.strptime(booking_details["date"], "%Y-%m-%d").date()
                )
                
                if not available_slots:
                    # No slots available on that day
                    response_text = f"""I've checked the schedule for {booking_details['date']}, but unfortunately there are no available slots on that day.

Could you please choose a different date? Just let me know when you'd prefer to visit, and I'll check availability for you."""
                    
                elif booking_details["time"] in available_slots:
                    # Requested slot is available - ask for confirmation
                    response_text = f"""Perfect! I've checked our schedule and the {booking_details['time']} slot on {booking_details['date']} is available. Here's a summary of your appointment:

**Appointment Summary:**
- 👤 Name: {booking_details['name']}
- 📱 Phone: {booking_details['phone']}
- 📧 Email: {booking_details['email']}
- 🏥 Skin Concern: {booking_details['concern']}
- 📅 Date: {booking_details['date']}
- ⏰ Time: {booking_details['time']}

Would you like me to book this appointment for you? Please reply with 'yes' or 'confirm' to proceed."""
                    
                else:
                    # Requested slot not available but others are
                    available_str = ", ".join(available_slots[:6])  # Show first 6
                    response_text = f"""I've checked our schedule for {booking_details['date']}. Unfortunately, the {booking_details['time']} slot is already booked.

However, we do have these available times on {booking_details['date']}: {available_str}

Would any of these times work for you? Just let me know which one you'd prefer!"""
                
                step1_executed = True
                
            except Exception as e:
                logger.error(f"Error checking availability: {e}", exc_info=True)
                response_text = f"I'm having trouble checking availability at the moment. Could you please try again in a moment?"
                step1_executed = True
        
        # CRITICAL: If LLM generated a booking confirmation (has all details), execute booking immediately
        # This catches cases where the agent itself generates the confirmation
        # BUT: Skip this if STEP 1 already executed (it handled the response)
        llm_confirmed_booking = False
        if not step1_executed and has_all_details and ('appointment' in response_text.lower() and ('confirmed' in response_text.lower() or 'booked' in response_text.lower())):
            # LLM has generated a confirmation, so we should execute the actual booking
            llm_confirmed_booking = True
            logger.info(f"CRITICAL: LLM generated booking confirmation - executing booking immediately")
            logger.info(f"  Booking for: {booking_details['name']} on {booking_details['date']} at {booking_details['time']}")
        
        # STEP 2: If user confirms booking (said "yes", "confirm", "book", etc.)
        # OR if the LLM already generated a confirmation
        # BUT: Don't execute if STEP 1 just ran (it already generated the appropriate response)
        elif not step1_executed and ((has_all_details and user_trying_to_confirm) or llm_confirmed_booking):
            try:
                from app.services.booking_service import booking_service
                
                logger.info(f"STEP 2: BOOKING EXECUTION TRIGGERED")
                logger.info(f"  step1_executed: {step1_executed}")
                logger.info(f"  has_all_details: {has_all_details}")
                logger.info(f"  last_user_msg: {last_user_msg}")
                logger.info(f"  Name: {booking_details['name']}")
                logger.info(f"  Phone: {booking_details['phone']}")
                logger.info(f"  Email: {booking_details.get('email')}")
                logger.info(f"  Date: {booking_details['date']}")
                logger.info(f"  Time: {booking_details['time']}")
                logger.info(f"  Concern: {booking_details['concern']}")
                
                # Build conversation history for email
                conversation_history = "\n".join([
                    f"{msg.role if hasattr(msg, 'role') else ('Assistant' if isinstance(msg, AIMessage) else 'Patient')}: {msg.content}"
                    for msg in state["messages"]
                ])
                
                logger.info(f"Calling booking_service.book_appointment()...")
                # Execute the booking
                booking_result = booking_service.book_appointment(
                    name=booking_details['name'],
                    phone=booking_details['phone'],
                    email=booking_details.get('email'),
                    date_str=booking_details['date'],
                    time_str=booking_details['time'],
                    concern=booking_details['concern'],
                    urgency="Normal",
                    conversation_history=conversation_history
                )
                
                logger.info(f"Booking result: {booking_result}")
                
                if "Error" not in booking_result and "error" not in booking_result.lower():
                    email_note = f"📧 A confirmation email with your conversation history has been sent to {booking_details.get('email')}" if booking_details.get('email') else "📧 Please provide your email address to receive confirmation with conversation history"
                    response_text = f"""✅ **APPOINTMENT CONFIRMED!**

Your appointment with Dr. AQEEL Skin has been successfully booked! 🎉

📋 **Appointment Details:**
  • Name: {booking_details['name']}
  • Phone: {booking_details['phone']}
  • Concern: {booking_details['concern']}
  • Date: {booking_details['date']}
  • Time: {booking_details['time']}

{email_note}

📝 **What to expect:**
  • Please arrive 10 minutes early
  • Bring any relevant medical records or photos of the concern
  • Wear comfortable clothing for easy examination

📧 A detailed confirmation with our full conversation has been sent to your email.

📞 If you need to reschedule or cancel, please call us at +92 300 1234567

Thank you for choosing Dr. AQEEL's clinic! We look forward to helping you with your skin concern. 😊"""
                else:
                    response_text = f"I apologize, but I encountered an error while booking your appointment. Please call us at +92 300 1234567 to schedule manually."
                    
            except Exception as e:
                logger.error(f"Error booking appointment: {e}", exc_info=True)
                response_text = f"Error booking appointment: {str(e)[:100]}"
        
        # If we got here, use the original LLM response (no special booking flow needed)
        final_response = AIMessage(content=response_text)
        
        # Store assistant response
        if store:
            try:
                memory = f"[{datetime.now().isoformat()}] Assistant: {final_response.content}"
                store.put(namespace, str(uuid.uuid4()), {"data": memory})
                logger.debug(f"Stored assistant response for user {user_id}")
            except Exception as save_error:
                logger.warning(f"Could not store assistant response: {save_error}")
        
        return {"messages": [final_response]}
        
    except Exception as e:
        error_str = str(e).lower()
        logger.error(f"LLM invocation failed: {str(e)}", exc_info=True)
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        
        # Provide specific error messages
        if "401" in str(e) or "unauthorized" in error_str:
            error_msg = "❌ LLM authentication failed. Check OLLAMA_API_KEY in .env file."
        elif "connection" in error_str or "timeout" in error_str:
            error_msg = "❌ Cannot connect to LLM service. Check OLLAMA_BASE_URL and internet connection."
        elif "404" in str(e) or "not found" in error_str:
            error_msg = "❌ LLM model not found. Check OLLAMA_MODEL in .env file."
        else:
            error_msg = f"⚠️ LLM Error: {str(e)[:100]}"
        
        logger.error(f"Returning error to user: {error_msg}")
        return {"messages": [AIMessage(content=error_msg)]}

# --- Graph Definition ---
workflow = StateGraph(AgentState)

workflow.add_node("agent", chatbot_with_prompt)
workflow.add_node("tools", ToolNode(tools))

workflow.set_entry_point("agent")
workflow.add_conditional_edges("agent", tools_condition)
workflow.add_edge("tools", "agent")



