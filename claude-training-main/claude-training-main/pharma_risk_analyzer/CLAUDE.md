# Pharma Risk Analyzer

**Quick Start**: `streamlit run main.py`

## Project Overview

A lightweight Streamlit application for analyzing pharmaceutical supply chain shipments and identifying high-risk deliveries based on temperature excursions, carrier performance, and logistics delays.

## Architecture

```
pharma-risk-analyzer/
├── main.py                  # Streamlit UI and dashboard
├── risk_analyzer.py         # Core risk calculation engine
├── create_sample_data.py    # Sample data generator
├── sample_shipments.xlsx    # Pre-generated sample dataset
├── requirements.txt         # Python dependencies
└── CLAUDE.md               # This file
```

## Key Features

1. **Automated Risk Scoring**: Calculates risk based on:
   - Temperature excursions (±5-50 points)
   - Transit time > 48 hours (+10 points)
   - Shipment delays (+25 points)
   - Carrier reliability profile (+0-20 points)

2. **Dashboard Metrics**:
   - Total shipments count
   - High-risk shipment percentage
   - Temperature excursion rate
   - Average and max risk scores
   - Delayed shipment count

3. **Risk Distribution Chart**: Visual breakdown of shipments across risk categories (Low/Medium/High/Very High/Critical)

4. **AI Recommendations**: Dynamic, context-aware recommendations based on:
   - High-risk percentage (>20% = alert)
   - Excursion rate (>10% = upgrade systems)
   - Critical shipments (>80 score = immediate action)
   - Delayed shipments (>5% = review logistics)

5. **Detailed Drilldown**: Expandable sections for:
   - Top 10 highest-risk shipments
   - All temperature excursions with min/max values

## Data Format

The Excel file must contain these columns:
- `Shipment_ID`: Unique identifier
- `Date`: Shipment date
- `Destination`: Destination city
- `Product`: Product name/type
- `Quantity_Units`: Number of units
- `Temp_Min_C`, `Temp_Max_C`: Actual temperature range
- `Required_Min_C`, `Required_Max_C`: Required temperature range
- `Humidity_Min_Percent`, `Humidity_Max_Percent`: Humidity levels
- `Transit_Hours`: Duration of shipment
- `Carrier`: Shipping company name
- `Status`: Delivery status (Delivered/In Transit/Delayed)

## How to Use

### Option 1: Use Sample Data (Quick Demo)
```bash
cd pharma-risk-analyzer
pip install -r requirements.txt
streamlit run main.py
```
The app will load sample_shipments.xlsx automatically. Enable "Use sample data" in the sidebar.

### Option 2: Upload Your Own Data
1. Prepare an Excel file matching the data format above
2. Run: `streamlit run main.py`
3. Use the file uploader in the left sidebar to upload your data
4. Adjust the High-Risk Threshold slider as needed

### Option 3: Generate Fresh Sample Data
```bash
python create_sample_data.py
streamlit run main.py
```

## Claude Code Workflow

### Skills & Components
- **dataviz**: Used for risk distribution chart (Plotly bar chart with risk-based color encoding)
- **run**: Launch the Streamlit dev server with `streamlit run main.py`

### Development Hooks (Optional)
Add to `.claude/settings.json` if desired:
```json
{
  "hooks": {
    "before_stop": "streamlit cache clear 2>/dev/null || true"
  }
}
```

### Testing Workflow
1. Edit risk_analyzer.py to adjust scoring algorithms
2. Streamlit auto-reloads on file changes
3. Upload test data or use sample_shipments.xlsx
4. Verify metrics and chart update in real-time

## Risk Scoring Formula

```
Base Score = 0
if Temp_Max > Required_Max: add min(50, (difference * 10))
if Temp_Min < Required_Min: add min(50, (difference * 10))
if Transit_Hours > 48: add 10
if Status == 'Delayed': add 25
add Carrier_Risk_Factor (0-20)

Final Score: 0-150+ (typically capped for display)
```

## Future Enhancements

- [ ] Historical trend analysis with date range filtering
- [ ] Carrier performance scorecard
- [ ] Export risk reports to PDF
- [ ] Integration with supply chain API for real-time data
- [ ] Predictive risk modeling with ML
- [ ] SMS/Email alerts for critical shipments
- [ ] Route optimization recommendations

## Dependencies

- **streamlit**: Web app framework
- **pandas**: Data manipulation
- **plotly**: Interactive charting
- **openpyxl**: Excel file handling
- **numpy**: Numerical operations

## Troubleshooting

**"ModuleNotFoundError: No module named 'streamlit'"**
→ Run: `pip install -r requirements.txt`

**"Excel file not found"**
→ Ensure sample_shipments.xlsx is in the project root, or generate it with `python create_sample_data.py`

**"Chart not displaying"**
→ Plotly may need a restart. Try: `streamlit cache clear && streamlit run main.py`

**Slow performance with large files (>5000 rows)**
→ Consider implementing data pagination or caching in risk_analyzer.py
