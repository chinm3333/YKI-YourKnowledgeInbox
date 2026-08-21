from fastapi import APIRouter, Response
from schemas import ItemListResponse
from services import store
from services.errors import AppError
from services.vector import delete_chunks
router = APIRouter()

@router.get("/items", response_model=ItemListResponse)
def list_items() -> ItemListResponse:
    return ItemListResponse(items=store.list_items())

@router.delete("/items/{item_id}", status_code=204)
def delete_item(item_id: str) -> Response:
    if not store.item_exists(item_id):
        raise AppError("Item not found", status_code=404, code="not_found")
    delete_chunks(item_id)
    store.delete_item(item_id)
    return Response(status_code=204)