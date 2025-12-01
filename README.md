# 💰 InvoiceHub - AI-Powered Billing Analytics Dashboard

A comprehensive invoice management and billing analysis system that combines real-time financial insights with AI-powered sentiment analysis to help businesses manage accounts receivable effectively.

## ✨ Features

### 📊 Dashboard Overview
- **Real-time Financial Metrics**: Track total receivables, overdue amounts, active customers, and high-risk clients
- **Interactive Visualizations**: Monthly revenue trends, risk distribution charts, and aging analysis
- **Invoice Management**: Filter, search, and analyze invoices with multiple payment statuses (Paid, Unpaid, Partially Paid)
- **Premium UI/UX**: Modern, responsive design with glassmorphism effects and smooth animations

### 🔍 Customer Billing Analysis
- **Client Scoring System**: Advanced algorithm that calculates client reliability scores based on:
  - Payment history and on-time payment ratios
  - Overdue amounts and aging buckets (0-30, 31-60, 61-90, 90+ days)
  - Behavioral patterns (disputes, recurring delays)
  - Payment trends (improving/declining)
  
- **Risk Assessment**: Automatic categorization of clients into High, Medium, or Low risk levels

- **AI-Powered Sentiment Analysis**: 
  - Analyzes client communication patterns using OpenAI GPT-3.5
  - Tracks relationship dynamics, trust levels, and engagement
  - Provides sentiment scores (0.0 to 1.0) based on communication tone
  - Identifies trends: improving, declining, or stable relationships

- **Aging Analysis**: Visual breakdown of overdue amounts by time buckets

- **Actionable Insights**: 
  - Key factors affecting client scores
  - AI-generated recommendations for payment terms
  - Structured payment plan suggestions

### 📈 Advanced Analytics
- **Weighted Scoring**: Combines billing behavior (70%) and communication sentiment (30%)
- **Trend Detection**: Identifies improving or worsening payment patterns
- **Dispute Tracking**: Monitors invoice disputes and their impact on client scores
- **Recurring Delay Detection**: Flags clients with consistent late payment patterns

## 🛠️ Technology Stack

- **Frontend**: Streamlit with custom CSS styling
- **Backend**: Django ORM for data management
- **Visualization**: Plotly for interactive charts and graphs
- **AI/ML**: OpenAI GPT-3.5 for sentiment analysis
- **Data Processing**: Pandas, NumPy for financial calculations
- **Database**: Django models (CustomerData, InvoiceData, FollowUp)

## 📁 Project Structure

```
ARA_New/
├── invoice_dashboard.py      # Main Streamlit dashboard application
├── BillingAnalysis.py        # Core billing analytics and scoring engine
├── Sentiment_analysis.py     # AI-powered sentiment analysis module
├── mock_data.py              # Mock data generator for testing
├── test_billing_analysis.py  # Unit tests for billing calculations
└── README.md                 # Project documentation
```

## 🚀 Getting Started

### Prerequisites

- Python 3.8+
- Django 3.2+
- OpenAI API key

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/invoicehub.git
   cd invoicehub
   ```

2. **Install dependencies**
   ```bash
   pip install streamlit pandas plotly numpy python-dateutil openai python-dotenv django
   ```

3. **Set up environment variables**
   Create a `.env` file in the project root:
   ```
   OPENAI_API_KEY=your_openai_api_key_here
   ```

4. **Run the dashboard**
   ```bash
   streamlit run invoice_dashboard.py
   ```

## 💡 Usage

### Dashboard Overview
- View aggregate financial metrics across all customers
- Monitor revenue trends and risk distribution
- Filter invoices by payment status
- Click "Analyze" on any invoice to view detailed billing analysis

### Customer Analysis
- Select a customer from the dropdown
- Review client score, sentiment score, and risk level
- Analyze aging buckets and overdue amounts
- Read AI-generated insights and recommendations
- Download detailed reports as CSV

## 🧮 Scoring Algorithm

The client score is calculated using a weighted formula:

```
Client Score = (Overdue Score × 0.40) + 
               (On-Time Ratio × 0.25) + 
               (Aging Score × 0.20) + 
               (Behavioral Score × 0.15) +
               Trend Adjustment + 
               Project Value Bonus
```

**Final Sentiment Score** combines:
- Billing behavior: 70%
- Communication sentiment: 30%

## 🎯 Key Metrics Explained

- **Client Score**: 0.0 to 1.0 scale indicating payment reliability
- **Sentiment Score**: AI-analyzed communication quality (0.0 = negative, 1.0 = positive)
- **Risk Level**: High (<0.5), Medium (0.5-0.7), Low (>0.7)
- **On-Time Payment Ratio**: Percentage of invoices paid before due date
- **Overdue Percentage**: Proportion of total amount currently overdue

## 🧪 Testing

Run unit tests for billing analysis:
```bash
python test_billing_analysis.py
```

## 📊 Mock Data

For testing and demonstration purposes, use the included mock data generator:
```python
from mock_data import get_mock_customer_data
data = get_mock_customer_data()
```

## 🔒 Security Notes

- Store API keys securely in environment variables
- Never commit `.env` files to version control
- Implement proper authentication for production deployments
- Sanitize user inputs in production environments

## 🤝 Contributing

Contributions are welcome! Please follow these steps:
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 👤 Author

**Harsh Pandya**

## 🙏 Acknowledgments

- OpenAI for GPT-3.5 API
- Streamlit for the amazing dashboard framework
- Plotly for interactive visualizations

---

**Version**: 2.0.0 | Premium Edition
