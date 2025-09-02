from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session
from db.database import SessionLocal
from models.item_movement import ItemMovement
from models.item_movement_group import ItemMovementGroup
from models.sale_group import SaleGroup
from schemas.item_movement_group import ItemMovementGroupCreate, ItemMovementGroupOut, ItemMovementGroupWithSummary
from schemas.sale_group import SaleGroupCreate, SaleGroupOut
from core.dependencies import get_current_user
from models.user import User

from datetime import timezone
from zoneinfo import ZoneInfo

router = APIRouter(prefix="/item-movement-groups", tags=["Item Movement Groups"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()




@router.get("/summary/{warehouse_id}", response_model=list[ItemMovementGroupWithSummary])
def get_item_movement_groups_with_total_items(
    warehouse_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    movement_totals = (
        db.query(
            ItemMovement.item_movement_group_id,
            func.sum(ItemMovement.quantity).label("total_items")
        )
        .group_by(ItemMovement.item_movement_group_id)
        .subquery()
    )

    results = (
        db.query(
            ItemMovementGroup,
            func.coalesce(movement_totals.c.total_items, 0).label("total_items")
        )
        .outerjoin(movement_totals, ItemMovementGroup.id == movement_totals.c.item_movement_group_id)
        .filter(ItemMovementGroup.warehouse_id == warehouse_id)
        .all()
    )

    zona_local = ZoneInfo("America/Managua")

    return [
        ItemMovementGroupWithSummary(
            id=group.id,
            warehouse_id=group.warehouse_id,
            note=group.note,
            user_id=group.user_id,
            created_at=group.created_at.replace(tzinfo=timezone.utc).astimezone(zona_local),
            total_items=total_items,
        )
        for group, total_items in results
    ]

@router.get("/{warehouse_id}", response_model=list[ItemMovementGroupOut])
def get_item_movement_groups(
    warehouse_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return db.query(ItemMovementGroup).filter(ItemMovementGroup.warehouse_id == warehouse_id).all()


@router.get(
    "/group/{item_movement_group_id}", 
    response_model=ItemMovementGroupWithSummary,
    # Se pueden agregar respuestas de error para la documentación de Swagger/OpenAPI
    responses={404: {"description": "Item Movement Group not found"}}
)
def get_item_movement_group_by_id(
    item_movement_group_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Obtiene un único grupo de movimiento por su ID, con un resumen de la
    cantidad total de artículos, el costo total de compra y el costo total de venta.
    """
    # La subconsulta para calcular los totales es exactamente la misma.
    # Es eficiente porque la base de datos la optimizará en el join.
    movement_totals = (
        db.query(
            ItemMovement.item_movement_group_id,
            func.sum(ItemMovement.quantity).label("total_items"),
            func.sum(ItemMovement.purchase_price * ItemMovement.quantity).label("total_purchase_price"),
            func.sum(ItemMovement.sale_price * ItemMovement.quantity).label("total_sale_price")
        )
        .group_by(ItemMovement.item_movement_group_id)
        .subquery()
    )

    # --- Consulta principal modificada para un solo ID ---
    result = (
        db.query(
            ItemMovementGroup,
            func.coalesce(movement_totals.c.total_items, 0).label("total_items"),
            func.coalesce(movement_totals.c.total_purchase_price, 0.0).label("total_purchase_price"),
            func.coalesce(movement_totals.c.total_sale_price, 0.0).label("total_sale_price")
        )
        .outerjoin(movement_totals, ItemMovementGroup.id == movement_totals.c.item_movement_group_id)
        # Cambio clave: Filtrar por el ID del grupo en lugar del warehouse_id
        .filter(ItemMovementGroup.id == item_movement_group_id)
        # Cambio clave: Usar .first() en lugar de .all() porque esperamos un único resultado
        .first()
    )

    # Desempaquetamos la tupla del resultado
    group, total_items, total_purchase, total_sale = result
    
    # Creamos y retornamos el objeto de respuesta Pydantic
    return ItemMovementGroupWithSummary(
        id=group.id,
        warehouse_id=group.warehouse_id,
        note=group.note,
        user_id=group.user_id,
        created_at=group.created_at,
        total_items=total_items,
        total_purchase_price=total_purchase,
        total_sale_price=total_sale
    )

@router.post("/", response_model=ItemMovementGroupOut)
def create_item_movement_group(
    group: ItemMovementGroupCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    db_group = ItemMovementGroup(
        note=group.note,
        user_id=current_user.id,
        warehouse_id=group.warehouse_id
    )
    db.add(db_group)
    db.commit()
    db.refresh(db_group)
    return db_group
