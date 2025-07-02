from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import case, func
from sqlalchemy.orm import Session
from db.database import SessionLocal
from models.sale import Sale
from models.sale_group import SaleGroup
from schemas.sale_group import SaleGroupCreate, SaleGroupOut, SaleGroupWithSummary
from core.dependencies import get_current_user
from models.user import User

router = APIRouter(prefix="/sale-groups", tags=["Sale Groups"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()



@router.get("/sumaryDebt", response_model=list[SaleGroupWithSummary])
def get_sale_groups_with_total_items(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # La subconsulta ya está bien, calcula los 3 valores que necesitamos.
    sale_totals = (
        db.query(
            Sale.sale_group_id,
            func.sum(Sale.quantity).label("total_items"),
            func.sum(Sale.quantity * Sale.sale_price).label("total_sale_price"),
            func.sum(
                case(
                    (Sale.paid == False, Sale.quantity * Sale.sale_price),
                    else_=0
                )
            ).label("total_debt")
        )
        .group_by(Sale.sale_group_id)
        .subquery()
    )

    # --- Consulta principal CORREGIDA ---
    # Ahora selecciona los 3 totales de la subconsulta.
    results = (
        db.query(
            SaleGroup,
            func.coalesce(sale_totals.c.total_items, 0).label("total_items"),
            # CAMBIO: Añadido para seleccionar el total_sale_price
            func.coalesce(sale_totals.c.total_sale_price, 0.0).label("total_sale_price"),
            # CAMBIO: Añadido para seleccionar el total_debt
            func.coalesce(sale_totals.c.total_debt, 0.0).label("total_debt")
        )
        .outerjoin(sale_totals, SaleGroup.id == sale_totals.c.sale_group_id)
        .filter(sale_totals.c.total_debt > 0)
        .all()
    )

    # --- Bucle de construcción CORREGIDO ---
    # Ahora desempaqueta los 4 valores de la tupla y los pasa al modelo.
    return [
        SaleGroupWithSummary(
            id=group.id,
            warehouse_id=group.warehouse_id,
            note=group.note,
            user_id=group.user_id,
            created_at=group.created_at,
            total_items=total_items,
            # CAMBIO: Se pasa el total_sale_price al constructor
            total_sale_price=total_sale_price,
            # CAMBIO: Se pasa el total_debt al constructor
            total_debt=total_debt
        )
        # CAMBIO: El bucle ahora desempaqueta 4 variables por cada fila del resultado
        for group, total_items, total_sale_price, total_debt in results
    ]


@router.get("/summary/{warehouse_id}", response_model=list[SaleGroupWithSummary])
def get_sale_groups_with_total_items(
    warehouse_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)

):
    sale_totals = (
        db.query(
            Sale.sale_group_id,
            func.sum(Sale.quantity).label("total_items"),
            func.sum(Sale.quantity * Sale.sale_price).label("total_sale_price"),

            func.sum(
                case(
                    (Sale.paid == False, Sale.quantity * Sale.sale_price),
                    else_=0
                )
            ).label("total_debt")
        )
        .group_by(Sale.sale_group_id)
        .subquery()
    )

    # Consulta principal: trae SaleGroup + total_items
    results = (
        db.query(
            SaleGroup,
            func.coalesce(sale_totals.c.total_items, 0).label("total_items")
        )
        .outerjoin(sale_totals, SaleGroup.id == sale_totals.c.sale_group_id)
        .filter(SaleGroup.warehouse_id == warehouse_id)
        .all()
    )

    return [
        SaleGroupWithSummary(
            id=group.id,
            warehouse_id=group.warehouse_id,
            note=group.note,
            user_id=group.user_id,
            created_at=group.created_at,
            total_items=total_items
        )

        for group, total_items in results
    ]



@router.get("/summaryGroup/{group_item_id}", response_model=SaleGroupWithSummary)
def get_sale_groups_with_total_items(
    group_item_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    sale_totals = (
        db.query(
            Sale.sale_group_id,
            func.sum(Sale.quantity).label("total_items"),
            func.sum(Sale.quantity * Sale.sale_price).label("total_sale_price"),
            
            func.sum(
                case(
                    (Sale.paid == False, Sale.quantity * Sale.sale_price),
                    else_=0
                )
            ).label("total_debt")

        )
        .group_by(Sale.sale_group_id)
        .subquery()
    )

    result = (
        db.query(
            SaleGroup,
            func.coalesce(sale_totals.c.total_items, 0).label("total_items"),
            func.coalesce(sale_totals.c.total_sale_price, 0.0).label("total_sale_price"),
            func.coalesce(sale_totals.c.total_debt, 0.0).label("total_debt") # <-- Seleccionar la deuda
        )
        .outerjoin(sale_totals, SaleGroup.id == sale_totals.c.sale_group_id)
        .filter(SaleGroup.id == group_item_id)
        .first() 
    )

    
    # Desempaquetamos la tupla con los 4 valores del resultado
    group, total_items, total_sale_price, total_debt = result
    
    # Construimos y retornamos el objeto de respuesta Pydantic
    return SaleGroupWithSummary(
        id=group.id,
        warehouse_id=group.warehouse_id,
        note=group.note,
        user_id=group.user_id,
        created_at=group.created_at,
        total_items=total_items,
        total_sale_price=total_sale_price,
        total_debt=total_debt # <-- Se pasa el nuevo campo de deuda
    )

@router.get("/{warehouse_id}", response_model=list[SaleGroupOut])
def get_sale_groups(
    warehouse_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return db.query(SaleGroup).filter(SaleGroup.warehouse_id == warehouse_id).all()


@router.post("/", response_model=SaleGroupOut)
def create_sale_group(
    group: SaleGroupCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    db_group = SaleGroup(
        note=group.note,
        user_id=current_user.id,
        warehouse_id=group.warehouse_id
    )
    db.add(db_group)
    db.commit()
    db.refresh(db_group)
    return db_group
