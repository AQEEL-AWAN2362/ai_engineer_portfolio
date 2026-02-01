from datetime import datetime, timedelta, time
from typing import List, Optional
from sqlmodel import Session, select, and_
from app.db.engine import sync_engine
from app.db.models import Doctor, Appointment, Patient
from app.services.gmail_service import email_service
import logging

logger = logging.getLogger(__name__)

class BookingService:
    def get_doctor_hours(self) -> dict:
        """Fetch doctor's working hours from database"""
        try:
            with Session(sync_engine) as session:
                doctor = session.exec(select(Doctor)).first()
                if not doctor:
                    logger.warning("No doctor configured in database")
                    return {}
                return doctor.clinic_hours
        except Exception as e:
            logger.error(f"Error fetching doctor hours: {e}")
            return {}

    def get_available_slots(self, query_date: datetime.date) -> List[str]:
        """
        Returns a list of available start times (strings "HH:MM") for a given date.
        Assumes 1-hour slots for simplicity.
        """
        try:
            with Session(sync_engine) as session:
                # Get doctor hours for the day
                day_name = query_date.strftime("%A")
                doctor_hours = self.get_doctor_hours()
                
                if day_name not in doctor_hours:
                    logger.debug(f"Clinic closed on {day_name}")
                    return []
                
                hours_str = doctor_hours[day_name]  # e.g., "09:00-17:00"
                
                try:
                    start_str, end_str = hours_str.split("-")
                except ValueError:
                    logger.error(f"Invalid hours format: {hours_str}")
                    return []
                
                # Convert to time objects
                start_time = datetime.strptime(start_str, "%H:%M").time()
                end_time = datetime.strptime(end_str, "%H:%M").time()
                
                # Generate all possible slots
                possible_slots = []
                current_time = datetime.combine(query_date, start_time)
                closing_time = datetime.combine(query_date, end_time)
                
                while current_time < closing_time:
                    possible_slots.append(current_time)
                    current_time += timedelta(hours=1)
                
                # Fetch existing appointments
                statement = select(Appointment).where(
                    and_(
                        Appointment.date >= datetime.combine(query_date, time.min),
                        Appointment.date <= datetime.combine(query_date, time.max),
                        Appointment.status != "cancelled"
                    )
                )
                existing_appointments = session.exec(statement).all()
                booked_times = {appt.date for appt in existing_appointments}
                
                # Filter available slots
                available_slots = []
                for slot in possible_slots:
                    if slot not in booked_times:
                        available_slots.append(slot.strftime("%H:%M"))
                
                logger.info(f"Found {len(available_slots)} available slots on {query_date}")
                return available_slots
                
        except Exception as e:
            logger.error(f"Error getting available slots: {e}", exc_info=True)
            return []

    def book_appointment(self, name: str, phone: str, email: str,
                         date_str: str, time_str: str, concern: str, urgency: str, 
                         conversation_history: Optional[str] = None) -> str:
        """Book an appointment with validation, error handling, and email confirmation"""
        try:
            logger.info(f"Attempting to book appointment for {name} on {date_str} at {time_str}")
            
            with Session(sync_engine) as session:
                # 1. Find or create patient
                patient = session.exec(select(Patient).where(Patient.phone == phone)).first()
                if not patient:
                    patient = Patient(name=name, phone=phone, email=email)
                    session.add(patient)
                    session.commit()
                    session.refresh(patient)
                    logger.info(f"Created new patient: {patient.id}")
                else:
                    logger.info(f"Using existing patient: {patient.id}")
                
                # 2. Parse and validate datetime
                try:
                    appt_dt = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
                except ValueError as e:
                    logger.warning(f"Invalid datetime format: {date_str} {time_str}")
                    return "Invalid date/time format. Use YYYY-MM-DD and HH:MM."
                
                # 3. Get doctor
                doctor = session.exec(select(Doctor)).first()
                if not doctor:
                    logger.error("No doctor configured in system")
                    return "System Error: No doctor configured. Please contact support."
                
                # 3.5 Validate working hours
                day_name = appt_dt.strftime("%A")
                doctor_hours = doctor.clinic_hours
                if day_name not in doctor_hours:
                    return f"Sorry, the clinic is closed on {day_name}s. Please choose a weekday."
                
                hours_str = doctor_hours[day_name]
                start_str, end_str = hours_str.split("-")
                start_time = datetime.strptime(start_str, "%H:%M").time()
                end_time = datetime.strptime(end_str, "%H:%M").time()
                
                if not (start_time <= appt_dt.time() < end_time):
                    return f"Sorry, our working hours on {day_name} are {hours_str}. Please choose a time within this range."

                # 4. Check if slot is available (race condition check)
                existing = session.exec(select(Appointment).where(
                    and_(
                        Appointment.date == appt_dt,
                        Appointment.status != "cancelled"
                    )
                )).first()
                
                if existing:
                    logger.warning(f"Slot {date_str} {time_str} is no longer available")
                    return f"Sorry, the slot {date_str} at {time_str} is no longer available. Please choose another time."
                
                # 5. Create appointment
                appointment = Appointment(
                    doctor_id=doctor.id,
                    patient_id=patient.id,
                    date=appt_dt,
                    concern=concern,
                    urgency=urgency,
                    status="booked"
                )
                session.add(appointment)
                session.commit()
                session.refresh(appointment)  # Ensure we have the ID
                
                logger.info(f"✅ Appointment saved to database successfully!")
                logger.info(f"  - Appointment ID: {appointment.id}")
                logger.info(f"  - Patient: {name} (ID: {patient.id})")
                logger.info(f"  - Date/Time: {appt_dt}")
                logger.info(f"  - Status: {appointment.status}")
                
                # 6. Send email confirmation with conversation history
                if email:
                    logger.info(f"Sending email confirmation to {email}...")
                    try:
                        email_result = email_service.send_booking_confirmation(
                            patient_email=email,
                            patient_name=name,
                            appointment_date=date_str,
                            appointment_time=time_str,
                            concern=concern,
                            conversation_history=conversation_history
                        )
                        logger.info(f"✅ Email sent successfully: {email_result}")
                    except Exception as email_error:
                        logger.error(f"❌ Email sending failed: {email_error}", exc_info=True)
                        # Don't fail the booking if email fails
                else:
                    logger.warning(f"⚠️ No email provided for patient {name} - skipping email confirmation")
                
                # Return confirmation
                return f"""✅ Appointment confirmed!

**Patient**: {name}
**Phone**: {phone}
**Date**: {date_str}
**Time**: {time_str}
**Concern**: {concern}

📧 A confirmation email with your conversation history has been sent.
We look forward to seeing you soon!"""
                
        except Exception as e:
            logger.error(f"Error booking appointment: {e}", exc_info=True)
            return "Error booking appointment. Please try again or call the clinic directly at +923001234567."

    def update_patient_phone(self, old_phone: str, new_phone: str) -> str:
        """Update patient's phone number"""
        try:
            logger.info(f"Attempting to update phone number from {old_phone} to {new_phone}")
            
            # Validate new phone
            if not self._validate_phone(new_phone):
                logger.warning(f"Invalid new phone number format: {new_phone}")
                return "Error: Invalid phone number format. Please use format like 03014567654 (10+ digits)."
            
            with Session(sync_engine) as session:
                # Find patient with old phone number
                patient = session.exec(select(Patient).where(Patient.phone == old_phone)).first()
                
                if not patient:
                    logger.warning(f"Patient with phone {old_phone} not found")
                    return f"Error: No patient found with phone number {old_phone}. Please check your phone number."
                
                # Check if new phone is already in use
                existing_patient = session.exec(select(Patient).where(Patient.phone == new_phone)).first()
                if existing_patient and existing_patient.id != patient.id:
                    logger.warning(f"Phone number {new_phone} already in use by another patient")
                    return f"Error: Phone number {new_phone} is already registered. Please use a different number."
                
                # Update phone number
                old_name = patient.name
                patient.phone = new_phone
                session.add(patient)
                session.commit()
                
                logger.info(f"Successfully updated phone for {old_name}: {old_phone} → {new_phone}")
                
                return f"""✅ Phone number updated successfully!

**Patient**: {patient.name}
**Old Phone**: {old_phone}
**New Phone**: {new_phone}

Your new phone number is now saved in our system. You'll receive future appointment confirmations at this number."""
        
        except Exception as e:
            logger.error(f"Error updating phone number: {e}", exc_info=True)
            return f"Error updating phone number: {str(e)[:100]}. Please try again or contact the clinic."
    
    @staticmethod
    def _validate_phone(phone: str) -> bool:
        """Validate phone number has at least 10 digits"""
        import re
        digits = re.sub(r'\D', '', phone)
        return len(digits) >= 10
    
booking_service = BookingService()      
