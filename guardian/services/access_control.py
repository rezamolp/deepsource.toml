import logging

logger = logging.getLogger(__name__)

class AccessControl:
    def __init__(self):
        self.admins = set()

    def add_admin(self, admin_id):
        if admin_id in self.admins:
            logger.info(f"⚠️ تلاش برای افزودن ادمین تکراری: {admin_id}")
            return False
        self.admins.add(admin_id)
        logger.info(f"✅ ادمین جدید اضافه شد: {admin_id}")
        return True


import logging
logger = logging.getLogger(__name__)

def add_admin(admins: set[int], admin_id: int) -> str:
    if admin_id in admins:
        logger.info("duplicate_admin", extra={"user_id": admin_id})
        return "این ادمین قبلاً اضافه شده است."
    admins.add(admin_id)
    return "ادمین جدید با موفقیت افزوده شد."
