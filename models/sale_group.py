from sqlalchemy import Column, Integer, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from db.database import Base

class SaleGroup(Base):
    __tablename__ = "sale_groups"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    note = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    warehouse_id = Column(Integer, ForeignKey("warehouses.id"), nullable=False)

    user = relationship("User")
    sales = relationship("Sale", back_populates="sale_group", cascade="all, delete")
    warehouse = relationship("Warehouse")

    @property
    def created_at_local(self):
        from zoneinfo import ZoneInfo
        from datetime import timezone
        return self.created_at.replace(tzinfo=timezone.utc).astimezone(ZoneInfo("America/Managua"))
