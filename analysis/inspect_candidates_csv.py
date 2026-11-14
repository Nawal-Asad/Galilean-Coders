
from pathlib import Path
import pandas as pd

csv_path = get_result_path("candidate_sources.csv")

if not csv_path.exists():
    print("CSV file not found:", csv_path)
else:
    df = pd.read_csv(csv_path)

    print("Columns:")
    print(df.columns.tolist())

    print("\nNumber of rows:", len(df))

    print("\nFirst 5 rows:")
    print(df.head().to_string(index=False))
