import pandas as pd
import numpy as np
from datetime import datetime 

print("="*70)
print("CHICAGO CRIME DATA - INITIAL EXPLORATION")
print("="*70)


df = pd.read_csv("/Users/mahmoudelboghdadi/Downloads/Chicago-Crime-Analytics/data/raw/chicago_crime_2021_2025.csv")

print(f"Total Records: {len(df):,}")
print(f"Memory Usage: {df.memory_usage(deep=True).sum() / 1024**2:.1f} MB")


print("COLUMNS ({})".format(len(df.columns)))
print("="*70)
for i, col in enumerate(df.columns, 1):
    dtype = df[col].dtype
    nulls = df[col].isna().sum()
    null_pct = (nulls / len(df) * 100)
    print(f"{i:2d}. {col:25s} | {str(dtype):10s} | Nulls: {nulls:8,} ({null_pct:5.1f}%)")


print("DATE RANGE")
df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
print(f"Earliest: {df['Date'].min()}")
print(f"Latest: {df['Date'].max()}")
print(f"Years: {sorted(df['Date'].dt.year.dropna().unique())}")
print(f"Total Days: {(df['Date'].max() - df['Date'].min()).days}")


print("TOP 15 CRIME TYPES")
crime_counts = df['Primary Type'].value_counts().head(15)
for crime, count in crime_counts.items():
    pct = (count / len(df)) * 100
    bar = "█" * int(pct * 2)
    print(f"{crime:30s} {count:8,} ({pct:5.1f}%) {bar}")


print("GEOGRAPHIC COVERAGE")
print(f"Districts: {df['District'].nunique():3d} unique")
print(f"Wards: {df['Ward'].nunique():3d} unique")
print(f"Community Areas: {df['Community Area'].nunique():3d} unique")
print(f"Beats: {df['Beat'].nunique():4d} unique")
print(f"\nRecords with Coordinates: {df['Latitude'].notna().sum():,} ({df['Latitude'].notna().sum()/len(df)*100:.1f}%)")


print("ARREST & DOMESTIC VIOLENCE DATA")
arrests = df['Arrest'].sum()
domestic = df['Domestic'].sum()
print(f"Arrests Made: {arrests:,} ({arrests/len(df)*100:.1f}%)")
print(f"Domestic Violence: {domestic:,} ({domestic/len(df)*100:.1f}%)")


print("DATA QUALITY SCORE")
critical_cols = ['Date', 'Primary Type', 'Latitude', 'Longitude', 'District']
quality_score = 0
for col in critical_cols:
    completeness = (df[col].notna().sum() / len(df)) * 100
    quality_score += completeness
    status = "✅" if completeness > 95 else "⚠️" if completeness > 80 else "❌"
    print(f"{status} {col:20s}: {completeness:5.1f}% complete")

avg_quality = quality_score / len(critical_cols)
print(f"\nOverall Quality Score: {avg_quality:.1f}/100")

print(df.head()[['Date', 'Primary Type', 'Description', 'Arrest', 'District']].to_string())
