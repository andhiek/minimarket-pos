from fastapi import APIRouter

router = APIRouter(prefix="/api/settings", tags=["Settings"])

@router.get("")
def get_settings():
    return {
        "store_name": "Minimarket POS",
        "receipt_footer": "Terima Kasih Telah Berbelanja!"
    }