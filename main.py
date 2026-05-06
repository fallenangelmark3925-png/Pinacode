import streamlit as st
import plotly.express as px
from datetime import date

import auth
from database import load_data, save_expense, delete_expense, EXPENSE_CATEGORIES

st.set_page_config(page_title="FinTrack Pro", page_icon="💎", layout="wide")
auth.init_auth()

st.markdown("""
    <style>
    .stApp {
        background: linear-gradient(rgba(0,0,0,0.6), rgba(0,0,0,0.6)), 
                    url("https://images.unsplash.com/photo-1550745165-9bc0b252726f?ixlib=rb-4.0.3&auto=format&fit=crop&w=1920&q=80");
        background-size: cover; background-attachment: fixed;
    }
    div[data-tested="stMetric"], .stForm, .stDataFrame, .stPlotlyChart {
        background: rgba(255, 255, 255, 0.08) !important;
        backdrop-filter: blur(12px); border-radius: 15px; padding: 20px; margin-bottom: 10px;
    }
    h1, h2, h3, p, span, label { color: #ffffff !important; text-shadow: 1px 1px 2px rgba(0,0,0,0.8); }
    section[data-tested="stSidebar"] { background-color: rgba(0, 0, 0, 0.😎 !important; }
    </style>
    """, unsafe_allow_html=True)

if not st.session_state.logged_in:
    auth.render_login_page()
else:
    current_user = st.session_state.username

    st.sidebar.image("https://cdn-icons-png.flaticon.com/512/3135/3135706.png", width=80)
    st.sidebar.title(f"👤 User: {current_user}")

    if st.sidebar.button("🚪 Log Out Systems", type="primary"):
        auth.logout()

    st.sidebar.markdown("---")

    with st.sidebar.form(key='expense_form', clear_on_submit=True):
        exp_date = st.date_input("Transaction Date", date.today())
        exp_category = st.selectbox("Category", EXPENSE_CATEGORIES)
        exp_desc = st.text_input("Note")
        exp_amount = st.number_input("Amount (₱)", min_value=0.0, step=100.0)

        if st.form_submit_button(label='Add'):
            if exp_amount > 0:
                save_expense({
                    "date": exp_date,
                    "category": exp_category,
                    "description": exp_desc,
                    "amount": float(exp_amount)
                }, current_user)
                st.success("Entry Saved")
                st.rerun()
            else:
                st.error("Amount must be greater than 0")

    st.title("💎 Executive Wealth Dashboard")
    df = load_data(current_user)

    if df.empty:
        st.info(f"System Ready. Welcome {current_user}! Please input your first financial record in the sidebar.")
    else:
        df['month_year'] = df['date'].dt.strftime('%B %Y')
        current_month_str = date.today().strftime('%B %Y')

        m1, m2, m3 = st.columns(3, gap="large")
        total_val = df['amount'].sum()
        monthly_val = df[df['month_year'] == current_month_str]['amount'].sum()

        m1.metric("Lifetime Volume", f"₱{total_val:,.2f}")
        m2.metric("Current Month", f"₱{monthly_val:,.2f}")
        m3.metric("Records", len(df))

        st.markdown("---")
        c1, c2 = st.columns(2, gap="large")

        with c1:
            st.subheader("📊 Allocation")
            cat_df = df.groupby('category')['amount'].sum().reset_index()
            fig = px.pie(cat_df, values='amount', names='category', hole=0.5,
                         color_discrete_sequence=px.colors.sequential.Electric)
            fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color="white")
            st.plotly_chart(fig, use_container_width=True)

        with c2:
            st.subheader("📈 Performance Trend")
            trend_df = df.groupby(df['date'].dt.date)['amount'].sum().reset_index()
            trend_df.columns = ['date', 'amount']
            trend_df = trend_df.sort_values('date')

            fig2 = px.area(trend_df, x='date', y='amount', line_shape="spline", color_discrete_sequence=['#00d4ff'])
            fig2.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color="white")
            fig2.update_xaxes(type='category')
            st.plotly_chart(fig2, use_container_width=True)

        st.markdown("---")
        st.subheader("📝 Ledger History & Audit Control")

        h1, h2, h3, h4, h5 = st.columns([1.5, 2, 3, 1.5, 1])
        h1.write("*Date*")
        h2.write("*Category*")
        h3.write("*Description*")
        h4.write("*Amount*")
        h5.write("*Delete*")

        display_df = df.sort_values(by='date', ascending=False)

        for index, row in display_df.iterrows():
            with st.container():
                r1, r2, r3, r4, r5 = st.columns([1.5, 2, 3, 1.5, 1])
                r1.write(f"{row['date'].date()}")
                r2.write(row['category'])
                r3.write(row['description'] if row['description'] else "---")
                r4.write(f"₱{row['amount']:,.2f}")

                if r5.button("🗑️", key=f"del_{row['id']}", help="Delete entry permanently"):
                    delete_expense(row['id'], current_user)
                    st.rerun()

    st.markdown("<br><center>FinTrack Pro © 2026 | Encrypted Data Environment</center>", unsafe_allow_html=True)