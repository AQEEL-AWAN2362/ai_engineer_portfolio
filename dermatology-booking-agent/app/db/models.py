from typing import Optional, List
from datetime import datetime, time
from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy import Column, JSON

# Shared Properties
class DoctorBase(SQLModel):
    name: str = Field(index=True)
    specialization: str
    clinic_hours: dict = Field(sa_column=Column(JSON)) # Store hours as JSON: {"Monday": "09:00-17:00", ...}

class Doctor(DoctorBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    appointments: List["Appointment"] = Relationship(back_populates="doctor")

class PatientBase(SQLModel):
    name: str = Field(index=True)
    phone: str = Field(unique=True, index=True)
    email: Optional[str] = Field(default=None)

class Patient(PatientBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    appointments: List["Appointment"] = Relationship(back_populates="patient")

class AppointmentBase(SQLModel):
    date: datetime
    concern: str
    urgency: Optional[str] = None
    status: str = Field(default="booked") # booked, cancelled, completed
    notes: Optional[str] = None

class Appointment(AppointmentBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    doctor_id: int = Field(foreign_key="doctor.id")
    patient_id: int = Field(foreign_key="patient.id")
    
    doctor: Doctor = Relationship(back_populates="appointments")
    patient: Patient = Relationship(back_populates="appointments")

class Conversation(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    session_id: str = Field(index=True)
    role: str # user, assistant, system
    message: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
