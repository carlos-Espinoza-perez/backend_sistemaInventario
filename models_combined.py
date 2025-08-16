from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from db.database import Base

class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)

    items = relationship("Item", back_populates="category")
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
    
    @property
    def updated_at_local(self):
        from zoneinfo import ZoneInfo
        from datetime import timezone
        return self.updated_at.replace(tzinfo=timezone.utc).astimezone(ZoneInfo("America/Managua"))
from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from db.database import Base

class Item(Base):
    __tablename__ = "items"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(50), unique=True, nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    category = relationship("Category", back_populates="items")

    @property
    def created_at_local(self):
        from zoneinfo import ZoneInfo
        from datetime import timezone
        return self.created_at.replace(tzinfo=timezone.utc).astimezone(ZoneInfo("America/Managua"))

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

    @property
    def timestamp_local(self):
        from zoneinfo import ZoneInfo
        from datetime import timezone
        return self.timestamp.replace(tzinfo=timezone.utc).astimezone(ZoneInfo("America/Managua"))
from sqlalchemy import Column, Integer, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from db.database import Base

class ItemMovementGroup(Base):
    __tablename__ = "item_movement_groups"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    note = Column(Text, nullable=True)
    warehouse_id = Column(Integer, ForeignKey("warehouses.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User")
    warehouse = relationship("Warehouse")

    @property
    def created_at_local(self):
        from zoneinfo import ZoneInfo
        from datetime import timezone
        return self.created_at.replace(tzinfo=timezone.utc).astimezone(ZoneInfo("America/Managua"))
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
    @property
    def created_at_local(self):
        from zoneinfo import ZoneInfo
        from datetime import timezone
        return self.created_at.replace(tzinfo=timezone.utc).astimezone(ZoneInfo("America/Managua"))

from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime
from db.database import Base

class Warehouse(Base):
    __tablename__ = "warehouses"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    location = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    @property
    def created_at_local(self):
        from zoneinfo import ZoneInfo
        from datetime import timezone
        return self.created_at.replace(tzinfo=timezone.utc).astimezone(ZoneInfo("America/Managua"))
