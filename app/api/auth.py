from fastapi import Security, HTTPException, status
from fastapi.security import APIKeyHeader
from app.core.config import settings

api_key_header = APIKeyHeader(name="X-Thola-API-Key", auto_error=False)

async def get_api_key(api_key_header: str = Security(api_key_header)):
    if not api_key_header:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="API Key is missing"
        )
    if api_key_header != settings.THOLA_INTERNAL_KEY:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Could not validate API Key"
        )
    return api_key_header
