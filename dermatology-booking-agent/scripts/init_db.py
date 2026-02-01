"""Database initialization script"""
import sys
from pathlib import Path
import logging

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlmodel import SQLModel, select, Session
from app.db.engine import sync_engine, init_db
from app.db.models import Doctor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def seed_doctor():
    """Seed initial doctor if not exists"""
    try:
        with Session(sync_engine) as session:
            doctor = session.exec(select(Doctor)).first()
            if not doctor:
                logger.info("Seeding doctor...")
                doc = Doctor(
                    name="Dr. AQEEL",
                    specialization="Dermatologist",
                    clinic_hours={
                        "Monday": "09:00-17:00",
                        "Tuesday": "09:00-17:00",
                        "Wednesday": "09:00-17:00",
                        "Thursday": "09:00-17:00",
                        "Friday": "09:00-13:00"
                    }
                )
                session.add(doc)
                session.commit()
                logger.info(f"Doctor seeded successfully (ID: {doc.id})")
            else:
                logger.info("Doctor already exists in database")
    except Exception as e:
        logger.error(f"Error seeding doctor: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    try:
        logger.info("Initializing database...")
        init_db()
        logger.info("Database tables created")
        
        seed_doctor()
        logger.info("Database initialization complete!")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        sys.exit(1)
