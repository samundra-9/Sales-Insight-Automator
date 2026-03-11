
import os
import logging
import pandas as pd
import google.generativeai as genai
from fastapi import HTTPException, status
from typing import List

from app.models.sales_data import SalesSummary, AISummaryOutput, Anomaly
from app.utils.logger import setup_logging

setup_logging()
logger = logging.getLogger(__name__)

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

async def detect_anomalies(df: pd.DataFrame) -> List[Anomaly]:
    """
    Detects anomalies in the sales DataFrame using simple rule-based methods.
    """
    anomalies = []

    # Anomaly 1: High cancellation rate
    if 'Cancelled' in df.columns and len(df) > 0:
        cancellation_rate = (df['Cancelled'].sum() / len(df)) * 100
        if cancellation_rate > 20: # Threshold for high cancellation rate
            anomalies.append(Anomaly(
                type="High Cancellation Rate",
                description=f"Cancellation rate is {cancellation_rate:.2f}%, which is unusually high.",
                severity="Warning"
            ))

    # Anomaly 2: Significantly low revenue in a region (requires more data for robust detection)
    if 'Revenue' in df.columns and 'Region' in df.columns:
        region_revenue = df.groupby('Region')['Revenue'].sum()
        if len(region_revenue) > 1:
            mean_revenue = region_revenue.mean()
            for region, revenue in region_revenue.items():
                if revenue < mean_revenue * 0.5: # 50% below average revenue
                    anomalies.append(Anomaly(
                        type="Low Regional Revenue",
                        description=f"Revenue in {region} ({revenue:,.2f}) is significantly lower than average.",
                        severity="Warning"
                    ))

    # Anomaly 3: Any negative revenue values (data quality anomaly)
    if 'Revenue' in df.columns and (df['Revenue'] < 0).any():
        anomalies.append(Anomaly(
            type="Negative Revenue Detected",
            description="Found one or more sales records with negative revenue values, indicating potential data quality issues.",
            severity="Critical"
        ))
    
    logger.info(f"Detected {len(anomalies)} anomalies in the sales data.")
    return anomalies

async def generate_sales_summary(df: pd.DataFrame) -> SalesSummary:
    """
    Analyzes sales data, computes key analytics, and uses the Google Gemini API
    to generate a narrative executive sales summary.
    """
    logger.info("Starting sales summary generation with AI.")

    if df.empty:
        logger.warning("Attempted to generate summary from an empty DataFrame.")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No data to analyze.")

    # 1. Compute Analytics
    total_revenue = df['Revenue'].sum() if 'Revenue' in df.columns else 0
    top_region = df['Region'].mode()[0] if 'Region' in df.columns and not df['Region'].empty else "N/A"
    best_product_category = df['ProductCategory'].mode()[0] if 'ProductCategory' in df.columns and not df['ProductCategory'].empty else "N/A"
    cancellation_rate = (df['Cancelled'].sum() / len(df) * 100) if 'Cancelled' in df.columns and len(df) > 0 else 0

    analytics_data = {
        "total_revenue": f"${total_revenue:,.2f}",
        "top_region": top_region,
        "best_product_category": best_product_category,
        "cancellation_rate": f"{cancellation_rate:.2f}%"
    }
    logger.info(f"Computed analytics: {analytics_data}")

    # 2. Detect Anomalies
    detected_anomalies = await detect_anomalies(df)
    anomaly_descriptions = [f"{a.severity}: {a.description}" for a in detected_anomalies]

    # 3. Prepare Prompt for Gemini
    prompt = f"""
    Analyze the following sales data and generate a comprehensive executive summary.
    Include key insights, potential warnings, or anomalies based on the provided metrics and detected anomalies.

    Sales Metrics:
    - Total Revenue: {analytics_data['total_revenue']}
    - Top Performing Region: {analytics_data['top_region']}
    - Best Selling Product Category: {analytics_data['best_product_category']}
    - Cancellation Rate: {analytics_data['cancellation_rate']}

    Detected Anomalies:
    {'; '.join(anomaly_descriptions) if anomaly_descriptions else 'None'}

    Please structure your response with the following sections:
    1.  Executive Summary: A concise overview of the sales performance.
    2.  Key Insights: Bullet points highlighting significant findings.
    3.  Warnings/Anomalies: Any concerns or unusual patterns observed. Prioritize explicit anomalies detected.
    """

    # 4. Call Gemini API
    try:
        model = genai.GenerativeModel('gemini-pro')
        response = model.generate_content(prompt)
        ai_summary_text = response.text
        logger.info("Successfully received response from Gemini API.")
    except Exception as e:
        logger.error(f"Error calling Gemini API: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to generate AI summary.")

    # 5. Parse Gemini's response (simple parsing for demonstration)
    executive_summary = "No executive summary provided."
    key_insights = ["No key insights provided."]
    warnings_anomalies_from_ai = ["No warnings/anomalies provided."]

    sections = ai_summary_text.split('\n\n')
    for section in sections:
        if "Executive Summary:" in section:
            executive_summary = section.replace("Executive Summary:", "").strip()
        elif "Key Insights:" in section:
            key_insights = [item.strip('- ') for item in section.split('\n') if item.strip().startswith('-')]
            if not key_insights: 
                key_insights = [section.replace("Key Insights:", "").strip()]
        elif "Warnings/Anomalies:" in section:
            warnings_anomalies_from_ai = [item.strip('- ') for item in section.split('\n') if item.strip().startswith('-')]
            if not warnings_anomalies_from_ai: 
                warnings_anomalies_from_ai = [section.replace("Warnings/Anomalies:", "").strip()]

    ai_output = AISummaryOutput(
        executive_summary=executive_summary,
        key_insights=key_insights,
        warnings_anomalies=warnings_anomalies_from_ai,
        detected_anomalies=detected_anomalies # Include detected anomalies here
    )

    return SalesSummary(
        analytics=analytics_data,
        ai_summary=ai_output
    )
