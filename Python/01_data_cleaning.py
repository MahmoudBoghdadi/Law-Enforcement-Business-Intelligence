import pandas as pd
import numpy as np
from datetime import datetime

print("="*70)
print("CHICAGO CRIME DATA - CLEANING PIPELINE")
print("="*70)

df = pd.read_csv("/Users/mahmoudelboghdadi/Downloads/Chicago-Crime-Analytics/data/raw/chicago_crime_2021_2025.csv")
initial_count = len(df)
print(f"   Loaded {initial_count:,} records")

# 1. Remove exact duplicates
print("\n[2/10] Removing exact duplicates...")
df = df.drop_duplicates()
print(f"   Removed {initial_count - len(df):,} duplicates")
print(f"   Remaining: {len(df):,} records")

# 2. Clean column names (standardize)
print("\n[3/10] Standardizing column names...")
df.columns = df.columns.str.strip().str.lower().str.replace(' ', '_')


# 3. Handle dates
print("\n[4/10] Processing date/time fields...")
df['date'] = pd.to_datetime(df['date'], errors='coerce')
df = df.dropna(subset=['date'])  # Remove records with invalid dates

# Extract temporal features
df['year'] = df['date'].dt.year
df['month'] = df['date'].dt.month
df['month_name'] = df['date'].dt.strftime('%B')
df['day'] = df['date'].dt.day
df['hour'] = df['date'].dt.hour
df['day_of_week'] = df['date'].dt.dayofweek  # 0=Monday, 6=Sunday
df['day_name'] = df['date'].dt.strftime('%A')
df['is_weekend'] = df['day_of_week'].isin([5, 6]).astype(int)
df['quarter'] = df['date'].dt.quarter
df['week_of_year'] = df['date'].dt.isocalendar().week

# Time of day categorization
def categorize_time(hour):
    if pd.isna(hour):
        return 'Unknown'
    elif 6 <= hour < 12:
        return 'Morning'
    elif 12 <= hour < 18:
        return 'Afternoon'
    elif 18 <= hour < 22:
        return 'Evening'
    else:
        return 'Night'

df['time_of_day'] = df['hour'].apply(categorize_time)

print(f"Temporal features created")
print(f"   Date range: {df['date'].min().date()} to {df['date'].max().date()}")

# 4. Handle missing critical fields
print("\n[5/10] Handling missing values...")
before_critical = len(df)

# Drop records missing critical fields
df = df.dropna(subset=['id', 'primary_type'])

# Fill missing coordinates with placeholder (we'll handle in analysis)
missing_coords = df['latitude'].isna().sum()
if missing_coords > 0:
    print(f"   ⚠️  {missing_coords:,} records missing coordinates (will filter during geo analysis)")

# Convert boolean fields
df['arrest'] = df['arrest'].fillna(False).astype(bool)
df['domestic'] = df['domestic'].fillna(False).astype(bool)

# Fill missing location descriptions
df['location_description'] = df['location_description'].fillna('Unknown')

print(f"   Removed {before_critical - len(df):,} records with missing critical data")
print(f"   Remaining: {len(df):,} records")

# 5. Clean crime types
print("\n[6/10] Cleaning crime type data...")
df['primary_type'] = df['primary_type'].str.strip().str.title()
df['description'] = df['description'].str.strip().str.title()

# Consolidate rare crime types
crime_counts = df['primary_type'].value_counts()
rare_crimes = crime_counts[crime_counts < 100].index
df.loc[df['primary_type'].isin(rare_crimes), 'primary_type'] = 'Other Crimes'

print(f"{df['primary_type'].nunique()} unique crime types after consolidation")

# 6. Add severity scoring
print("\n[7/10] Adding crime severity scores...")
severity_map = {
    'Homicide': 10,
    'Criminal Sexual Assault': 10,
    'Robbery': 8,
    'Aggravated Assault': 8,
    'Assault': 7,
    'Aggravated Battery': 7,
    'Battery': 6,
    'Burglary': 6,
    'Motor Vehicle Theft': 6,
    'Theft': 5,
    'Criminal Damage': 4,
    'Deceptive Practice': 4,
    'Narcotics': 5,
    'Weapons Violation': 7,
    'Other Offense': 3,
    'Other Crimes': 3
}

df['severity_level'] = df['primary_type'].map(severity_map).fillna(3)
print(f"Severity scores assigned")

# 7. Clean geographic data
print("\n[8/10] Cleaning geographic data...")
# Chicago bounds: roughly 41.6-42.1 lat, -87.9 to -87.5 long
df_with_coords = df[df['latitude'].notna() & df['longitude'].notna()].copy()

