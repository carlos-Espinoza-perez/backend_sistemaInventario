from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from db.database import SessionLocal
from models.item import Item
from models.item_movement import ItemMovement
from models.sale import Sale
from schemas.sale import SaleCreate, SaleOut
from core.dependencies import get_current_user
from models.user import User

router = APIRouter(prefix="/sales", tags=["Sales"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/bulk", response_model=List[SaleOut])
def create_sales_bulk(
    sales: List[SaleCreate],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    db_sales = []
    db_movements = []

    for sale in sales:
        db_sale = Sale(
            **sale.dict(),
            user_id=current_user.id
        )
        db.add(db_sale)
        db_sales.append(db_sale)

        # Crear un movimiento de salida
        db_movement = ItemMovement(
            item_id=sale.item_id,
            source_warehouse_id=sale.warehouse_id,
            quantity=sale.quantity,
            type="salida",
        )
        db.add(db_movement)
        db_movements.append(db_movement)
    
    db.commit()

    # Refrescar ventas
    for sale in db_sales:
        db.refresh(sale)

    # Refrescar movimientos
    for movement in db_movements:
        db.refresh(movement)

    return db_sales

@router.post("/", response_model=SaleOut)
def create_sale(
    sale: SaleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    db_sale = Sale(
        **sale.dict(),
        user_id=current_user.id  # Se guarda automáticamente el usuario que está logueado
    )
    db.add(db_sale)
    db.commit()
    db.refresh(db_sale)
    return db_sale


@router.get("/{sale_group_id}", response_model=list[SaleOut])
def get_sales(
    sale_group_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Obtiene las ventas de un grupo, añadiendo el nombre del item de forma plana.
    """
    # 1. Hacemos un JOIN para tener acceso tanto al objeto Sale como al Item.
    #    La consulta devuelve una lista de tuplas: [(sale1, item1), (sale2, item2), ...]
    results = (
        db.query(Sale, Item)
        .join(Item, Sale.item_id == Item.id)
        .filter(Sale.sale_group_id == sale_group_id)
        .all()
    )

    # 2. Construimos la lista de respuesta manualmente.
    #    Usaremos una "list comprehension" por ser más conciso y eficiente.
    response = [
        SaleOut(
            # Mapeamos todos los campos del objeto 'sale'
            id=sale.id,
            item_id=sale.item_id,
            warehouse_id=sale.warehouse_id,
            user_id=sale.user_id,
            quantity=sale.quantity,
            sale_price=sale.sale_price,
            paid=sale.paid,
            note=sale.note,
            sold_at=sale.sold_at,
            created_at=sale.created_at,
            sale_group_id=sale.sale_group_id,
            
            # Y añadimos el campo del objeto 'item'
            item_name=item.name
        )
        for sale, item in results
    ]
    
    return response

@router.patch("/{sale_id}/paid", response_model=SaleOut)
def update_sale_paid_status(
    sale_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Actualiza el estado de 'paid' (pagado) de una venta específica.
    """
    # 1. Buscar la venta en la base de datos por su ID.
    sale_to_update = db.query(Sale).filter(Sale.id == sale_id).first()

    # (Opcional pero recomendado) Aquí podrías añadir una comprobación de permisos.
    # Por ejemplo, que solo un admin o el usuario que creó la venta pueda modificarla.
    # if sale_to_update.user_id != current_user.id and not current_user.is_admin:
    #     raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No tienes permiso para esta acción.")

    # 3. Actualizar el campo 'paid' con el valor del payload.
    sale_to_update.paid = True

    # 4. Guardar los cambios en la base de datos.
    db.commit()

    # 5. Refrescar el objeto para obtener el estado actualizado desde la BD.
    db.refresh(sale_to_update)

    # 6. Devolver el objeto de venta actualizado.
    # Nota: Para que esto funcione, el response_model (SaleOut) debe estar
    # configurado para cargar las relaciones (item, user, etc.) o la consulta
    # debe incluir 'joinedload' si el modelo lo requiere.
    # En este caso simple, lo retornamos y FastAPI lo serializará.
    return sale_to_update