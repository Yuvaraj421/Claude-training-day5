"""Risk analysis module for pharma shipments."""
import pandas as pd
import numpy as np

class PharmaRiskAnalyzer:
    """Analyzes pharmaceutical shipments for temperature and compliance risks."""

    def __init__(self, df):
        self.df = df.copy()
        self.calculate_risk_scores()

    def calculate_risk_scores(self):
        """Calculate risk score for each shipment."""
        risk_scores = []
        excursions = []

        for idx, row in self.df.iterrows():
            score = 0
            excursion = False

            # Temperature excursion detection
            if row['Temp_Max_C'] > row['Required_Max_C']:
                temp_diff = row['Temp_Max_C'] - row['Required_Max_C']
                score += min(50, temp_diff * 10)
                excursion = True

            if row['Temp_Min_C'] < row['Required_Min_C']:
                temp_diff = row['Required_Min_C'] - row['Temp_Min_C']
                score += min(50, temp_diff * 10)
                excursion = True

            # Long transit time risk
            if row['Transit_Hours'] > 48:
                score += 10

            # Delayed status risk
            if row['Status'] == 'Delayed':
                score += 25

            # Carrier reliability (simplified)
            carrier_risk = {'PharmaCourier': 5, 'GlobalTemp': 15, 'BioExpress': 20, 'ColdChain Inc': 0}
            score += carrier_risk.get(row['Carrier'], 10)

            risk_scores.append(score)
            excursions.append(excursion)

        self.df['Risk_Score'] = risk_scores
        self.df['Temp_Excursion'] = excursions

    def get_high_risk_shipments(self, threshold=40):
        """Filter shipments with risk score above threshold."""
        return self.df[self.df['Risk_Score'] >= threshold].sort_values('Risk_Score', ascending=False)

    def get_temperature_excursions(self):
        """Get shipments with temperature excursions."""
        return self.df[self.df['Temp_Excursion'] == True]

    def get_statistics(self):
        """Get summary statistics."""
        return {
            'total_shipments': len(self.df),
            'high_risk_count': len(self.df[self.df['Risk_Score'] >= 40]),
            'excursion_count': len(self.df[self.df['Temp_Excursion'] == True]),
            'avg_risk_score': self.df['Risk_Score'].mean(),
            'max_risk_score': self.df['Risk_Score'].max(),
        }

    def get_risk_distribution(self):
        """Get risk distribution for charting."""
        bins = [0, 20, 40, 60, 80, 100]
        labels = ['Low (0-20)', 'Medium (20-40)', 'High (40-60)', 'Very High (60-80)', 'Critical (80+)']
        self.df['Risk_Category'] = pd.cut(self.df['Risk_Score'], bins=bins, labels=labels, include_lowest=True)
        return self.df['Risk_Category'].value_counts().sort_index()

    def generate_recommendations(self):
        """Generate AI-style recommendations."""
        stats = self.get_statistics()
        excursion_pct = (stats['excursion_count'] / stats['total_shipments']) * 100
        high_risk_pct = (stats['high_risk_count'] / stats['total_shipments']) * 100

        recommendations = []

        if high_risk_pct > 20:
            recommendations.append("⚠️ **High Risk Alert**: Over 20% of shipments are high-risk. Review carrier performance and route optimization.")

        if excursion_pct > 10:
            recommendations.append("🌡️ **Temperature Control**: Significant temperature excursions detected. Consider upgrading cooling systems or shorter routes.")

        if stats['max_risk_score'] > 80:
            recommendations.append("🔴 **Critical Issues**: Critical-risk shipments exist. Immediate investigation and corrective action required.")

        if 'Delayed' in self.df['Status'].values:
            delayed_pct = (len(self.df[self.df['Status'] == 'Delayed']) / stats['total_shipments']) * 100
            if delayed_pct > 5:
                recommendations.append(f"📦 **Logistics Delays**: {delayed_pct:.1f}% of shipments are delayed. Review scheduling and routing.")

        if not recommendations:
            recommendations.append("✅ **Good Compliance**: Overall shipment quality is good. Continue current practices.")

        return recommendations