valid_coords = (
    (df_with_coords['latitude'].between(41.6, 42.1)) &
    (df_with_coords['longitude'].between(-87.95, -87.5))
)

invalid_coords = (~valid_coords).sum()
if invalid_coords > 0:
    print(f"   ⚠️  {invalid_coords:,} records with invalid coordinates (outside Chicago bounds)")
    df_with_coords = df_with_coords[valid_coords]

# Keep all records but flag which have valid coordinates
df['has_valid_coords'] = False
df.loc[df_with_coords.index, 'has_valid_coords'] = True

print(f"{df['has_valid_coords'].sum():,} records with valid coordinates")

# Convert district, ward, beat to integers (handle missing as 0)
df['district'] = pd.to_numeric(df['district'], errors='coerce').fillna(0).astype(int)
df['ward'] = pd.to_numeric(df['ward'], errors='coerce').fillna(0).astype(int)
df['beat'] = pd.to_numeric(df['beat'], errors='coerce').fillna(0).astype(int)
df['community_area'] = pd.to_numeric(df['community_area'], errors='coerce').fillna(0).astype(int)

# 8. Create derived features
print("\n[9/10] Creating derived features...")

# Clearance rate indicator (arrest = cleared)
df['is_cleared'] = df['arrest'].astype(int)

# High severity crimes
df['is_high_severity'] = (df['severity_level'] >= 7).astype(int)

# Location type categories
location_categories = {
    'Street': ['Street', 'Sidewalk', 'Alley'],
    'Residence': ['Residence', 'Apartment', 'House', 'Driveway'],
    'Commercial': ['Restaurant', 'Store', 'Bank', 'Bar', 'Gas Station', 'Commercial'],
    'Transport': ['Cta', 'Vehicle', 'Parking', 'Airport'],
    'Public': ['School', 'Park', 'Hospital', 'Church'],
    'Other': []
}

def categorize_location(loc_desc):
    if pd.isna(loc_desc):
        return 'Other'
    loc_desc_upper = str(loc_desc).upper()
    for category, keywords in location_categories.items():
        if any(keyword.upper() in loc_desc_upper for keyword in keywords):
            return category
    return 'Other'

df['location_category'] = df['location_description'].apply(categorize_location)



# 9. Final data quality checks
print("\n[10/10] Final data quality validation...")
final_count = len(df)
retention_rate = (final_count / initial_count) * 100

quality_metrics = {
    'Initial Records': initial_count,
    'Final Records': final_count,
    'Retention Rate': f"{retention_rate:.1f}%",
    'Date Coverage': f"{df['date'].min().date()} to {df['date'].max().date()}",
    'Years': sorted(df['year'].unique()),
    'Crime Types': df['primary_type'].nunique(),
    'Districts': df[df['district'] > 0]['district'].nunique(),
    'With Coordinates': df['has_valid_coords'].sum(),
    'Arrests': df['arrest'].sum(),
    'Domestic Cases': df['domestic'].sum(),
    'Avg Severity': f"{df['severity_level'].mean():.2f}"
}

print("\n" + "="*70)
print("DATA QUALITY SUMMARY")
print("="*70)
for metric, value in quality_metrics.items():
    print(f"{metric:.<30} {value}")

# 10. Save cleaned data
print("\n" + "="*70)
print("SAVING CLEANED DATA")
print("="*70)

# Save full cleaned dataset
output_path = "/Users/mahmoudelboghdadi/Downloads/Chicago-Crime-Analytics/data/processed/chicago_crime_clean.csv"
df.to_csv(output_path, index=False)
print(f"Full dataset saved: {output_path}")
print(f"Size: {df.memory_usage(deep=True).sum() / 1024**2:.1f} MB")

# Save geo-only dataset (for mapping)
geo_path = "/Users/mahmoudelboghdadi/Downloads/Chicago-Crime-Analytics/data/processed/chicago_crime_geo.csv"
df[df['has_valid_coords']].to_csv(geo_path, index=False)
print(f"Geo dataset saved: {geo_path}")
print(f"Records: {df['has_valid_coords'].sum():,}")

# Save summary statistics
summary_path = "/Users/mahmoudelboghdadi/Downloads/Chicago-Crime-Analytics/data/processed/cleaning_summary.csv"
pd.DataFrame([quality_metrics]).to_csv(summary_path, index=False)
print(f"Summary saved: {summary_path}")
