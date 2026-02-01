from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field
from langchain_core.messages import HumanMessage
from app.agent.graph import workflow
import logging
import traceback

logger = logging.getLogger(__name__)

router = APIRouter()

class BookingDetails(BaseModel):
    name: str | None = None
    phone: str | None = None
    email: str | None = None
    concern: str | None = None
    date: str | None = None
    time: str | None = None

class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=5000)
    session_id: str = Field(..., min_length=1)
    booking_details: BookingDetails | None = None

class ChatResponse(BaseModel):
    response: str

@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: Request, body: ChatRequest):
    """
    Interact with the AI Agent with persistent memory and long-term patient history.
    Uses PostgreSQL store (Supabase) for long-term memory and checkpointer for conversation state.
    Input messages are converted to LangChain HumanMessage format.
    """
    try:
        config = {
            "configurable": {
                "thread_id": body.session_id,
                "user_id": body.session_id,  # Use session_id as user_id for patient identification
            }
        }
        
        # Convert input message to LangChain format
        message_content = body.message
        
        # If booking_details are provided (e.g., on confirmation), embed them in the message
        if body.booking_details:
            details_parts = []
            if body.booking_details.name:
                details_parts.append(f"name={body.booking_details.name}")
            if body.booking_details.phone:
                details_parts.append(f"phone={body.booking_details.phone}")
            if body.booking_details.email:
                details_parts.append(f"email={body.booking_details.email}")
            if body.booking_details.concern:
                details_parts.append(f"concern={body.booking_details.concern}")
            if body.booking_details.date:
                details_parts.append(f"date={body.booking_details.date}")
            if body.booking_details.time:
                details_parts.append(f"time={body.booking_details.time}")
            
            if details_parts:
                message_content = f"{body.message}. Booking details: {', '.join(details_parts)}"
        
        input_message = HumanMessage(content=message_content)
        
        # Get shared checkpointer and store from app state
        checkpointer = request.app.state.checkpointer
        store = request.app.state.store
        
        # Compile with both checkpointer for conversation history and store for long-term memory
        app = workflow.compile(checkpointer=checkpointer, store=store)
        result = await app.ainvoke({"messages": [input_message]}, config=config)
        
        # Extract last message content
        last_message = result["messages"][-1]
        response_text = last_message.content if hasattr(last_message, 'content') else str(last_message)
        
        logger.info(f"Chat response sent for session {body.session_id}")
        return ChatResponse(response=response_text)
        
    except Exception as e:
        logger.error(f"Chat endpoint error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="An error occurred processing your message. Please try again.")
