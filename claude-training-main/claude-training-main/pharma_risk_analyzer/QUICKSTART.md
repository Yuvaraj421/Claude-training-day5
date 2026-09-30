# 🚀 Quick Start Guide - Pharma Risk Analyzer

## 5-Minute Setup

### 1️⃣ Install Dependencies
```bash
cd /home/labuser/pharma-risk-analyzer
pip install -r requirements.txt
```
⏱️ *First time takes ~2-3 min (pandas compiles from source). Subsequent runs are instant.*

### 2️⃣ Run the Application
```bash
streamlit run main.py
```

### 3️⃣ Open in Browser
The app will auto-open at `http://localhost:8501`

---

## 📊 What You'll See

### Dashboard Shows:
- **5 Key Metrics**: Total shipments, high-risk count, temp excursions, avg/max risk
- **Risk Distribution Chart**: Visual breakdown across 5 risk categories
- **Top 5 Highest-Risk**: Quick glance at the riskiest shipments
- **AI Recommendations**: Context-aware alerts and suggestions

### Interactive Features:
- **Risk Threshold Slider**: Adjust what counts as "high-risk" (20-80 scale)
- **File Uploader**: Upload your own Excel data
- **Sample Data Checkbox**: Instantly load 150 test shipments
- **Expandable Details**: View detailed high-risk and excursion lists

---

## 📥 Using Your Own Data

### Excel Format Required:
```
Shipment_ID | Date | Destination | Product | Quantity_Units | Temp_Min_C | Temp_Max_C | 
Required_Min_C | Required_Max_C | Humidity_Min | Humidity_Max | Transit_Hours | Carrier | Status
```

### Upload Steps:
1. Prepare Excel file (.xlsx)
2. Click "Browse files" in left sidebar
3. Select your Excel file
4. Dashboard updates automatically ✅

---

## 🎯 Risk Score Examples

| Scenario | Score | Category | Status |
|----------|-------|----------|--------|
| Perfect delivery, on-time | 5-10 | 🟢 Low | ✅ Safe |
| Minor delay, no excursion | 25-35 | 🟡 Medium | ⚠️ Watch |
| 2°C over limit | 40-50 | 🟠 High | 🔍 Review |
| 5°C over limit + delayed | 70-80 | 🔴 Very High | ⚠️ Alert |
| 10°C excursion + 72hr transit | 85+ | ⛔ Critical | 🚨 Investigate |

---

## 🔧 Customization

### Adjust Risk Thresholds
Edit `risk_analyzer.py` line ~20 in `calculate_risk_scores()`:
```python
# Change multiplier to scale temperature impact
score += min(50, temp_diff * 10)  # ← Increase to 20 for stricter scoring
```

### Add New Risk Factors
Add in `calculate_risk_scores()`:
```python
# Example: penalize specific carriers
if row['Carrier'] == 'UnreliableShipper':
    score += 30
```

### Modify Recommendation Rules
Edit `generate_recommendations()` method to add custom alerts:
```python
if some_condition:
    recommendations.append("📢 Your custom recommendation")
```

---

## 🐛 Troubleshooting

| Issue | Solution |
|-------|----------|
| "ModuleNotFoundError: pandas" | Run: `pip install -r requirements.txt` |
| App won't start | Check: `pip list` includes streamlit, pandas, plotly |
| Charts not showing | Try: `streamlit cache clear && streamlit run main.py` |
| Excel upload fails | Verify file is .xlsx (not .xls) with correct column names |
| Slow performance | Use smaller files (<5000 rows) or add pagination to main.py |

---

## 📚 Deep Dive

- **Risk Algorithm**: See `risk_analyzer.py` class `PharmaRiskAnalyzer`
- **UI Components**: See `main.py` for Streamlit layout
- **Data Generation**: See `create_sample_data.py` to understand test data structure
- **Development Guide**: See `CLAUDE.md` for architecture & Claude Code integration

---

## 🎓 Learning Path

1. **Try it**: Run with sample data first
2. **Explore**: Check expandable sections for detailed drilldowns
3. **Experiment**: Upload test data, adjust thresholds
4. **Customize**: Modify `risk_analyzer.py` and reload (auto-refresh)
5. **Deploy**: Use Streamlit Cloud or Docker when ready

---

## 💡 Pro Tips

✅ **Enable autoreload**: Streamlit auto-updates when you edit code  
✅ **Sample data included**: No need to upload files to test  
✅ **Risk is customizable**: Change scoring in `risk_analyzer.py` anytime  
✅ **Mobile-friendly**: Works on tablets and phones via Streamlit  
✅ **No database needed**: Everything works with CSV/Excel files  

---

**Ready?** Run `streamlit run main.py` and see the app! 🏥✨
