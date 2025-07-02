from sqlalchemy import Column, Integer, Enum, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from enum import Enum as PyEnum
from db.database import Base

class MovementType(PyEnum):
    entrada = "entrada"
    salida = "salida"
    traslado = "traslado"

class ItemMovement(Base):
    __tablename__ = "item_movements"

    id = Column(Integer, primary_key=True, index=True)
    item_id = Column(Integer, ForeignKey("items.id"), nullable=False)
    source_warehouse_id = Column(Integer, ForeignKey("warehouses.id"), nullable=True)
    target_warehouse_id = Column(Integer, ForeignKey("warehouses.id"), nullable=True)
    quantity = Column(Integer, nullable=False)
    type = Column(Enum(MovementType), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)

    # Optional fields for purchase and sale prices
    purchase_price = Column(Integer, nullable=True) 
    sale_price = Column(Integer, nullable=True)

    item_movement_group_id = Column(Integer, nullable=True)

    item = relationship("Item")
    source_warehouse = relationship("Warehouse", foreign_keys=[source_warehouse_id])
    target_warehouse = relationship("Warehouse", foreign_keys=[target_warehouse_id])
    user = relationship("User")
