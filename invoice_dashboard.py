import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import time
from mock_data import get_mock_customer_data

# Set page configuration
st.set_page_config(
    page_title="Invoice Dashboard",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Custom CSS for Dark Theme Premium Styling ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    .stApp {
        background: linear-gradient(135deg, #0a0a0a 0%, #1a1a2e 100%);
    }

    .metric-card {
        background: linear-gradient(145deg, #1e1e2e 0%, #252538 100%);
        padding: 24px;
        border-radius: 16px;
        box-shadow: 0 8px 32px rgba(0,0,0,0.4);
        border: 1px solid rgba(255,255,255,0.1);
        transition: transform 0.3s ease, box-shadow 0.3s ease, border 0.3s ease;
    }
    .metric-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 12px 40px rgba(59, 130, 246, 0.3);
        border: 1px solid rgba(59, 130, 246, 0.5);
    }
    .metric-value {
        font-size: 32px;
        font-weight: 700;
        background: linear-gradient(135deg, #60a5fa 0%, #a78bfa 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin-bottom: 4px;
    }
    .metric-label {
        font-size: 14px;
        color: #94a3b8;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    .metric-delta {
        font-size: 13px;
        font-weight: 600;
        margin-top: 6px;
    }
    .delta-pos { color: #34d399; }
    .delta-neg { color: #f87171; }
    
    /* Custom Button Styling */
    .stButton button {
        width: 100%;
        border-radius: 8px;
        font-weight: 600;
        padding: 0.5rem 1rem;
        background: linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%);
        color: white;
        border: none;
        transition: all 0.3s;
    }
    .stButton button:hover {
        background: linear-gradient(135deg, #2563eb 0%, #7c3aed 100%);
        box-shadow: 0 4px 20px rgba(59, 130, 246, 0.4);
        transform: translateY(-2px);
    }
    
    /* Table Styling */
    .stDataFrame {
        border-radius: 12px;
        overflow: hidden;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.3);
        background-color: #1e1e2e;
    }
    
    /* Header Styling */
    h1, h2, h3 {
        color: #f1f5f9;
        font-weight: 700;
        text-shadow: 0 2px 10px rgba(59, 130, 246, 0.3);
    }
    
    /* Sidebar Styling */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #16213e 0%, #0f3460 100%);
        border-right: 1px solid rgba(59, 130, 246, 0.2);
    }
    
    [data-testid="stSidebar"] * {
        color: #e2e8f0 !important;
    }
    
    /* Text color adjustments */
    p, span, div {
        color: #cbd5e1;
    }
    
    /* Input fields */
    .stSelectbox, .stMultiSelect {
        background-color: #1e1e2e;
        border-radius: 8px;
    }
    
    /* Download button */
    .stDownloadButton button {
        background: linear-gradient(135deg, #10b981 0%, #059669 100%);
        color: white;
        border: none;
    }
    .stDownloadButton button:hover {
        background: linear-gradient(135deg, #059669 0%, #047857 100%);
        box-shadow: 0 4px 20px rgba(16, 185, 129, 0.4);
    }
</style>
""", unsafe_allow_html=True)

# --- Load Data ---
@st.cache_data
def load_data():
    return get_mock_customer_data()

data = load_data()

# --- Session State Management ---
if 'view_mode' not in st.session_state:
    st.session_state['view_mode'] = "Dashboard Overview"
if 'selected_customer' not in st.session_state:
    st.session_state['selected_customer'] = data[0]['customer_name']
if 'is_loading' not in st.session_state:
    st.session_state['is_loading'] = False

def simulate_api_call():
    """Simulates an API call with a spinner."""
    with st.spinner('Loading billing insights...'):
        time.sleep(0.1)  # Minimal delay for smooth UX

def switch_to_analysis(customer_name):
    st.session_state['selected_customer'] = customer_name
    st.session_state['view_mode'] = "Customer Analysis"
    st.session_state['is_loading'] = True

# --- Helper Functions ---
def format_currency(value):
    return f"${value:,.2f}"

@st.cache_data(ttl=300)
def calculate_aggregate_metrics(data):
    """Calculate aggregate metrics with caching."""
    total_receivable = sum(item['total_receivable'] for item in data)
    total_overdue = sum(item['total_overdue_amount'] for item in data)
    total_customers = len(data)
    high_risk_customers = sum(1 for item in data if item['risk_level'] == 'High')
    return {
        'total_receivable': total_receivable,
        'total_overdue': total_overdue,
        'total_customers': total_customers,
        'high_risk_customers': high_risk_customers
    }

@st.cache_data(ttl=300)
def prepare_invoice_dataframe(data):
    """Prepare invoice dataframe with caching."""
    all_invoices_list = []
    for customer in data:
        for inv in customer['invoices_details']:
            inv_copy = inv.copy()
            inv_copy['customer_name'] = customer['customer_name']
            all_invoices_list.append(inv_copy)
    return pd.DataFrame(all_invoices_list)

def create_metric_card(label, value, delta=None, delta_color="normal"):
    delta_html = ""
    if delta:
        color_class = "delta-pos" if (delta_color == "normal" and delta.startswith("+")) or (delta_color == "inverse" and delta.startswith("-")) else "delta-neg"
        delta_html = f'<div class="metric-delta {color_class}">{delta}</div>'
    
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">{label}</div>
        <div class="metric-value">{value}</div>
        {delta_html}
    </div>
    """, unsafe_allow_html=True)

# --- Sidebar ---
with st.sidebar:
    st.title("💰 InvoiceHub")
    st.markdown("Professional Billing Dashboard")
    st.markdown("---")
    
    # Navigation
    selection = st.radio(
        "Navigation", 
        ["Dashboard Overview", "Customer Analysis"], 
        index=0 if st.session_state['view_mode'] == "Dashboard Overview" else 1,
        key="sidebar_nav"
    )
    
    st.markdown("---")
    st.caption("v2.0.0 | Premium Edition")

# Sync sidebar with session state
if selection != st.session_state['view_mode']:
    st.session_state['view_mode'] = selection
    if selection == "Customer Analysis":
         st.session_state['is_loading'] = True
    st.rerun()

# --- Main Content ---

if st.session_state['view_mode'] == "Dashboard Overview":
    st.title("📊 Dashboard Overview")
    st.markdown("Real-time financial insights and performance metrics.")
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Aggregate Metrics (cached)
    metrics = calculate_aggregate_metrics(data)

    # Display Metrics in Custom Cards
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        create_metric_card("Total Receivable", format_currency(metrics['total_receivable']), "+12% vs last month")
    with col2:
        create_metric_card("Total Overdue", format_currency(metrics['total_overdue']), "+5% vs last month", delta_color="inverse")
    with col3:
        create_metric_card("Active Customers", str(metrics['total_customers']), "+2 new this month")
    with col4:
        create_metric_card("High Risk Clients", str(metrics['high_risk_customers']), "-1 vs last month", delta_color="inverse")

    st.markdown("<br>", unsafe_allow_html=True)

    # Charts Section
    c1, c2 = st.columns([3, 2])
    
    with c1:
        st.subheader("📈 Revenue & Overdue Trends")
        # Prepare data for trend chart (simulated for demo purposes as we don't have historical snapshots)
        # We'll use invoice generation dates to show volume over time
        all_invoices = []
        for customer in data:
            for inv in customer['invoices_details']:
                all_invoices.append(inv)
        df_inv = pd.DataFrame(all_invoices)
        df_inv['invoice_generated_date'] = pd.to_datetime(df_inv['invoice_generated_date'])
        df_trend = df_inv.groupby(pd.Grouper(key='invoice_generated_date', freq='M')).sum(numeric_only=True).reset_index()
        
        fig_trend = px.line(
            df_trend, 
            x='invoice_generated_date', 
            y='invoice_amount', 
            markers=True,
            line_shape='spline',
            title="Monthly Invoice Volume",
            color_discrete_sequence=['#3b82f6']
        )
        fig_trend.update_layout(
            plot_bgcolor='#1e1e2e',
            paper_bgcolor='#1e1e2e',
            xaxis_title="Date",
            yaxis_title="Amount ($)",
            hovermode="x unified",
            font=dict(color='#cbd5e1')
        )
        fig_trend.update_xaxes(showgrid=False, color='#cbd5e1')
        fig_trend.update_yaxes(showgrid=True, gridcolor='rgba(255,255,255,0.1)', color='#cbd5e1')
        st.plotly_chart(fig_trend, use_container_width=True)

    with c2:
        st.subheader("⚠️ Risk Distribution")
        df_overview = pd.DataFrame(data)
        risk_counts = df_overview['risk_level'].value_counts().reset_index()
        risk_counts.columns = ['risk_level', 'count']
        
        fig_pie = px.pie(
            risk_counts, 
            values='count', 
            names='risk_level',
            color='risk_level',
            color_discrete_map={'High': '#ef4444', 'Medium': '#f97316', 'Low': '#22c55e'},
            title="Customer Risk Levels",
            hole=0.6
        )
        fig_pie.update_layout(
            plot_bgcolor='#1e1e2e',
            paper_bgcolor='#1e1e2e',
            showlegend=True,
            legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5, font=dict(color='#cbd5e1')),
            font=dict(color='#cbd5e1')
        )
        st.plotly_chart(fig_pie, use_container_width=True)

    # Recent Invoices Table
    st.subheader("Recent Invoices")
    
    # Prepare Table Data (cached)
    df_invoices = prepare_invoice_dataframe(data)

    # Filter
    col_filter, _ = st.columns([2, 4])
    with col_filter:
        status_filter = st.multiselect(
            "Filter by Status", 
            options=df_invoices['payment_status'].unique(), 
            default=df_invoices['payment_status'].unique()
        )
    
    if not df_invoices.empty:
        df_filtered = df_invoices[df_invoices['payment_status'].isin(status_filter)]
        
        # Custom Table Header
        h1, h2, h3, h4, h5, h6 = st.columns([1.5, 2, 1.5, 1.5, 1.5, 1])
        h1.markdown("**Invoice #**")
        h2.markdown("**Client**")
        h3.markdown("**Due Date**")
        h4.markdown("**Amount**")
        h5.markdown("**Status**")
        h6.markdown("**Action**")
        st.markdown("<hr style='margin: 0.5rem 0; border-color: #e2e8f0;'>", unsafe_allow_html=True)
        
        for index, row in df_filtered.iterrows():
            c1, c2, c3, c4, c5, c6 = st.columns([1.5, 2, 1.5, 1.5, 1.5, 1])
            c1.write(row['invoice_number'])
            c2.write(row['customer_name'])
            c3.write(row['invoice_due_date'])
            c4.write(format_currency(row['invoice_amount']))
            
            # Status Badge
            status = row['payment_status']
            if status == "Unpaid" and row['days_past_due'] > 0:
                bg_color = "linear-gradient(135deg, #dc2626 0%, #991b1b 100%)"
                text_color = "white"
            elif status == "Paid":
                bg_color = "linear-gradient(135deg, #10b981 0%, #059669 100%)"
                text_color = "white"
            else:
                bg_color = "linear-gradient(135deg, #f97316 0%, #ea580c 100%)"
                text_color = "white"
            
            c5.markdown(f"""
            <span style='background: {bg_color}; color: {text_color}; padding: 4px 12px; border-radius: 12px; font-size: 12px; font-weight: 600; box-shadow: 0 2px 8px rgba(0,0,0,0.3);'>
                {status}
            </span>
            """, unsafe_allow_html=True)
            
            if c6.button("Analyze", key=f"btn_{row['invoice_number']}"):
                switch_to_analysis(row['customer_name'])
                st.rerun()
            
            st.markdown("<hr style='margin: 0.5rem 0; border-color: #f1f5f9;'>", unsafe_allow_html=True)

    else:
        st.info("No invoices found matching criteria.")

elif st.session_state['view_mode'] == "Customer Analysis":
    
    # Check if we need to simulate loading
    if st.session_state.get('is_loading', False):
        simulate_api_call()
        st.session_state['is_loading'] = False
        st.rerun()

    # Top Bar
    col_title, col_sel = st.columns([3, 1])
    with col_title:
        st.title("🔍 Billing Analysis")
    with col_sel:
        customer_names = [item['customer_name'] for item in data]
        try:
            current_index = customer_names.index(st.session_state['selected_customer'])
        except ValueError:
            current_index = 0
            
        selected_customer_name = st.selectbox(
            "Select Client", 
            customer_names, 
            index=current_index,
            key="customer_selector",
            label_visibility="collapsed"
        )
    
    # Update session state if dropdown changes
    if selected_customer_name != st.session_state['selected_customer']:
        st.session_state['selected_customer'] = selected_customer_name
        st.session_state['is_loading'] = True
        st.rerun()
    
    # Get selected customer data
    customer_data = next(item for item in data if item['customer_name'] == st.session_state['selected_customer'])
    
    # Customer Header Card
    st.markdown(f"""
    <div style="background: linear-gradient(145deg, #1e1e2e 0%, #252538 100%); padding: 24px; border-radius: 16px; border: 1px solid rgba(59, 130, 246, 0.3); margin-bottom: 24px; box-shadow: 0 8px 32px rgba(0,0,0,0.4);">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <div>
                <h2 style="margin: 0; color: #f1f5f9; text-shadow: 0 2px 10px rgba(59, 130, 246, 0.3);">{customer_data['customer_name']}</h2>
                <p style="margin: 4px 0 0 0; color: #94a3b8;">Customer ID: {customer_data['customer_id']} • <span style="color: #60a5fa;">Premium Tier</span></p>
            </div>
            <div style="text-align: right;">
                <div style="background: {'linear-gradient(135deg, #dc2626 0%, #991b1b 100%)' if customer_data['risk_level'] == 'High' else 'linear-gradient(135deg, #f97316 0%, #ea580c 100%)' if customer_data['risk_level'] == 'Medium' else 'linear-gradient(135deg, #10b981 0%, #059669 100%)'}; 
                            color: white; 
                            padding: 8px 16px; border-radius: 20px; font-weight: 700; display: inline-block; box-shadow: 0 4px 15px rgba(0,0,0,0.3);">
                    {customer_data['risk_level']} Risk
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Key Stats Row
    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        create_metric_card("Client Score", f"{customer_data['client_score']:.2f}", "Reliability Index")
    with c2:
        # Sentiment Score with Trend
        trend_icon = "↗" if customer_data['sentiment_trend'] == "Rising" else "↘" if customer_data['sentiment_trend'] == "Falling" else "→"
        trend_color = "delta-pos" if customer_data['sentiment_trend'] == "Rising" else "delta-neg" if customer_data['sentiment_trend'] == "Falling" else ""
        
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Sentiment Score</div>
            <div class="metric-value">{customer_data['sentiment_score']:.2f}</div>
            <div class="metric-delta {trend_color}">{trend_icon} {customer_data['sentiment_trend']}</div>
        </div>
        """, unsafe_allow_html=True)
        
    with c3:
        create_metric_card("Total Invoiced", format_currency(customer_data['total_invoice_amount']))
    with c4:
        create_metric_card("Outstanding", format_currency(customer_data['total_receivable']))
    with c5:
        create_metric_card("Overdue", format_currency(customer_data['total_overdue_amount']), "Critical", delta_color="inverse")

    st.markdown("<br>", unsafe_allow_html=True)

    # Analysis Section
    row1_1, row1_2 = st.columns([2, 1])
    
    with row1_1:
        st.subheader("📅 Aging Analysis")
        buckets = customer_data['overdue_buckets']
        bucket_df = pd.DataFrame([
            {"Bucket": k, "Amount": v["amount"]} for k, v in buckets.items()
        ])
        
        fig_aging = px.bar(
            bucket_df, 
            x='Bucket', 
            y='Amount', 
            text_auto='.2s',
            color='Amount',
            color_continuous_scale='Reds'
        )
        fig_aging.update_layout(
            plot_bgcolor='#1e1e2e',
            paper_bgcolor='#1e1e2e',
            xaxis_title="",
            yaxis_title="Amount ($)",
            showlegend=False,
            font=dict(color='#cbd5e1')
        )
        fig_aging.update_xaxes(color='#cbd5e1')
        fig_aging.update_yaxes(showgrid=True, gridcolor='rgba(255,255,255,0.1)', color='#cbd5e1')
        st.plotly_chart(fig_aging, use_container_width=True)

    with row1_2:
        st.subheader("💡 AI Insights")
        with st.container():
            st.info(f"**Summary:** {customer_data['analysis_summary']}")
            st.markdown("**Key Factors:**")
            for factor in customer_data['key_factors']:
                st.markdown(f"- {factor}")
            st.markdown("**Recommendations:**")
            for rec in customer_data['recommendations']:
                st.success(f"✓ {rec}")

    # Invoices Table
    st.markdown("---")
    c_head, c_btn = st.columns([4, 1])
    with c_head:
        st.subheader("Invoice History")
    with c_btn:
        # Download Button
        csv = pd.DataFrame(customer_data['invoices_details']).to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Download Report",
            data=csv,
            file_name=f"{customer_data['customer_name']}_report.csv",
            mime="text/csv",
        )

    inv_df = pd.DataFrame(customer_data['invoices_details'])
    if not inv_df.empty:
        st.dataframe(
            inv_df[['invoice_number', 'project_name', 'invoice_generated_date', 'invoice_due_date', 'invoice_amount', 'outstanding_amount', 'payment_status', 'days_past_due']],
            use_container_width=True,
            hide_index=True,
            column_config={
                "invoice_amount": st.column_config.NumberColumn("Amount", format="$%.2f"),
                "outstanding_amount": st.column_config.NumberColumn("Outstanding", format="$%.2f"),
            }
        )
    else:
        st.write("No invoices found for this customer.")
