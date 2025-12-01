"""
Test script to validate BillingAnalysis output structure.
This script validates that the response matches the expected JSON structure.
"""

import json
from datetime import date

def validate_billing_response(response_data):
    """Validate the billing analysis response structure."""

    errors = []

    # Check top-level structure
    if not isinstance(response_data, dict):
        errors.append("Response must be a dictionary")
        return errors

    if "results" not in response_data:
        errors.append("Response must contain 'results' key")
        return errors

    if not isinstance(response_data["results"], list):
        errors.append("'results' must be a list")
        return errors

    # Validate each customer result
    for idx, customer in enumerate(response_data["results"]):
        prefix = f"Customer {idx}"

        # Required string fields
        string_fields = ["customer_id", "customer_name", "risk_level", "analysis_summary"]
        for field in string_fields:
            if field not in customer:
                errors.append(f"{prefix}: Missing field '{field}'")
            elif not isinstance(customer.get(field), str):
                errors.append(f"{prefix}: Field '{field}' must be a string")

        # Required numeric fields
        numeric_fields = [
            "total_invoices", "total_invoice_amount", "total_received", 
            "total_receivable", "total_overdue_amount", "overdue_invoice_count",
            "client_score", "sentiment_score"
        ]
        for field in numeric_fields:
            if field not in customer:
                errors.append(f"{prefix}: Missing field '{field}'")
            elif not isinstance(customer.get(field), (int, float)):
                errors.append(f"{prefix}: Field '{field}' must be numeric")

        # Required list fields
        list_fields = ["key_factors", "recommendations", "invoices_details"]
        for field in list_fields:
            if field not in customer:
                errors.append(f"{prefix}: Missing field '{field}'")
            elif not isinstance(customer.get(field), list):
                errors.append(f"{prefix}: Field '{field}' must be a list")

        # Validate overdue_buckets structure
        if "overdue_buckets" not in customer:
            errors.append(f"{prefix}: Missing 'overdue_buckets'")
        else:
            buckets = customer["overdue_buckets"]
            required_buckets = ["Upcoming", "0-30 days", "31-60 days", "61-90 days", "90+ days"]
            for bucket in required_buckets:
                if bucket not in buckets:
                    errors.append(f"{prefix}: Missing bucket '{bucket}' in overdue_buckets")
                else:
                    if "count" not in buckets[bucket] or "amount" not in buckets[bucket]:
                        errors.append(f"{prefix}: Bucket '{bucket}' missing 'count' or 'amount'")

        # Validate invoice details structure
        if "invoices_details" in customer and isinstance(customer["invoices_details"], list):
            for inv_idx, invoice in enumerate(customer["invoices_details"]):
                inv_prefix = f"{prefix}, Invoice {inv_idx}"
                required_invoice_fields = [
                    "invoice_number", "invoice_generated_date", "invoice_due_date",
                    "days_past_due", "client_name", "project_name", "milestone",
                    "invoice_amount", "payment_status", "outstanding_amount", "currency"
                ]
                for field in required_invoice_fields:
                    if field not in invoice:
                        errors.append(f"{inv_prefix}: Missing field '{field}'")

    return errors


def test_sample_response():
    """Test with a sample response structure."""

    sample_response = {
        "results": [
            {
                "customer_id": "353",
                "customer_name": "Test Customer",
                "total_invoices": 5,
                "total_invoice_amount": 25000.0,
                "total_received": 25000.0,
                "total_receivable": 0.0,
                "total_overdue_amount": 0.0,
                "overdue_invoice_count": 0,
                "client_score": 0.885,
                "sentiment_score": 0.6645,
                "risk_level": "Low",
                "key_factors": ["Test factor"],
                "recommendations": ["Test recommendation"],
                "analysis_summary": "Test summary",
                "overdue_buckets": {
                    "Upcoming": {"count": 0, "amount": 0.0},
                    "0-30 days": {"count": 0, "amount": 0.0},
                    "31-60 days": {"count": 0, "amount": 0.0},
                    "61-90 days": {"count": 0, "amount": 0.0},
                    "90+ days": {"count": 0, "amount": 0.0}
                },
                "invoices_details": [
                    {
                        "invoice_number": "INV-001",
                        "invoice_generated_date": "2024-01-01",
                        "invoice_due_date": "2024-02-01",
                        "days_past_due": 0,
                        "client_name": "Test Customer",
                        "project_name": "Test Project",
                        "milestone": "Phase 1",
                        "invoice_amount": 5000.0,
                        "payment_status": "Paid",
                        "payment_received_date": "2024-01-15",
                        "outstanding_amount": 0.0,
                        "currency": "USD"
                    }
                ],
                "paid_on_time_count": 5,
                "paid_late_count": 0,
                "upcoming_invoice_count": 0,
                "upcoming_invoice_amount": 0.0,
                "partial_paid_on_time_count": 0,
                "partial_paid_late_count": 0,
                "disputed_invoice_count": 0,
                "recurring_delay_count": 0,
                "overdue_percentage": 0.0,
                "overdue_percentage_amount": 0.0,
                "overdue_percentage_count": 0.0,
                "max_overdue_days": 0,
                "overdue_amount_percentile_25": 0.0,
                "overdue_amount_median": 0.0,
                "overdue_amount_percentile_75": 0.0,
                "avg_overdue_days": 0.0,
                "total_past_invoices": 5,
                "on_time_payment_ratio": 1.0,
                "late_payment_ratio": 0.0,
                "recurring_delay_ratio": 0.0,
                "next_upcoming_payment_date": None,
                "last_invoice_date": "2024-05-01",
                "last_payment_date": "2024-05-15",
                "sentiment_score_from_comm": 0.5
            }
        ]
    }

    errors = validate_billing_response(sample_response)

    if errors:
        print("❌ Validation FAILED:")
        for error in errors:
            print(f"  - {error}")
        return False
    else:
        print("✅ Validation PASSED: Response structure is correct!")
        print(f"   Validated {len(sample_response['results'])} customer record(s)")
        return True


if __name__ == "__main__":
    print("=" * 60)
    print("BillingAnalysis Response Structure Validator")
    print("=" * 60)
    print()

    success = test_sample_response()

    print()
    print("=" * 60)
    if success:
        print("✅ All tests passed!")
    else:
        print("❌ Some tests failed. Please review the errors above.")
    print("=" * 60)