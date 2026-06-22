import streamlit as st
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime

def validate_inputs(source, destination, start_date, end_date, budget):
    """
    Validates user input fields. Returns (is_valid, error_message).
    """
    if not source.strip():
        return False, "Please enter your source location."
    if not destination.strip():
        return False, "Please enter your destination."
    if not start_date or not end_date:
        return False, "Please select both start and end travel dates."
    if start_date < datetime.today().date():
        return False, "Start date cannot be in the past. Select today's date or a future date."
    if end_date < start_date:
        return False, "Return date must be on or after the departure date."
    if budget <= 0:
        return False, "Travel budget must be a positive number greater than zero."
    return True, ""


def calculate_budget_breakdown(total_budget, allocation_pcts, days, local_currency, exchange_rate):
    """
    Calculates numerical values for budget allocation and handles currency conversion.
    """
    breakdown = {}
    total_local = total_budget * exchange_rate
    
    daily_budget_inr = total_budget / days if days > 0 else total_budget
    daily_budget_local = total_local / days if days > 0 else total_local
    
    for category, percentage in allocation_pcts.items():
        inr_value = (percentage / 100.0) * total_budget
        local_value = inr_value * exchange_rate
        breakdown[category] = {
            "percentage": percentage,
            "inr": inr_value,
            "local": local_value
        }
        
    return {
        "categories": breakdown,
        "daily_inr": daily_budget_inr,
        "daily_local": daily_budget_local,
        "total_local": total_local
    }


def generate_budget_chart(breakdown_dict, is_dark_theme=True):
    """
    Generates a beautiful Plotly Donut Chart showing the budget allocation.
    """
    categories = list(breakdown_dict.keys())
    values = [info["inr"] for info in breakdown_dict.values()]
    
    # Modern color palette matching the UI
    colors = ['#00E5FF', '#00FF87', '#00A3FF', '#8B5CF6', '#F59E0B']
    
    # Capitalize categories for the label
    labels = [cat.replace('_', ' ').title() for cat in categories]
    
    fig = go.Figure(data=[go.Pie(
        labels=labels,
        values=values,
        hole=0.55,
        marker=dict(colors=colors, line=dict(color='#0A0F1D', width=2)),
        hoverinfo='label+value+percent',
        textinfo='label+percent',
        textposition='inside',
        insidetextorientation='radial',
        textfont=dict(size=11, color='#F8FAFC' if is_dark_theme else '#0F172A')
    )])
    
    fig.update_layout(
        showlegend=False,
        margin=dict(t=10, b=10, l=10, r=10),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        width=380,
        height=320,
        annotations=[dict(
            text='Allocations',
            x=0.5, y=0.5,
            font_size=16,
            font_color='#94A3B8',
            showarrow=False
        )]
    )
    
    return fig


def generate_offline_report(inputs, plan_data, budget_info):
    """
    Generates a beautifully structured Markdown report that can be exported.
    """
    days = (inputs["end_date"] - inputs["start_date"]).days + 1
    
    report = f"""# TravelSafe-AI - Trip Report & Safety Briefing
Generated on: {datetime.today().strftime('%Y-%m-%d %H:%M:%S')}

## 🌍 Trip Summary
* **Origin**: {inputs["source"]}
* **Destination**: {inputs["destination"].title()}
* **Dates**: {inputs["start_date"]} to {inputs["end_date"]} ({days} Days)
* **Travel Type**: {inputs["travel_type"]}
* **Budget**: ₹{inputs["budget"]:,} INR (~ {budget_info["total_local"]:.2f} {plan_data["trip_overview"]["currency_code"]})
* **Languages**: {", ".join(plan_data["trip_overview"]["local_languages"])}
* **Weather Forecast**: {plan_data["trip_overview"]["weather_summary"]}
* **Safety Index**: {plan_data["trip_overview"]["safety_level"]} (Safety Risk Score: {plan_data["trip_overview"]["risk_score"]}/100)

---

## 📅 Daily Itinerary
"""
    for day in plan_data["itinerary"]:
        report += f"""
### Day {day['day']}: {day['date']}
* **Theme**: {day['theme']}
* **Morning**: {day['morning']}
* **Afternoon**: {day['afternoon']}
* **Evening**: {day['evening']}
* **Recommended Dining**: {day['dining']}
"""

    report += """
---

## 🛡️ Safety & Travel Risk Advisory
"""
    for category in plan_data["safety_recommendations"]:
        report += f"\n### {category['category']}\n"
        for tip in category["tips"]:
            report += f"- {tip}\n"

    report += f"""
### 🏥 Emergency Contacts
* **Police**: {plan_data['emergency_contacts']['police']}
* **Fire & Ambulance**: {plan_data['emergency_contacts']['fire_ambulance']}
* **Tourist Helpline**: {plan_data['emergency_contacts'].get('tourist_helpline', 'N/A')}

### 🏢 Consular Contact
* **Embassy**: {plan_data['embassy_info']['embassy_name']}
* **Address**: {plan_data['embassy_info']['address']}
* **Phone**: {plan_data['embassy_info']['phone']}
* **Website**: {plan_data['embassy_info']['website']}
"""

    report += """
---

## 🎒 Weather-Optimized Packing Checklist
"""
    for category in ["Clothing", "Electronics", "Security", "Health", "Documents", "Financial", "Personal Care"]:
        items = [x for x in plan_data["packing_list"] if x["category"].lower() == category.lower()]
        if items:
            report += f"\n### {category}\n"
            for item in items:
                report += f"- [ ] {item['item']} - *Reason: {item['reason']}*\n"

    # Add general items if not matched
    other_items = [x for x in plan_data["packing_list"] if x["category"].lower() not in [y.lower() for y in ["Clothing", "Electronics", "Security", "Health", "Documents", "Financial", "Personal Care"]]]
    if other_items:
        report += "\n### Miscellaneous / General\n"
        for item in other_items:
            report += f"- [ ] {item['item']} - *Reason: {item['reason']}*\n"

    report += """
---

## 🗣️ Emergency & Safety Language Pocket Guide
"""
    for phrase in plan_data.get("pocket_phrases", []):
        local_phrase = phrase.get("local_phrase") or phrase.get("phrase") or "N/A"
        english_meaning = phrase.get("english_meaning") or phrase.get("meaning") or "N/A"
        pronunciation = phrase.get("pronunciation") or "N/A"
        category = phrase.get("category") or "General"
        report += f"* **Local Language**: {local_phrase} — **English Meaning**: {english_meaning} (Pronunciation: *{pronunciation}*) | Category: {category}\n"

    report += f"""
---
Thank you for using TravelSafe AI. Have a safe and wonderful trip!
"""
    return report
