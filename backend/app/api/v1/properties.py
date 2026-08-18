from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any
from sqlalchemy import text
from ...core.auth import authenticate_request as get_current_user
from ...core.database_pool import db_pool

router = APIRouter()


@router.get("/properties")
async def list_properties(
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """Lists the properties belonging to the authenticated user's tenant.

    Property IDs are only unique per tenant (see the composite primary key on
    the properties table), so the tenant must come from the verified token and
    never from the request.
    """

    tenant_id = getattr(current_user, "tenant_id", None)
    if not tenant_id:
        raise HTTPException(status_code=403, detail="No tenant associated with this user")

    try:
        if not db_pool.session_factory:
            await db_pool.initialize()

        async with db_pool.get_session() as session:
            query = text("""
                SELECT id, name, timezone
                FROM properties
                WHERE tenant_id = :tenant_id
                ORDER BY name
            """)

            result = await session.execute(query, {"tenant_id": tenant_id})
            items = [
                {"id": row.id, "name": row.name, "timezone": row.timezone}
                for row in result.fetchall()
            ]

        return {"items": items, "total": len(items)}

    except Exception as e:
        print(f"Database error listing properties (tenant: {tenant_id}): {e}")
        raise HTTPException(status_code=503, detail="Unable to load properties")
