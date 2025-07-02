from sqlalchemy import Column, Float, Integer, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from db.database import Base

class Inventory(Base):
    __tablename__ = "inventory"

    id = Column(Integer, primary_key=True, index=True)
    warehouse_id = Column(Integer, ForeignKey("warehouses.id"))
    item_id = Column(Integer, ForeignKey("items.id"))
    quantity = Column(Integer, default=0)
    updated_at = Column(DateTime, default=datetime.utcnow)

    purchase_price = Column(Float, nullable=False, default=0.0)
    sale_price = Column(Float, nullable=False, default=0.0)

    warehouse = relationship("Warehouse")
    item = relationship("Item")
    
