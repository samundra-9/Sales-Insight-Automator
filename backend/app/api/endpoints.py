
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, BackgroundTasks, Depends, status
from fastapi.responses import JSONResponse
from typing import Optional
import logging
from pydantic import EmailStr

from app.services.file_processor import process_sales_file
from app.services.ai_summary_service import generate_sales_summary
from app.services.email_service import send_summary_email
from app.models.sales_data import SalesSummary
from app.security.rate_limiter import rate_limit
from app.utils.logger import setup_logging

setup_logging()
logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/upload", tags=["Sales Data"], summary="Upload a sales file for processing")
@rate_limit(max_requests=5, window_seconds=60)
async def upload_file(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    logger.info(f"File upload request received for {file.filename}")
    try:
        df = await process_sales_file(file)
        # Store the dataframe temporarily or process immediately. For this example, we'll just acknowledge processing.
        # In a real-world scenario, you might save it to a database or a temporary file storage linked to a session/user.
        logger.info(f"File {file.filename} processed successfully. Contains {len(df)} rows.")
        return JSONResponse(content={
            "message": "File uploaded and processed successfully",
            "filename": file.filename,
            "rows": len(df)
        }, status_code=status.HTTP_200_OK)
    except HTTPException as e:
        logger.warning(f"File upload failed for {file.filename}: {e.detail}")
        raise e
    except Exception as e:
        logger.error(f"Unexpected error during file upload for {file.filename}: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to process file: {e}")

@router.post("/generate-summary", response_model=SalesSummary, tags=["Sales Data"], summary="Generate an AI-powered sales summary")
@rate_limit(max_requests=5, window_seconds=60)
async def generate_summary(file_path: str = Form(...), client_email: Optional[EmailStr] = Form(None)):
    logger.info(f"Summary generation request received for file: {file_path}")
    try:
        # This is a placeholder. In a real app, file_path would refer to a stored file.
        # For simplicity, we'll assume process_sales_file can re-read or we have the data already.
        # Or, ideally, the file_path is an ID to retrieve the processed DataFrame.
        # For this example, let's assume we have a mock dataframe or a way to get it.
        # In a production app, you would retrieve the dataframe associated with the file_path/session.
        # Since we don't have persistent storage setup here, we will simulate the data.

        # --- Simulation of retrieving processed data ---
        # In a real scenario, retrieve the DataFrame based on file_path or a session ID
        # For now, let's create a dummy DataFrame for demonstration.
        import pandas as pd
        data = {
            'Revenue': [1000, 1500, 2000, 500, 1200, 300, 2500, 800, 1800, 700],
            'Region': ['North', 'South', 'East', 'West', 'North', 'South', 'East', 'West', 'North', 'South'],
            'ProductCategory': ['Electronics', 'Clothing', 'Electronics', 'HomeGoods', 'Clothing', 'Electronics', 'HomeGoods', 'Clothing', 'Electronics', 'HomeGoods'],
            'Cancelled': [False, False, True, False, False, True, False, False, True, False]
        }
        df = pd.DataFrame(data)
        # --- End Simulation ---

        summary = await generate_sales_summary(df)
        logger.info(f"Summary generated successfully for file: {file_path}")
        return summary
    except HTTPException as e:
        logger.warning(f"Summary generation failed for file {file_path}: {e.detail}")
        raise e
    except Exception as e:
        logger.error(f"Unexpected error during summary generation for file {file_path}: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to generate summary: {e}")

@router.post("/send-email", tags=["Sales Data"], summary="Send the generated sales summary via email")
@rate_limit(max_requests=5, window_seconds=60)
async def send_email(recipient_email: EmailStr = Form(...), summary_content: str = Form(...)):
    logger.info(f"Email send request received for {recipient_email}")
    try:
        await send_summary_email(recipient_email, summary_content)
        logger.info(f"Email sent successfully to {recipient_email}")
        return JSONResponse(content={
            "message": "Sales summary email sent successfully!"
        }, status_code=status.HTTP_200_OK)
    except HTTPException as e:
        logger.warning(f"Email send failed for {recipient_email}: {e.detail}")
        raise e
    except Exception as e:
        logger.error(f"Unexpected error during email send to {recipient_email}: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to send email: {e}")
