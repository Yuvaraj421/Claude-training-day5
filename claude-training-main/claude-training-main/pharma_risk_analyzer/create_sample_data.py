"""Generate sample pharma shipment dataset for testing."""
import pandas as pd
from datetime import datetime, timedelta
import random

def create_sample_data():
    """Create a sample Excel dataset with pharmaceutical shipments."""
    random.seed(42)

    num_shipments = 150
    dates = [datetime.now() - timedelta(days=random.randint(0, 90)) for _ in range(num_shipments)]

    data = {
        'Shipment_ID': [f'SHIP-{i:05d}' for i in range(1, num_shipments + 1)],
        'Date': dates,
        'Destination': random.choices(['NYC', 'LA', 'Chicago', 'Houston', 'Miami', 'Boston', 'Seattle', 'Denver'], k=num_shipments),
        'Product': random.choices(['Vaccine A', 'Vaccine B', 'Biologic X', 'Injectable Y', 'Oral Z'], k=num_shipments),
        'Quantity_Units': [random.randint(100, 5000) for _ in range(num_shipments)],
        'Temp_Min_C': [random.uniform(1, 8) for _ in range(num_shipments)],
        'Temp_Max_C': [random.uniform(8, 12) for _ in range(num_shipments)],
        'Required_Min_C': [2.0] * num_shipments,
        'Required_Max_C': [8.0] * num_shipments,
        'Humidity_Min_Percent': [random.uniform(30, 60) for _ in range(num_shipments)],
        'Humidity_Max_Percent': [random.uniform(60, 80) for _ in range(num_shipments)],
        'Transit_Hours': [random.randint(2, 72) for _ in range(num_shipments)],
        'Carrier': random.choices(['ColdChain Inc', 'PharmaCourier', 'GlobalTemp', 'BioExpress'], k=num_shipments),
        'Status': random.choices(['Delivered', 'In Transit', 'Delayed'], k=num_shipments, weights=[0.7, 0.2, 0.1]),
    }

    df = pd.DataFrame(data)

    # Add temperature excursions for some shipments
    for i in range(20):
        idx = random.randint(0, num_shipments - 1)
        df.loc[idx, 'Temp_Max_C'] = df.loc[idx, 'Required_Max_C'] + random.uniform(1, 5)

    df.to_excel('/home/labuser/pharma-risk-analyzer/sample_shipments.xlsx', index=False)
    print("✅ Sample data created: sample_shipments.xlsx")

if __name__ == '__main__':
    create_sample_data()
