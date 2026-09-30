# 🏥 Pharma Shipment Risk Analyzer

A real-time supply chain risk analysis tool for pharmaceutical shipments built with Streamlit, designed to identify temperature excursions, logistics delays, and compliance risks.

## 🚀 Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Generate sample data (optional - will auto-load)
python create_sample_data.py

# Run the application
streamlit run main.py
```

Then open your browser to `http://localhost:8501`

## 📊 Features

✅ **Dashboard Metrics**
- Total shipments count
- High-risk shipment percentage
- Temperature excursion rate
- Average and max risk scores
- Delayed shipment tracking

✅ **Risk Analysis**
- Automated risk scoring algorithm
- Temperature excursion detection
- Carrier performance evaluation
- Transit time analysis

✅ **Visualizations**
- Risk distribution bar chart
- Top 5 highest-risk shipments list
- Detailed excursion drill-down
- Full shipment details view

✅ **AI Recommendations**
- Dynamic, context-aware insights
- Actionable recommendations based on:
  - High-risk thresholds (>20%)
  - Temperature excursion rates (>10%)
  - Critical shipments (>80 score)
  - Logistics delays (>5%)

## 📁 Project Structure

```
pharma-risk-analyzer/
├── main.py                    # Streamlit dashboard
├── risk_analyzer.py           # Risk calculation engine
├── create_sample_data.py      # Sample dataset generator
├── sample_shipments.xlsx      # Pre-generated test data
├── requirements.txt           # Python dependencies
├── .claude/settings.json      # Claude Code configuration
├── CLAUDE.md                  # Development guide
└── README.md                  # This file
```

## 📊 Risk Scoring System

| Factor | Points | Condition |
|--------|--------|-----------|
| Temp Excursion High | 5-50 | Max > Required Max |
| Temp Excursion Low | 5-50 | Min < Required Min |
| Long Transit | 10 | > 48 hours |
| Delayed Status | 25 | Status = "Delayed" |
| Carrier Risk | 0-20 | ColdChain Inc (0) → BioExpress (20) |

**Risk Categories:**
- 🟢 **Low**: 0-20
- 🟡 **Medium**: 20-40
- 🟠 **High**: 40-60
- 🔴 **Very High**: 60-80
- ⛔ **Critical**: 80+

## 📤 Data Format

Upload an Excel file (.xlsx) with these columns:

| Column | Type | Description |
|--------|------|-------------|
| Shipment_ID | String | Unique identifier |
| Date | Date | Shipment date |
| Destination | String | City destination |
| Product | String | Product/drug name |
| Quantity_Units | Integer | Units shipped |
| Temp_Min_C | Float | Actual min temperature |
| Temp_Max_C | Float | Actual max temperature |
| Required_Min_C | Float | Required min temperature |
| Required_Max_C | Float | Required max temperature |
| Humidity_Min_Percent | Float | Min humidity % |
| Humidity_Max_Percent | Float | Max humidity % |
| Transit_Hours | Integer | Duration in hours |
| Carrier | String | Shipping company |
| Status | String | Delivered/In Transit/Delayed |

## 🔧 Configuration

Edit `.claude/settings.json` to customize:
- Default risk threshold
- Enabled skills (dataviz, run)
- Development hooks

## 🧪 Testing

1. **Use Sample Data**: Enable "Use sample data" in sidebar for instant testing
2. **Upload Custom**: Use the file uploader to analyze your data
3. **Generate Fresh**: Run `python create_sample_data.py` for new sample data

## 🎯 Use Cases

- **Compliance Auditing**: Identify shipments violating temperature requirements
- **Carrier Performance**: Compare carrier reliability scores
- **Route Optimization**: Find patterns in delayed/high-risk routes
- **Risk Prioritization**: Focus investigation on critical shipments
- **Trend Analysis**: Monitor risk metrics over time

## 📦 Dependencies

- **streamlit** - Web UI framework
- **pandas** - Data manipulation
- **plotly** - Interactive charting
- **openpyxl** - Excel file support
- **numpy** - Numerical computation

## 🤖 AI Integration

The AI Recommendations section uses rule-based logic to generate context-aware insights:

```python
# Pseudo-logic for recommendations
if high_risk_pct > 20:
    suggest("Review carrier performance and routing")
if excursion_pct > 10:
    suggest("Upgrade cooling systems or shorten routes")
if max_risk_score > 80:
    suggest("Investigate critical shipments immediately")
if delayed_pct > 5:
    suggest("Review scheduling and logistics partners")
```

Extend this in `risk_analyzer.py:generate_recommendations()` for more sophisticated analysis.

## 🚀 Deployment

**Streamlit Cloud** (easiest):
```bash
git push  # to GitHub
# Go to share.streamlit.io and connect your repo
```

**Docker**:
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY . .
RUN pip install -r requirements.txt
CMD ["streamlit", "run", "main.py"]
```

**Local Server**:
```bash
streamlit run main.py --server.port 8080 --server.address 0.0.0.0
```

## 📝 License

MIT - Use freely in your projects

## 🤝 Contributing

Suggestions for enhancements:
1. Historical trend analysis
2. Predictive risk modeling with ML
3. Real-time data API integration
4. Alert notifications (SMS/Email)
5. Performance dashboards by carrier
6. Route optimization engine

---

**Questions?** Check CLAUDE.md for development notes or review risk_analyzer.py for the scoring algorithm.
# pharma_risk_analyzer
