
import pandas as pd
from fastapi import UploadFile, HTTPException, status
import io
import logging

from app.utils.logger import setup_logging

setup_logging()
logger = logging.getLogger(__name__)

MAX_FILE_SIZE_MB = 10
ALLOWED_FILE_TYPES = [
    "text/csv",
    "application/vnd.ms-excel", # .xls
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" # .xlsx
]

async def process_sales_file(file: UploadFile) -> pd.DataFrame:
    """
    Processes an uploaded sales file (CSV or XLSX), validates it, and returns a pandas DataFrame.
    """
    logger.info(f"Starting to process file: {file.filename} with content type: {file.content_type}")

    # 1. Validate file type
    if file.content_type not in ALLOWED_FILE_TYPES:
        logger.warning(f"Invalid file type uploaded: {file.content_type} for {file.filename}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file type. Only CSV and XLSX files are allowed. Received: {file.content_type}"
        )

    # 2. Read file content and validate size
    content = await file.read()
    if len(content) > MAX_FILE_SIZE_MB * 1024 * 1024:
        logger.warning(f"File size exceeded for {file.filename}. Size: {len(content)} bytes")
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File size exceeds the maximum limit of {MAX_FILE_SIZE_MB}MB."
        )

    # 3. Parse with pandas based on file type
    try:
        if file.content_type == "text/csv":
            df = pd.read_csv(io.BytesIO(content))
            logger.info(f"Successfully read CSV file: {file.filename}")
        else:
            df = pd.read_excel(io.BytesIO(content))
            logger.info(f"Successfully read XLSX file: {file.filename}")
        return df
    except Exception as e:
        logger.error(f"Error parsing file {file.filename}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Could not parse file content. Ensure it's a valid CSV/XLSX. Error: {e}"
        )
