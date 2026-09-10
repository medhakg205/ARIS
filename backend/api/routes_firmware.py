"""
ARIS Firmware Upload & Management REST API Routes.
Endpoints:
- POST /api/firmware/upload
- GET /api/firmware
- GET /api/firmware/{firmware_id}
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from fastapi import APIRouter

from backend.api.dependencies import get_firmware_mgr
from backend.database.models import FirmwareRecord

router = APIRouter(tags=["Firmware"])


class FirmwareUploadRequest(BaseModel):
    """Payload for uploading new firmware artifacts."""
    name: str = Field(..., description="Project name")
    source_code: Optional[str] = None
    hex_content: Optional[str] = None
    elf_path: Optional[str] = None
    map_content: Optional[str] = None


@router.post("/api/firmware/upload")
def upload_firmware(req: FirmwareUploadRequest) -> Dict[str, Any]:
    """
    Uploads firmware artifacts (source, hex, elf, or map).
    Returns created FirmwareRecord.
    """
    mgr = get_firmware_mgr()
    record = mgr.upload_firmware(
        name=req.name,
        source_code=req.source_code,
        hex_content=req.hex_content,
        elf_path=req.elf_path,
        map_content=req.map_content
    )
    return record.model_dump()


@router.get("/api/firmware")
def list_all_firmware() -> List[Dict[str, Any]]:
    """Lists all stored firmware bundles."""
    mgr = get_firmware_mgr()
    return [fw.model_dump() for fw in mgr.list_firmwares()]


@router.get("/api/firmware/{firmware_id}")
def get_firmware_detail(firmware_id: str) -> Dict[str, Any]:
    """Retrieves specific firmware details and normalized memory sections."""
    mgr = get_firmware_mgr()
    fw = mgr.get_firmware(firmware_id)
    return fw.model_dump()
