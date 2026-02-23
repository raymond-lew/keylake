"""Streamlit App for AI-Powered CRM - Full CRUD Operations"""

import streamlit as st
from datetime import datetime, timedelta, date
import pandas as pd

from database.connection import storage

# ============================================================================
# PAGE CONFIGURATION
# ============================================================================

st.set_page_config(
    page_title="Keylake",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================================
# SESSION STATE INITIALIZATION
# ============================================================================

if 'editing_contact' not in st.session_state:
    st.session_state.editing_contact = None
if 'editing_deal' not in st.session_state:
    st.session_state.editing_deal = None
if 'editing_customer' not in st.session_state:
    st.session_state.editing_customer = None
if 'editing_email' not in st.session_state:
    st.session_state.editing_email = None
if 'editing_meeting' not in st.session_state:
    st.session_state.editing_meeting = None

# ============================================================================
# CUSTOM CSS
# ============================================================================

st.markdown("""
<style>
    .metric-card {
        background-color: #f0f2f6;
        border-radius: 10px;
        padding: 20px;
        margin: 10px 0;
    }
    .stAlert {
        border-radius: 10px;
    }
    div[data-testid="stMetricValue"] {
        font-size: 2rem;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_company_name(company_id: str) -> str:
    """Get company name by ID"""
    if not company_id:
        return "N/A"
    company = storage.get_company(company_id)
    return company.get('name', 'Unknown') if company else "Unknown"


def get_contact_name(contact_id: str) -> str:
    """Get contact name by ID"""
    if not contact_id:
        return "N/A"
    contact = storage.get_contact(contact_id)
    if contact:
        return f"{contact.get('first_name', '')} {contact.get('last_name', '')}"
    return "Unknown"


def get_deal_stage_color(stage):
    """Get emoji for deal stage"""
    colors = {
        'prospecting': '🔵',
        'qualification': '🟡',
        'proposal': '🟠',
        'negotiation': '🟣',
        'closed_won': '🟢',
        'closed_lost': '🔴'
    }
    return colors.get(stage, '⚪')


def get_health_color(score):
    """Get emoji for health score"""
    if score >= 80:
        return "🟢"
    elif score >= 60:
        return "🟡"
    elif score >= 40:
        return "🟠"
    else:
        return "🔴"


def get_churn_risk_color(risk):
    """Get emoji for churn risk"""
    colors = {
        'low': '🟢',
        'medium': '🟡',
        'high': '🔴'
    }
    return colors.get(risk, '⚪')


def format_currency(value):
    """Format value as currency"""
    return f"${value:,.0f}"


# ============================================================================
# SIDEBAR NAVIGATION
# ============================================================================

with st.sidebar:
    st.markdown('<h1 style="color: #FA8072;">Keylake</h1>', unsafe_allow_html=True)
    st.markdown("---")
    
    page = st.radio(
        "Navigation",
        [
            "📊 Dashboard",
            "👥 Contacts",
            "💼 Deals",
            "🎉 Customers",
            "📧 Emails",
            "📅 Meetings",
            "📈 Analytics",
            "⚙️ Settings"
        ],
        label_visibility="collapsed"
    )
    
    st.markdown("---")
    st.markdown("### Agent Status")
    
    agents = {
        "Lead Qualification": "🟢 Active",
        "Email Intelligence": "🟢 Active",
        "Sales Pipeline": "🟢 Active",
        "Customer Success": "🟢 Active",
        "Meeting Scheduler": "🟢 Active",
        "Analytics": "🟢 Active"
    }
    
    for agent, status in agents.items():
        st.caption(f"{agent}: {status}")
    
    st.markdown("---")
    stats = storage.get_stats()
    st.markdown("### Database Stats")
    for key, value in stats.items():
        st.caption(f"{key.title()}: {value}")

# ============================================================================
# DASHBOARD PAGE
# ============================================================================

def show_dashboard():
    """Display main dashboard"""
    st.title("📊 Dashboard")
    st.markdown("Real-time overview of your CRM metrics")
    
    # Top Metrics Row
    col1, col2, col3, col4 = st.columns(4)
    
    total_leads = storage.count('contacts')
    total_deals = storage.count('deals')
    total_customers = storage.count('customers')
    
    deals = storage.get_all_deals()
    total_pipeline = sum(d.get('value', 0) for d in deals 
                        if d.get('stage') in ['prospecting', 'qualification', 'proposal', 'negotiation'])
    
    with col1:
        st.metric("Total Leads", total_leads)
    
    with col2:
        st.metric("Active Deals", total_deals)
    
    with col3:
        st.metric("Customers", total_customers)
    
    with col4:
        st.metric("Pipeline Value", f"${total_pipeline/1000:.0f}K")
    
    st.markdown("---")
    
    # Pipeline and Health charts
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📈 Pipeline by Stage")
        
        stages = ['prospecting', 'qualification', 'proposal', 'negotiation', 'closed_won', 'closed_lost']
        pipeline_data = []
        
        for stage in stages:
            stage_deals = [d for d in deals if d.get('stage') == stage]
            count = len(stage_deals)
            pipeline_data.append({
                "Stage": stage.replace('_', ' ').title(),
                "Deals": count
            })
        
        pipeline_df = pd.DataFrame(pipeline_data)
        if not pipeline_df.empty:
            st.bar_chart(pipeline_df.set_index("Stage")["Deals"])
    
    with col2:
        st.subheader("🎯 Customer Health Distribution")
        
        customers = storage.get_all_customers()
        health_ranges = [
            ("Excellent", 80, 101),
            ("Healthy", 60, 80),
            ("Warning", 40, 60),
            ("At Risk", 0, 40)
        ]
        
        health_data = []
        for name, min_score, max_score in health_ranges:
            count = sum(1 for c in customers if min_score <= c.get('health_score', 0) < max_score)
            health_data.append({"Health": name, "Customers": count})
        
        health_df = pd.DataFrame(health_data)
        if not health_df.empty:
            st.bar_chart(health_df.set_index("Health")["Customers"])

# ============================================================================
# CONTACTS PAGE - FULL CRUD
# ============================================================================

def show_contacts():
    """Display contacts management with full CRUD"""
    st.title("👥 Contacts")
    
    tab1, tab2 = st.tabs(["All Contacts", "➕ Add Contact"])
    
    with tab1:
        st.subheader("Contact List")
        
        # Filters
        col1, col2, col3 = st.columns(3)
        with col1:
            status_filter = st.selectbox(
                "Status",
                ["All", "new", "qualified", "contacted", "unqualified"]
            )
        with col2:
            search = st.text_input("Search", placeholder="Name or email...")
        
        # Get contacts - sorted by newest first
        contacts = storage.get_all_contacts(limit=100)
        contacts = sorted(contacts, key=lambda x: x.get('created_at', ''), reverse=True)

        if status_filter != "All":
            contacts = [c for c in contacts if c.get('lead_status') == status_filter]
        
        if search:
            search_lower = search.lower()
            contacts = [c for c in contacts 
                       if search_lower in c.get('email', '').lower() 
                       or search_lower in f"{c.get('first_name', '')} {c.get('last_name', '')}".lower()]
        
        if contacts:
            # Display as table with actions
            for contact in contacts:
                with st.expander(f"**{contact.get('first_name')} {contact.get('last_name')}** - {contact.get('email')} {get_lead_status_emoji(contact.get('lead_status'))}"):
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.write(f"**Company:** {get_company_name(contact.get('company_id'))}")
                        st.write(f"**Job Title:** {contact.get('job_title') or 'N/A'}")
                        st.write(f"**Phone:** {contact.get('phone') or 'N/A'}")
                    
                    with col2:
                        st.write(f"**Lead Score:** {contact.get('lead_score', 0)}")
                        st.write(f"**Status:** {contact.get('lead_status')}")
                        st.write(f"**Source:** {contact.get('lead_source')}")
                    
                    with col3:
                        st.write(f"**LinkedIn:** [Profile]({contact.get('linkedin_url', '#')})")
                        st.write(f"**Created:** {contact.get('created_at', '')[:10]}")
                    
                    # Edit and Delete actions
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        if st.button("✏️ Edit", key=f"edit_contact_{contact.get('id')}"):
                            st.session_state.editing_contact = contact.get('id')
                            st.rerun()

                    with col2:
                        if st.button("🗑️ Delete", key=f"delete_contact_{contact.get('id')}"):
                            storage.delete_contact(contact.get('id'))
                            st.success("Contact deleted!")
                            st.rerun()
                    
                    with col3:
                        new_status = st.selectbox(
                            "Quick Status",
                            ["new", "qualified", "contacted", "unqualified"],
                            index=["new", "qualified", "contacted", "unqualified"].index(contact.get('lead_status', 'new')),
                            key=f"status_{contact.get('id')}"
                        )
                        if new_status != contact.get('lead_status'):
                            storage.update_contact(contact.get('id'), lead_status=new_status)
                            st.success("Status updated!")
                            st.rerun()
                    
                    # Edit form
                    if st.session_state.editing_contact == contact.get('id'):
                        st.markdown("---")
                        with st.form(f"edit_contact_form_{contact.get('id')}"):
                            c1, c2 = st.columns(2)
                            with c1:
                                first_name = st.text_input("First Name", contact.get('first_name', ''))
                                last_name = st.text_input("Last Name", contact.get('last_name', ''))
                                email = st.text_input("Email", contact.get('email', ''))
                            with c2:
                                job_title = st.text_input("Job Title", contact.get('job_title', ''))
                                phone = st.text_input("Phone", contact.get('phone', ''))
                                lead_score = st.number_input("Lead Score", 0, 100, contact.get('lead_score', 50))

                            if st.form_submit_button("💾 Save Changes"):
                                storage.update_contact(contact.get('id'),
                                    first_name=first_name,
                                    last_name=last_name,
                                    email=email,
                                    job_title=job_title,
                                    phone=phone,
                                    lead_score=lead_score
                                )
                                st.success("Contact updated!")
                                st.session_state.editing_contact = None
                                st.rerun()
        else:
            st.info("No contacts found.")
    
    with tab2:
        st.subheader("Create New Contact")
        
        with st.form("create_contact_form"):
            c1, c2 = st.columns(2)

            with c1:
                first_name = st.text_input("First Name *")
                last_name = st.text_input("Last Name *")
                email = st.text_input("Email *")

            with c2:
                # Get companies for selection
                companies = storage.get_all_companies()
                company_options = {c.get('name'): c.get('id') for c in companies}
                selected_company = st.selectbox("Company", [""] + list(company_options.keys()))
                job_title = st.text_input("Job Title")
                phone = st.text_input("Phone")

            c3, c4 = st.columns(2)
            with c3:
                lead_source = st.selectbox("Lead Source",
                    ["Website", "Referral", "Cold Outreach", "Event", "LinkedIn", "Other"])
            with c4:
                lead_score = st.slider("Lead Score", 0, 100, 50)

            submitted = st.form_submit_button("➕ Create Contact", type="primary")

            if submitted:
                if not first_name or not last_name or not email:
                    st.error("Please fill in all required fields (First Name, Last Name, Email)")
                else:
                    company_id = company_options.get(selected_company) if selected_company else None
                    storage.create_contact(
                        email=email,
                        first_name=first_name,
                        last_name=last_name,
                        company_id=company_id,
                        job_title=job_title,
                        phone=phone,
                        lead_source=lead_source,
                        lead_score=lead_score
                    )
                    st.success(f"✅ Contact {first_name} {last_name} created!")
                    st.rerun()


def get_lead_status_emoji(status):
    """Get emoji for lead status"""
    emojis = {'new': '🔵', 'qualified': '🟢', 'contacted': '🟡', 'unqualified': '🔴'}
    return emojis.get(status, '⚪')

# ============================================================================
# DEALS PAGE - FULL CRUD
# ============================================================================

def show_deals():
    """Display deals management with full CRUD"""
    st.title("💼 Deals")
    
    tab1, tab2 = st.tabs(["Pipeline View", "➕ Add Deal"])
    
    with tab1:
        st.subheader("Sales Pipeline")
        
        # Filter by stage
        stage_filter = st.selectbox(
            "Filter by Stage",
            ["All", "prospecting", "qualification", "proposal", "negotiation", "closed_won", "closed_lost"]
        )
        
        deals = storage.get_all_deals(limit=100)
        
        if stage_filter != "All":
            deals = [d for d in deals if d.get('stage') == stage_filter]
        
        deals = sorted(deals, key=lambda x: x.get('created_at', ''), reverse=True)
        
        if deals:
            stages = ['prospecting', 'qualification', 'proposal', 'negotiation', 'closed_won', 'closed_lost']
            
            for stage in stages:
                stage_deals = [d for d in deals if d.get('stage') == stage]
                if stage_deals or stage_filter == stage or stage_filter == "All":
                    st.markdown(f"### {get_deal_stage_color(stage)} {stage.replace('_', ' ').title()}")
                    
                    for deal in stage_deals:
                        with st.expander(f"**{deal.get('name')}** - {format_currency(deal.get('value', 0))} (Health: {get_health_color(deal.get('health_score', 50))} {deal.get('health_score', 50)})"):
                            col1, col2, col3 = st.columns(3)
                            
                            with col1:
                                st.write(f"**Contact:** {get_contact_name(deal.get('contact_id'))}")
                                st.write(f"**Company:** {get_company_name(deal.get('company_id'))}")
                            
                            with col2:
                                st.write(f"**Probability:** {deal.get('probability', 50)}%")
                                st.write(f"**Expected Close:** {deal.get('expected_close_date', 'N/A')[:10] if deal.get('expected_close_date') else 'N/A'}")
                            
                            with col3:
                                st.write(f"**Stage:** {deal.get('stage')}")
                                st.write(f"**Created:** {deal.get('created_at', '')[:10]}")
                            
                            # Actions
                            col1, col2, col3, col4 = st.columns(4)
                            
                            with col1:
                                if st.button("✏️ Edit", key=f"edit_deal_{deal.get('id')}"):
                                    st.session_state.editing_deal = deal.get('id')
                                    st.rerun()
                            
                            with col2:
                                if st.button("🗑️ Delete", key=f"delete_deal_{deal.get('id')}"):
                                    storage.delete_deal(deal.get('id'))
                                    st.success("Deal deleted!")
                                    st.rerun()
                            
                            with col3:
                                new_stage = st.selectbox(
                                    "Move to",
                                    stages,
                                    index=stages.index(deal.get('stage', 'prospecting')),
                                    key=f"move_{deal.get('id')}"
                                )
                                if new_stage != deal.get('stage'):
                                    storage.update_deal_stage(deal.get('id'), new_stage)
                                    st.success("Stage updated!")
                                    st.rerun()
                            
                            with col4:
                                health = st.slider("Health", 0, 100, deal.get('health_score', 50), key=f"health_{deal.get('id')}")
                                if health != deal.get('health_score', 50):
                                    storage.update_deal(deal.get('id'), health_score=health)
                                    st.success("Health updated!")
                                    st.rerun()
                            
                            # Edit form
                            if st.session_state.editing_deal == deal.get('id'):
                                st.markdown("---")
                                with st.form(f"edit_deal_form_{deal.get('id')}"):
                                    c1, c2 = st.columns(2)
                                    with c1:
                                        name = st.text_input("Deal Name", deal.get('name', ''))
                                        value = st.number_input("Value", min_value=0.0, value=float(deal.get('value', 0)))
                                        probability = st.slider("Probability", 0, 100, deal.get('probability', 50))
                                    with c2:
                                        expected_close = st.date_input("Expected Close", 
                                            value=date.fromisoformat(deal.get('expected_close_date')) if deal.get('expected_close_date') else date.today())
                                        notes = st.text_area("Notes", deal.get('notes', ''))
                                    
                                    if st.form_submit_button("💾 Save Changes"):
                                        storage.update_deal(deal.get('id'),
                                            name=name,
                                            value=value,
                                            probability=probability,
                                            expected_close_date=expected_close.isoformat(),
                                            notes=notes
                                        )
                                        st.success("Deal updated!")
                                        st.session_state.editing_deal = None
                                        st.rerun()
        else:
            st.info("No deals found.")
    
    with tab2:
        st.subheader("Create New Deal")
        
        with st.form("create_deal_form"):
            c1, c2 = st.columns(2)

            with c1:
                name = st.text_input("Deal Name *")
                value = st.number_input("Deal Value *", min_value=0.0, step=1000.0)
                stage = st.selectbox("Stage", ["prospecting", "qualification", "proposal", "negotiation"])

            with c2:
                contacts = storage.get_all_contacts()
                contact_options = {f"{c.get('first_name')} {c.get('last_name')}": c.get('id') for c in contacts}
                selected_contact = st.selectbox("Contact", [""] + list(contact_options.keys()))

                probability = st.slider("Probability", 0, 100, 50)
                expected_close = st.date_input("Expected Close", min_value=date.today())

            notes = st.text_area("Notes")

            submitted = st.form_submit_button("➕ Create Deal", type="primary")

            if submitted:
                if not name or value <= 0:
                    st.error("Please fill in required fields (Deal Name, Value)")
                else:
                    contact_id = contact_options.get(selected_contact) if selected_contact else None
                    storage.create_deal(
                        name=name,
                        value=value,
                        stage=stage,
                        contact_id=contact_id,
                        probability=probability,
                        expected_close_date=expected_close.isoformat(),
                        notes=notes
                    )
                    st.success(f"✅ Deal '{name}' created!")
                    st.rerun()

# ============================================================================
# CUSTOMERS PAGE - FULL CRUD
# ============================================================================

def show_customers():
    """Display customers management with full CRUD"""
    st.title("🎉 Customers")
    
    tab1, tab2 = st.tabs(["All Customers", "➕ Add Customer"])
    
    with tab1:
        st.subheader("Customer Portfolio")
        
        # Filters
        col1, col2 = st.columns(2)
        with col1:
            risk_filter = st.selectbox(
                "Churn Risk",
                ["All", "low", "medium", "high"]
            )
        
        customers = storage.get_all_customers(limit=100)
        customers = sorted(customers, key=lambda x: x.get('created_at', ''), reverse=True)

        if risk_filter != "All":
            customers = [c for c in customers if c.get('churn_risk') == risk_filter]
        
        if customers:
            # Summary metrics
            col1, col2, col3, col4 = st.columns(4)
            
            total_mrr = sum(c.get('mrr', 0) for c in customers)
            avg_health = sum(c.get('health_score', 50) for c in customers) / len(customers)
            at_risk = sum(1 for c in customers if c.get('churn_risk') == 'high')
            
            with col1:
                st.metric("Total MRR", f"${total_mrr:,.0f}")
            with col2:
                st.metric("Avg Health", f"{avg_health:.0f}")
            with col3:
                st.metric("At Risk", at_risk)
            with col4:
                st.metric("Total", len(customers))
            
            st.markdown("---")
            
            # Customer list
            for customer in customers:
                company_name = get_company_name(customer.get('company_id'))
                with st.expander(f"**{company_name}** - {customer.get('plan')} Plan | MRR: {format_currency(customer.get('mrr'))} | Health: {get_health_color(customer.get('health_score'))} {customer.get('health_score')} | Churn: {get_churn_risk_color(customer.get('churn_risk'))} {customer.get('churn_risk').title()}"):
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.write(f"**Contract End:** {customer.get('contract_end_date', 'N/A')[:10]}")
                        st.write(f"**Logins/Week:** {customer.get('logins_per_week', 0)}")
                        st.write(f"**Features Used:** {customer.get('features_used', 0)}/{customer.get('total_features', 10)}")
                    
                    with col2:
                        st.write(f"**CSAT:** {customer.get('csat_score', 0)}/5.0")
                        st.write(f"**NPS:** {customer.get('nps_score', 0)}")
                        st.write(f"**License Usage:** {customer.get('license_usage_percent', 0)}%")
                    
                    with col3:
                        st.write(f"**Support Tickets:** {customer.get('support_tickets_30d', 0)}")
                        st.write(f"**Critical Open:** {customer.get('critical_tickets_open', 0)}")
                    
                    # Actions
                    col1, col2, col3 = st.columns(3)

                    with col1:
                        if st.button("✏️ Edit", key=f"edit_customer_{customer.get('id')}"):
                            st.session_state.editing_customer = customer.get('id')
                            st.rerun()

                    with col2:
                        if st.button("🗑️ Delete", key=f"delete_customer_{customer.get('id')}"):
                            storage.delete_customer(customer.get('id'))
                            st.success("Customer deleted!")
                            st.rerun()

                    with col3:
                        new_health = st.slider("Health", 0, 100, customer.get('health_score', 50), key=f"health_cust_{customer.get('id')}")
                        if new_health != customer.get('health_score', 50):
                            storage.update_customer_health(customer.get('id'), new_health)
                            st.success("Health updated!")
                            st.rerun()

                    # Edit form
                    if st.session_state.editing_customer == customer.get('id'):
                        st.markdown("---")
                        with st.form(f"edit_customer_form_{customer.get('id')}"):
                            c1, c2 = st.columns(2)
                            with c1:
                                plan = st.text_input("Plan", customer.get('plan', ''))
                                mrr = st.number_input("MRR", min_value=0.0, value=float(customer.get('mrr', 0)))
                                logins = st.number_input("Logins/Week", 0, 100, customer.get('logins_per_week', 0))
                            with c2:
                                csat = st.number_input("CSAT", 0.0, 5.0, float(customer.get('csat_score', 0)))
                                nps = st.number_input("NPS", -10, 10, customer.get('nps_score', 0))
                                tickets = st.number_input("Support Tickets", 0, 100, customer.get('support_tickets_30d', 0))

                            if st.form_submit_button("💾 Save Changes"):
                                storage.update_customer(customer.get('id'),
                                    plan=plan,
                                    mrr=mrr,
                                    logins_per_week=logins,
                                    csat_score=csat,
                                    nps_score=nps,
                                    support_tickets_30d=tickets
                                )
                                st.success("Customer updated!")
                                st.session_state.editing_customer = None
                                st.rerun()
        else:
            st.info("No customers found.")
    
    with tab2:
        st.subheader("Create New Customer")
        
        with st.form("create_customer_form"):
            c1, c2 = st.columns(2)

            with c1:
                company_name = st.text_input("Company Name *", placeholder="Enter new company name")
                plan = st.selectbox("Plan", ["Starter", "Professional", "Enterprise", "Enterprise Plus"], index=0)
                mrr = st.number_input("MRR ($)", min_value=0.0, step=100.0, value=0.0)

            with c2:
                health_score = st.slider("Health Score", 0, 100, 50)
                logins = st.number_input("Logins/Week", 0, 100, 0)
                csat = st.number_input("CSAT Score", 0.0, 5.0, 0.0)
                nps = st.number_input("NPS Score", -10, 10, 0)

            submitted = st.form_submit_button("➕ Create Customer", type="primary")

            if submitted:
                if not company_name:
                    st.error("Please enter a company name")
                else:
                    # Find or create company
                    companies = storage.get_all_companies()
                    company = next((c for c in companies if c.get('name') == company_name), None)
                    
                    if company:
                        company_id = company.get('id')
                    else:
                        # Create new company
                        new_company = storage.create_company(name=company_name)
                        company_id = new_company.get('id')
                    
                    storage.create_customer(
                        company_id=company_id,
                        plan=plan,
                        mrr=mrr,
                        health_score=health_score,
                        logins_per_week=logins,
                        csat_score=csat,
                        nps_score=nps
                    )
                    st.success(f"✅ Customer created for {company_name}!")
                    st.rerun()

# ============================================================================
# EMAILS PAGE - FULL CRUD
# ============================================================================

def show_emails():
    """Display emails management with full CRUD"""
    st.title("📧 Emails")
    
    tab1, tab2 = st.tabs(["Inbox", "➕ Add Email"])
    
    with tab1:
        st.subheader("Email Inbox")
        
        # Filter
        priority_filter = st.selectbox(
            "Priority",
            ["All", "high", "medium", "low"]
        )
        
        emails = storage.get_all_emails(limit=100)
        
        if priority_filter != "All":
            emails = [e for e in emails if e.get('priority') == priority_filter]
        
        emails = sorted(emails, key=lambda x: x.get('created_at', ''), reverse=True)
        
        if emails:
            for email in emails:
                sentiment_icon = {"positive": "😊", "neutral": "😐", "negative": "😞"}.get(email.get('sentiment'), "")
                priority_icon = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(email.get('priority'), "")
                
                with st.expander(f"{priority_icon} {email.get('subject') or 'No Subject'} {sentiment_icon}"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write(f"**From:** {email.get('from_email')}")
                        st.write(f"**To:** {email.get('to_email')}")
                        st.write(f"**Direction:** {email.get('direction', 'inbound')}")
                    
                    with col2:
                        st.write(f"**Sentiment:** {email.get('sentiment', 'Unknown')}")
                        st.write(f"**Category:** {email.get('category', 'Uncategorized')}")
                        st.write(f"**Response Sent:** {'✅' if email.get('response_sent') else '❌'}")
                    
                    st.markdown("---")
                    st.write(email.get('body', 'No content'))
                    
                    if email.get('draft_response'):
                        st.info("🤖 **AI Draft Response:**")
                        st.write(email.get('draft_response'))
                    
                    # Actions
                    col1, col2, col3 = st.columns(3)

                    with col1:
                        if st.button("✏️ Edit", key=f"edit_email_{email.get('id')}"):
                            st.session_state.editing_email = email.get('id')
                            st.rerun()

                    with col2:
                        if st.button("🗑️ Delete", key=f"delete_email_{email.get('id')}"):
                            storage.delete_email(email.get('id'))
                            st.success("Email deleted!")
                            st.rerun()

                    with col3:
                        if st.button("📤 Mark Sent", key=f"sent_email_{email.get('id')}", disabled=email.get('response_sent')):
                            storage.mark_email_sent(email.get('id'))
                            st.success("Marked as sent!")
                            st.rerun()

                    # Edit form
                    if st.session_state.editing_email == email.get('id'):
                        st.markdown("---")
                        with st.form(f"edit_email_form_{email.get('id')}"):
                            subject = st.text_input("Subject", email.get('subject', ''))
                            body = st.text_area("Body", email.get('body', ''))
                            c1, c2 = st.columns(2)
                            with c1:
                                sentiment = st.selectbox("Sentiment", ["positive", "neutral", "negative"],
                                                       index=["positive", "neutral", "negative"].index(email.get('sentiment', 'neutral')))
                                priority = st.selectbox("Priority", ["high", "medium", "low"],
                                                      index=["high", "medium", "low"].index(email.get('priority', 'medium')))
                            with c2:
                                category = st.text_input("Category", email.get('category', ''))
                                draft = st.text_area("Draft Response", email.get('draft_response', ''))

                            if st.form_submit_button("💾 Save Changes"):
                                storage.update_email(email.get('id'),
                                    subject=subject,
                                    body=body,
                                    sentiment=sentiment,
                                    priority=priority,
                                    category=category,
                                    draft_response=draft
                                )
                                st.success("Email updated!")
                                st.session_state.editing_email = None
                                st.rerun()
        else:
            st.info("No emails found.")
    
    with tab2:
        st.subheader("Create New Email")
        
        with st.form("create_email_form"):
            c1, c2 = st.columns(2)

            with c1:
                from_email = st.text_input("From Email *")
                to_email = st.text_input("To Email *")
                subject = st.text_input("Subject")

            with c2:
                direction = st.selectbox("Direction", ["inbound", "outbound"])
                priority = st.selectbox("Priority", ["high", "medium", "low"])
                category = st.text_input("Category", "general")

            body = st.text_area("Body", height=150)

            submitted = st.form_submit_button("➕ Create Email", type="primary")

            if submitted:
                if not from_email or not to_email:
                    st.error("Please fill in required fields (From Email, To Email)")
                else:
                    storage.create_email(
                        from_email=from_email,
                        to_email=to_email,
                        subject=subject,
                        body=body,
                        direction=direction,
                        priority=priority,
                        category=category
                    )
                    st.success("✅ Email created!")
                    st.rerun()

# ============================================================================
# MEETINGS PAGE - FULL CRUD
# ============================================================================

def show_meetings():
    """Display meetings management with full CRUD"""
    st.title("📅 Meetings")

    tab1, tab2, tab3 = st.tabs(["All Meetings", "📆 Calendar View", "➕ Schedule Meeting"])

    with tab1:
        st.subheader("Meeting Schedule")
        
        # Filter
        status_filter = st.selectbox(
            "Status",
            ["All", "scheduled", "completed", "cancelled", "no-show"]
        )
        
        meetings = storage.get_all_meetings(limit=100)
        
        if status_filter != "All":
            meetings = [m for m in meetings if m.get('status') == status_filter]
        
        meetings = sorted(meetings, key=lambda x: x.get('scheduled_at', ''), reverse=True)
        
        if meetings:
            for meeting in meetings:
                icon = "🎯" if meeting.get('meeting_type') == "demo" else "📞" if meeting.get('meeting_type') == "call" else "🤝"
                status_icon = {"scheduled": "📅", "completed": "✅", "cancelled": "❌", "no-show": "😞"}.get(meeting.get('status'), "")
                
                scheduled = meeting.get('scheduled_at', '')
                if scheduled:
                    scheduled_dt = scheduled[:16].replace('T', ' ')
                else:
                    scheduled_dt = 'N/A'
                
                with st.expander(f"{icon} {meeting.get('title')} - {scheduled_dt} {status_icon}"):
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.write(f"**Type:** {meeting.get('meeting_type', 'General')}")
                        st.write(f"**Duration:** {meeting.get('duration_minutes', 30)} min")
                        st.write(f"**Location:** {meeting.get('location', 'TBD')}")
                    
                    with col2:
                        deal_name = "N/A"
                        if meeting.get('deal_id'):
                            deal = storage.get_deal(meeting.get('deal_id'))
                            if deal:
                                deal_name = deal.get('name', 'Unknown')
                        st.write(f"**Related Deal:** {deal_name}")
                        st.write(f"**Created:** {meeting.get('created_at', '')[:10]}")
                    
                    with col3:
                        st.write(f"**Status:** {meeting.get('status', 'scheduled')}")
                    
                    if meeting.get('notes'):
                        st.markdown("---")
                        st.write(f"**Notes:** {meeting.get('notes')}")
                    
                    if meeting.get('context'):
                        with st.expander("📋 Meeting Context"):
                            st.write(meeting.get('context'))
                    
                    # Actions
                    col1, col2, col3 = st.columns(3)

                    with col1:
                        if st.button("✏️ Edit", key=f"edit_meeting_{meeting.get('id')}"):
                            st.session_state.editing_meeting = meeting.get('id')
                            st.rerun()

                    with col2:
                        if st.button("🗑️ Delete", key=f"delete_meeting_{meeting.get('id')}"):
                            storage.delete_meeting(meeting.get('id'))
                            st.success("Meeting deleted!")
                            st.rerun()

                    with col3:
                        new_status = st.selectbox(
                            "Status",
                            ["scheduled", "completed", "cancelled", "no-show"],
                            index=["scheduled", "completed", "cancelled", "no-show"].index(meeting.get('status', 'scheduled')),
                            key=f"status_mtg_{meeting.get('id')}"
                        )
                        if new_status != meeting.get('status'):
                            storage.update_meeting_status(meeting.get('id'), new_status)
                            st.success("Status updated!")
                            st.rerun()

                    # Edit form
                    if st.session_state.editing_meeting == meeting.get('id'):
                        st.markdown("---")
                        with st.form(f"edit_meeting_form_{meeting.get('id')}"):
                            c1, c2 = st.columns(2)
                            with c1:
                                title = st.text_input("Title", meeting.get('title', ''))
                                meeting_type = st.selectbox("Type", ["demo", "call", "discovery", "negotiation", "check-in", "other"],
                                                          index=["demo", "call", "discovery", "negotiation", "check-in", "other"].index(meeting.get('meeting_type', 'call')))
                                duration = st.number_input("Duration (min)", 15, 120, meeting.get('duration_minutes', 30))
                            with c2:
                                location = st.text_input("Location", meeting.get('location', ''))
                                scheduled = st.text_input("Scheduled At (ISO)", meeting.get('scheduled_at', ''))
                                notes = st.text_area("Notes", meeting.get('notes', ''))

                            if st.form_submit_button("💾 Save Changes"):
                                storage.update_meeting(meeting.get('id'),
                                    title=title,
                                    meeting_type=meeting_type,
                                    duration_minutes=duration,
                                    location=location,
                                    scheduled_at=scheduled,
                                    notes=notes
                                )
                                st.success("Meeting updated!")
                                st.session_state.editing_meeting = None
                                st.rerun()
        else:
            st.info("No meetings found.")

    with tab2:
        st.subheader("📆 Meeting Calendar")
        
        # Check if viewing/editing a specific meeting
        if st.session_state.editing_meeting:
            meeting = storage.get_meeting(st.session_state.editing_meeting)
            if meeting:
                st.markdown("### 📋 Meeting Details")
                
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.markdown(f"#### {meeting.get('title', 'No Title')}")
                with col2:
                    if st.button("← Back to Calendar"):
                        st.session_state.editing_meeting = None
                        st.rerun()
                
                # Meeting details
                c1, c2, c3 = st.columns(3)
                with c1:
                    icon = "🎯" if meeting.get('meeting_type') == "demo" else "📞" if meeting.get('meeting_type') == "call" else "🤝"
                    st.write(f"**Type:** {icon} {meeting.get('meeting_type', 'General')}")
                    st.write(f"**Duration:** {meeting.get('duration_minutes', 30)} min")
                with c2:
                    scheduled = meeting.get('scheduled_at', '')
                    if scheduled:
                        scheduled_dt = scheduled.replace('T', ' ')
                        st.write(f"**Scheduled:** {scheduled_dt[:16]}")
                    st.write(f"**Status:** {meeting.get('status', 'scheduled')}")
                with c3:
                    st.write(f"**Location:** {meeting.get('location', 'TBD')}")
                    deal_id = meeting.get('deal_id')
                    if deal_id:
                        deal = storage.get_deal(deal_id)
                        if deal:
                            st.write(f"**Related Deal:** {deal.get('name', 'Unknown')}")
                
                if meeting.get('context'):
                    st.markdown("---")
                    with st.expander("📋 Meeting Context", expanded=False):
                        st.write(meeting.get('context'))
                
                if meeting.get('notes'):
                    st.markdown("---")
                    st.markdown("### 📝 Notes")
                    st.write(meeting.get('notes'))
                
                # Actions
                st.markdown("---")
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    if st.button("✏️ Edit Meeting", use_container_width=True):
                        st.session_state.editing_meeting_form = st.session_state.editing_meeting
                        st.rerun()
                
                with col2:
                    new_status = st.selectbox(
                        "Update Status",
                        ["scheduled", "completed", "cancelled", "no-show"],
                        index=["scheduled", "completed", "cancelled", "no-show"].index(meeting.get('status', 'scheduled')),
                        key=f"status_cal_{meeting.get('id')}"
                    )
                    if new_status != meeting.get('status'):
                        storage.update_meeting_status(meeting.get('id'), new_status)
                        st.success("Status updated!")
                        st.rerun()
                
                with col3:
                    if st.button("🗑️ Delete Meeting", use_container_width=True):
                        storage.delete_meeting(meeting.get('id'))
                        st.success("Meeting deleted!")
                        st.session_state.editing_meeting = None
                        st.rerun()
                
                # Edit form
                if st.session_state.get('editing_meeting_form') == meeting.get('id'):
                    st.markdown("---")
                    st.markdown("### ✏️ Edit Meeting")
                    with st.form(f"edit_meeting_cal_form_{meeting.get('id')}"):
                        c1, c2 = st.columns(2)
                        with c1:
                            title = st.text_input("Title", meeting.get('title', ''))
                            meeting_type = st.selectbox("Type", ["demo", "call", "discovery", "negotiation", "check-in", "other"],
                                                      index=["demo", "call", "discovery", "negotiation", "check-in", "other"].index(meeting.get('meeting_type', 'call')))
                            duration = st.number_input("Duration (min)", 15, 120, meeting.get('duration_minutes', 30))
                        with c2:
                            location = st.text_input("Location", meeting.get('location', ''))
                            scheduled = st.text_input("Scheduled At (ISO format)", meeting.get('scheduled_at', ''))
                            notes = st.text_area("Notes", meeting.get('notes', ''))
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            submitted = st.form_submit_button("💾 Save Changes", use_container_width=True)
                        with col2:
                            cancel = st.form_submit_button("Cancel", use_container_width=True)
                        
                        if submitted:
                            storage.update_meeting(meeting.get('id'),
                                title=title,
                                meeting_type=meeting_type,
                                duration_minutes=duration,
                                location=location,
                                scheduled_at=scheduled,
                                notes=notes
                            )
                            st.success("Meeting updated!")
                            st.session_state.editing_meeting_form = None
                            st.rerun()
                        
                        if cancel:
                            st.session_state.editing_meeting_form = None
                            st.rerun()
                
                st.markdown("---")
        
        # Calendar view (shown when not editing)
        else:
            # Calendar navigation
            col1, col2, col3 = st.columns([1, 2, 1])
            with col1:
                prev_month = st.button("◀ Previous")
            with col3:
                next_month = st.button("Next ▶")
            
            # Initialize session state for calendar navigation
            if 'calendar_year' not in st.session_state:
                st.session_state.calendar_year = date.today().year
            if 'calendar_month' not in st.session_state:
                st.session_state.calendar_month = date.today().month
            
            if prev_month:
                if st.session_state.calendar_month == 1:
                    st.session_state.calendar_year -= 1
                    st.session_state.calendar_month = 12
                else:
                    st.session_state.calendar_month -= 1
            
            if next_month:
                if st.session_state.calendar_month == 12:
                    st.session_state.calendar_year += 1
                    st.session_state.calendar_month = 1
                else:
                    st.session_state.calendar_month += 1
            
            # Display current month/year
            from calendar import month_name
            st.markdown(f"### {month_name[st.session_state.calendar_month]} {st.session_state.calendar_year}")
            
            # Get meetings for the selected month
            meetings = storage.get_meetings_by_month(st.session_state.calendar_year, st.session_state.calendar_month)
            
            # Create calendar grid
            import calendar as cal
            month_calendar = cal.monthcalendar(st.session_state.calendar_year, st.session_state.calendar_month)
            
            # Group meetings by date
            meetings_by_date = {}
            for meeting in meetings:
                scheduled_at = meeting.get('scheduled_at', '')
                if scheduled_at:
                    meeting_date = datetime.fromisoformat(scheduled_at).date()
                    date_str = meeting_date.isoformat()
                    if date_str not in meetings_by_date:
                        meetings_by_date[date_str] = []
                    meetings_by_date[date_str].append(meeting)
            
            # Calendar header (weekdays)
            weekdays = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
            cols = st.columns(7)
            for i, day in enumerate(weekdays):
                with cols[i]:
                    st.markdown(f"**{day}**")
            
            st.markdown("---")
            
            # Calendar grid
            for week in month_calendar:
                cols = st.columns(7)
                for i, day in enumerate(week):
                    with cols[i]:
                        if day == 0:
                            st.write("")
                        else:
                            current_date = date(st.session_state.calendar_year, st.session_state.calendar_month, day)
                            date_str = current_date.isoformat()
                            is_today = current_date == date.today()
                            
                            # Style for today
                            if is_today:
                                st.markdown(f"**🔵 {day}**")
                            else:
                                st.markdown(f"**{day}**")
                            
                            # Show meetings for this day
                            day_meetings = meetings_by_date.get(date_str, [])
                            for meeting in day_meetings[:3]:  # Show max 3 meetings per day
                                icon = "🎯" if meeting.get('meeting_type') == "demo" else \
                                       "📞" if meeting.get('meeting_type') == "call" else \
                                       "🤝" if meeting.get('meeting_type') == "discovery" else \
                                       "💼" if meeting.get('meeting_type') == "negotiation" else "📅"
                                
                                status = meeting.get('status', 'scheduled')
                                status_icon = "✅" if status == "completed" else "❌" if status == "cancelled" else ""
                                
                                time_str = meeting.get('scheduled_at', 'T')[11:16] if meeting.get('scheduled_at') else ""
                                
                                # Make clickable with expander
                                with st.expander(f"{icon} {time_str}"):
                                    st.write(f"**{meeting.get('title', 'No Title')}**")
                                    st.write(f"Type: {meeting.get('meeting_type', 'General')}")
                                    st.write(f"Status: {status} {status_icon}")
                                    if meeting.get('location'):
                                        st.write(f"Location: {meeting.get('location')}")
                                    
                                    # Quick actions
                                    if st.button("View Details", key=f"view_cal_{meeting.get('id')}"):
                                        st.session_state.editing_meeting = meeting.get('id')
                                        st.rerun()
                                    
                                    if st.button("Edit", key=f"edit_cal_{meeting.get('id')}"):
                                        st.session_state.editing_meeting = meeting.get('id')
                                        st.session_state.editing_meeting_form = meeting.get('id')
                                        st.rerun()
                            
                            if len(day_meetings) > 3:
                                st.caption(f"+{len(day_meetings) - 3} more")
            
            # Summary for selected month
            st.markdown("---")
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Meetings", len(meetings))
            with col2:
                scheduled_count = sum(1 for m in meetings if m.get('status') == 'scheduled')
                st.metric("Scheduled", scheduled_count)
            with col3:
                completed_count = sum(1 for m in meetings if m.get('status') == 'completed')
                st.metric("Completed", completed_count)
            with col4:
                cancelled_count = sum(1 for m in meetings if m.get('status') == 'cancelled')
                st.metric("Cancelled", cancelled_count)
            
            # Upcoming meetings list
            st.markdown("### 📋 Upcoming Meetings")
            upcoming = [m for m in meetings if m.get('status') == 'scheduled']
            upcoming = sorted(upcoming, key=lambda x: x.get('scheduled_at', ''))
            
            if upcoming:
                for meeting in upcoming[:10]:
                    scheduled = meeting.get('scheduled_at', '')
                    if scheduled:
                        scheduled_dt = scheduled[:16].replace('T', ' ')
                    else:
                        scheduled_dt = 'N/A'
                    
                    icon = "🎯" if meeting.get('meeting_type') == "demo" else "📞" if meeting.get('meeting_type') == "call" else "🤝"
                    
                    col1, col2, col3, col4 = st.columns([3, 2, 2, 1])
                    with col1:
                        st.write(f"{icon} **{meeting.get('title')}**")
                    with col2:
                        st.write(f"📅 {scheduled_dt}")
                    with col3:
                        st.write(f"📍 {meeting.get('location', 'TBD')}")
                    with col4:
                        if st.button("View", key=f"view_upcoming_{meeting.get('id')}"):
                            st.session_state.editing_meeting = meeting.get('id')
                            st.rerun()
            else:
                st.info("No upcoming meetings scheduled.")

    with tab3:
        st.subheader("Schedule New Meeting")
        
        with st.form("create_meeting_form"):
            c1, c2 = st.columns(2)

            with c1:
                title = st.text_input("Meeting Title *")
                meeting_type = st.selectbox("Type", ["demo", "call", "discovery", "negotiation", "check-in", "other"])
                duration = st.selectbox("Duration", [15, 30, 45, 60, 90], index=1)

            with c2:
                meeting_date = st.date_input("Date *", min_value=date.today())
                meeting_time = st.time_input("Time *")
                location = st.text_input("Location / Video Link")

            # Select related deal
            deals = storage.get_all_deals()
            deal_options = {d.get('name'): d.get('id') for d in deals}
            selected_deal = st.selectbox("Related Deal", [""] + list(deal_options.keys()))

            notes = st.text_area("Notes")

            submitted = st.form_submit_button("➕ Schedule Meeting", type="primary")

            if submitted:
                if not title or not meeting_date:
                    st.error("Please fill in required fields (Title, Date)")
                else:
                    deal_id = deal_options.get(selected_deal) if selected_deal else None
                    scheduled_dt = datetime.combine(meeting_date, meeting_time).isoformat()

                    storage.create_meeting(
                        title=title,
                        scheduled_at=scheduled_dt,
                        meeting_type=meeting_type,
                        duration_minutes=duration,
                        deal_id=deal_id,
                        location=location,
                        notes=notes
                    )
                    st.success(f"✅ Meeting '{title}' scheduled!")
                    st.rerun()

# ============================================================================
# ANALYTICS PAGE
# ============================================================================

def show_analytics():
    """Display analytics and reports"""
    st.title("📈 Analytics")
    
    # Key Metrics
    total_leads = storage.count('contacts')
    total_deals = storage.count('deals')
    won_deals = len([d for d in storage.get_all_deals() if d.get('stage') == 'closed_won'])
    total_customers = storage.count('customers')
    
    deals = storage.get_all_deals()
    pipeline_value = sum(d.get('value', 0) for d in deals 
                        if d.get('stage') in ['prospecting', 'qualification', 'proposal', 'negotiation'])
    
    customers = storage.get_all_customers()
    total_mrr = sum(c.get('mrr', 0) for c in customers)
    
    win_rate = (won_deals / total_deals * 100) if total_deals > 0 else 0
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric("Win Rate", f"{win_rate:.1f}%")
    with col2:
        st.metric("Pipeline", f"${pipeline_value/1000:.0f}K")
    with col3:
        st.metric("MRR", f"${total_mrr:,.0f}")
    with col4:
        st.metric("Avg Deal", f"${pipeline_value/total_deals:,.0f}" if total_deals > 0 else "$0")
    with col5:
        st.metric("Customers", total_customers)
    
    st.markdown("---")
    
    # Charts
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Pipeline by Stage")
        stages = ['prospecting', 'qualification', 'proposal', 'negotiation']
        stage_values = [
            sum(d.get('value', 0) for d in deals if d.get('stage') == s)
            for s in stages
        ]
        chart_df = pd.DataFrame({"Stage": [s.title() for s in stages], "Value": stage_values})
        st.bar_chart(chart_df.set_index("Stage"))
    
    with col2:
        st.subheader("Customer Health")
        if customers:
            health_df = pd.DataFrame({"Health Score": [c.get('health_score', 50) for c in customers]})
            st.bar_chart(health_df)
    
    st.markdown("---")
    
    # AI Insights
    st.subheader("🤖 AI Insights")
    
    if win_rate >= 60 and total_deals > 0:
        st.success(f"✅ **Excellent Win Rate**: Your {win_rate:.1f}% win rate is above industry average (47%)")
    elif win_rate < 40 and total_deals > 0:
        st.warning(f"⚠️ **Win Rate Alert**: Current {win_rate:.1f}% is below target")
    
    at_risk = sum(1 for c in customers if c.get('churn_risk') == 'high')
    if at_risk > 0:
        st.error(f"🚨 **Churn Alert**: {at_risk} customers at high churn risk")
    
    stalled = sum(1 for d in deals if d.get('is_stalled'))
    if stalled > 0:
        st.warning(f"⏸️ **Stalled Deals**: {stalled} deals need re-engagement")
    
    st.markdown("---")
    
    # Agent Performance
    st.subheader("⚙️ AI Agent Performance")
    
    agent_data = [
        {"Agent": "Lead Qualification", "Tasks": 1247, "Accuracy": 94, "Time Saved": 52},
        {"Agent": "Email Intelligence", "Tasks": 3421, "Accuracy": 91, "Time Saved": 128},
        {"Agent": "Sales Pipeline", "Tasks": 892, "Accuracy": 96, "Time Saved": 38},
        {"Agent": "Customer Success", "Tasks": 567, "Accuracy": 93, "Time Saved": 45},
        {"Agent": "Meeting Scheduler", "Tasks": 423, "Accuracy": 98, "Time Saved": 67},
        {"Agent": "Analytics", "Tasks": 156, "Accuracy": 99, "Time Saved": 24},
    ]
    
    st.dataframe(pd.DataFrame(agent_data), use_container_width=True, hide_index=True)

# ============================================================================
# SETTINGS PAGE
# ============================================================================

def show_settings():
    """Display settings and configuration"""
    st.title("⚙️ Settings")
    
    tab1, tab2, tab3 = st.tabs(["General", "AI Agents", "Data"])
    
    with tab1:
        st.subheader("General Settings")
        
        c1, c2 = st.columns(2)
        with c1:
            st.text_input("Company Name", "Acme Corp")
            st.text_input("Industry", "Technology")
        with c2:
            st.text_input("Timezone", "UTC")
            st.selectbox("Currency", ["USD", "EUR", "GBP", "JPY"])
    
    with tab2:
        st.subheader("AI Agent Configuration")
        
        agents = {
            "Lead Qualification": True,
            "Email Intelligence": True,
            "Sales Pipeline": True,
            "Customer Success": True,
            "Meeting Scheduler": True,
            "Analytics": True
        }
        
        for agent, enabled in agents.items():
            st.toggle(f"🤖 {agent}", value=enabled)
    
    with tab3:
        st.subheader("Data Management")
        
        stats = storage.get_stats()
        st.markdown("**Current Data:**")
        
        c1, c2, c3 = st.columns(3)
        with c1:
            st.metric("Companies", stats.get('companies', 0))
            st.metric("Contacts", stats.get('contacts', 0))
        with c2:
            st.metric("Deals", stats.get('deals', 0))
            st.metric("Customers", stats.get('customers', 0))
        with c3:
            st.metric("Emails", stats.get('emails', 0))
            st.metric("Meetings", stats.get('meetings', 0))
        

# ============================================================================
# MAIN APP LOGIC
# ============================================================================

def main():
    """Main application"""
    
    if page == "📊 Dashboard":
        show_dashboard()
    elif page == "👥 Contacts":
        show_contacts()
    elif page == "💼 Deals":
        show_deals()
    elif page == "🎉 Customers":
        show_customers()
    elif page == "📧 Emails":
        show_emails()
    elif page == "📅 Meetings":
        show_meetings()
    elif page == "📈 Analytics":
        show_analytics()
    elif page == "⚙️ Settings":
        show_settings()


if __name__ == "__main__":
    main()
