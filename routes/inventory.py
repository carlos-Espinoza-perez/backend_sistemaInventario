from datetime import datetime, time, timedelta, timezone
from typing import Dict, List
from zoneinfo import ZoneInfo
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy import case, desc, func
from sqlalchemy.orm import Session, joinedload, aliased
from core.dependencies import get_current_user
from core.limpiar_base_de_datos import limpiar_base_de_datos
from core.load_file_inventory import importar_excel_inventario
from db.database import SessionLocal
from models.inventory import Inventory
from models.item import Item
from models.item_movement import ItemMovement
from models.sale import Sale
from models.user import User
from schemas.inventory import InventoryBulkCreate, InventoryCreate, InventoryOut

router = APIRouter(prefix="/inventory", tags=["Inventory"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/", response_model=InventoryOut)
def create_inventory(entry: InventoryCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    db_entry = Inventory(**entry.dict())
    db.add(db_entry)
    db.commit()
    db.refresh(db_entry)
    return db_entry

@router.post("/bulk", response_model=list[InventoryOut])
def create_inventories_bulk(
    bulk_data: InventoryBulkCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    created_items = []
    try:
        for entry in bulk_data.items:
            db_entry = Inventory(**entry.dict())
            db.add(db_entry)
            created_items.append(db_entry)
        db.commit()
        for item in created_items:
            db.refresh(item)
        return created_items
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Error al guardar inventario: {str(e)}")


@router.get("/", response_model=list[InventoryOut])
def get_inventory(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.query(Inventory).options(joinedload(Inventory.item)).all()

from sqlalchemy.orm import aliased

@router.get("/grouped/{warehouse_id}")
def get_inventory_grouped_warehouse(
    warehouse_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Subconsulta para obtener el último registro de cada item_id en la bodega
    subquery = (
        db.query(
            Inventory.item_id,
            func.max(Inventory.updated_at).label("max_updated_at")
        )
        .filter(Inventory.warehouse_id == warehouse_id)
        .group_by(Inventory.item_id)
        .subquery()
    )

    LastInventory = aliased(Inventory)

    # Consulta principal optimizada
    results = (
        db.query(
            Inventory.item_id,
            func.sum(Inventory.quantity).label("total_quantity"),
            func.sum(Inventory.quantity * Inventory.purchase_price).label("total_investment"),
            Item.name.label("item_name"),
            LastInventory.sale_price.label("last_sale_price"),
            LastInventory.purchase_price.label("last_purchase_price")
        )
        .join(Item, Item.id == Inventory.item_id)
        .join(subquery,
              (Inventory.item_id == subquery.c.item_id) &
              (Inventory.updated_at == subquery.c.max_updated_at))
        .join(LastInventory,
              (LastInventory.item_id == subquery.c.item_id) &
              (LastInventory.updated_at == subquery.c.max_updated_at))
        .filter(Inventory.warehouse_id == warehouse_id)
        .group_by(
            Inventory.item_id,
            Item.name,
            LastInventory.sale_price,
            LastInventory.purchase_price
        )
        .having(func.sum(Inventory.quantity) > 0)
        .all()
    )

    # Armar la respuesta
    summary = [
        {
            "item_id": r.item_id,
            "item_name": r.item_name,
            "total_quantity": r.total_quantity,
            "total_investment": r.total_investment,
            "last_sale_price": r.last_sale_price,
            "last_purchase_price": r.last_purchase_price,
        }
        for r in results
    ]

    return summary



@router.get("/grouped")
def get_inventory_grouped(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    results = (
        db.query(
            Inventory.item_id,
            Inventory.warehouse_id,
            func.sum(Inventory.quantity).label("total_quantity"),
            func.sum(Inventory.quantity * Inventory.purchase_price).label("total_investment"),
            Inventory.id
        )
        .group_by(Inventory.item_id, Inventory.warehouse_id)
        .all()
    )

    summary = []
    for item_id, warehouse_id, total_quantity, total_investment, inventory_id in results:
        item = db.query(Item).get(item_id)
        if (total_quantity == 0):
            continue
        
        summary.append({
            "item_id": item_id,
            "item_name": item.name if item else None,
            "warehouse_id": warehouse_id,
            "total_quantity": total_quantity,
            "total_investment": total_investment,
            "category_id": item.category_id,
            "inventory_id": inventory_id
        })

    return summary

@router.get("/summary")
def get_inventory_summary(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    inventories = db.query(Inventory).all()

    total_quantity = sum(inv.quantity for inv in inventories)
    total_investment = sum(inv.quantity * inv.purchase_price for inv in inventories)

    salesNoPaid = db.query(Sale).filter(Sale.paid == False).all()
    total_debt = sum(sale.quantity * sale.sale_price for sale in salesNoPaid)

    # Filtrar un rango de 2 semanas
    salesPaid = db.query(Sale).filter(Sale.paid == True).filter(Sale.created_at >= datetime.now() - timedelta(days=14)).all()
    total_paid = sum(sale.quantity * sale.sale_price for sale in salesPaid)

    return {
        "total_items": total_quantity,
        "total_investment": round(total_investment, 2),
        "total_debt": round(total_debt, 2)
    }

@router.get("/summary_sales")
def get_summary_sales(
    db: Session = Depends(get_db),
    dateStart: datetime = datetime.now() - timedelta(days=29),
    dateEnd: datetime = datetime.now(),
    current_user: User = Depends(get_current_user)
):
    # Asumimos que dateStart y dateEnd vienen en zona local (America/Managua)
    zona_local = ZoneInfo("America/Managua")

    start_local = datetime.combine(dateStart.date(), time.min, tzinfo=zona_local)
    end_local = datetime.combine(dateEnd.date(), time.max, tzinfo=zona_local)

    # Convertir a UTC para filtrar en base de datos
    start_utc = start_local.astimezone(timezone.utc)
    end_utc = end_local.astimezone(timezone.utc)

    salesPaid = (
        db.query(Sale)
        .join(Item)
        .filter(Sale.paid == True)
        .filter(func.date(Sale.created_at) >= start_utc.date())
        .filter(func.date(Sale.created_at) <= end_utc.date())
        .all()
    )

    total_paid = 0.0
    total_profit = 0.0

    for sale in salesPaid:
        total_paid += sale.quantity * sale.sale_price

        # Buscar el último precio de compra (entrada más reciente antes o igual a la venta)
        last_movement = (
            db.query(ItemMovement)
            .filter(ItemMovement.item_id == sale.item_id)
            .filter(ItemMovement.type == 'entrada')
            .filter(ItemMovement.timestamp <= sale.created_at)
            .order_by(desc(ItemMovement.timestamp))
            .first()
        )

        if last_movement:
            purchase_price = last_movement.purchase_price
            profit = sale.quantity * (sale.sale_price - purchase_price)
            total_profit += profit
        else:
            # No hay costo conocido, no sumamos ganancia
            continue

    return {
        "total_paid": round(total_paid, 2),
        "total_profit": round(total_profit, 2)
    }


@router.get("/summary_sales_by_day")
def get_summary_sales_by_day(
    db: Session = Depends(get_db),
    dateStart: datetime = datetime.now() - timedelta(days=29),
    dateEnd: datetime = datetime.now(),
    current_user: User = Depends(get_current_user)
) -> List[Dict]:
    zona_local = ZoneInfo("America/Managua")

    # Asegurar zona horaria
    if dateStart.tzinfo is None:
        dateStart = dateStart.replace(tzinfo=zona_local)
    if dateEnd.tzinfo is None:
        dateEnd = dateEnd.replace(tzinfo=zona_local)

    start_local = datetime.combine(dateStart.date(), time.min, tzinfo=zona_local)
    end_local = datetime.combine(dateEnd.date(), time.max, tzinfo=zona_local)

    # Convertir a UTC
    start_utc = start_local.astimezone(timezone.utc)
    end_utc = end_local.astimezone(timezone.utc)

    # Traer ventas dentro del rango
    sales = (
        db.query(Sale)
        .filter(Sale.created_at >= start_utc)
        .filter(Sale.created_at <= end_utc)
        .all()
    )

    # Traer últimos movimientos de entrada por item_id antes del end_utc
    movimientos = (
        db.query(ItemMovement)
        .filter(ItemMovement.type == "entrada")
        .filter(ItemMovement.timestamp <= end_utc)
        .order_by(ItemMovement.item_id, desc(ItemMovement.timestamp))
        .all()
    )

    movimientos_por_item = {}
    for mov in movimientos:
        if mov.item_id not in movimientos_por_item:
            movimientos_por_item[mov.item_id] = mov  # último movimiento por item

    # Construir resumen diario
    resumen_diario: Dict[str, Dict] = {}

    for sale in sales:
        created_at_local = sale.created_at.astimezone(zona_local)
        fecha_str = created_at_local.date().isoformat()

        if fecha_str not in resumen_diario:
            resumen_diario[fecha_str] = {
                "fecha": created_at_local.strftime("%d/%m/%Y"),
                "ventas": 0.0,
                "ganancias": 0.0,
                "fiados": 0.0,
            }

        monto_venta = sale.quantity * sale.sale_price
        resumen_diario[fecha_str]["ventas"] += monto_venta

        if sale.paid:
            last_mov = movimientos_por_item.get(sale.item_id)
            if last_mov:
                compra = last_mov.purchase_price
                ganancia = sale.quantity * (sale.sale_price - compra)
                resumen_diario[fecha_str]["ganancias"] += ganancia
        else:
            resumen_diario[fecha_str]["fiados"] += monto_venta

    # Convertir dict a lista ordenada por fecha ascendente
    resultado = [resumen_diario[fecha] for fecha in sorted(resumen_diario)]

    return resultado

@router.get("/warehouse/{warehouse_id}", response_model=list[InventoryOut])
def get_inventory_warehouse_id(warehouse_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    entries = db.query(Inventory).filter(Inventory.warehouse_id == warehouse_id).all()
    return entries








def rebuild_inventory_table(db: Session):
    # 1. Obtener la cantidad neta por item y bodega
    movement_sums = db.query(
        case(
            (ItemMovement.source_warehouse_id != None, ItemMovement.source_warehouse_id),
            else_=ItemMovement.target_warehouse_id
        ).label("warehouse_id"),
        ItemMovement.item_id,
        func.sum(
            case(
                (ItemMovement.source_warehouse_id != None, -ItemMovement.quantity),
                else_=ItemMovement.quantity
            )
        ).label("net_quantity")
    ).group_by("warehouse_id", ItemMovement.item_id).all()

    # 2. Obtener el último movimiento de entrada por (item_id, target_warehouse_id)
    sub_last_entry = (
        db.query(
            ItemMovement.item_id,
            ItemMovement.target_warehouse_id.label("warehouse_id"),
            func.max(ItemMovement.timestamp).label("max_date")
        )
        .filter(ItemMovement.target_warehouse_id != None)
        .group_by(ItemMovement.item_id, ItemMovement.target_warehouse_id)
    ).subquery()

    IM = aliased(ItemMovement)

    latest_entries = db.query(
        IM.item_id,
        IM.target_warehouse_id.label("warehouse_id"),
        IM.purchase_price,
        IM.sale_price
    ).join(
        sub_last_entry,
        (IM.item_id == sub_last_entry.c.item_id) &
        (IM.target_warehouse_id == sub_last_entry.c.warehouse_id) &
        (IM.timestamp == sub_last_entry.c.max_date)
    ).all()

    # 3. Armar diccionario de precios
    prices = {
        (x.item_id, x.warehouse_id): {
            "purchase_price": x.purchase_price or 0.0,
            "sale_price": x.sale_price or 0.0
        }
        for x in latest_entries
    }

    # 4. Actualizar o crear registros en Inventory
    for record in movement_sums:
        item_id = record.item_id
        warehouse_id = record.warehouse_id
        quantity = record.net_quantity or 0

        price_data = prices.get((item_id, warehouse_id), {"purchase_price": 0.0, "sale_price": 0.0})
        purchase_price = price_data["purchase_price"]
        sale_price = price_data["sale_price"]

        existing = db.query(Inventory).filter_by(
            item_id=item_id,
            warehouse_id=warehouse_id
        ).first()

        if existing:
            existing.quantity = quantity
            existing.purchase_price = purchase_price
            existing.sale_price = sale_price
            existing.updated_at = datetime.utcnow()
        else:
            db.add(Inventory(
                item_id=item_id,
                warehouse_id=warehouse_id,
                quantity=quantity,
                purchase_price=purchase_price,
                sale_price=sale_price,
                updated_at=datetime.utcnow()
            ))

    db.commit()
    return {"status": "Inventory table rebuilt successfully"}


@router.post("/rebuild-inventory")
def rebuild_inventory(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return rebuild_inventory_table(db)

@router.post("/load-file")
def load_file_inventory(file: UploadFile = File(...), warehouse_id: int = None, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return importar_excel_inventario(file.file, db, warehouse_id, current_user.id)

@router.delete("/reset-inventory")
def reset_inventory(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return limpiar_base_de_datos()    

@router.get("/{inventory_id}", response_model=InventoryOut)
def get_inventory_entry(inventory_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    entry = db.query(Inventory).get(inventory_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Inventory entry not found")
    return entry

@router.put("/{inventory_id}", response_model=InventoryOut)
def update_inventory(inventory_id: int, data: InventoryCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    entry = db.query(Inventory).get(inventory_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Inventory entry not found")
    for key, value in data.dict().items():
        setattr(entry, key, value)
    db.commit()
    db.refresh(entry)
    return entry

@router.delete("/{inventory_id}")
def delete_inventory(inventory_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    entry = db.query(Inventory).get(inventory_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Inventory entry not found")
    db.delete(entry)
    db.commit()
    return {"ok": True}