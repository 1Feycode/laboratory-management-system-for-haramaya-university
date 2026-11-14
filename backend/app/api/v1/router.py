from fastapi import APIRouter

from app.api.v1.assets import assets_router, categories_router
from app.api.v1.auth import router as auth_router
from app.api.v1.calibrations import router as calibrations_router
from app.api.v1.hierarchy import router as hierarchy_router
from app.api.v1.maintenance import router as maintenance_router
from app.api.v1.reports import router as reports_router
from app.api.v1.transfers import router as transfers_router
from app.api.v1.users import router as users_router

router = APIRouter()
router.include_router(auth_router)
router.include_router(users_router)
router.include_router(hierarchy_router)
router.include_router(assets_router)
router.include_router(categories_router)
router.include_router(transfers_router)
router.include_router(maintenance_router)
router.include_router(calibrations_router)
router.include_router(reports_router)
