from fastapi import (
    APIRouter
)

router = APIRouter(

    prefix="/system",

    tags=["System"]
)


@router.get("/health")
def health():

    return {

        "api": "online",

        "db": "online",

        "ae": "online",

        "lgbm": "online",

        "shap": "online",

        "adwin": "online",

        "rl": "online",

        "pktcap": "online",

        "flow": "online"
    }