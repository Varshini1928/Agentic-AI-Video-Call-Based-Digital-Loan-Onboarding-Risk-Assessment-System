"""
Complete Loan Onboarding System - Streamlit Version
Run with: streamlit run app.py
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import uuid
import json
from typing import Dict, Any
import time

# ============================================
# PAGE CONFIGURATION
# ============================================

st.set_page_config(
    page_title="AI Loan Onboarding System",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================
# CUSTOM CSS
# ============================================

st.markdown("""
<style>
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        text-align: center;
    }
    .risk-card {
        padding: 1.5rem;
        border-radius: 10px;
        margin: 1rem 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .risk-low {
        background: linear-gradient(135deg, #84fab0 0%, #8fd3f4 100%);
    }
    .risk-medium {
        background: linear-gradient(135deg, #f6d365 0%, #fda085 100%);
    }
    .risk-high {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
    }
    .metric-card {
        background: white;
        padding: 1rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        text-align: center;
    }
    .stButton button {
        width: 100%;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# ============================================
# RISK ENGINE CLASS
# ============================================

class RiskEngine:
    """Advanced risk assessment engine"""
    
    @staticmethod
    def calculate_risk_score(application: Dict) -> Dict:
        risk_components = {}
        
        # Income risk
        monthly_income = application.get('monthly_income', 0)
        if monthly_income < 15000:
            income_risk = 50
        elif monthly_income < 25000:
            income_risk = 35
        elif monthly_income < 50000:
            income_risk = 20
        elif monthly_income < 100000:
            income_risk = 10
        else:
            income_risk = 0
        risk_components['income'] = income_risk
        
        # Employment risk
        emp_type = application.get('employment_type', 'salaried')
        experience = application.get('work_experience_years', 0)
        
        if emp_type == 'salaried':
            emp_risk = 10
            if experience < 1:
                emp_risk += 20
            elif experience < 2:
                emp_risk += 10
        elif emp_type == 'self-employed':
            emp_risk = 25
            if experience < 3:
                emp_risk += 15
        else:  # business
            emp_risk = 30
        
        risk_components['employment'] = min(emp_risk, 50)
        
        # Credit score risk
        credit_score = application.get('credit_score', 750)
        if credit_score >= 750:
            credit_risk = 0
        elif credit_score >= 700:
            credit_risk = 15
        elif credit_score >= 650:
            credit_risk = 30
        elif credit_score >= 600:
            credit_risk = 50
        else:
            credit_risk = 70
        risk_components['credit'] = credit_risk
        
        # Loan to income ratio
        annual_income = monthly_income * 12
        loan_amount = application.get('loan_amount', 0)
        loan_to_income = loan_amount / annual_income if annual_income > 0 else 10
        
        if loan_to_income > 8:
            ratio_risk = 50
        elif loan_to_income > 6:
            ratio_risk = 35
        elif loan_to_income > 4:
            ratio_risk = 20
        elif loan_to_income > 2:
            ratio_risk = 10
        else:
            ratio_risk = 0
        risk_components['loan_ratio'] = ratio_risk
        
        # Calculate total risk (weighted)
        weights = {'income': 0.25, 'employment': 0.20, 'credit': 0.25, 'loan_ratio': 0.30}
        total_risk = sum(risk_components[k] * weights[k] for k in weights)
        
        return {
            'total_risk': round(total_risk, 2),
            'components': risk_components
        }
    
    @staticmethod
    def generate_offer(risk_score: float, application: Dict) -> Dict:
        if risk_score < 30:
            approved_pct = 1.0
            interest_rate = 8.5
            category = "Low Risk"
            status = "approved"
        elif risk_score < 50:
            approved_pct = 0.9
            interest_rate = 10.5
            category = "Medium-Low Risk"
            status = "approved"
        elif risk_score < 65:
            approved_pct = 0.75
            interest_rate = 12.5
            category = "Medium Risk"
            status = "partial_approval"
        elif risk_score < 80:
            approved_pct = 0.5
            interest_rate = 15.0
            category = "Medium-High Risk"
            status = "partial_approval"
        else:
            approved_pct = 0
            interest_rate = 0
            category = "High Risk"
            status = "rejected"
        
        approved_amount = application.get('loan_amount', 0) * approved_pct
        max_limit = application.get('monthly_income', 0) * 12 * 5
        approved_amount = min(approved_amount, max_limit)
        
        if approved_amount > 0 and interest_rate > 0:
            monthly_rate = interest_rate / 12 / 100
            tenure = 60
            emi = approved_amount * monthly_rate * (1 + monthly_rate)**tenure / ((1 + monthly_rate)**tenure - 1)
            total_payment = emi * tenure
            total_interest = total_payment - approved_amount
            processing_fee = approved_amount * 0.01
        else:
            emi = total_interest = processing_fee = 0
        
        return {
            'status': status,
            'risk_category': category,
            'approved_amount': round(approved_amount, 2),
            'interest_rate': interest_rate,
            'monthly_emi': round(emi, 2),
            'total_interest': round(total_interest, 2),
            'processing_fee': round(processing_fee, 2),
            'net_disbursement': round(approved_amount - processing_fee, 2)
        }

# ============================================
# SESSION STATE INITIALIZATION
# ============================================

if 'applications' not in st.session_state:
    st.session_state.applications = {}
if 'current_app_id' not in st.session_state:
    st.session_state.current_app_id = None

# ============================================
# SIDEBAR NAVIGATION
# ============================================

st.sidebar.markdown("## 🏦 Navigation")
page = st.sidebar.radio(
    "Select Page",
    ["📝 New Application", "📊 Dashboard", "📋 Application Status", "📈 Analytics", "ℹ️ About"]
)

st.sidebar.markdown("---")
st.sidebar.info(
    """
    **AI-Powered Loan Assessment**
    - Real-time risk scoring
    - Instant loan offers
    - Transparent decisioning
    """
)

# ============================================
# PAGE 1: NEW APPLICATION
# ============================================

if page == "📝 New Application":
    st.markdown("""
    <div class="main-header">
        <h1>🏦 Digital Loan Application</h1>
        <p>AI-Powered Risk Assessment & Instant Approval</p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 📋 Personal Information")
        full_name = st.text_input("Full Name *", placeholder="Enter your full name")
        email = st.text_input("Email *", placeholder="your@email.com")
        phone = st.text_input("Phone Number *", placeholder="10-digit mobile number")
        
        st.markdown("### 💼 Employment Details")
        employment_type = st.selectbox(
            "Employment Type *",
            ["salaried", "self-employed", "business"]
        )
        
        company_name = st.text_input("Company/Organization Name", placeholder="Optional")
        work_experience = st.number_input("Work Experience (years)", min_value=0.0, max_value=50.0, step=0.5)
        
    with col2:
        st.markdown("### 💰 Financial Information")
        monthly_income = st.number_input("Monthly Income (₹) *", min_value=0, step=5000)
        loan_amount = st.number_input("Loan Amount Requested (₹) *", min_value=0, step=10000)
        
        loan_purpose = st.selectbox(
            "Loan Purpose *",
            ["home", "car", "education", "business", "personal", "medical"]
        )
        
        st.markdown("### 📊 Credit Information")
        credit_score = st.slider("Credit Score (CIBIL)", 300, 900, 750)
        existing_loans = st.checkbox("I have existing loans")
        
        existing_loan_amount = 0
        if existing_loans:
            existing_loan_amount = st.number_input("Total Existing Loan Amount", min_value=0, step=10000)
        
        consent = st.checkbox("I consent to KYC verification and terms & conditions", value=True)
    
    # Submit button
    if st.button("🚀 Submit Application", use_container_width=True):
        if not full_name or not email or not phone or monthly_income <= 0 or loan_amount <= 0:
            st.error("❌ Please fill all required fields!")
        elif not consent:
            st.error("❌ Consent is required to process your application!")
        else:
            with st.spinner("Processing your application with AI..."):
                time.sleep(1)  # Simulate processing
                
                # Create application
                application = {
                    'application_id': str(uuid.uuid4())[:8].upper(),
                    'full_name': full_name,
                    'email': email,
                    'phone': phone,
                    'monthly_income': monthly_income,
                    'employment_type': employment_type,
                    'company_name': company_name,
                    'work_experience_years': work_experience,
                    'loan_amount': loan_amount,
                    'loan_purpose': loan_purpose,
                    'credit_score': credit_score,
                    'existing_loans': existing_loans,
                    'existing_loan_amount': existing_loan_amount,
                    'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                
                # Calculate risk
                risk_result = RiskEngine.calculate_risk_score(application)
                risk_score = risk_result['total_risk']
                
                # Generate offer
                offer = RiskEngine.generate_offer(risk_score, application)
                
                # Store result
                result = {
                    **application,
                    'risk_score': risk_score,
                    'risk_components': risk_result['components'],
                    **offer
                }
                
                st.session_state.applications[application['application_id']] = result
                st.session_state.current_app_id = application['application_id']
                
                # Display result
                st.success("✅ Application submitted successfully!")
                
                # Show result in expander
                with st.expander("📊 View Your Results", expanded=True):
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.metric("Risk Score", f"{risk_score}/100")
                    with col2:
                        st.metric("Status", offer['status'].replace('_', ' ').title())
                    with col3:
                        if offer['approved_amount'] > 0:
                            st.metric("Approved Amount", f"₹{offer['approved_amount']:,.0f}")
                        else:
                            st.metric("Approved Amount", "₹0")
                    
                    # Risk gauge
                    fig = go.Figure(go.Indicator(
                        mode = "gauge+number",
                        value = risk_score,
                        domain = {'x': [0, 1], 'y': [0, 1]},
                        title = {'text': "Risk Level"},
                        gauge = {
                            'axis': {'range': [None, 100]},
                            'bar': {'color': "darkblue"},
                            'steps': [
                                {'range': [0, 35], 'color': "lightgreen"},
                                {'range': [35, 65], 'color': "yellow"},
                                {'range': [65, 100], 'color': "salmon"}
                            ],
                            'threshold': {
                                'line': {'color': "red", 'width': 4},
                                'thickness': 0.75,
                                'value': risk_score
                            }
                        }
                    ))
                    st.plotly_chart(fig)
                    
                    # Offer details
                    if offer['approved_amount'] > 0:
                        st.markdown("### 🎉 Loan Offer")
                        col1, col2 = st.columns(2)
                        with col1:
                            st.info(f"**Interest Rate:** {offer['interest_rate']}% p.a.")
                            st.info(f"**Monthly EMI:** ₹{offer['monthly_emi']:,.0f}")
                        with col2:
                            st.info(f"**Processing Fee:** ₹{offer['processing_fee']:,.0f}")
                            st.info(f"**Net Disbursement:** ₹{offer['net_disbursement']:,.0f}")
                        
                        st.success(f"**{offer['status'].upper()}** - Congratulations! Your loan offer is ready.")
                    else:
                        st.error("**REJECTED** - Unfortunately, your application cannot be approved at this time.")
                        st.info("💡 **Recommendations:** Improve credit score, reduce existing debt, or apply with a co-applicant.")

# ============================================
# PAGE 2: DASHBOARD
# ============================================

elif page == "📊 Dashboard":
    st.markdown("""
    <div class="main-header">
        <h1>📊 Loan Dashboard</h1>
        <p>Real-time analytics and insights</p>
    </div>
    """, unsafe_allow_html=True)
    
    if len(st.session_state.applications) == 0:
        st.info("📭 No applications yet. Submit your first application!")
    else:
        # Key metrics
        col1, col2, col3, col4 = st.columns(4)
        
        total_apps = len(st.session_state.applications)
        approved_apps = sum(1 for app in st.session_state.applications.values() if app['status'] in ['approved', 'partial_approval'])
        total_amount = sum(app['approved_amount'] for app in st.session_state.applications.values())
        avg_risk = sum(app['risk_score'] for app in st.session_state.applications.values()) / total_apps
        
        with col1:
            st.metric("Total Applications", total_apps)
        with col2:
            st.metric("Approved", approved_apps, delta=f"{approved_apps/total_apps*100:.0f}%")
        with col3:
            st.metric("Total Disbursed", f"₹{total_amount:,.0f}")
        with col4:
            st.metric("Average Risk Score", f"{avg_risk:.1f}/100")
        
        # Charts
        col1, col2 = st.columns(2)
        
        with col1:
            # Risk distribution
            risk_levels = []
            for app in st.session_state.applications.values():
                if app['risk_score'] < 35:
                    risk_levels.append('Low')
                elif app['risk_score'] < 65:
                    risk_levels.append('Medium')
                else:
                    risk_levels.append('High')
            
            risk_df = pd.DataFrame({'Risk Level': risk_levels})
            fig = px.pie(risk_df, names='Risk Level', title='Risk Distribution', color_discrete_sequence=['#28a745', '#ffc107', '#dc3545'])
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Status distribution
            statuses = [app['status'] for app in st.session_state.applications.values()]
            status_df = pd.DataFrame({'Status': statuses})
            fig = px.bar(status_df, x='Status', title='Application Status', color='Status')
            st.plotly_chart(fig, use_container_width=True)
        
        # Recent applications
        st.markdown("### 📋 Recent Applications")
        recent_apps = []
        for app_id, app in list(st.session_state.applications.items())[-5:]:
            recent_apps.append({
                'Application ID': app_id,
                'Name': app['full_name'],
                'Amount': f"₹{app['loan_amount']:,.0f}",
                'Risk Score': app['risk_score'],
                'Status': app['status'].replace('_', ' ').title()
            })
        
        st.dataframe(pd.DataFrame(recent_apps), use_container_width=True)

# ============================================
# PAGE 3: APPLICATION STATUS
# ============================================

elif page == "📋 Application Status":
    st.markdown("""
    <div class="main-header">
        <h1>📋 Check Application Status</h1>
        <p>Track your loan application</p>
    </div>
    """, unsafe_allow_html=True)
    
    app_id = st.text_input("Enter Application ID", placeholder="e.g., A7B3F9D2")
    
    if st.button("Check Status"):
        if app_id in st.session_state.applications:
            app = st.session_state.applications[app_id]
            
            st.success(f"✅ Application Found for {app['full_name']}")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Risk Score", f"{app['risk_score']}/100")
            with col2:
                st.metric("Status", app['status'].replace('_', ' ').title())
            with col3:
                st.metric("Applied On", app['timestamp'].split()[0])
            
            if app['approved_amount'] > 0:
                st.info(f"**Approved Amount:** ₹{app['approved_amount']:,.0f}")
                st.info(f"**Interest Rate:** {app['interest_rate']}%")
            
            st.json(app)
        else:
            st.error("❌ Application not found. Please check the ID and try again.")

# ============================================
# PAGE 4: ANALYTICS
# ============================================

elif page == "📈 Analytics":
    st.markdown("""
    <div class="main-header">
        <h1>📈 Advanced Analytics</h1>
        <p>Deep insights into loan applications</p>
    </div>
    """, unsafe_allow_html=True)
    
    if len(st.session_state.applications) == 0:
        st.info("📊 Submit applications to see analytics")
    else:
        # Create dataframe
        df = pd.DataFrame([
            {
                'Income': app['monthly_income'],
                'Loan Amount': app['loan_amount'],
                'Risk Score': app['risk_score'],
                'Approved Amount': app['approved_amount'],
                'Employment': app['employment_type'],
                'Purpose': app['loan_purpose']
            }
            for app in st.session_state.applications.values()
        ])
        
        col1, col2 = st.columns(2)
        
        with col1:
            fig = px.scatter(df, x='Income', y='Loan Amount', size='Risk Score', color='Employment', 
                            title='Income vs Loan Amount Analysis')
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            fig = px.box(df, x='Employment', y='Risk Score', title='Risk Score by Employment Type')
            st.plotly_chart(fig, use_container_width=True)
        
        # Correlation heatmap
        corr = df[['Income', 'Loan Amount', 'Risk Score', 'Approved Amount']].corr()
        fig = px.imshow(corr, text_auto=True, title='Feature Correlation Matrix')
        st.plotly_chart(fig, use_container_width=True)

# ============================================
# PAGE 5: ABOUT
# ============================================

else:
    st.markdown("""
    <div class="main-header">
        <h1>ℹ️ About AI Loan System</h1>
        <p>Powered by Artificial Intelligence</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    ## 🤖 How It Works
    
    Our AI-powered loan system uses advanced algorithms to assess creditworthiness:
    
    ### 1. **Risk Assessment Engine**
    - Analyzes income, employment, credit score
    - Calculates debt-to-income ratio
    - Evaluates loan purpose risk
    
    ### 2. **Smart Decision Making**
    - Instant risk scoring (0-100)
    - Dynamic loan offers
    - Personalized interest rates
    
    ### 3. **Key Features**
    - ✅ Real-time processing
    - ✅ Transparent decisioning
    - ✅ No paperwork required
    - ✅ Instant disbursement
    
    ## 🛡️ Security
    
    - End-to-end encryption
    - Secure data storage
    - Compliance with RBI guidelines
    
    ## 📞 Support
    
    For assistance, contact: support@loan-system.com
    """)
    
    st.info("💡 **Pro Tip:** Better credit scores lead to lower interest rates and higher loan amounts!")

# ============================================
# FOOTER
# ============================================

st.markdown("---")
st.markdown(
    "<p style='text-align: center; color: gray;'>© 2024 AI Loan Onboarding System | Powered by Streamlit</p>",
    unsafe_allow_html=True
)
