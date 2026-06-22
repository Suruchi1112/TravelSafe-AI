import streamlit as st
import os
from PIL import Image
from datetime import datetime, timedelta
import pandas as pd

from ai_engine import generate_travel_plan
from utils import (
    validate_inputs,
    calculate_budget_breakdown,
    generate_budget_chart,
    generate_offline_report
)

# Page configuration
st.set_page_config(
    page_title="TravelSafe-AI - Intelligent Travel Planning and Safety Assistant",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Helper function to load custom CSS
def load_css(file_name):
    if os.path.exists(file_name):
        with open(file_name) as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    else:
        st.warning("Styling CSS file not found. Loading with standard theme.")

load_css("src/styles.css")

# Initialize session states
if "plan_data" not in st.session_state:
    st.session_state.plan_data = None
if "inputs" not in st.session_state:
    st.session_state.inputs = {}
if "custom_items" not in st.session_state:
    st.session_state.custom_items = []
if "checked_items" not in st.session_state:
    st.session_state.checked_items = {}

# Logo handler
logo_path = "assets/logo.png"
logo_loaded = False
try:
    if os.path.exists(logo_path):
        logo_img = Image.open(logo_path)
        logo_loaded = True
except Exception as e:
    pass

# Sidebar layout
with st.sidebar:
    if logo_loaded:
        st.image(logo_img, use_column_width=True)
    else:
        st.markdown("<h2 style='text-align: center; color: #00E5FF;'>🌍 TravelSafe AI</h2>", unsafe_allow_html=True)
    
    st.markdown("<p style='text-align: center; color: #94A3B8; font-size: 0.85rem;'>Your Intelligent Travel & Security Assistant</p>", unsafe_allow_html=True)
    st.markdown("---")
    
    # API Configurations
    st.subheader("🔑 API Configuration")
    use_demo = st.checkbox("Run in Demo Mode", value=True, help="Disable Live AI and use rich local profiles for Goa, Kerala, Ladakh, Jaipur, Tokyo, or Paris.")
    
    api_key_input = ""
    if not use_demo:
        api_key_input = st.text_input("Gemini API Key", type="password", help="Enter your Google Gemini API Key. Keys are not stored and run in-memory.")
        if not api_key_input:
            st.info("💡 You can find your Gemini API key in Google AI Studio. Running in Demo fallback since no key is supplied.")
    else:
        st.success("⚡ Demo Mode Active: High-Fidelity local data profiles will be used.")

    st.markdown("---")
    
    # Trip Planning Inputs
    st.subheader("✈️ Trip Parameters")
    
    source = st.text_input("Source Location", value="New Delhi, India", placeholder="City, Country")
    destination = st.text_input("Destination City", value="Goa, India", placeholder="City, Country")
    
    col_dates = st.columns(2)
    with col_dates[0]:
        start_date = st.date_input("Departure", min_value=datetime.today().date(), value=datetime.today().date() + timedelta(days=14))
    with col_dates[1]:
        end_date = st.date_input("Return", min_value=datetime.today().date(), value=datetime.today().date() + timedelta(days=19))
        
    budget = st.number_input("Budget (₹ INR)", min_value=1000, max_value=10000000, value=50000, step=5000)
    
    travel_type = st.selectbox("Travel Type", ["Solo", "Family", "Business", "Couples / Friends"])
    
    citizenship = st.text_input("Passport Citizenship", value="India", help="Used to automatically determine visa warnings and consular assistance addresses.")
    
    activity_level = st.select_slider("Preferred Activity Pace", options=["Relaxed", "Moderate", "Active"], value="Moderate")
    
    interests = st.multiselect(
        "Interests (Select all that apply)",
        ["Culture & Heritage", "Adventure & Outdoors", "Local Gastronomy", "Shopping & Fashion", "Nightlife", "Nature & Wildlife", "Relaxation & Wellness"],
        default=["Culture & Heritage", "Local Gastronomy"]
    )
    
    st.markdown("---")
    generate_btn = st.button("🗺️ Generate Safe Itinerary", use_container_width=True)

# Main Screen Layout
st.markdown("<div class='app-title'>TravelSafe-AI</div>", unsafe_allow_html=True)
st.markdown("<div class='app-subtitle'>Intelligent Travel Planning and Safety Assistant</div>", unsafe_allow_html=True)

# Run generation process
if generate_btn:
    # 1. Input Validation
    is_valid, err_msg = validate_inputs(source, destination, start_date, end_date, budget)
    if not is_valid:
        st.error(f"⚠️ Validation Error: {err_msg}")
    else:
        with st.spinner(f"🤖 AI is analyzing {destination} safety protocols and plotting a custom plan... Please wait."):
            inputs = {
                "source": source,
                "destination": destination,
                "start_date": start_date,
                "end_date": end_date,
                "budget": budget,
                "travel_type": travel_type,
                "citizenship": citizenship,
                "interests": interests,
                "activity_level": activity_level
            }
            
            # Fetch response
            key_to_use = None if use_demo else api_key_input
            plan_data = generate_travel_plan(inputs, api_key=key_to_use)
            
            if plan_data:
                # Save to state
                st.session_state.plan_data = plan_data
                st.session_state.inputs = inputs
                # Reset checklists
                st.session_state.custom_items = []
                st.session_state.checked_items = {}
                st.success("🎉 Travel Plan generated successfully!")
            else:
                st.error("❌ An error occurred during plan generation. Please check your API key or network connection.")

# Retrieve data from state
plan = st.session_state.plan_data
trip_inputs = st.session_state.inputs

if plan and trip_inputs:
    days = (trip_inputs["end_date"] - trip_inputs["start_date"]).days + 1
    
    # Calculate budget info
    exchange_rate = plan["trip_overview"]["exchange_rate_vs_usd"] # Treated as rate vs INR
    currency_code = plan["trip_overview"]["currency_code"]
    budget_breakdown = calculate_budget_breakdown(
        trip_inputs["budget"], 
        plan["budget_allocation"], 
        days, 
        currency_code, 
        exchange_rate
    )
    
    # Dashboard Widgets
    st.markdown("<h3 style='color: #00E5FF; margin-top: 15px;'>🌍 Trip Summary Dashboard</h3>", unsafe_allow_html=True)
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f"""
        <div class="metric-box">
            <div class="metric-label">📍 Destination</div>
            <div class="metric-value" style="font-size: 1.5rem; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">{trip_inputs['destination'].title()}</div>
            <div style="color: #94A3B8; font-size: 0.8rem;">From: {trip_inputs['source']}</div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div class="metric-box">
            <div class="metric-label">📅 Trip Duration</div>
            <div class="metric-value">{days} Days</div>
            <div style="color: #94A3B8; font-size: 0.8rem;">{trip_inputs['start_date']} to {trip_inputs['end_date']}</div>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown(f"""
        <div class="metric-box">
            <div class="metric-label">💳 Daily Budget</div>
            <div class="metric-value">₹{budget_breakdown['daily_inr']:,.0f} <span style="font-size: 0.9rem; font-weight: normal; color: #94A3B8;">INR</span></div>
            <div style="color: #94A3B8; font-size: 0.8rem;">~ {budget_breakdown['daily_local']:,.0f} {currency_code} / Day</div>
        </div>
        """, unsafe_allow_html=True)
    with col4:
        # Determine safety badge class
        risk = plan["trip_overview"]["risk_score"]
        badge_style = "badge-low" if risk < 20 else ("badge-moderate" if risk < 50 else "badge-high")
        st.markdown(f"""
        <div class="metric-box">
            <div class="metric-label">🛡️ Advisory Level</div>
            <div class="metric-value" style="font-size: 1.3rem; margin-top: 10px;">
                <span class="badge {badge_style}">{plan['trip_overview']['safety_level']}</span>
            </div>
            <div style="color: #94A3B8; font-size: 0.8rem; margin-top: 5px;">Risk Score: {risk}/100</div>
        </div>
        """, unsafe_allow_html=True)

    # Weather quick notice banner
    st.markdown(f"""
    <div class="pro-tip" style="margin-top: 15px;">
        <strong>☀️ Seasonal Weather Forecast:</strong> {plan['trip_overview']['weather_summary']} | 
        <strong>🗣️ Languages:</strong> {", ".join(plan['trip_overview']['local_languages'])}
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Main Tabs
    tab_itinerary, tab_safety, tab_packing, tab_budget = st.tabs([
        "📅 Smart Itinerary", 
        "🛡️ Safety & Consular Prep", 
        "🎒 Interactive Packing Checklist", 
        "💰 Budget Planner"
    ])

    # Tab 1: Itinerary
    with tab_itinerary:
        st.markdown("### 🗺️ Custom Itinerary Planner")
        st.markdown("<p style='color: #94A3B8; margin-bottom: 20px;'>Tailored around your interests: <b>" + ", ".join(trip_inputs['interests']) + "</b> at a <b>" + trip_inputs['activity_level'] + "</b> pace.</p>", unsafe_allow_html=True)
        
        for day in plan["itinerary"]:
            st.markdown(f"""
            <div class="itinerary-day">
                <div class="itinerary-day-title">{day['date']} - {day['theme']}</div>
                <div class="grid-3">
                    <div class="activity-item">
                        <strong>🌅 Morning</strong><br>
                        <span style="font-size: 0.9rem; color: #E2E8F0;">{day['morning']}</span>
                    </div>
                    <div class="activity-item" style="border-left-color: #00A3FF;">
                        <strong>☀️ Afternoon</strong><br>
                        <span style="font-size: 0.9rem; color: #E2E8F0;">{day['afternoon']}</span>
                    </div>
                    <div class="activity-item" style="border-left-color: #8B5CF6;">
                        <strong>🌙 Evening & Dining</strong><br>
                        <span style="font-size: 0.9rem; color: #E2E8F0;">{day['evening']}</span>
                        <div style="font-size: 0.85rem; color: #00FF87; margin-top: 5px; font-style: italic;">
                            🍽️ Eat: {day['dining']}
                        </div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

    # Tab 2: Safety & Consular
    with tab_safety:
        st.markdown("### 🛡️ Travel Risk & Emergency Readiness Briefing")
        
        # Risk Scorecard UI using nice styled progress indicators
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.markdown("<div class='card-title'>📊 Risk Domain Scorecard</div>", unsafe_allow_html=True)
        st.markdown("<p style='font-size: 0.9rem; color: #94A3B8;'>Scores represent resistance to risk (higher is better/safer):</p>", unsafe_allow_html=True)
        
        col_sc1, col_sc2 = st.columns(2)
        with col_sc1:
            st.markdown("🛡️ **Physical & Crime Safety**")
            st.progress(plan["risk_scorecard"]["physical_safety"] / 100.0)
            st.markdown(f"<span style='color: #00FF87; font-weight: bold;'>{plan['risk_scorecard']['physical_safety']}/100</span> (Safe from violent crime)", unsafe_allow_html=True)
            
            st.markdown("<br>🏥 **Health & Medical Access**", unsafe_allow_html=True)
            st.progress(plan["risk_scorecard"]["health_medical"] / 100.0)
            st.markdown(f"<span style='color: #00FF87; font-weight: bold;'>{plan['risk_scorecard']['health_medical']}/100</span> (Sanitation and hospital standards)", unsafe_allow_html=True)
            
        with col_sc2:
            st.markdown("👛 **Theft & Scam Resistance**")
            st.progress(plan["risk_scorecard"]["scams_theft"] / 100.0)
            st.markdown(f"<span style='color: #00FF87; font-weight: bold;'>{plan['risk_scorecard']['scams_theft']}/100</span> (Protection from theft/petty fraud)", unsafe_allow_html=True)
            
            st.markdown("<br>👩 Solo Traveler Safety", unsafe_allow_html=True)
            st.progress(plan["risk_scorecard"]["solo_traveler"] / 100.0)
            st.markdown(f"<span style='color: #00FF87; font-weight: bold;'>{plan['risk_scorecard']['solo_traveler']}/100</span> (Solo friendliness and walkability)", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
        
        # Local Recommendations
        col_saf_rec1, col_saf_rec2 = st.columns(2)
        with col_saf_rec1:
            for rec in plan["safety_recommendations"][:1]:
                st.markdown(f"""
                <div class="card">
                    <div class="card-title">⚠️ {rec['category']}</div>
                    <ul>
                        {"".join([f"<li style='font-size: 0.95rem; color: #E2E8F0; margin-bottom: 6px;'>{tip}</li>" for tip in rec['tips']])}
                    </ul>
                </div>
                """, unsafe_allow_html=True)
        with col_saf_rec2:
            # Show the scams or second category
            recs_to_show = plan["safety_recommendations"][1:] if len(plan["safety_recommendations"]) > 1 else plan["safety_recommendations"]
            for rec in recs_to_show:
                st.markdown(f"""
                <div class="card">
                    <div class="card-title">🚨 {rec['category']}</div>
                    <ul>
                        {"".join([f"<li style='font-size: 0.95rem; color: #E2E8F0; margin-bottom: 6px;'>{tip}</li>" for tip in rec['tips']])}
                    </ul>
                </div>
                """, unsafe_allow_html=True)
                
        # Consular Finder and emergency numbers
        col_c1, col_c2 = st.columns([2, 1])
        with col_c1:
            st.markdown(f"""
            <div class="card">
                <div class="card-title">🏢 Consular / Support Contact ({trip_inputs['citizenship']})</div>
                <p style="font-size: 0.9rem; color: #94A3B8;">Embassy or local office details for a citizen of <b>{trip_inputs['citizenship']}</b> traveling to <b>{trip_inputs['destination'].title()}</b>.</p>
                <div class="embassy-card">
                    <strong>📍 {plan['embassy_info']['embassy_name']}</strong><br>
                    🏛️ Address: {plan['embassy_info']['address']}<br>
                    📞 Phone: {plan['embassy_info']['phone']}<br>
                    🌐 Website: <a href="{plan['embassy_info']['website']}" target="_blank" style="color: #00E5FF;">{plan['embassy_info']['website']}</a>
                </div>
            </div>
            """, unsafe_allow_html=True)
        with col_c2:
            st.markdown(f"""
            <div class="card" style="height: 100%;">
                <div class="card-title">📞 Emergency Hotline</div>
                <div style="font-size: 0.95rem; line-height: 1.6;">
                    🚨 <b>Police:</b> <span style="color: #EF4444; font-weight: bold; font-size: 1.1rem;">{plan['emergency_contacts']['police']}</span><br>
                    🚒 <b>Fire & Ambulance:</b> <span style="color: #EF4444; font-weight: bold; font-size: 1.1rem;">{plan['emergency_contacts']['fire_ambulance']}</span><br>
                    ☎️ <b>Tourist Support:</b> <span style="color: #00FF87;">{plan['emergency_contacts'].get('tourist_helpline', 'N/A')}</span>
                </div>
                <div class="warning-callout" style="padding: 8px; margin-top: 10px; font-size: 0.8rem;">
                    ⚠️ Save these hotlines in your contacts before boarding.
                </div>
            </div>
            """, unsafe_allow_html=True)

        # Language pocket phrases
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.markdown("<div class='card-title'>🗣️ Safety & Emergency Language Pocket Guide</div>", unsafe_allow_html=True)
        st.markdown("<p style='font-size: 0.9rem; color: #94A3B8;'>Keep these phrases handy in case of emergencies or for basic polite conversation:</p>", unsafe_allow_html=True)
        
        phr_cols = st.columns(3)
        for i, phrase in enumerate(plan["pocket_phrases"]):
            col_idx = i % 3
            with phr_cols[col_idx]:
                st.markdown(f"""
                <div style="background: rgba(255,255,255,0.03); padding: 10px; border-radius: 6px; margin-bottom: 8px; border-left: 2px solid #00E5FF;">
                    <div style="font-size: 1rem; color: #F8FAFC; font-weight: bold;">"{phrase['phrase']}"</div>
                    <div style="font-size: 0.8rem; color: #94A3B8; font-style: italic;">Pronunciation: {phrase['pronunciation']}</div>
                    <div style="font-size: 0.85rem; color: #00FF87; margin-top: 2px;">Meaning: {phrase['meaning']}</div>
                </div>
                """, unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    # Tab 3: Packing Checklist
    with tab_packing:
        st.markdown("### 🎒 Weather-Optimized Packing Checklist")
        st.markdown("<p style='color: #94A3B8;'>Check items off as you pack. Streamlit will remember checked items during your session.</p>", unsafe_allow_html=True)
        
        # Add custom item builder
        col_add1, col_add2 = st.columns([3, 1])
        with col_add1:
            new_item = st.text_input("Need to pack something specific? Add custom items here:", key="new_packing_input", placeholder="e.g. Hiking boots, Asthma inhaler, Scuba card")
        with col_add2:
            st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
            add_item_btn = st.button("➕ Add Custom Item", use_container_width=True)
            
        if add_item_btn and new_item.strip():
            st.session_state.custom_items.append({
                "item": new_item.strip(),
                "category": "Custom Items",
                "reason": "User-added custom checklist item."
            })
            st.success(f"Added '{new_item}' to your packing checklist!")
            st.rerun()

        # Combine AI list and custom items
        full_packing_list = plan["packing_list"] + st.session_state.custom_items
        
        # Group list by category
        categories = sorted(list(set([x["category"] for x in full_packing_list])))
        
        for cat in categories:
            st.markdown(f"#### 📂 {cat}")
            cat_items = [x for x in full_packing_list if x["category"] == cat]
            
            # Display items in columns
            for x in cat_items:
                item_key = f"pack_{cat}_{x['item']}"
                # Get previous state
                default_val = st.session_state.checked_items.get(item_key, False)
                
                checked = st.checkbox(
                    f"**{x['item']}** — *{x['reason']}*",
                    value=default_val,
                    key=item_key
                )
                st.session_state.checked_items[item_key] = checked
            st.markdown("---")

    # Tab 4: Budget
    with tab_budget:
        st.markdown("### 💰 Trip Budgeting & Expense Allocator")
        
        col_b1, col_b2 = st.columns([1, 1.2])
        with col_b1:
            st.markdown("<div class='card' style='height: 100%;'>", unsafe_allow_html=True)
            st.markdown("<div class='card-title'>💵 Budget Overview</div>", unsafe_allow_html=True)
            
            st.markdown(f"""
            <div style="font-size: 1rem; line-height: 1.8;">
                💵 <b>Total Budget:</b> <span style="color: #00E5FF; font-weight: bold;">₹{trip_inputs['budget']:,} INR</span><br>
                💱 <b>Local Currency Code:</b> <span style="color: #00FF87; font-weight: bold;">{currency_code}</span><br>
                📉 <b>Exchange Rate:</b> 1 INR = <span style="color: #00FF87; font-weight: bold;">{exchange_rate:.4f} {currency_code}</span><br>
                🏛️ <b>Total Local Currency:</b> <span style="color: #00FF87; font-weight: bold;">{budget_breakdown['total_local']:,.2f} {currency_code}</span>
            </div>
            <hr style="margin: 15px 0; border: 0; border-top: 1px solid rgba(255,255,255,0.08);">
            <div style="font-size: 1.1rem;">
                📅 <b>Daily Budget Allocation:</b><br>
                • <b>INR:</b> <span style="color: #00E5FF; font-weight: bold;">₹{budget_breakdown['daily_inr']:,.2f} / Day</span><br>
                • <b>{currency_code}:</b> <span style="color: #00FF87; font-weight: bold;">{budget_breakdown['daily_local']:,.2f} / Day</span>
            </div>
            """, unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)
            
        with col_b2:
            st.markdown("<div class='card' style='text-align: center;'>", unsafe_allow_html=True)
            st.markdown("<div class='card-title' style='text-align: left;'>📊 Expense Category Allocation</div>", unsafe_allow_html=True)
            
            # Generate donut chart
            fig = generate_budget_chart(budget_breakdown["categories"])
            st.plotly_chart(fig, use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)
            
        # Detailed Allocation Table
        st.markdown("<h4 style='color: #00E5FF; margin-top: 20px;'>📝 Allocation Breakdown Matrix</h4>", unsafe_allow_html=True)
        
        table_rows = []
        for cat, values in budget_breakdown["categories"].items():
            table_rows.append({
                "Category": cat.replace('_', ' ').title(),
                "Percentage (%)": f"{values['percentage']:.1f}%",
                "Value (INR)": f"₹{values['inr']:,.2f}",
                "Value (Local Currency)": f"{values['local']:,.2f} {currency_code}"
            })
            
        df_budget = pd.DataFrame(table_rows)
        st.dataframe(df_budget, use_container_width=True, hide_index=True)

    # Export Trip Details Section
    st.markdown("---")
    st.markdown("### 📥 Save Trip Planning Offline")
    st.markdown("<p style='color: #94A3B8;'>Generate and download a comprehensive trip file. Keep this file locally on your mobile phone or laptop for offline safety and reference during transit.</p>", unsafe_allow_html=True)
    
    # Generate the markdown report
    markdown_report = generate_offline_report(trip_inputs, plan, budget_breakdown)
    
    st.download_button(
        label="📥 Download Trip Briefing Report (.md)",
        data=markdown_report,
        file_name=f"TravelSafe_AI_Briefing_{trip_inputs['destination'].replace(' ', '_')}.md",
        mime="text/markdown",
        use_container_width=True
    )
else:
    # App Welcome Dashboard
    st.info("👈 Enter your origin, destination, and budget details in the sidebar and click 'Generate Safe Itinerary' to begin planning!")
    
    col_welcome1, col_welcome2 = st.columns(2)
    with col_welcome1:
        st.markdown("""
        <div class="card">
            <div class="card-title">🤖 AI-Powered Itineraries</div>
            <p style="font-size: 0.95rem; color: #E2E8F0; line-height: 1.6;">
                Get days custom-fit to your travel goals and physical capacity. Our AI ensures sightseeing, cultural interactions, and relaxing intervals are harmonized and paced correctly.
            </p>
        </div>
        <div class="card">
            <div class="card-title">🎒 Adaptive Packing Checklists</div>
            <p style="font-size: 0.95rem; color: #E2E8F0; line-height: 1.6;">
                No more packing mistakes. TravelSafe AI estimates weather constraints and trip types to build lists covering electronics adaptors, clothing styles, and safety/medical items.
            </p>
        </div>
        """, unsafe_allow_html=True)
        
    with col_welcome2:
        st.markdown("""
        <div class="card">
            <div class="card-title">🛡️ Smart Travel Safety Guards</div>
            <p style="font-size: 0.95rem; color: #E2E8F0; line-height: 1.6;">
                View country warnings, localized scams, consular locations, emergency contact numbers, and essential travel language guidelines to stay prepared for any emergency.
            </p>
        </div>
        <div class="card">
            <div class="card-title">💰 Dynamic Expense Breakdown</div>
            <p style="font-size: 0.95rem; color: #E2E8F0; line-height: 1.6;">
                Visualize how your funds are distributed across accommodation, transit, food, and emergency reserves. View costs in INR and local currencies with simulated exchange estimators.
            </p>
        </div>
        """, unsafe_allow_html=True)
