"""Streamlit App for AI-Powered CRM - Full CRUD Operations"""

import streamlit as st
from datetime import datetime, timedelta, date
import pandas as pd

from database.connection import storage

# ============================================================================
# PAGE CONFIGURATION
# ============================================================================

st.set_page_config(
    page_title=" Keylake",
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
    """Display emails management with full CRUD - Smart CRM Inbox"""
    st.title("📧 Email Inbox")

    # Initialize session state for email selection and assignment
    if 'selected_email_id' not in st.session_state:
        st.session_state.selected_email_id = None
    if 'email_assignees' not in st.session_state:
        st.session_state.email_assignees = ["Me", "John (Sales)", "Sarah (Support)", "Mike (Success)"]
    if 'email_templates' not in st.session_state:
        st.session_state.email_templates = [
            {"name": "Follow Up", "subject": "Following up on our conversation", "body": "Hi {{first_name}},\n\nI hope this email finds you well. I wanted to follow up on our recent conversation regarding {{company_name}}.\n\nWould you be available for a quick call this week?\n\nBest regards,\n{{sender_name}}"},
            {"name": "Demo Request", "subject": "Demo Request - {{company_name}}", "body": "Hi {{first_name}},\n\nThank you for your interest in our product! I'd love to show you how our solution can help {{company_name}}.\n\nHere are some available time slots for a demo:\n- [Date/Time 1]\n- [Date/Time 2]\n- [Date/Time 3]\n\nLooking forward to connecting!\n\nBest regards,\n{{sender_name}}"},
            {"name": "Proposal Sent", "subject": "Proposal for {{company_name}}", "body": "Hi {{first_name}},\n\nAs discussed, please find attached our proposal for {{company_name}}.\n\nKey highlights:\n- [Benefit 1]\n- [Benefit 2]\n- [Benefit 3]\n\nLet me know if you have any questions!\n\nBest regards,\n{{sender_name}}"},
            {"name": "Support Response", "subject": "Re: {{subject}}", "body": "Hi {{first_name}},\n\nThank you for reaching out. I understand your concern regarding this issue.\n\nI've looked into this and here's what I found:\n\n[Solution details]\n\nPlease let me know if this resolves your issue or if you need further assistance.\n\nBest regards,\n{{sender_name}}"},
            {"name": "Check-in", "subject": "Checking in - {{company_name}}", "body": "Hi {{first_name}},\n\nI wanted to check in and see how things are going with {{company_name}}.\n\nIs there anything I can help you with or any questions you might have?\n\nBest regards,\n{{sender_name}}"},
        ]

    # Sidebar filters
    with st.sidebar:
        st.subheader("📧 Inbox Filters")
        
        col1, col2 = st.columns(2)
        with col1:
            direction_filter = st.selectbox("Direction", ["All", "inbound", "outbound"])
        with col2:
            priority_filter = st.selectbox("Priority", ["All", "high", "medium", "low"])
        
        category_filter = st.selectbox("Category", ["All", "inquiry", "support", "sales", "partnership", "general"])
        sentiment_filter = st.selectbox("Sentiment", ["All", "positive", "neutral", "negative"])
        
        st.divider()
        
        # Quick stats
        all_emails = storage.get_all_emails(limit=500)
        inbound_count = len([e for e in all_emails if e.get('direction') == 'inbound'])
        outbound_count = len([e for e in all_emails if e.get('direction') == 'outbound'])
        unread_count = len([e for e in all_emails if e.get('direction') == 'inbound' and not e.get('response_sent')])
        high_priority = len([e for e in all_emails if e.get('priority') == 'high' and not e.get('response_sent')])
        
        st.metric("Total Emails", len(all_emails))
        st.metric("Inbound", inbound_count)
        st.metric("Outbound", outbound_count)
        st.metric("🔴 Unread", unread_count)
        st.metric("⚠️ High Priority", high_priority)

    # Main tabs
    tab1, tab2, tab3, tab4 = st.tabs(["📥 Inbox", "✉️ Compose", "📋 Templates", "📊 Analytics"])

    # ==========================================================================
    # TAB 1: INBOX VIEW
    # ==========================================================================
    with tab1:
        st.subheader("Email Inbox")

        # Get and filter emails
        emails = storage.get_all_emails(limit=200)
        
        # Apply filters
        if direction_filter != "All":
            emails = [e for e in emails if e.get('direction') == direction_filter]
        if priority_filter != "All":
            emails = [e for e in emails if e.get('priority') == priority_filter]
        if category_filter != "All":
            emails = [e for e in emails if e.get('category') == category_filter]
        if sentiment_filter != "All":
            emails = [e for e in emails if e.get('sentiment') == sentiment_filter]

        # Sort by date (newest first)
        emails = sorted(emails, key=lambda x: x.get('created_at', ''), reverse=True)

        # Search
        search = st.text_input("🔍 Search emails", placeholder="Search by subject, sender, or content...")
        if search:
            search_lower = search.lower()
            emails = [e for e in emails 
                     if search_lower in (e.get('subject') or '').lower()
                     or search_lower in (e.get('from_email') or '').lower()
                     or search_lower in (e.get('to_email') or '').lower()
                     or search_lower in (e.get('body') or '').lower()]

        if emails:
            # Display as two-column layout: email list + context panel
            list_col, context_col = st.columns([2, 1])
            
            with list_col:
                st.markdown("### Email List")
                
                for email in emails:
                    sentiment_icon = {"positive": "😊", "neutral": "😐", "negative": "😞"}.get(email.get('sentiment'), "⚪")
                    priority_icon = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(email.get('priority'), "⚪")
                    direction_icon = "📥" if email.get('direction') == 'inbound' else "📤"
                    read_status = "" if email.get('response_sent') or email.get('direction') == 'outbound' else "🔵"
                    
                    # Create a unique key for the expander
                    email_id = email.get('id', '')
                    
                    with st.expander(f"{read_status}{priority_icon} {direction_icon} **{email.get('subject') or 'No Subject'}** {sentiment_icon}", 
                                   expanded=(st.session_state.selected_email_id == email_id)):
                        
                        # Email header
                        c1, c2, c3 = st.columns([3, 2, 1])
                        with c1:
                            st.write(f"**From:** {email.get('from_email', 'Unknown')}")
                            st.write(f"**To:** {email.get('to_email', 'Unknown')}")
                        with c2:
                            created = email.get('created_at', '')[:16].replace('T', ' ') if email.get('created_at') else 'N/A'
                            st.write(f"**Date:** {created}")
                            st.write(f"**Category:** {email.get('category', 'general')}")
                        with c3:
                            st.write(f"**Priority:** {priority_icon}")
                            responded = "✅" if email.get('response_sent') else "❌"
                            st.write(f"**Responded:** {responded}")
                        
                        st.divider()
                        
                        # Email body
                        st.markdown(email.get('body', 'No content'))
                        
                        # AI Draft Response
                        if email.get('draft_response'):
                            with st.expander("🤖 AI Draft Response", expanded=False):
                                st.markdown(email.get('draft_response'))
                        
                        # Quick Actions
                        st.divider()
                        c1, c2, c3, c4 = st.columns(4)
                        
                        with c1:
                            if st.button("✏️ Edit", key=f"edit_email_{email_id}", use_container_width=True):
                                st.session_state.editing_email = email_id
                                st.session_state.selected_email_id = email_id
                                st.rerun()
                        
                        with c2:
                            if st.button("📤 Mark Sent", key=f"sent_{email_id}", 
                                       disabled=email.get('response_sent'), use_container_width=True):
                                storage.mark_email_sent(email_id)
                                st.success("Marked as sent!")
                                st.rerun()
                        
                        with c3:
                            if st.button("🔖 Add Reminder", key=f"reminder_{email_id}", use_container_width=True):
                                st.session_state.selected_email_id = email_id
                                st.rerun()
                        
                        with c4:
                            if st.button("🗑️ Delete", key=f"delete_email_{email_id}", use_container_width=True):
                                storage.delete_email(email_id)
                                st.success("Email deleted!")
                                st.rerun()
                        
                        # Edit form (inline)
                        if st.session_state.editing_email == email_id:
                            st.divider()
                            with st.form(f"edit_email_form_{email_id}"):
                                c1, c2 = st.columns(2)
                                with c1:
                                    subject = st.text_input("Subject", email.get('subject', ''))
                                    priority = st.selectbox("Priority", ["high", "medium", "low"],
                                                          index=["high", "medium", "low"].index(email.get('priority', 'medium')))
                                with c2:
                                    category = st.text_input("Category", email.get('category', ''))
                                    sentiment = st.selectbox("Sentiment", ["positive", "neutral", "negative"],
                                                           index=["positive", "neutral", "negative"].index(email.get('sentiment', 'neutral')))
                                
                                body = st.text_area("Body", email.get('body', ''), height=150)
                                draft = st.text_area("AI Draft Response", email.get('draft_response', ''), height=100)
                                
                                if st.form_submit_button("💾 Save Changes"):
                                    storage.update_email(email_id,
                                        subject=subject,
                                        body=body,
                                        priority=priority,
                                        category=category,
                                        sentiment=sentiment,
                                        draft_response=draft
                                    )
                                    st.success("Email updated!")
                                    st.session_state.editing_email = None
                                    st.rerun()
            
            with context_col:
                st.markdown("### 📋 Context Panel")
                
                # Get related contact info
                contact_id = emails[0].get('contact_id') if emails else None
                if contact_id:
                    contact = storage.get_contact(contact_id)
                    if contact:
                        st.markdown(f"**👤 Contact**")
                        st.info(f"{contact.get('first_name', '')} {contact.get('last_name', '')}\n\n{contact.get('job_title', 'N/A')}")
                        st.write(f"📧 {contact.get('email', 'N/A')}")
                        st.write(f"📱 {contact.get('phone', 'N/A')}")
                        st.write(f"🏢 {get_company_name(contact.get('company_id'))}")
                        st.write(f"📊 Lead Score: {contact.get('lead_score', 0)}")
                        st.write(f"📈 Status: {contact.get('lead_status', 'N/A')}")
                        
                        # Find related deals
                        deals = storage.get_all_deals()
                        related_deals = [d for d in deals if d.get('contact_id') == contact_id]
                        if related_deals:
                            st.divider()
                            st.markdown("**💼 Related Deals**")
                            for deal in related_deals:
                                stage_color = get_deal_stage_color(deal.get('stage', ''))
                                st.write(f"{stage_color} {deal.get('name', 'Unknown')} - ${deal.get('value', 0):,}")
                                st.write(f"   Stage: {deal.get('stage', 'N/A')} | Probability: {deal.get('probability', 0)}%")
                
                # Email history with this contact
                if contact_id:
                    st.divider()
                    st.markdown("**📜 Email History**")
                    contact_emails = [e for e in emails if e.get('contact_id') == contact_id][:5]
                    for ce in contact_emails:
                        icon = "📥" if ce.get('direction') == 'inbound' else "📤"
                        st.write(f"{icon} {ce.get('subject', 'No Subject')[:40]}...")
                
                # Assignment section (Shared Inbox)
                st.divider()
                st.markdown("**👥 Assign To**")
                assignee = st.selectbox("Assign email to", st.session_state.email_assignees, 
                                       key=f"assign_{contact_id or 'general'}")
                if st.button("📋 Assign", key=f"assign_btn_{contact_id or 'general'}", use_container_width=True):
                    st.success(f"Assigned to: {assignee}")
                
                # Quick reply with template
                st.divider()
                st.markdown("**⚡ Quick Reply**")
                selected_template = st.selectbox("Use template", [""] + [t["name"] for t in st.session_state.email_templates])
                if selected_template:
                    template = next((t for t in st.session_state.email_templates if t["name"] == selected_template), None)
                    if template:
                        st.session_state.quick_reply_subject = template["subject"]
                        st.session_state.quick_reply_body = template["body"]
                
                if st.button("📝 Use Template for Reply", key="use_template_reply"):
                    if hasattr(st.session_state, 'quick_reply_subject'):
                        st.session_state.compose_subject = st.session_state.quick_reply_subject
                        st.session_state.compose_body = st.session_state.quick_reply_body
                        st.rerun()
        else:
            st.info("📭 No emails found matching your filters.")

    # ==========================================================================
    # TAB 2: COMPOSE EMAIL
    # ==========================================================================
    with tab2:
        st.subheader("✉️ Compose New Email")

        with st.form("compose_email_form"):
            c1, c2 = st.columns(2)

            with c1:
                # Get contacts for selection
                contacts = storage.get_all_contacts()
                contact_options = {f"{c.get('first_name')} {c.get('last_name')} ({c.get('email')})": c for c in contacts}
                selected_contact_str = st.selectbox("To Contact", [""] + list(contact_options.keys()))
                
                from_email = st.text_input("From Email", "sales@ourcrm.com")
                subject = st.text_input("Subject *")

            with c2:
                direction = st.selectbox("Direction", ["outbound", "inbound"])
                priority = st.selectbox("Priority", ["high", "medium", "low"])
                category = st.selectbox("Category", ["sales", "inquiry", "support", "partnership", "general"])

            # Template selector
            template_name = st.selectbox("📋 Use Template (Optional)", [""] + [t["name"] for t in st.session_state.email_templates])
            
            body = st.text_area("Body *", height=200, 
                              value=st.session_state.get('compose_body', ''))
            
            # Merge fields info
            with st.expander("🔖 Available Merge Fields"):
                st.markdown("""
                - `{{first_name}}` - Contact's first name
                - `{{last_name}}` - Contact's last name  
                - `{{company_name}}` - Company name
                - `{{job_title}}` - Contact's job title
                - `{{sender_name}}` - Your name
                - `{{subject}}` - Email subject
                """)

            submitted = st.form_submit_button("📤 Send Email", type="primary")

            if submitted:
                if not from_email or not subject or not body:
                    st.error("Please fill in required fields (From Email, Subject, Body)")
                else:
                    # Get contact details
                    contact = contact_options.get(selected_contact_str) if selected_contact_str else None
                    contact_id = contact.get('id') if contact else None
                    to_email = contact.get('email') if contact else st.text_input("Enter recipient email")
                    
                    # Simple merge field replacement
                    merged_body = body
                    merged_subject = subject
                    if contact:
                        merged_body = merged_body.replace("{{first_name}}", contact.get('first_name', ''))
                        merged_body = merged_body.replace("{{last_name}}", contact.get('last_name', ''))
                        company = get_company_name(contact.get('company_id'))
                        merged_body = merged_body.replace("{{company_name}}", company)
                        merged_body = merged_body.replace("{{job_title}}", contact.get('job_title', ''))
                        merged_subject = merged_subject.replace("{{first_name}}", contact.get('first_name', ''))
                        merged_subject = merged_subject.replace("{{company_name}}", company)
                    
                    merged_body = merged_body.replace("{{sender_name}}", "Sales Team")
                    merged_subject = merged_subject.replace("{{subject}}", subject)
                    
                    storage.create_email(
                        from_email=from_email,
                        to_email=to_email if to_email else "",
                        subject=merged_subject,
                        body=merged_body,
                        direction=direction,
                        priority=priority,
                        category=category,
                        contact_id=contact_id,
                        response_sent=(direction == "outbound")
                    )
                    st.success("✅ Email sent successfully!")
                    st.session_state.compose_body = ''
                    st.rerun()

    # ==========================================================================
    # TAB 3: EMAIL TEMPLATES
    # ==========================================================================
    with tab3:
        st.subheader("📋 Email Templates")

        templates_tab, create_tab = st.tabs(["View Templates", "➕ Create Template"])

        with templates_tab:
            if st.session_state.email_templates:
                for i, template in enumerate(st.session_state.email_templates):
                    with st.expander(f"📄 {template['name']}"):
                        st.write(f"**Subject:** {template['subject']}")
                        st.write("**Body:**")
                        st.text_area("Template Body", template['body'], height=150, key=f"tpl_{i}")
                        
                        c1, c2 = st.columns(2)
                        with c1:
                            if st.button("✏️ Edit", key=f"edit_tpl_{i}"):
                                st.session_state.editing_template = i
                        with c2:
                            if st.button("🗑️ Delete", key=f"delete_tpl_{i}"):
                                st.session_state.email_templates.pop(i)
                                st.success("Template deleted!")
                                st.rerun()
                        
                        # Edit form
                        if st.session_state.get('editing_template') == i:
                            with st.form(f"edit_template_form_{i}"):
                                name = st.text_input("Template Name", template['name'])
                                subject = st.text_input("Subject", template['subject'])
                                body = st.text_area("Body", template['body'], height=150)
                                
                                if st.form_submit_button("💾 Save"):
                                    st.session_state.email_templates[i] = {
                                        "name": name,
                                        "subject": subject,
                                        "body": body
                                    }
                                    st.success("Template updated!")
                                    st.session_state.editing_template = None
                                    st.rerun()
            else:
                st.info("No templates created yet.")

        with create_tab:
            st.markdown("### Create New Template")
            
            with st.form("create_template_form"):
                name = st.text_input("Template Name *")
                subject = st.text_input("Subject *")
                body = st.text_area("Body *", height=200)
                
                st.info("💡 Tip: Use merge fields like {{first_name}}, {{company_name}}, {{sender_name}} to personalize emails")
                
                submitted = st.form_submit_button("➕ Create Template", type="primary")
                
                if submitted:
                    if not name or not subject or not body:
                        st.error("Please fill in all required fields")
                    else:
                        st.session_state.email_templates.append({
                            "name": name,
                            "subject": subject,
                            "body": body
                        })
                        st.success(f"✅ Template '{name}' created!")
                        st.rerun()

    # ==========================================================================
    # TAB 4: EMAIL ANALYTICS
    # ==========================================================================
    with tab4:
        st.subheader("📊 Email Analytics")

        all_emails = storage.get_all_emails(limit=500)
        
        # Metrics
        c1, c2, c3, c4, c5 = st.columns(5)
        
        total = len(all_emails)
        inbound = len([e for e in all_emails if e.get('direction') == 'inbound'])
        outbound = len([e for e in all_emails if e.get('direction') == 'outbound'])
        responded = len([e for e in all_emails if e.get('response_sent')])
        high_priority = len([e for e in all_emails if e.get('priority') == 'high'])
        
        response_rate = (responded / inbound * 100) if inbound > 0 else 0
        
        with c1:
            st.metric("Total Emails", total)
        with c2:
            st.metric("Inbound", inbound)
        with c3:
            st.metric("Outbound", outbound)
        with c4:
            st.metric("Response Rate", f"{response_rate:.1f}%")
        with c5:
            st.metric("High Priority", high_priority)
        
        st.divider()
        
        # Charts
        c1, c2 = st.columns(2)
        
        with c1:
            st.subheader("Emails by Category")
            categories = ['inquiry', 'support', 'sales', 'partnership', 'general']
            cat_data = {cat: len([e for e in all_emails if e.get('category') == cat]) for cat in categories}
            cat_df = pd.DataFrame({"Category": list(cat_data.keys()), "Count": list(cat_data.values())})
            st.bar_chart(cat_df.set_index("Category"))
        
        with c2:
            st.subheader("Emails by Sentiment")
            sentiments = ['positive', 'neutral', 'negative']
            sent_data = {s: len([e for e in all_emails if e.get('sentiment') == s]) for s in sentiments}
            sent_df = pd.DataFrame({"Sentiment": list(sent_data.keys()), "Count": list(sent_data.values())})
            st.bar_chart(sent_df.set_index("Sentiment"))
        
        st.divider()
        
        # Priority breakdown
        st.subheader("Priority Distribution")
        c1, c2, c3 = st.columns(3)
        
        with c1:
            high_count = len([e for e in all_emails if e.get('priority') == 'high'])
            st.metric("🔴 High", high_count)
        with c2:
            med_count = len([e for e in all_emails if e.get('priority') == 'medium'])
            st.metric("🟡 Medium", med_count)
        with c3:
            low_count = len([e for e in all_emails if e.get('priority') == 'low'])
            st.metric("🟢 Low", low_count)
        
        st.divider()
        
        # Recent activity table
        st.subheader("Recent Email Activity")
        if all_emails:
            recent = sorted(all_emails, key=lambda x: x.get('created_at', ''), reverse=True)[:10]
            df_data = []
            for e in recent:
                df_data.append({
                    "Date": e.get('created_at', '')[:10],
                    "Direction": "📥" if e.get('direction') == 'inbound' else "📤",
                    "Subject": e.get('subject', 'No Subject')[:40],
                    "From": e.get('from_email', ''),
                    "Priority": e.get('priority', 'medium'),
                    "Responded": "✅" if e.get('response_sent') else "❌"
                })
            st.dataframe(pd.DataFrame(df_data), use_container_width=True, hide_index=True)

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
    
    #  Insights
    st.subheader("Insights")
    
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

   

# ============================================================================
# SETTINGS PAGE
# ============================================================================

def show_settings():
    """Display settings and configuration"""
    st.title("⚙️ Settings")
    
    tab1, tab2 = st.tabs(["General", "Data"])
    
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
