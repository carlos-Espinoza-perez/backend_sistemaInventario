import pandas as pd
from datetime import datetime
from sqlalchemy.orm import Session

from models.category import Category
from models.inventory import Inventory
from models.item import Item
from models.item_movement import ItemMovement, MovementType

def importar_excel_inventario(
    excel_path: str,
    db: Session,
    warehouse_id: int,
    user_id: int
):
    df = pd.read_excel(excel_path)

    # Rellenar NaN con valores válidos por defecto
    df["Precio de compra"] = df["Precio de compra"].fillna(0)
    df["Precio de venta"] = df["Precio de venta"].fillna(0)
    df["Cantidad"] = df["Cantidad"].fillna(0)

    categoria = db.query(Category).first()
    if not categoria:
        raise Exception("No hay ninguna categoría registrada.")

    for _, row in df.iterrows():
        nombre = str(row["Nombre"]).strip()
        cantidad = int(row["Cantidad"])
        precio_compra = float(row["Precio de compra"])
        precio_venta = float(row["Precio de venta"])

        if not nombre:
            continue  # Saltar filas vacías

        item = db.query(Item).filter_by(code=nombre).first()
        if not item:
            item = Item(
                code=nombre,
                name=nombre,
                description='',
                category_id=categoria.id,
                created_at=datetime.utcnow()
            )
            db.add(item)
            db.flush()

        inventario = db.query(Inventory).filter_by(
            warehouse_id=warehouse_id,
            item_id=item.id
        ).first()

        if inventario:
            inventario.quantity += cantidad
            inventario.purchase_price = precio_compra
            inventario.sale_price = precio_venta
            inventario.updated_at = datetime.utcnow()
        else:
            inventario = Inventory(
                warehouse_id=warehouse_id,
                item_id=item.id,
                quantity=cantidad,
                purchase_price=precio_compra,
                sale_price=precio_venta,
                updated_at=datetime.utcnow()
            )
            db.add(inventario)

        movimiento = ItemMovement(
            item_id=item.id,
            source_warehouse_id=None,
            target_warehouse_id=warehouse_id,
            quantity=cantidad,
            type=MovementType.entrada,
            user_id=user_id,
            timestamp=datetime.utcnow(),
            purchase_price=precio_compra,
            sale_price=precio_venta
        )
        db.add(movimiento)

    db.commit()
    print("✅ Inventario importado correctamente.")
