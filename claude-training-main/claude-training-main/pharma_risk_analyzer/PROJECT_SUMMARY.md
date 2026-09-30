# 🏥 Pharma Risk Analyzer - Project Summary

## What You've Built

A **mini pharmaceutical supply chain risk analyzer** built in 20 minutes with Streamlit, designed to identify and prioritize high-risk shipments.

---

## 📦 Project Contents

### Core Application
```
main.py              → Streamlit UI with 6 dashboard components
risk_analyzer.py     → Risk scoring & recommendation engine  
create_sample_data.py → Generates 150 test shipments
sample_shipments.xlsx → Pre-built sample dataset
```

### Documentation
```
CLAUDE.md           → Comprehensive development guide
QUICKSTART.md       → 5-minute setup & troubleshooting
README.md           → Full feature documentation
PROJECT_SUMMARY.md  → This file
```

### Configuration
```
.claude/settings.json  → Claude Code project settings
.claude/prompt.md      → Claude context for development
requirements.txt       → Python dependencies
.gitignore            → Version control config
```

---

## 🎯 Dashboard Features

### 1. **Key Metrics** (5-Metric Card Row)
- Total shipments
- High-risk shipments (%)
- Temperature excursions (%)
- Average risk score (with max)
- Delayed shipments count

### 2. **Risk Distribution Chart** (Plotly Bar Chart)
- Visual breakdown: Low → Medium → High → Very High → Critical
- Color-coded by severity
- Hover tooltips with counts

### 3. **Top 5 Highest-Risk List** (Quick Reference)
- Shipment ID with risk emoji
- Risk score for each
- Instant identification of critical items

### 4. **AI Recommendations** (Dynamic Alerts)
- Alerts triggered by data analysis:
  - 🔴 High-risk threshold exceeded
  - 🌡️ Temperature control issues
  - 🔴 Critical shipments detected
  - 📦 Logistics delays
  - ✅ All-clear message

### 5. **Detailed Drilldown Sections** (Expandable)
- Top 10 highest-risk shipments table
- All temperature excursions detailed
- Full shipment records with filtering

### 6. **Interactive Controls** (Sidebar)
- Risk threshold slider (20-80)
- File uploader for custom data
- Sample data toggle
- Real-time filtering

---

## 🎲 Risk Scoring Algorithm

```python
score = 0

# Temperature Excursions (±5-50 points each)
if actual_max > required_max:
    score += min(50, (difference * 10))
if actual_min < required_min:
    score += min(50, (difference * 10))

# Logistics Factors
if transit_hours > 48:
    score += 10
if status == 'Delayed':
    score += 25

# Carrier Performance (0-20 points)
score += carrier_risk_score

# Final Categories
0-20   → 🟢 Low Risk
20-40  → 🟡 Medium Risk
40-60  → 🟠 High Risk
60-80  → 🔴 Very High Risk
80+    → ⛔ Critical
```

---

## 💡 Design Decisions

### Why Streamlit?
✅ No frontend framework needed  
✅ Python-only, rapid development  
✅ Auto-reload on file changes  
✅ Built-in caching & state management  
✅ Mobile-responsive UI  

### Why Plotly for Charts?
✅ Interactive hover tooltips  
✅ Professional styling  
✅ No configuration needed  
✅ Color coding by risk level  

### Why CSV Sample Data?
✅ Easy to generate programmatically  
✅ No database dependencies  
✅ Quick to test with large datasets  
✅ Users can upload their own Excel files  

### Why Risk Scoring Over ML?
✅ Interpretable and explainable  
✅ No training data needed  
✅ Domain experts can validate easily  
✅ Real-time analysis without latency  

---

## 🚀 How to Run

### First Time Setup
```bash
cd /home/labuser/pharma-risk-analyzer
pip install -r requirements.txt          # ~2-3 min (pandas compiles)
python create_sample_data.py             # Creates sample data
streamlit run main.py                    # Launches on localhost:8501
```

### Subsequent Runs
```bash
streamlit run main.py
```

### With Your Own Data
1. Prepare Excel file with columns: `Shipment_ID, Date, Destination, Product, Quantity_Units, Temp_Min_C, Temp_Max_C, Required_Min_C, Required_Max_C, Humidity_Min_Percent, Humidity_Max_Percent, Transit_Hours, Carrier, Status`
2. In sidebar: Click "Browse files" and upload
3. Adjust risk threshold slider if needed
4. Dashboard updates automatically ✅

---

## 🔧 Customization Examples

### Example 1: Change Temperature Impact
```python
# risk_analyzer.py, line ~25
score += min(50, temp_diff * 20)  # Increase from 10 to 20 for stricter
```

