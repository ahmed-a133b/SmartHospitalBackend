from fastapi import APIRouter

router = APIRouter(prefix="/staff", tags=["Staff"])

@router.get("/load")
def get_staff_load():
    
    return {"ER": 0.75, "ICU": 0.9}
