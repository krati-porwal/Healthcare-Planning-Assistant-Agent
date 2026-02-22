"""
SQLAlchemy ORM models matching the ER Diagram exactly.
All tables and relationships defined here.
"""
import uuid
from datetime import datetime
from sqlalchemy import (
    Column, String, Integer, Float, Boolean, Text, DateTime,
    ForeignKey, JSON
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from backend.db.database import Base


def generate_uuid():
    return str(uuid.uuid4())


# ─────────────────────────────────────────────────────────────────────────────
# User
# ─────────────────────────────────────────────────────────────────────────────
class User(Base):
    __tablename__ = "users"

    user_id = Column(UUID(as_uuid=False), primary_key=True, default=generate_uuid)
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    location = Column(String(255), nullable=True)
    budget = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    sessions = relationship("UserSession", back_populates="user", cascade="all, delete-orphan")
    medical_profiles = relationship("MedicalProfile", back_populates="user", cascade="all, delete-orphan")


# ─────────────────────────────────────────────────────────────────────────────
# UserSession
# ─────────────────────────────────────────────────────────────────────────────
class UserSession(Base):
    __tablename__ = "user_sessions"

    session_id = Column(UUID(as_uuid=False), primary_key=True, default=generate_uuid)
    user_id = Column(UUID(as_uuid=False), ForeignKey("users.user_id"), nullable=False)
    start_time = Column(DateTime, default=datetime.utcnow)
    end_time = Column(DateTime, nullable=True)
    goal = Column(Text, nullable=True)
    status = Column(String(50), default="active")  # active, completed, error

    # Relationships
    user = relationship("User", back_populates="sessions")


# ─────────────────────────────────────────────────────────────────────────────
# MedicalProfile
# ─────────────────────────────────────────────────────────────────────────────
class MedicalProfile(Base):
    __tablename__ = "medical_profiles"

    profile_id = Column(UUID(as_uuid=False), primary_key=True, default=generate_uuid)
    user_id = Column(UUID(as_uuid=False), ForeignKey("users.user_id"), nullable=False)
    disease_type = Column(String(255), nullable=True)
    cancer_type = Column(String(255), nullable=True)
    stage = Column(String(100), nullable=True)
    medical_history = Column(Text, nullable=True)
    surgery_allowed = Column(Boolean, nullable=True)
    age = Column(Integer, nullable=True)
    gender = Column(String(50), nullable=True)
    symptoms = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="medical_profiles")
    lab_reports = relationship("LabReport", back_populates="medical_profile", cascade="all, delete-orphan")
    constraints = relationship("Constraint", back_populates="medical_profile", cascade="all, delete-orphan")
    treatment_plans = relationship("TreatmentPlan", back_populates="medical_profile", cascade="all, delete-orphan")


# ─────────────────────────────────────────────────────────────────────────────
# LabReport
# ─────────────────────────────────────────────────────────────────────────────
class LabReport(Base):
    __tablename__ = "lab_reports"

    report_id = Column(UUID(as_uuid=False), primary_key=True, default=generate_uuid)
    profile_id = Column(UUID(as_uuid=False), ForeignKey("medical_profiles.profile_id"), nullable=False)
    report_type = Column(String(255), nullable=False)
    report_date = Column(DateTime, nullable=True)
    report_data = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    medical_profile = relationship("MedicalProfile", back_populates="lab_reports")


# ─────────────────────────────────────────────────────────────────────────────
# Constraint
# ─────────────────────────────────────────────────────────────────────────────
class Constraint(Base):
    __tablename__ = "constraints"

    constraint_id = Column(UUID(as_uuid=False), primary_key=True, default=generate_uuid)
    profile_id = Column(UUID(as_uuid=False), ForeignKey("medical_profiles.profile_id"), nullable=False)
    budget_limit = Column(Float, nullable=True)
    location_type = Column(String(100), nullable=True)  # local, national, international
    hospital_preference = Column(String(100), nullable=True)  # government, private
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    medical_profile = relationship("MedicalProfile", back_populates="constraints")


# ─────────────────────────────────────────────────────────────────────────────
# TreatmentPlan
# ─────────────────────────────────────────────────────────────────────────────
class TreatmentPlan(Base):
    __tablename__ = "treatment_plans"

    plan_id = Column(UUID(as_uuid=False), primary_key=True, default=generate_uuid)
    profile_id = Column(UUID(as_uuid=False), ForeignKey("medical_profiles.profile_id"), nullable=False)
    treatment_type = Column(String(255), nullable=True)
    timeline = Column(String(255), nullable=True)
    disclaimer = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    raw_output = Column(JSON, nullable=True)  # stores the full structured JSON output
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    medical_profile = relationship("MedicalProfile", back_populates="treatment_plans")
    recommendations = relationship("Recommendation", back_populates="treatment_plan", cascade="all, delete-orphan")


# ─────────────────────────────────────────────────────────────────────────────
# Hospital
# ─────────────────────────────────────────────────────────────────────────────
class Hospital(Base):
    __tablename__ = "hospitals"

    hospital_id = Column(String(50), primary_key=True)
    name = Column(String(255), nullable=False)
    type = Column(String(100), nullable=False)
    location = Column(String(255), nullable=False)
    city = Column(String(100), nullable=True)
    state = Column(String(100), nullable=True)
    contact = Column(String(100), nullable=True)
    email = Column(String(255), nullable=True)
    accreditation = Column(String(255), nullable=True)
    rating = Column(Float, nullable=True)
    budget_category = Column(String(50), nullable=True)  # Premium, Standard, Government
    accepts_insurance = Column(Boolean, default=True)
    specializations = Column(JSON, nullable=True)
    summary = Column(Text, nullable=True)

    # Relationships
    recommendations = relationship("Recommendation", back_populates="hospital")


# ─────────────────────────────────────────────────────────────────────────────
# Recommendation
# ─────────────────────────────────────────────────────────────────────────────
class Recommendation(Base):
    __tablename__ = "recommendations"

    recommendation_id = Column(UUID(as_uuid=False), primary_key=True, default=generate_uuid)
    plan_id = Column(UUID(as_uuid=False), ForeignKey("treatment_plans.plan_id"), nullable=False)
    hospital_id = Column(String(50), ForeignKey("hospitals.hospital_id"), nullable=False)
    priority_rank = Column(Integer, nullable=False)
    reasoning = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    treatment_plan = relationship("TreatmentPlan", back_populates="recommendations")
    hospital = relationship("Hospital", back_populates="recommendations")
