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

# --- Custom CSS for Premium Styling ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
        color: #e2e8f0; /* Lighter text for dark theme */
    }
    .stApp {
        background-color: #0f172a; /* Dark blue background */
    }
    .metric-card {
        background-color: #1e293b; /* Darker card background */
        padding: 24px;
        border-radius: 16px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.2);
        border: 1px solid #334155;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        height: 100%;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    .metric-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 25px rgba(0,0,0,0.3);
    }
    .metric-value {
        font-size: 32px;
        font-weight: 700;
        color: #f8fafc; /* White text for values */
        margin-bottom: 4px;
    }
    .metric-label {
        font-size: 14px;
        color: #94a3b8; /* Lighter grey for labels */
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    .metric-delta {
        font-size: 13px;
        font-weight: 600;
        margin-top: 8px;
    }
    .delta-pos { color: #22c55e; } /* Brighter green */
    .delta-neg { color: #f87171; } /* Brighter red */
    
    /* Custom Button Styling */
    .stButton button {
        width: 100%;
        border-radius: 8px;
        font-weight: 600;
        padding: 0.5rem 1rem;
        transition: all 0.2s;
    }
    
    /* Table Styling */
    .stDataFrame {
        border-radius: 12px;
        overflow: hidden;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    
    /* Header Styling */
    h1, h2, h3 {
        color: #f8fafc; /* White text for headers */
        font-weight: 700;
    }
    
    /* Sidebar Styling */
    [data-testid="stSidebar"] {
        background-color: #1e293b; /* Dark sidebar */
        border-right: 1px solid #334155;
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
    with st.spinner('Fetching billing insights from server...'):
        time.sleep(1.2)  # Simulate latency

def switch_to_analysis(customer_name):
    st.session_state['selected_customer'] = customer_name
    st.session_state['view_mode'] = "Customer Analysis"
    st.session_state['is_loading'] = True

# --- Helper Functions ---
def format_currency(value):
    return f"${value:,.2f}"

def create_metric_card(label, value, delta=None, delta_color="normal", trend_icon=None):
    delta_html = ""
    if delta:
        color_class = "delta-pos" if (delta_color == "normal" and (not delta or delta.startswith("+"))) or (delta_color == "inverse" and delta.startswith("-")) else "delta-neg"
        icon_html = f"{trend_icon} " if trend_icon else ""
        delta_html = f'<div class="metric-delta {color_class}">{icon_html}{delta}</div>'

    st.markdown(f"""
    <div class="metric-card">
        <div>
            <div class="metric-label">{label}</div>
            <div class="metric-value">{value}</div>
        </div>
        {delta_html if delta else "<div></div>"}
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

    # --- Cached Metric Calculations ---
    @st.cache_data
    def get_aggregate_metrics(_data):
        total_receivable = sum(item['total_receivable'] for item in _data)
        total_overdue = sum(item['total_overdue_amount'] for item in _data)
        total_customers = len(_data)
        high_risk_customers = sum(1 for item in _data if item['risk_level'] == 'High')
        return total_receivable, total_overdue, total_customers, high_risk_customers

    @st.cache_data
    def prepare_trend_data(_data):
        all_invoices = [inv for customer in _data for inv in customer['invoices_details']]
        df_inv = pd.DataFrame(all_invoices)
        df_inv['invoice_generated_date'] = pd.to_datetime(df_inv['invoice_generated_date'])
        return df_inv.groupby(pd.Grouper(key='invoice_generated_date', freq='M')).sum(numeric_only=True).reset_index()

    total_receivable, total_overdue, total_customers, high_risk_customers = get_aggregate_metrics(data)
    
    # Display Metrics in Custom Cards
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        create_metric_card("Total Receivable", format_currency(total_receivable), "+12% vs last month")
    with col2:
        create_metric_card("Total Overdue", format_currency(total_overdue), "+5% vs last month", delta_color="inverse")
    with col3:
        create_metric_card("Active Customers", str(total_customers), "+2 new this month")
    with col4:
        create_metric_card("High Risk Clients", str(high_risk_customers), "-1 vs last month", delta_color="inverse")

    st.markdown("<br>", unsafe_allow_html=True)

    # Charts Section
    c1, c2 = st.columns([3, 2])

    with c1:
        st.subheader("📈 Revenue & Overdue Trends")
        df_trend = prepare_trend_data(data)

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
            plot_bgcolor='#1e293b',
            paper_bgcolor='#1e293b',
            xaxis_title="Date",
            yaxis_title="Amount ($)",
            hovermode="x unified",
            font_color="#e2e8f0"
        )
        fig_trend.update_xaxes(showgrid=False)
        fig_trend.update_yaxes(showgrid=True, gridcolor='#f1f5f9')
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
            plot_bgcolor='#1e293b',
            paper_bgcolor='#1e293b',
            showlegend=True,
            legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5),
            font_color="#e2e8f0"
        )
        st.plotly_chart(fig_pie, use_container_width=True)

    # Recent Invoices Table
    st.subheader("Recent Invoices")

    # Prepare Table Data
    all_invoices_list = []
    for customer in data:
        for inv in customer['invoices_details']:
            inv_copy = inv.copy()
            inv_copy['customer_name'] = customer['customer_name']
            all_invoices_list.append(inv_copy)

    df_invoices = pd.DataFrame(all_invoices_list)

    if not df_invoices.empty:
        # The filter section was removed, so we use the full df_invoices DataFrame
        df_filtered = df_invoices.copy()
        
        # --- Pagination ---
        items_per_page = 10
        total_items = len(df_filtered)
        total_pages = (total_items // items_per_page) + (1 if total_items % items_per_page > 0 else 0)
        
        if 'page_number' not in st.session_state:
            st.session_state.page_number = 1

        # Page selector
        col_nav1, col_nav2 = st.columns([4, 1])
        with col_nav2:
            page_num = st.number_input(f"Page (1-{total_pages})", min_value=1, max_value=total_pages, value=st.session_state.page_number, key="page_selector")
            st.session_state.page_number = page_num

        start_idx = (st.session_state.page_number - 1) * items_per_page
        end_idx = start_idx + items_per_page
        paginated_df = df_filtered.iloc[start_idx:end_idx]

        # --- Custom Table with Buttons ---
        # Custom Table Header
        h1, h2, h3, h4, h5, h6 = st.columns([1.5, 2, 1.5, 1.5, 1.5, 1])
        h1.markdown("**Invoice #**")
        h2.markdown("**Client**")
        h3.markdown("**Due Date**")
        h4.markdown("**Amount**")
        h5.markdown("**Status**")
        h6.markdown("**Action**")
        st.markdown("<hr style='margin: 0.5rem 0; border-color: #334155;'>", unsafe_allow_html=True)

        for index, row in paginated_df.iterrows():
            c1, c2, c3, c4, c5, c6 = st.columns([1.5, 2, 1.5, 1.5, 1.5, 1])
            c1.write(row['invoice_number'])
            c2.write(row['customer_name'])
            c3.write(row['invoice_due_date'])
            c4.write(format_currency(row['invoice_amount']))

            # Status Badge
            status = row['payment_status']
            bg_color = "#fee2e2" if status == "Unpaid" and row['days_past_due'] > 0 else "#dcfce7" if status == "Paid" else "#ffedd5"
            text_color = "#991b1b" if status == "Unpaid" and row['days_past_due'] > 0 else "#166534" if status == "Paid" else "#9a3412"
            c5.markdown(f"""
            <span style='background-color: {bg_color}; color: {text_color}; padding: 4px 8px; border-radius: 12px; font-size: 12px; font-weight: 600;'>
                {status}
            </span>
            """, unsafe_allow_html=True)

            if c6.button("Analyze", key=f"btn_{row['invoice_number']}"):
                switch_to_analysis(row['customer_name'])
                st.rerun()

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

   
    if selected_customer_name != st.session_state['selected_customer']:
        st.session_state['selected_customer'] = selected_customer_name
        st.session_state['is_loading'] = True
        st.rerun()

    
    customer_data = next(item for item in data if item['customer_name'] == st.session_state['selected_customer'])

   
    st.markdown(f"""
    <div style="background-color: #1e293b; padding: 24px; border-radius: 16px; border: 1px solid #334155; margin-bottom: 24px;">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <div>
                <h2 style="margin: 0; color: #0f172a;">{customer_data['customer_name']}</h2>
                <p style="margin: 4px 0 0 0; color: #64748b;">Customer ID: {customer_data['customer_id']} • <span style="color: #3b82f6;">Premium Tier</span></p>
            </div>
            <div style="text-align: right;">
                <div style="background-color: {'#fee2e2' if customer_data['risk_level'] == 'High' else '#ffedd5' if customer_data['risk_level'] == 'Medium' else '#dcfce7'}; 
                            color: {'#991b1b' if customer_data['risk_level'] == 'High' else '#9a3412' if customer_data['risk_level'] == 'Medium' else '#166534'}; 
                            padding: 8px 16px; border-radius: 20px; font-weight: 700; display: inline-block;">
                    {customer_data['risk_level']} Risk
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

   
    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        create_metric_card("Client Score", f"{customer_data['client_score']:.2f}", "Reliability Index")
    with c2:
        trend_icon = "↗" if customer_data['sentiment_trend'] == "Rising" else "↘" if customer_data['sentiment_trend'] == "Falling" else "→"
        delta_color = "normal" if customer_data['sentiment_trend'] == "Rising" else "inverse" if customer_data['sentiment_trend'] == "Falling" else ""
        create_metric_card("Sentiment Score", f"{customer_data['sentiment_score']:.2f}", customer_data['sentiment_trend'], delta_color=delta_color, trend_icon=trend_icon)
    with c3:
        create_metric_card("Total Invoice Amount", format_currency(customer_data['total_invoice_amount']))
    with c4:
        create_metric_card("Total Receivable", format_currency(customer_data['total_receivable']))
    with c5:
        create_metric_card("Total Overdue", format_currency(customer_data['total_overdue_amount']), "Critical Amount", delta_color="inverse")

    st.markdown("<br>", unsafe_allow_html=True)

    # Analysis Section
    row1_1, row1_2 = st.columns([2, 1])

    with row1_1:
        st.subheader(" Aging Analysis")
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
            plot_bgcolor='#1e293b',
            paper_bgcolor='#1e293b',
            xaxis_title="",
            yaxis_title="Amount ($)",
            showlegend=False,
            font_color="#e2e8f0"
        )
        fig_aging.update_yaxes(showgrid=True, gridcolor='#f1f5f9')
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
                "outstanding_amount": st.column_config.NumberColumn("Amount Receivable", format="$%.2f"),
            }
        )
    else:
        st.write("No invoices found for this customer.")