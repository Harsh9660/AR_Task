import datetime
import random

def generate_mock_clients(num_clients=1500):
    """
    Generate a large number of mock clients with realistic data patterns.
    """
    today = datetime.date.today()
    
    # Company name templates
    company_prefixes = ["Tech", "Global", "Advanced", "Digital", "Smart", "Innovative", "Prime", "Elite", "Dynamic", "Strategic"]
    company_suffixes = ["Solutions", "Systems", "Corp", "Inc", "Technologies", "Enterprises", "Group", "Partners", "Industries", "Ventures"]
    
    # Project templates
    projects = ["Cloud Migration", "Website Redesign", "Mobile App", "Data Analytics", "Security Audit", 
                "Infrastructure Upgrade", "CRM Implementation", "API Development", "Consulting Services", "Training Program"]
    
    clients = []
    
    for i in range(num_clients):
        customer_id = 1000 + i
        company_name = f"{random.choice(company_prefixes)} {random.choice(company_suffixes)} {i+1}"
        
        # Randomize payment behavior
        payment_profile = random.choice(["excellent", "good", "medium", "poor", "critical"])
        
        if payment_profile == "excellent":
            total_invoices = random.randint(10, 30)
            total_amount = random.uniform(500000, 2000000)
            payment_ratio = random.uniform(0.95, 1.0)
            overdue_ratio = 0.0
            client_score = random.uniform(0.90, 1.0)
            sentiment_score = random.uniform(0.85, 1.0)
            sentiment_trend = random.choice(["Rising", "Stable"])
            risk_level = "Low"
        elif payment_profile == "good":
            total_invoices = random.randint(8, 25)
            total_amount = random.uniform(200000, 800000)
            payment_ratio = random.uniform(0.85, 0.95)
            overdue_ratio = random.uniform(0.0, 0.05)
            client_score = random.uniform(0.75, 0.90)
            sentiment_score = random.uniform(0.70, 0.85)
            sentiment_trend = random.choice(["Rising", "Stable", "Stable"])
            risk_level = "Low"
        elif payment_profile == "medium":
            total_invoices = random.randint(5, 20)
            total_amount = random.uniform(100000, 500000)
            payment_ratio = random.uniform(0.60, 0.85)
            overdue_ratio = random.uniform(0.05, 0.20)
            client_score = random.uniform(0.50, 0.75)
            sentiment_score = random.uniform(0.45, 0.70)
            sentiment_trend = random.choice(["Stable", "Stable", "Falling"])
            risk_level = "Medium"
        elif payment_profile == "poor":
            total_invoices = random.randint(5, 15)
            total_amount = random.uniform(50000, 300000)
            payment_ratio = random.uniform(0.40, 0.60)
            overdue_ratio = random.uniform(0.20, 0.40)
            client_score = random.uniform(0.30, 0.50)
            sentiment_score = random.uniform(0.25, 0.45)
            sentiment_trend = random.choice(["Falling", "Falling", "Stable"])
            risk_level = "High"
        else:  # critical
            total_invoices = random.randint(3, 12)
            total_amount = random.uniform(30000, 200000)
            payment_ratio = random.uniform(0.10, 0.40)
            overdue_ratio = random.uniform(0.40, 0.80)
            client_score = random.uniform(0.10, 0.30)
            sentiment_score = random.uniform(0.10, 0.25)
            sentiment_trend = "Falling"
            risk_level = "High"
        
        total_received = total_amount * payment_ratio
        total_receivable = total_amount - total_received
        total_overdue = total_receivable * overdue_ratio
        overdue_count = max(1, int(total_invoices * overdue_ratio)) if total_overdue > 0 else 0
        
        # Generate key factors and recommendations based on profile
        key_factors = []
        recommendations = []
        
        if payment_profile in ["excellent", "good"]:
            key_factors.append("Excellent payment behavior")
            recommendations.append("Offer extended credit terms for retention")
        elif payment_profile == "medium":
            key_factors.append("Inconsistent payment schedule")
            recommendations.append("Monitor upcoming invoices closely")
        else:
            key_factors.append("Multiple overdue invoices")
            recommendations.append("Implement stricter payment terms")
        
        # Distribute overdue amounts across buckets
        overdue_buckets = {
            "Upcoming": {"count": 0, "amount": 0.0},
            "0-30 days": {"count": 0, "amount": 0.0},
            "31-60 days": {"count": 0, "amount": 0.0},
            "61-90 days": {"count": 0, "amount": 0.0},
            "90+ days": {"count": 0, "amount": 0.0},
        }
        
        if total_overdue > 0:
            # Distribute overdue across buckets
            bucket_keys = ["0-30 days", "31-60 days", "61-90 days", "90+ days"]
            remaining_overdue = total_overdue
            remaining_count = overdue_count
            
            for bucket in bucket_keys:
                if remaining_count > 0:
                    count = random.randint(0, remaining_count)
                    amount = remaining_overdue * random.uniform(0.1, 0.5) if remaining_count > 1 else remaining_overdue
                    overdue_buckets[bucket]["count"] = count
                    overdue_buckets[bucket]["amount"] = round(amount, 2)
                    remaining_count -= count
                    remaining_overdue -= amount
        
        # Add upcoming invoices
        upcoming_count = random.randint(0, 3)
        upcoming_amount = total_receivable - total_overdue if total_receivable > total_overdue else 0
        overdue_buckets["Upcoming"]["count"] = upcoming_count
        overdue_buckets["Upcoming"]["amount"] = round(upcoming_amount, 2)
        
        # Generate sample invoices (limit to 5 for performance)
        invoices_details = []
        num_sample_invoices = min(5, total_invoices)
        
        for j in range(num_sample_invoices):
            days_ago = random.randint(10, 180)
            due_days = random.randint(20, 40)
            invoice_date = today - datetime.timedelta(days=days_ago)
            due_date = invoice_date + datetime.timedelta(days=due_days)
            days_past_due = max(0, (today - due_date).days) if due_date < today else 0
            
            invoice_amount = total_amount / total_invoices
            
            # Determine payment status
            if random.random() < payment_ratio:
                if random.random() < 0.8:
                    payment_status = "Paid"
                    outstanding = 0.0
                else:
                    payment_status = "Partially Paid"
                    outstanding = invoice_amount * random.uniform(0.2, 0.5)
            else:
                payment_status = "Unpaid"
                outstanding = invoice_amount
            
            invoices_details.append({
                "invoice_number": f"INV-{customer_id}-{j+1:03d}",
                "invoice_generated_date": invoice_date,
                "invoice_due_date": due_date,
                "days_past_due": days_past_due,
                "client_name": company_name,
                "project_name": random.choice(projects),
                "milestone": f"Phase {j+1}",
                "invoice_amount": round(invoice_amount, 2),
                "payment_status": payment_status,
                "outstanding_amount": round(outstanding, 2),
                "currency": "USD"
            })
        
        client = {
            "customer_id": customer_id,
            "customer_name": company_name,
            "total_invoices": total_invoices,
            "total_invoice_amount": round(total_amount, 2),
            "total_received": round(total_received, 2),
            "total_receivable": round(total_receivable, 2),
            "total_overdue_amount": round(total_overdue, 2),
            "overdue_invoice_count": overdue_count,
            "client_score": round(client_score, 2),
            "sentiment_score": round(sentiment_score, 2),
            "sentiment_trend": sentiment_trend,
            "risk_level": risk_level,
            "key_factors": key_factors,
            "recommendations": recommendations,
            "analysis_summary": f"Client score is {client_score:.2f} ({risk_level} risk). {key_factors[0]}.",
            "overdue_buckets": overdue_buckets,
            "invoices_details": invoices_details
        }
        
        clients.append(client)
    
    return clients


def get_mock_customer_data():
    """
    Returns mock customer data.
    Set num_clients parameter to control the dataset size.
    """
    # Generate 1500 clients for comprehensive testing
    return generate_mock_clients(num_clients=1500)