### Example 2: Add Humidity Excursion Penalty
```python
# risk_analyzer.py, calculate_risk_scores() method
if row['Humidity_Max_Percent'] > 80:
    score += 15  # Penalize high humidity
```

### Example 3: Custom Carrier Scoring
```python
carrier_risk = {
    'ColdChain Inc': 0,
    'PharmaCourier': 5,
    'GlobalTemp': 15,
    'BioExpress': 20,
    'NewCarrier': 25,  # Added!
}
```

### Example 4: Add New Recommendation
```python
# risk_analyzer.py, generate_recommendations() method
if delayed_count > 10:
    recommendations.append("📍 Consider alternative carriers for 20% of routes")
```

---

## 📊 Data Format Specification

### Required Excel Columns
| Column | Type | Example | Purpose |
|--------|------|---------|---------|
| Shipment_ID | String | SHIP-00001 | Unique identifier |
| Date | Date | 2026-09-05 | Shipment date |
| Destination | String | NYC | Target city |
| Product | String | Vaccine A | Drug/product name |
| Quantity_Units | Integer | 500 | Units shipped |
| Temp_Min_C | Float | 2.5 | Actual min temp |
| Temp_Max_C | Float | 7.8 | Actual max temp |
| Required_Min_C | Float | 2.0 | Specification min |
| Required_Max_C | Float | 8.0 | Specification max |
| Humidity_Min_Percent | Float | 45.0 | Actual min humidity |
| Humidity_Max_Percent | Float | 75.0 | Actual max humidity |
| Transit_Hours | Integer | 36 | Duration of shipment |
| Carrier | String | ColdChain Inc | Shipping company |
| Status | String | Delivered | Delivered/In Transit/Delayed |

---

## 🎓 Project Structure for Learning

### For Beginners
1. Run `streamlit run main.py` with sample data
2. Explore the dashboard UI
3. Try uploading your own Excel file
4. Adjust the risk threshold slider

### For Intermediate Users
1. Read `risk_analyzer.py` to understand scoring
2. Edit `create_sample_data.py` to create custom test cases
3. Modify risk weights in `calculate_risk_scores()`
4. Add new recommendation rules

### For Advanced Users
1. Implement ML-based risk prediction
2. Add real-time data integration (APIs)
3. Build alert system (SMS/Email)
4. Deploy with Docker/Kubernetes
5. Add database persistence (PostgreSQL)

---

## ✅ Deliverables Checklist

- [x] Folder structure created with all files
- [x] Streamlit dashboard built with 6 components
- [x] Risk scoring algorithm implemented
- [x] Sample data generator (150 shipments)
- [x] Interactive charts with Plotly
- [x] AI-style recommendations system
- [x] Full documentation (CLAUDE.md, README, QUICKSTART)
- [x] Git repository initialized with commits
- [x] .claude/settings.json with project config
- [x] Requirements.txt with all dependencies
- [x] Comprehensive error handling
- [x] Mobile-responsive Streamlit UI

---

## 🎯 Success Criteria Met

✅ **Total shipments display** - Shows count of all shipments  
✅ **High-risk count** - Displays number and percentage  
✅ **Temperature excursions** - Filters and counts excursions  
✅ **Top 5 highest-risk** - Sorted list with scores  
✅ **Risk distribution chart** - Plotly bar chart with 5 categories  
✅ **AI recommendations** - Context-aware alerts based on data  

---

## 🚢 Next Steps (Post-Activity)

1. **Test with real pharma data** - Upload your actual shipment records
2. **Tune scoring weights** - Adjust based on domain expertise
3. **Add historical trends** - Track risk over time
4. **Implement alerts** - Email/SMS for critical shipments
5. **Deploy to production** - Streamlit Cloud or internal server
6. **Integrate with APIs** - Connect to supply chain systems
7. **Add ML predictions** - Forecast future risk scores

---

## 💾 File Sizes

```
main.py              4.4 KB  - Streamlit UI
risk_analyzer.py     4.2 KB  - Risk engine
create_sample_data.py 2.0 KB  - Data generator
CLAUDE.md            4.7 KB  - Development guide
QUICKSTART.md        4.0 KB  - Setup guide
README.md            5.2 KB  - Full documentation
Total Code:          ~24 KB  - Lightweight & efficient
```

---

## 📝 License & Attribution

This project was created as part of a 20-minute hands-on activity to demonstrate rapid prototyping with Claude Code, Streamlit, and Python. Feel free to extend and customize for your pharmaceutical supply chain needs.

**Ready to run?**
```bash
cd /home/labuser/pharma-risk-analyzer
streamlit run main.py
```

🎉 **Happy analyzing!**
