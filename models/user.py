from datetime import datetime
from sqlalchemy import Column, DateTime, Integer, String
from sqlalchemy.orm import relationship
from db.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False)
    full_name = Column(String(100), nullable=True)


    email = Column(String(50), unique=True, nullable=False)
    hashed_password = Column(String(128), nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow)

    # movements = relationship("ItemMovement", back_populates="user")
