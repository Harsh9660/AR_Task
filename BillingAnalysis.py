from django.utils import timezone
from dateutil.parser import parse
from datetime import datetime, date
import statistics
import numpy as np
from api.models import CustomerData, InvoiceData
from django.db.models import Prefetch
from Sentiment_analysis import get_client_followups
from typing import Optional, Any, Dict, List, Union
import logging

class Invoice_Analysis:

    """Class for analyzing customer invoices and calculating financial metrics"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    # Function to parse date
    def parse_date(self, date_input: Optional[Any], multi_format: bool = False) -> Optional[date]:
        if not date_input:
            return None
        if isinstance(date_input, datetime):
            return date_input.date()
        if isinstance(date_input, date):
            return date_input
        try:
            parsed_date = parse(str(date_input), dayfirst=True, fuzzy=False)
            return parsed_date.date() if isinstance(parsed_date, datetime) else parsed_date
        except (ValueError, TypeError):
            return None

    def _get(self, obj: Union[Dict, Any], key: str, default: Any = None):
        """Safe getter that works for dict-like objects and model instances."""
        if obj is None:
            return default
        try:
            if isinstance(obj, dict):
                return obj.get(key, default)
            # try attribute access for Django model instances
            return getattr(obj, key, default)
        except Exception:
            return default

    # Function to get overdue bucket
    def get_overdue_bucket(self, days_overdue: int) -> str:
        """Categorize overdue days into aging buckets."""
        if days_overdue <= 30:
            return "0-30 days"
        elif 31 <= days_overdue <= 60:
            return "31-60 days"
        elif 61 <= days_overdue <= 90:
            return "61-90 days"
        else:
            return "90+ days"
                                                    
    def calculate_client_score(self, metrics: Dict, invoices: List[Dict]) -> Dict:
        """
        Calculates an enhanced client score based on a variety of financial metrics,
        including payment history, trends, and invoice characteristics, incorporating new requirements.
        """
        total_invoice_amount = metrics.get("total_invoice_amount", 0) or 1.0
        total_invoices = metrics.get("total_invoices", 0) or 1
        upcoming_invoices = metrics.get("upcoming_invoice_count", 0) or 0
        overdue_amount = metrics.get("total_overdue_amount", 0) or 0
        avg_overdue_days = metrics.get("avg_overdue_days", 0) or 0
        overdue_percentage = metrics.get("overdue_percentage", 0) or 0
        on_time_payment_ratio = metrics.get("on_time_payment_ratio", 0.0)
        dispute_count = metrics.get("disputed_invoice_count", 0)
        recurring_delay_ratio = metrics.get("recurring_delay_ratio", 0.0)
        sentiment_score_from_comm = metrics.get("sentiment_score_from_comm", 0.5)

        # Handle cases with insufficient historical data
        total_past_invoices = total_invoices - upcoming_invoices
        if total_past_invoices <= 1:
            return {
                "client_score": 0.5,
                "sentiment_score": 0.5,
                "risk_level": "Medium",
                "key_factors": ["Limited or no payment history available"],
                "recommendations": ["Monitor initial payments closely", "Request upfront deposit for trust"],
                "analysis_summary": f"Client has limited invoice data, resulting in a neutral score of 0.5."
            }

        
        # --- Score Components ---
        # 1. Overdue Amount Score: How much of the total amount is overdue?
        overdue_score = 1 - min(overdue_amount / total_invoice_amount, 1)

        # 2. On-Time Payment Ratio Score: How consistently do they pay on time?
        on_time_ratio_score = on_time_payment_ratio

        # 3. Severe Aging Score: Are payments severely late (60+ days)?
        overdue_buckets = metrics.get("overdue_buckets", {})
        severe_overdue_amount = overdue_buckets.get("61-90 days", {}).get("amount", 0.0) + \
                                overdue_buckets.get("90+ days", {}).get("amount", 0.0)
        aging_penalty = severe_overdue_amount / total_invoice_amount
        aging_score = 1 - min(aging_penalty, 1) 

        # 4. Behavioral Score: Are there disputes or recurring delays?
        behavioral_penalty = 0.0
        if dispute_count > 0:
            behavioral_penalty += 0.05 * dispute_count # 5% penalty per dispute
        behavioral_penalty += min(recurring_delay_ratio * 0.10, 0.10) # Max 10% penalty for recurring delays
        behavioral_score = 1 - min(behavioral_penalty, 1)

        # 5. High-Value Client Bonus: Small bonus for large total billing amounts
        project_value_bonus = min(total_invoice_amount / 500000, 0.05) # Bonus up to 5% for clients over 500k

        # 6. Payment Trend Analysis: Is payment behavior getting better or worse?
        overdue_days_list = []
        today = timezone.now().date()
        for inv in invoices:
            due_date = self.parse_date(inv.get("due_date"))
            invoice_date = self.parse_date(inv.get("invoice_date"))
            if due_date and invoice_date and due_date < today and float(inv.get("amount_overdue", 0)) > 0:
                days_overdue = (today - due_date).days
                overdue_days_list.append((invoice_date, days_overdue))

        trend_adjustment = 0.0
        if len(overdue_days_list) >= 2:
            overdue_days_list.sort(key=lambda x: x[0])
            midpoint = len(overdue_days_list) // 2
            recent_days = [days for _, days in overdue_days_list[midpoint:]]
            older_days = [days for _, days in overdue_days_list[:midpoint]]
            avg_recent = sum(recent_days) / len(recent_days) if recent_days else 0
            avg_older = sum(older_days) / len(older_days) if older_days else 0

            if avg_recent > avg_older * 1.1 and avg_older > 0:
                trend_adjustment = -0.1  # Worsening trend
            elif avg_recent < avg_older * 0.9: 
                trend_adjustment = 0.1  # Improving trend

        WEIGHTS = {
            "overdue_score": 0.40,      
            "on_time_ratio": 0.25,      
            "aging_score": 0.20,        
            "behavioral_score": 0.15,   
        }

        score = (
            overdue_score * WEIGHTS["overdue_score"] +
            on_time_ratio_score * WEIGHTS["on_time_ratio"] +
            aging_score * WEIGHTS["aging_score"] +
            behavioral_score * WEIGHTS["behavioral_score"]
        )

        # Combine billing score with communication sentiment score
        # 70% billing behavior, 30% communication sentiment
        final_sentiment_score = (score * 0.7) + (sentiment_score_from_comm * 0.3)

        # Apply trend adjustment
        score += trend_adjustment
        score += project_value_bonus

        # Clamp score to be within [0, 1]
        score = max(0.0, min(1.0, score))

        # Determine risk level
        if score < 0.5:
            risk_level = "High"
        elif score < 0.7:
            risk_level = "Medium"
        else:
            risk_level = "Low"

        key_factors = []
        if overdue_amount / total_invoice_amount > 0.3:
            key_factors.append(f"High overdue amount ratio: {(overdue_amount / total_invoice_amount):.2%}")
        if on_time_payment_ratio < 0.6:
            key_factors.append(f"Low on-time payment ratio: {on_time_payment_ratio:.2%}")
        if trend_adjustment < 0.0:
            key_factors.append("Worsening payment trend")
        elif trend_adjustment > 0:
            key_factors.append("Improving payment trend")
        if severe_overdue_amount > 0:
            key_factors.append(f"Has invoices overdue by more than 60 days.")
        if dispute_count > 0:
             key_factors.append(f"High number of invoice disputes: {dispute_count}")
        if recurring_delay_ratio > 0.2:
             key_factors.append(f"Recurring payment delays detected.")
        if not key_factors:
            key_factors.append("Excellent payment behavior")

        recommendations = []
        if risk_level == "High":
            recommendations.extend(["Implement stricter payment terms and late payment penalties", "Require upfront deposits for new projects"])
        elif risk_level == "Medium":
            recommendations.extend(["Offer incentives for early payments", "Monitor upcoming invoices closely"])
        else:
            recommendations.extend(["Offer extended credit terms for retention", "Maintain current terms"])
        if overdue_amount > 0:
            recommendations.append("Propose structured payment plan for overdue amounts")
 
        return {
            "client_score": round(score, 4),
            "sentiment_score": round(final_sentiment_score, 4),
            "risk_level": risk_level,
            "key_factors": key_factors[:5],
            "recommendations": recommendations[:4],
            "analysis_summary": f"Client score is {score:.2f} ({risk_level} risk), driven by: {', '.join(key_factors)}."
        }

    def calculate_client_metrics(self, customer: CustomerData, invoices: List[Dict], today: Optional[date] = None) -> Dict[str, Any]:
        """Calculate financial metrics for a customer based on their invoices. Includes new validation metrics like disputes and recurring delays."""
        today = today or timezone.now().date()
        metrics_data = {
            "total_invoice_amount": 0.0,
            "total_received": 0.0,
            "total_receivable": 0.0,
            "total_overdue_amount": 0.0,
            "overdue_invoice_count": 0,
            "paid_on_time_count": 0,
            "paid_late_count": 0,
            "upcoming_invoice_count": 0,
            "upcoming_invoice_amount": 0.0,
            "partial_paid_on_time_count": 0,
            "partial_paid_late_count": 0,
            "disputed_invoice_count": 0,
            "recurring_delay_count": 0,
        }
        overdue_days_list: List[int] = []
        overdue_invoice_ids: List[Union[str, int]] = []
        overdue_amount_list: List[float] = []
        last_invoice_date = None
        last_payment_date = None

        overdue_buckets = {
            "Upcoming": {"count": 0, "amount": 0.0},
            "0-30 days": {"count": 0, "amount": 0.0},
            "31-60 days": {"count": 0, "amount": 0.0},
            "61-90 days": {"count": 0, "amount": 0.0},
            "90+ days": {"count": 0, "amount": 0.0},
        }

        late_payments_dates: List[date] = []
        next_upcoming_payment_date = None
        invoice_count = len(invoices)
        all_invoices_details: List[Dict[str, Any]] = []

        for inv in invoices:
            # Use _get to support both dicts and model instances
            amount = float(self._get(inv, "invoice_amount") or 0.0)
            received = float(self._get(inv, "last_paid_amount") or 0.0)
            due_date = self.parse_date(self._get(inv, "due_date"))
            last_paid_date_val = self.parse_date(self._get(inv, "last_paid_date"))
            upcoming_payment_date = self.parse_date(self._get(inv, "upcoming_payment_date"))
            invoice_date = self.parse_date(self._get(inv, "invoice_date"))
            invoice_id_val = self._get(inv, "db_invoice_id")

            receivable = max(amount - received, 0.0)
            days_past_due = 0
            payment_status = "Unpaid"

            if received > 0:
                if receivable <= 0:
                    payment_status = "Paid"
                else:
                    payment_status = "Partially Paid"
            
            if due_date and due_date < today:
                days_past_due = (today - due_date).days
            else:
                days_past_due = 0

            is_disputed = bool(self._get(inv, "is_disputed", False))

            metrics_data["total_invoice_amount"] += amount
            metrics_data["total_received"] += received
            metrics_data["total_receivable"] += receivable

            if is_disputed:
                metrics_data["disputed_invoice_count"] += 1

            if invoice_date and (not last_invoice_date or invoice_date > last_invoice_date):
                last_invoice_date = invoice_date

            if due_date and due_date < today and receivable > 0:
                days_overdue = (today - due_date).days
                overdue_days_list.append(days_overdue)
                overdue_invoice_ids.append(self._get(inv, "db_invoice_id"))
                metrics_data["total_overdue_amount"] += receivable
                overdue_amount_list.append(receivable)
                metrics_data["overdue_invoice_count"] += 1

                bucket_name = self.get_overdue_bucket(days_overdue)
                overdue_buckets[bucket_name]["count"] += 1
                overdue_buckets[bucket_name]["amount"] += receivable

            if received >= amount and due_date and last_paid_date_val:
                if not last_payment_date or last_paid_date_val > last_payment_date:
                    last_payment_date = last_paid_date_val
                if last_paid_date_val <= due_date:
                    metrics_data["paid_on_time_count"] += 1
                else:
                    metrics_data["paid_late_count"] += 1
                    late_payments_dates.append(last_paid_date_val)
            elif 0 < received < amount and due_date and last_paid_date_val:
                if last_paid_date_val <= due_date:
                    metrics_data["partial_paid_on_time_count"] += 1
                else:
                    metrics_data["partial_paid_late_count"] += 1
                    late_payments_dates.append(last_paid_date_val)

            if upcoming_payment_date and upcoming_payment_date > today:
                metrics_data["upcoming_invoice_count"] += 1
                metrics_data["upcoming_invoice_amount"] += receivable
                if not next_upcoming_payment_date or upcoming_payment_date < next_upcoming_payment_date:
                    next_upcoming_payment_date = upcoming_payment_date

            all_invoices_details.append({
                "invoice_number": self._get(inv, "invoice_number"),
                "invoice_generated_date": str(invoice_date) if invoice_date else None,
                "invoice_due_date": str(due_date) if due_date else None,
                "days_past_due": days_past_due,
                "client_name": customer.customer_name,
                "project_name": self._get(inv, "project_name"),
                "milestone": self._get(inv, "milestone_name") or "",
                "invoice_amount": amount,
                "payment_status": payment_status,
                "payment_received_date": str(last_paid_date_val) if last_paid_date_val else None,
                "outstanding_amount": receivable,
                "currency": self._get(inv, "currency_type"),
            })

        # Weighted average overdue days
        weighted_overdue_days = sum(
            days * next((float(self._get(inv_item, "amount_overdue", 0.0)) for inv_item in invoices if self._get(inv_item, "db_invoice_id") == inv_id), 0.0)
            for days, inv_id in zip(overdue_days_list, overdue_invoice_ids)
        )
        total_weight = sum(overdue_amount_list)
        avg_overdue_days = weighted_overdue_days / total_weight if total_weight else 0.0

        # Overdue percentages
        invoice_count = len(invoices)
        overdue_percentage_count = (metrics_data["overdue_invoice_count"] / invoice_count) * 100 if invoice_count else 0.0
        overdue_percentage = round(0.7 * overdue_percentage_count + 0.3 * overdue_percentage_count, 2)

        # Percentiles
        percentile_25, median_amount, percentile_75 = (
            (np.percentile(overdue_amount_list, 25),
             statistics.median(overdue_amount_list),
             np.percentile(overdue_amount_list, 75))
            if overdue_amount_list else (0.0, 0.0, 0.0)
        )

        # Payment ratios
        total_past_invoices = invoice_count - metrics_data["upcoming_invoice_count"]
        on_time_payment_ratio = ((metrics_data["paid_on_time_count"] + metrics_data["partial_paid_on_time_count"]) / total_past_invoices) if total_past_invoices > 0 else 0.0
        late_payment_ratio = ((metrics_data["paid_late_count"] + metrics_data["partial_paid_late_count"]) / total_past_invoices) if total_past_invoices > 0 else 0.0

        # Recurring delay logic
        total_late_payments = metrics_data["paid_late_count"] + metrics_data["partial_paid_late_count"]
        is_recurring_delay = total_late_payments >= 3 and total_past_invoices >= 5
        recurring_delay_ratio = 1.0 if is_recurring_delay else 0.0

        # Calculate overdue_percentage_amount correctly
        overdue_percentage_amount = (metrics_data["total_overdue_amount"] / metrics_data["total_invoice_amount"] * 100) if metrics_data["total_invoice_amount"] > 0 else 0.0
        
        final_metrics = {
            "customer_id": str(customer.customer_id),
            "customer_name": customer.customer_name,
            "total_invoices": invoice_count,
            **metrics_data,
            "invoices_details": all_invoices_details,
            "overdue_percentage": overdue_percentage,
            "overdue_percentage_amount": round(overdue_percentage_amount, 2),
            "overdue_percentage_count": round(overdue_percentage_count, 2),
            "max_overdue_days": max(overdue_days_list) if overdue_days_list else 0,
            "overdue_amount_percentile_25": round(percentile_25, 2),
            "overdue_amount_median": round(median_amount, 2),
            "overdue_amount_percentile_75": round(percentile_75, 2),
            "avg_overdue_days": round(avg_overdue_days, 2),
            "overdue_buckets": overdue_buckets,
            "total_past_invoices": total_past_invoices,
            "on_time_payment_ratio": round(on_time_payment_ratio, 4),
            "late_payment_ratio": round(late_payment_ratio, 4),
            "recurring_delay_ratio": round(recurring_delay_ratio, 4),
            "next_upcoming_payment_date": str(next_upcoming_payment_date) if next_upcoming_payment_date else None,
            "last_invoice_date": str(last_invoice_date) if last_invoice_date else None,
            "last_payment_date": str(last_payment_date) if last_payment_date else None
        }
        return final_metrics

    def get_grouped_customer_invoice_data(self, customers_queryset=None, invoice_id=None) -> Optional[List[Dict]]:
        """Fetch and process invoice data for customers."""
        from django.db.models import Q
        invoice_qs = InvoiceData.objects.filter(is_deleted=False).select_related('customer_id')

        if invoice_id is not None:
            try:
                invoice_id = int(invoice_id)
                customer = invoice_qs.get(id=invoice_id).customer_id
                if customer:
                    customers_queryset = CustomerData.objects.filter(id=customer.id)
                else: 
                    return None
            except (InvoiceData.DoesNotExist, ValueError):
                return None
        else:
            customers_queryset = CustomerData.objects.filter(
                is_active=True, is_deleted=False
            ).prefetch_related(Prefetch('customer_invoice', queryset=invoice_qs.filter(is_deleted=False)))

        results = []
        for customer in customers_queryset:
            invoice_list = []
            for inv in customer.customer_invoice.all():
                invoice_data = {
                    "db_invoice_id": inv.id,
                    "invoice_number": inv.invoice_number,
                    "project_name": inv.project_name,
                    "milestone_name": inv.milestone_name,
                    "currency_type": inv.currency_type,
                    "invoice_date": self.parse_date(inv.invoice_date),
                    "due_date": self.parse_date(inv.due_date),
                    "invoice_amount": float(inv.invoice_amount or 0),
                    "amount_overdue": round(float(inv.amount_overdue or 0), 2),
                    "total_recivable": float(inv.total_recivable or 0),
                    "is_overdue": inv.is_overdue,
                    "is_disputed": getattr(inv, "is_disputed", False),
                    "upcoming_payment_date": self.parse_date(inv.upcoming_payment_date),
                    "last_paid_amount": float(inv.last_paid_amount or 0),
                    "last_paid_date": self.parse_date(inv.last_paid_date),
                }
                invoice_list.append(invoice_data)

            metrics = self.calculate_client_metrics(customer, invoice_list)

            # Get sentiment score from communication with improved error handling
            sentiment_score_from_comm = 0.5  # Default neutral
            try:
                sentiment_data = get_client_followups(customer_id=customer.id)
                if sentiment_data and len(sentiment_data) > 0:
                    analysis = sentiment_data[0].get("data", {}).get("analysis", {})
                    sentiment_score_from_comm = analysis.get("sentiment_score", 0.5)
                    self.logger.info(f"Fetched sentiment score {sentiment_score_from_comm} for customer {customer.id}")
            except Exception as e:
                self.logger.warning(f"Could not fetch sentiment for customer {customer.id}: {e}")
            
            metrics['sentiment_score_from_comm'] = sentiment_score_from_comm

            score_details = self.calculate_client_score(metrics, invoice_list)
            metrics.update(score_details)
            results.append(metrics)
        
        self.logger.info(f"Successfully processed billing data for {len(results)} customers.")
        
        # Wrap results in the expected format
        return {"results": results} if results else {"results": []} 