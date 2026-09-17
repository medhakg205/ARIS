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

import os
import json
import glob
import urllib.parse

router = APIRouter(tags=["Firmware"])


class FirmwareUploadRequest(BaseModel):
    """Payload for uploading new firmware artifacts."""
    name: str = Field(..., description="Project name")
    source_code: Optional[str] = None
    hex_content: Optional[str] = None
    elf_path: Optional[str] = None
    map_content: Optional[str] = None


class SaveIDESketchRequest(BaseModel):
    path: str = Field(..., description="Absolute path to the .ino file to overwrite")
    source_code: str = Field(..., description="Optimized source code")


def _discover_arduino_ide_sketches() -> List[Dict[str, Any]]:
    """Helper to detect recent sketches from Arduino IDE 2.x and standard sketchbooks."""
    results = []
    seen_paths = set()

    # 1. Check Arduino IDE 2.x recent-sketches.json
    recent_file = os.path.expanduser('~/.arduinoIDE/recent-sketches.json')
    if os.path.exists(recent_file):
        try:
            with open(recent_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            sorted_items = sorted(data.items(), key=lambda x: x[1], reverse=True)
            for uri, ts in sorted_items:
                clean_path = urllib.parse.unquote(uri.replace('file:///', ''))
                clean_path = os.path.normpath(clean_path)
                if os.path.exists(clean_path):
                    if os.path.isdir(clean_path):
                        for ino in glob.glob(os.path.join(clean_path, '*.ino')):
                            ino_norm = os.path.normpath(ino)
                            if ino_norm not in seen_paths:
                                seen_paths.add(ino_norm)
                                results.append({
                                    'name': os.path.basename(ino_norm),
                                    'path': ino_norm,
                                    'last_modified': ts / 1000 if ts > 1e11 else ts
                                })
                    elif clean_path.endswith('.ino') and clean_path not in seen_paths:
                        seen_paths.add(clean_path)
                        results.append({
                            'name': os.path.basename(clean_path),
                            'path': clean_path,
                            'last_modified': ts / 1000 if ts > 1e11 else ts
                        })
        except Exception:
            pass

    # 2. Check standard Arduino sketchbook folders
    sketchbook_dirs = [
        os.path.expanduser('~/OneDrive/Documents/Arduino'),
        os.path.expanduser('~/Documents/Arduino'),
    ]
    for sb in sketchbook_dirs:
        if os.path.exists(sb):
            for ino in glob.glob(os.path.join(sb, '**', '*.ino'), recursive=True):
                ino_norm = os.path.normpath(ino)
                if ino_norm not in seen_paths:
                    seen_paths.add(ino_norm)
                    results.append({
                        'name': os.path.basename(ino_norm),
                        'path': ino_norm,
                        'last_modified': os.path.getmtime(ino_norm)
                    })

    results.sort(key=lambda x: x['last_modified'], reverse=True)
    return results


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


@router.get("/api/firmware/ide-recent")
def get_recent_ide_sketches() -> Dict[str, Any]:
    """
    Auto-discovers sketches compiled or opened in the Arduino IDE.
    Returns the list and automatically reads the source code of the most recent sketch.
    """
    sketches = _discover_arduino_ide_sketches()
    if not sketches:
        return {"found": False, "sketches": [], "active_sketch": None}

    latest = sketches[0]
    source = ""
    try:
        with open(latest["path"], "r", encoding="utf-8", errors="replace") as f:
            source = f.read()
    except Exception:
        pass

    latest_with_code = {
        **latest,
        "source_code": source
    }

    return {
        "found": True,
        "sketches": sketches[:10],
        "active_sketch": latest_with_code
    }


@router.post("/api/firmware/sync-ide")
def sync_ide_sketch(req: Dict[str, Any]) -> Dict[str, Any]:
    """
    Takes an Arduino IDE sketch path, reads it, and registers it into ARIS firmware manager.
    """
    import os
    path = req.get("path")
    if not path or not os.path.exists(path):
        # Fallback to latest
        sketches = _discover_arduino_ide_sketches()
        if not sketches:
            return {"success": False, "error": "No Arduino sketches found on machine"}
        path = sketches[0]["path"]

    name = os.path.basename(path)
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        source = f.read()

    mgr = get_firmware_mgr()
    fw = mgr.upload_firmware(name=name, source_code=source)
    return {
        "success": True,
        "firmware": fw.model_dump(),
        "path": path,
        "source_code": source,
        "name": name
    }


@router.post("/api/firmware/save-ide")
def save_ide_sketch(req: SaveIDESketchRequest) -> Dict[str, Any]:
    """
    Overwrites the specified .ino file on disk with optimized code (creating a .bak backup).
    Allows user to immediately re-flash in Arduino IDE with zero copy-pasting.
    """
    import os
    if not os.path.exists(req.path):
        return {"success": False, "error": f"File does not exist: {req.path}"}

    try:
        # Create backup
        bak_path = f"{req.path}.bak"
        with open(req.path, "r", encoding="utf-8") as orig:
            original_code = orig.read()
        with open(bak_path, "w", encoding="utf-8") as bak:
            bak.write(original_code)

        # Write optimized code
        with open(req.path, "w", encoding="utf-8") as f:
            f.write(req.source_code)

        return {"success": True, "path": req.path, "backup_path": bak_path}
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.get("/api/firmware/{firmware_id}")
def get_firmware_detail(firmware_id: str) -> Dict[str, Any]:
    """Retrieves specific firmware details and normalized memory sections."""
    mgr = get_firmware_mgr()
    fw = mgr.get_firmware(firmware_id)
    return fw.model_dump()

