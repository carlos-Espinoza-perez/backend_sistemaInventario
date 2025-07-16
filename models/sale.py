from sqlalchemy import Column, Integer, ForeignKey, Float, Boolean, Text, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from db.database import Base

class Sale(Base):
    __tablename__ = "sales"

    id = Column(Integer, primary_key=True, index=True)
    item_id = Column(Integer, ForeignKey("items.id"), nullable=False)
    warehouse_id = Column(Integer, ForeignKey("warehouses.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)  # Nuevo campo
    quantity = Column(Integer, nullable=False)
    sale_price = Column(Float, nullable=False)
    paid = Column(Boolean, default=False)
    note = Column(Text, nullable=True)
    sold_at = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)

    sale_group_id = Column(Integer, ForeignKey("sale_groups.id"), nullable=False)

    item = relationship("Item")
    warehouse = relationship("Warehouse")
    user = relationship("User")  # Relación con usuario que hizo la venta
    sale_group = relationship("SaleGroup", back_populates="sales")

    @property
    def created_at_local(self):
        from zoneinfo import ZoneInfo
        from datetime import timezone
        return self.created_at.replace(tzinfo=timezone.utc).astimezone(ZoneInfo("America/Managua"))
