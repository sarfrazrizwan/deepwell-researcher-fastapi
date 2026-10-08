from fastapi import APIRouter

router = APIRouter(prefix="/messages", tags=["messages"])


@router.get("")
async def index():
    
    return {"message" :"hello"}
