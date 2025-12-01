import os
import json
from dotenv import load_dotenv
from openai import OpenAI
from api.models import FollowUp, CustomerSentimentSummary


load_dotenv()


class SentimentAnalyzer:
    """Sentiment + relationship dynamics analyzer."""

    def __init__(self, api_key=None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise RuntimeError(" Missing OpenAI API key. Set OPENAI_API_KEY in environment.")
        self.client = OpenAI(api_key=self.api_key)

    def analyze(self, comments: str, past_summary: str = "", past_status: str = "") -> dict:
        if not comments:
            return {"error": "No text provided for analysis."}

        prompt = f"""
        You are a relationship and sentiment analysis engine.
        Your goal is to evaluate the relationship dynamics between two individuals
        based solely on their communication.

        Focus only on interpersonal cues: trust, engagement, satisfaction,
        commitment, cooperation, and overall relationship health.

        Analyze sentiment as positive, neutral, or negative based strictly on tone,
        wording, and context. Compare the current communication with past interactions
        to identify improvement, decline, or stability.

        Always return ONLY valid JSON with no extra text.

        Past Status: "{past_status or 'none'}"
        Past Summary: "{past_summary or 'No previous summary available.'}"

        Current Text: "{comments}"

        Return JSON with:
        - "past_status": "strong", "weak", "inconsistent", or "none"
        - "current_status": "strong", "weak", or "inconsistent"
        - "relationship_trend": "improving", "declining", or "stable"
        - "sentiment_score": floating-point value strictly between 0.0 (very negative) and 1.0 (very positive)
        - "sentiment": "positive", "neutral", or "negative"
        - "communication_clarity": "clear", "ambiguous", or "confused"
        - "response_pattern": "balanced", "one-sided", or "avoidant"
        - "key_notes": ["bullet point 1", "bullet point 2", "bullet point 3"]
        """

        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.0,
            )
            output = response.choices[0].message.content.strip()
            return json.loads(output)
        except json.JSONDecodeError:
            return {"error": "Invalid JSON returned from model", "raw_output": output}
        except Exception as e:
            return {"error": str(e)}


def get_client_followups(limit: int = 50, customer_id: int = None):
    """
    Collect followups per client and return sentiment analysis summary
    in the exact response format required.
    If customer_id is provided, only that customer is processed.
    """

    followup_qs = FollowUp.objects.filter(invoice__customer_id=customer_id).select_related('invoice__customer_id')
    followups = followup_qs[:limit]
    if not followups:
        return []

    analyzer = SentimentAnalyzer()
    client_data = {}

   
    for f in followups:
        client = f.invoice.customer_id
        client_id = client.id

        if client_id not in client_data:
            client_sentiment, _ = CustomerSentimentSummary.objects.get_or_create(customer=client)

            client_data[client_id] = {
                "customer_id": getattr(client, "customer_id", str(client.id)),
                "customer_name": getattr(client, "customer_name", client.customer_name),
                "all_texts": [],
                # "past_summary": client_sentiment.past_summary or "",
                # "past_status": client_sentiment.past_status or "none",
                "followups_flow": [],
                "sentiment_record": client_sentiment,
            }
        analysis = analyzer.analyze(
            comments=f.comments
        )
        client_data[client_id]["all_texts"].append(f.comments)
        client_data[client_id]["followups_flow"].append({
            "date": f.created_at.strftime("%Y-%m-%d"),
            "sentiment_score": analysis.get("sentiment_score", 0.0)
        })
    
    # print("Client data from followups --------",client_data)

    results = []

    
    for client_id, data in client_data.items():
        full_text = " ".join(data["all_texts"])

        analysis = analyzer.analyze(
            comments=full_text
        )

      
        # for flow in data["followups_flow"]:
        #     flow["sentiment_score"] = analysis.get("sentiment_score", 0.0)

        
        combined_summary = " | ".join(analysis.get("key_notes", []))

        
        sentiment_record = data["sentiment_record"]
        # sentiment_record.past_summary = combined_summary
        # sentiment_record.past_status = analysis.get("current_status", "none")
        sentiment_record.save()

        results.append({
            "status": "success",
            "message": "Sentiment analysis fetched successfully.",
            "customer_id": data["customer_id"],
            "customer_name": data["customer_name"],
            "total_invoices": len(data["followups_flow"]),
            "data": {
                "id": len(data["followups_flow"]),
                "analysis": analysis,
                "followups_flow": data["followups_flow"],
                "combined_summary": combined_summary,
                "total_followups": len(data["followups_flow"])
            }
        })
        # print("results -------------------------",results)

    return results
