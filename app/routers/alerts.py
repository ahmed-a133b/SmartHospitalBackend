from fastapi import APIRouter
from app.firebase_config import get_ref

router = APIRouter(prefix="/alerts", tags=["Alerts"])

@router.get("/")
def get_current_alerts():
    alerts = get_ref("iotData").get()
    all_alerts = []
    for dev_id, dev in alerts.items():
        dev_alerts = dev.get("alerts", {})
        for aid, alert in dev_alerts.items():
            if not alert["resolved"]:
                all_alerts.append(alert)
    return all_alerts
