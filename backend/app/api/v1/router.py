from fastapi import APIRouter

from app.api.v1.endpoints import auth, bots, exchanges, trades

router = APIRouter()
router.include_router(auth.router, prefix="/auth", tags=["auth"])
router.include_router(bots.router, prefix="/bots", tags=["bots"])
router.include_router(exchanges.router, prefix="/exchanges", tags=["exchanges"])
router.include_router(trades.router, prefix="/trades", tags=["trades"])
