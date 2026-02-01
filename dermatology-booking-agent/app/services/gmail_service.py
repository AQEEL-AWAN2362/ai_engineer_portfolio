"""Email Service - Send booking confirmations and conversation history via Gmail"""

import logging
import base64
from pathlib import Path
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.core.config import settings

logger = logging.getLogger(__name__)

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# LangChain Google community utilities (simpler OAuth helper)
from langchain_google_community import GmailToolkit
from langchain_google_community.gmail.utils import get_gmail_credentials


class EmailService:
    """Service for sending emails via Gmail API"""
    
    def __init__(self):
        self.sender_email = settings.GMAIL_SENDER_EMAIL
        self.sender_name = "Dr. AQEEL Skin Clinic"
        self.credentials_file = settings.GMAIL_CREDENTIALS_FILE
        self.token_file = settings.GMAIL_TOKEN_FILE
        self.is_configured = bool(self.sender_email and self.credentials_file)
        self.gmail_service = None
        self.credentials = None
        
        if self.is_configured:
            self._initialize_gmail()
    
    def _initialize_gmail(self):
        """Initialize Gmail with OAuth2 credentials"""
        try:
            # Check if credentials file exists
            creds_path = Path(self.credentials_file)
            if not creds_path.exists():
                logger.error(f"Credentials file not found at: {self.credentials_file}")
                self.is_configured = False
                return
            
            # Try to use existing token first
            token_path = Path(self.token_file)
            if token_path.exists():
                logger.info(f"Loading existing token from {self.token_file}")
                try:
                    self.credentials = Credentials.from_authorized_user_file(
                        self.token_file,
                        scopes=["https://www.googleapis.com/auth/gmail.send"]
                    )
                    # Try to refresh if needed and has refresh token
                    if self.credentials.expired and self.credentials.refresh_token:
                        try:
                            self.credentials.refresh(Request())
                            # Save refreshed token
                            with open(self.token_file, 'w') as token:
                                token.write(self.credentials.to_json())
                        except Exception as refresh_error:
                            logger.warning(f"Could not refresh token: {refresh_error}")
                            # Continue with current token even if refresh fails
                except ValueError as e:
                    # Token missing refresh_token field - this is OK for send-only tokens
                    logger.warning(f"Token format issue (likely missing refresh_token): {e}")
                    logger.info("Attempting to re-authorize with OAuth flow...")
                    # Delete bad token and start fresh OAuth
                    token_path.unlink()
                    self.credentials = None  # Reset so OAuth flow runs
            
            # If no credentials yet (token didn't exist or was deleted), run OAuth flow
            if not self.credentials:
                # Try OAuth flow with better error handling
                try:
                    from google_auth_oauthlib.flow import InstalledAppFlow
                    
                    SCOPES = ["https://www.googleapis.com/auth/gmail.send"]
                    flow = InstalledAppFlow.from_client_secrets_file(
                        self.credentials_file,
                        scopes=SCOPES
                    )
                    # Use port 8888 as fallback
                    self.credentials = flow.run_local_server(port=8888)
                    
                    # Save credentials
                    with open(self.token_file, 'w') as token:
                        token.write(self.credentials.to_json())
                    
                    logger.info("✅ Gmail OAuth2 authorization successful")
                except Exception as oauth_error:
                    logger.warning(f"OAuth flow failed: {oauth_error}")
                    logger.info("To authorize Gmail, run: python authorize_gmail.py")
                    self.is_configured = False
                    return

            # Build Gmail service
            self.gmail_service = build('gmail', 'v1', credentials=self.credentials)
            logger.info("✅ Gmail service initialized successfully")
            logger.info(f"   Sender email: {self.sender_email}")
            
        except Exception as e:
            logger.error(f"Failed to initialize Gmail service: {e}", exc_info=True)
            logger.warning("Gmail email notifications will be disabled")
            self.is_configured = False
            self.gmail_service = None
    
    def send_booking_confirmation(
        self, 
        patient_email: str,
        patient_name: str,
        appointment_date: str,
        appointment_time: str,
        concern: str,
        conversation_history: str = None
    ) -> str:
        """
        Send booking confirmation email with appointment details and conversation history via Gmail
        
        Args:
            patient_email: Patient's email address
            patient_name: Patient's full name
            appointment_date: Appointment date (YYYY-MM-DD format)
            appointment_time: Appointment time (HH:MM format)
            concern: Patient's medical concern
            conversation_history: Full conversation transcript (optional)
        
        Returns:
            Success/error message
        """
        
        if not self.is_configured:
            logger.warning("Gmail service not configured - skipping email send")
            return "Gmail email service not configured. Please set GMAIL_SENDER_EMAIL and GMAIL_CREDENTIALS_FILE."
        
        if not self.gmail_service:
            logger.warning("Gmail service failed to initialize")
            return "Gmail service initialization failed. Please check credentials."
        
        try:
            # Format the confirmation HTML
            confirmation_html = f"""
            <html>
                <body style="font-family: Arial, sans-serif; color: #333;">
                    <div style="max-width: 600px; margin: 0 auto;">
                        
                        <div style="background-color: #2c5aa0; padding: 20px; color: white; border-radius: 5px 5px 0 0;">
                            <h2 style="margin: 0;">✅ Appointment Confirmed!</h2>
                        </div>
                        
                        <div style="background-color: #f9f9f9; padding: 20px; border: 1px solid #ddd; border-radius: 0 0 5px 5px;">
                            
                            <p>Dear <strong>{patient_name}</strong>,</p>
                            
                            <p>Your appointment with Dr. AQEEL Skin has been successfully booked. Here are your appointment details:</p>
                            
                            <div style="background-color: white; padding: 15px; border-left: 4px solid #2c5aa0; margin: 20px 0;">
                                <p style="margin: 8px 0;"><strong>📅 Date:</strong> {appointment_date}</p>
                                <p style="margin: 8px 0;"><strong>⏰ Time:</strong> {appointment_time}</p>
                                <p style="margin: 8px 0;"><strong>🏥 Concern:</strong> {concern}</p>
                            </div>
                            
                            <h3>📋 Next Steps:</h3>
                            <ul>
                                <li>Please arrive <strong>10 minutes early</strong> for your appointment</li>
                                <li>Bring any relevant medical history or documents</li>
                                <li>Wear comfortable clothing</li>
                            </ul>
                            
                            <h3>📞 Important Contact:</h3>
                            <p>If you need to reschedule or cancel, please call us at: <strong>+92 300 1234567</strong></p>
                            
                            <hr style="border: none; border-top: 1px solid #ddd; margin: 20px 0;">
                            
                            <h3>📝 Conversation Summary:</h3>
                            <div style="background-color: #f0f0f0; padding: 15px; border-radius: 5px; font-size: 12px; max-height: 400px; overflow-y: auto;">
                                <pre style="margin: 0; white-space: pre-wrap; word-wrap: break-word; font-family: monospace;">{conversation_history if conversation_history else "No conversation history available"}</pre>
                            </div>
                            
                            <hr style="border: none; border-top: 1px solid #ddd; margin: 20px 0;">
                            
                            <p style="color: #666; font-size: 12px;">
                                This is an automated confirmation email from Dr. AQEEL Skin Clinic's AI Assistant. 
                                Please do not reply to this email. For inquiries, call our clinic directly.
                            </p>
                            
                            <p style="color: #2c5aa0; font-weight: bold;">
                                Thank you for choosing Dr. AQEEL Skin Clinic! 😊
                            </p>
                        </div>
                    </div>
                </body>
            </html>
            """
            
            # Compose email message
            subject = "Appointment Confirmation - Dr. AQEEL Skin Clinic"
            
            # Build MIME message
            message = MIMEMultipart("alternative")
            message["to"] = patient_email
            message["from"] = f"{self.sender_name} <{self.sender_email}>"
            message["subject"] = subject
            
            # Add both text and HTML versions
            text_part = MIMEText(
                f"Appointment Confirmation\n\n"
                f"Dear {patient_name},\n\n"
                f"Your appointment has been confirmed.\n"
                f"Date: {appointment_date}\n"
                f"Time: {appointment_time}\n"
                f"Concern: {concern}\n\n"
                f"Thank you for choosing Dr. AQEEL Skin Clinic!",
                "plain"
            )
            html_part = MIMEText(confirmation_html, "html")
            
            message.attach(text_part)
            message.attach(html_part)
            
            # Encode message
            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
            
            # Send via Gmail API
            logger.info(f"Sending appointment confirmation email to {patient_email}...")
            
            send_message = {"raw": raw_message}
            result = self.gmail_service.users().messages().send(
                userId="me",
                body=send_message
            ).execute()
            
            message_id = result.get("id")
            logger.info(f"✅ SUCCESS: Booking confirmation email sent to {patient_email}")
            logger.info(f"Message ID: {message_id}")
            
            return f"Confirmation email sent to {patient_email}"
        
        except Exception as e:
            error_msg = f"Failed to send email via Gmail: {str(e)[:100]}"
            logger.error(error_msg, exc_info=True)
            return f"Error: {error_msg}"
    
    def send_cancellation_notification(
        self, 
        patient_email: str,
        patient_name: str,
        appointment_date: str
    ) -> str:
        """
        Send appointment cancellation notification via Gmail
        
        Args:
            patient_email: Patient's email address
            patient_name: Patient's full name
            appointment_date: Cancelled appointment date
        
        Returns:
            Success/error message
        """
        
        if not self.is_configured:
            logger.warning("Gmail service not configured - skipping email send")
            return "Gmail email service not configured"
        
        if not self.gmail_service:
            logger.warning("Gmail service failed to initialize")
            return "Gmail service initialization failed"
        
        try:
            cancellation_html = f"""
            <html>
                <body style="font-family: Arial, sans-serif; color: #333;">
                    <div style="max-width: 600px; margin: 0 auto;">
                        
                        <div style="background-color: #d32f2f; padding: 20px; color: white; border-radius: 5px 5px 0 0;">
                            <h2 style="margin: 0;">⚠️ Appointment Cancelled</h2>
                        </div>
                        
                        <div style="background-color: #f9f9f9; padding: 20px; border: 1px solid #ddd; border-radius: 0 0 5px 5px;">
                            
                            <p>Dear <strong>{patient_name}</strong>,</p>
                            
                            <p>Your appointment scheduled for <strong>{appointment_date}</strong> has been cancelled.</p>
                            
                            <p>If you would like to reschedule, please contact us at: <strong>+92 300 1234567</strong></p>
                            
                            <hr style="border: none; border-top: 1px solid #ddd; margin: 20px 0;">
                            
                            <p style="color: #666; font-size: 12px;">
                                Dr. AQEEL Skin Clinic
                            </p>
                        </div>
                    </div>
                </body>
            </html>
            """
            
            subject = "Appointment Cancellation Notice"
            
            # Build MIME message
            message = MIMEMultipart("alternative")
            message["to"] = patient_email
            message["from"] = f"{self.sender_name} <{self.sender_email}>"
            message["subject"] = subject
            
            text_part = MIMEText(
                f"Appointment Cancellation Notice\n\n"
                f"Dear {patient_name},\n\n"
                f"Your appointment scheduled for {appointment_date} has been cancelled.\n\n"
                f"If you would like to reschedule, please contact us at +92 300 1234567.\n\n"
                f"Thank you,\nDr. AQEEL Skin Clinic",
                "plain"
            )
            html_part = MIMEText(cancellation_html, "html")
            
            message.attach(text_part)
            message.attach(html_part)
            
            # Encode message
            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
            
            # Send via Gmail API
            logger.info(f"Sending cancellation notification to {patient_email}...")
            
            send_message = {"raw": raw_message}
            result = self.gmail_service.users().messages().send(
                userId="me",
                body=send_message
            ).execute()
            
            logger.info(f"✅ Cancellation notification sent to {patient_email}")
            return f"Cancellation notification sent to {patient_email}"
        
        except Exception as e:
            error_msg = f"Failed to send cancellation email: {str(e)[:100]}"
            logger.error(error_msg, exc_info=True)
            return f"Error: {error_msg}"


# Singleton instance
email_service = EmailService()
