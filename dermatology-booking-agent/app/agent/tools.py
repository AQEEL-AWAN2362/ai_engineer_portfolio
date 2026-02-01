from datetime import datetime, timedelta, date
from typing import Optional
from langchain.tools import tool
from app.services.booking_service import booking_service
import re
import logging

logger = logging.getLogger(__name__)

def validate_phone(phone: str) -> bool:
    """Validate phone number format"""
    # Simple validation: at least 10 digits
    digits = re.sub(r'\D', '', phone)
    return len(digits) >= 10

def validate_email(email: Optional[str]) -> bool:
    """Validate email format"""
    if not email:
        return True  # Email is optional
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

@tool
def get_clinic_info():
    """
    Returns general information about the clinic, such as hours, location, and specialization.
    Use this when the user asks about the clinic operations.
    """
    return """
    **Clinic Name**: Dr. AQEEL Skin Clinic
    **Specialization**: Dermatology (Acne, Rashes, Hair Loss, Cosmetic)
    **Doctor**: Dr. AQEEL 
    **Location**: 123 Health St, Wellness City Pakistan
    **Hours**: Mon-Thu 09:00-17:00, Fri 09:00-13:00, Sat-Sun Closed.
    **Contact**: +923001234567
    """

@tool
def check_availability(query_date: str) -> str:
    """
    Checks for available appointment slots on a given date.
    Args:
        query_date: The date to check in 'YYYY-MM-DD' format.
    """
    try:
        # Validate date format
        target_date = datetime.strptime(query_date, "%Y-%m-%d").date()
        
        # Validate date is not in the past
        if target_date < date.today():
            return f"Cannot book appointments in the past. Please select a future date."
        
        # Validate date is not too far in future (e.g., max 90 days)
        max_date = date.today() + timedelta(days=90)
        if target_date > max_date:
            return f"Appointments can only be booked up to 90 days in advance."
        
        slots = booking_service.get_available_slots(target_date)
        if not slots:
            return f"No slots available on {query_date}. Please try another day."
        
        logger.info(f"Found {len(slots)} available slots on {query_date}")
        return f"Available slots on {query_date}: {', '.join(slots)}"
        
    except ValueError as e:
        logger.warning(f"Invalid date format: {query_date}")
        return "Invalid date format. Please use YYYY-MM-DD (e.g., 2026-02-15)."
    except Exception as e:
        logger.error(f"Error checking availability: {e}", exc_info=True)
        return "Error checking availability. Please try again."

@tool
def book_appointment(name: str, phone: str, email: Optional[str], date_str: str, time_str: str, concern: str, urgency: str = "Normal", conversation_history: Optional[str] = None) -> str:
    """
    Books an appointment for the patient.
    Args:
        name: Patient's full name (required).
        phone: Patient's phone number (required).
        email: Patient's email address (optional but recommended for confirmation).
        date_str: Date in 'YYYY-MM-DD' format (required).
        time_str: Time in 'HH:MM' format (required).
        concern: Brief description of the skin issue (required).
        urgency: 'Normal', 'Urgent', or 'Emergency' (optional, defaults to Normal).
        conversation_history: Full conversation transcript to include in email (optional).
    """
    try:
        # Validate required fields
        if not name or not name.strip():
            return "Error: Patient name is required."
        
        if not phone or not validate_phone(phone):
            return "Error: Valid phone number is required (at least 10 digits)."
        
        if not concern or not concern.strip():
            return "Error: Please describe your skin concern."
        
        if urgency not in ["Normal", "Urgent", "Emergency"]:
            urgency = "Normal"
        
        # Validate datetime format
        try:
            datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
        except ValueError:
            return "Error: Invalid date/time format. Use YYYY-MM-DD and HH:MM."
        
        logger.info(f"Booking appointment for {name} on {date_str} at {time_str}")
        
        # Book appointment with conversation history
        result = booking_service.book_appointment(
            name=name.strip(),
            phone=phone.strip(),
            email=email,
            date_str=date_str,
            time_str=time_str,
            concern=concern.strip(),
            urgency=urgency,
            conversation_history=conversation_history
        )
        
        logger.info(f"Booking result: {result}")
        return result
        
    except Exception as e:
        logger.error(f"Error booking appointment: {e}", exc_info=True)
        return "Error booking appointment. Please try again or call the clinic."
