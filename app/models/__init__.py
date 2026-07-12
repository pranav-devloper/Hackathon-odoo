from app.models.role import Role
from app.models.user import User
from app.models.otp import OTP
from app.models.refresh_token import RefreshToken
from app.models.department import Department
from app.models.asset_category import AssetCategory
from app.models.asset import Asset
from app.models.allocation import Allocation
from app.models.maintenance_ticket import MaintenanceTicket
from app.models.transfer import Transfer
from app.models.notification import Notification

__all__ = [
    "Role", "User", "OTP", "RefreshToken",
    "Department", "AssetCategory", "Asset", "Allocation", "MaintenanceTicket",
    "Transfer", "Notification",
]
