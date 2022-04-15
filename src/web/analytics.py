"""Analytics web REST API."""


import datetime
import fastapi

import posts
from web import posts as web_posts


router = fastapi.APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("")
def get_analytics(
    date_from: datetime.date | None = fastapi.Query(None),
    date_to: datetime.date | None = fastapi.Query(None),
    catalog: posts.Catalog = fastapi.Depends(web_posts.catalog),
):
    return {"likes": catalog.analytics(date_from, date_to)}
