import logging
from django.core.management import call_command

logger = logging.getLogger("tax_registration.etl")


def run_tax_import():
    logger.info("開始執行定時 ETL 任務...")
    try:
        call_command("load_tax_registration", truncate=True, auto=True)
        logger.info("定時 ETL 任務執行成功！")
        return "Success"
    except Exception as e:
        logger.error(f"定時 ETL 任務失敗: {str(e)}")
        raise e


# For testing dry run scheduler
def run_tax_import_dry_run():
    logger.info("開始執行定時 ETL DRY RUN 任務...")
    try:
        call_command("load_tax_registration", limit=10000, dry_run=True)
        logger.info("定時 ETL DRY RUN 任務執行成功！")
        return "Success"
    except Exception as e:
        logger.error(f"定時 ETL DRY RUN 任務失敗: {str(e)}")
        raise e
