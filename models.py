from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=False)
    role = Column(String, default="parent")
    is_active = Column(Boolean, default=True)
    observer_role = Column(String, nullable=True)  # роль наблюдателя: мама, папа, сестра...
    created_at = Column(DateTime, default=datetime.utcnow)
    observations = relationship("Observation", back_populates="author")
    children = relationship("Child", back_populates="parent", cascade="all, delete")

class Child(Base):
    __tablename__ = "children"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    name = Column(String, nullable=False)
    parent = relationship("User", back_populates="children")

class Observation(Base):
    __tablename__ = "observations"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    child_name = Column(String, nullable=False)
    observer_name = Column(String, nullable=False)
    obs_date = Column(String, nullable=False)
    obs_time = Column(String, nullable=False)
    location = Column(String, nullable=False)
    antecedent = Column(Text, nullable=False)
    behavior = Column(Text, nullable=False)
    consequence = Column(Text, nullable=False)
    function = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    author = relationship("User", back_populates="observations")

class Setting(Base):
    __tablename__ = "settings"
    id = Column(Integer, primary_key=True, index=True)
    key = Column(String, unique=True, index=True)
    value = Column(Text)
