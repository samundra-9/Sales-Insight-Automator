import os
import logging
from typing import List

import pandas as pd
from fastapi import HTTPException, status

from app.models.sales_data import AISummaryOutput, Anomaly, SalesSummary
from app.utils.logger import setup_logging

# Gemini import is optional (not everyone may have the dependency or API access)
try:
    import google.generativeai as genai

    GEMINI_AVAILABLE = True
except Exception:
    GEMINI_AVAILABLE = False

setup_logging()
logger = logging.getLogger(__name__)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if GEMINI_AVAILABLE and GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)


async def detect_anomalies(df: pd.DataFrame) -> List[Anomaly]:
    """Detect simple anomalies in the sales dataset."""

    anomalies: List[Anomaly] = []

    # High cancellation rate
    if "Cancelled" in df.columns and len(df) > 0:
        cancellation_rate = (df["Cancelled"].sum() / len(df)) * 100
        if cancellation_rate > 20:
            anomalies.append(
                Anomaly(
                    type="High Cancellation Rate",
                    description=f"Cancellation rate is {cancellation_rate:.2f}%, which is unusually high.",
                    severity="Warning",
                )
            )

    # Low revenue in a region
    if "Revenue" in df.columns and "Region" in df.columns:
        region_revenue = df.groupby("Region")["Revenue"].sum()
        if len(region_revenue) > 1:
            mean_revenue = region_revenue.mean()
            for region, revenue in region_revenue.items():
                if revenue < mean_revenue * 0.5:
                    anomalies.append(
                        Anomaly(
                            type="Low Regional Revenue",
                            description=f"Revenue in {region} ({revenue:,.2f}) is significantly lower than average.",
                            severity="Warning",
                        )
                    )

    # Negative revenue values
    if "Revenue" in df.columns and (df["Revenue"] < 0).any():
        anomalies.append(
            Anomaly(
                type="Negative Revenue Detected",
                description="Found one or more sales records with negative revenue values, indicating potential data quality issues.",
                severity="Critical",
            )
        )

    logger.info(f"Detected {len(anomalies)} anomalies in the sales data.")
    return anomalies


async def generate_sales_summary(df: pd.DataFrame) -> SalesSummary:
    """Generate a sales summary using a structured prompt (Gemini or fallback)."""

    logger.info("Starting sales summary generation.")

    if df.empty:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No data to analyze.",
        )

    total_revenue = df["Revenue"].sum() if "Revenue" in df.columns else 0
    top_region = df["Region"].mode()[0] if "Region" in df.columns and not df["Region"].empty else "N/A"
    best_product_category = df["ProductCategory"].mode()[0] if "ProductCategory" in df.columns and not df["ProductCategory"].empty else "N/A"
    cancellation_rate = (
        (df["Cancelled"].sum() / len(df)) * 100
        if "Cancelled" in df.columns and len(df) > 0
        else 0
    )

    analytics_data = {
        "total_revenue": f"${total_revenue:,.2f}",
        "top_region": top_region,
        "best_product_category": best_product_category,
        "cancellation_rate": f"{cancellation_rate:.2f}%",
    }

    logger.info(f"Computed analytics: {analytics_data}")

    detected_anomalies = await detect_anomalies(df)
    anomaly_descriptions = [f"{a.severity}: {a.description}" for a in detected_anomalies]

    prompt = f"""
You are a senior sales analyst.

Sales Metrics:
- Total Revenue: {analytics_data['total_revenue']}
- Top Region: {analytics_data['top_region']}
- Best Product Category: {analytics_data['best_product_category']}
- Cancellation Rate: {analytics_data['cancellation_rate']}

Detected Anomalies:
{'; '.join(anomaly_descriptions) if anomaly_descriptions else 'None'}

Please generate:
1) Executive Summary
2) Key Insights (bulleted list)
3) Warnings / Anomalies
"""

    ai_summary_text: str | None = None

    # Try Gemini first (if available)
    if GEMINI_AVAILABLE and GEMINI_API_KEY:
        try:
            model = genai.GenerativeModel("gemini-1.5-flash")
            response = model.generate_content(prompt)
            ai_summary_text = response.text
            logger.info("Gemini summary generated successfully.")
        except Exception as e:
            logger.warning(f"Gemini generation failed, falling back: {e}")

    # Fallback summary generator
    if not ai_summary_text:
        logger.info("Using fallback summary generator.")

        ai_summary_text = f"""
Executive Summary:
Sales performance shows total revenue of {analytics_data['total_revenue']}, with strongest activity in the {top_region} region.

Key Insights:
- {best_product_category} is the most frequently sold category.
- Revenue concentration suggests regional imbalance.
- Cancellation rate currently at {analytics_data['cancellation_rate']}.

Warnings/Anomalies:
{'; '.join(anomaly_descriptions) if anomaly_descriptions else 'No major anomalies detected.'}
"""

    # Parse the generated summary into sections
    sections = [s.strip() for s in ai_summary_text.split("\n\n") if s.strip()]

    executive_summary = sections[0] if sections else "Summary unavailable."
    key_insights: List[str] = []
    warnings_anomalies: List[str] = []

    for line in ai_summary_text.split("\n"):
        line = line.strip()
        if line.startswith("-"):
            key_insights.append(line.lstrip("- ").strip())

    if not key_insights:
        key_insights = ["Sales performance trends detected."]

    warnings_anomalies = anomaly_descriptions if anomaly_descriptions else ["No anomalies detected."]

    ai_output = AISummaryOutput(
        executive_summary=executive_summary,
        key_insights=key_insights,
        warnings_anomalies=warnings_anomalies,
        detected_anomalies=detected_anomalies,
    )

    return SalesSummary(analytics=analytics_data, ai_summary=ai_output)
