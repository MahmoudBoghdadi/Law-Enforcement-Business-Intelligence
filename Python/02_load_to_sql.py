import pandas as pd
import pymssql
from tqdm import tqdm
import sys

print("CHICAGO CRIME ANALYTICS - ETL PIPELINE")

DB_CONFIG = {
    'server': 'localhost',
    'port': '1433',
    'database': 'ChicagoCrimeAnalytics',
    'user': 'sa',
    'password': 'YourStrong@Password123'
}

DATA_FILE = "/Users/mahmoudelboghdadi/Downloads/Chicago-Crime-Analytics/data/processed/chicago_crime_clean.csv"

try:
    conn = pymssql.connect(
        server=DB_CONFIG['server'],
        port=DB_CONFIG['port'],
        user=DB_CONFIG['user'],
        password=DB_CONFIG['password'],
        database=DB_CONFIG['database']
    )
    cursor = conn.cursor()
    cursor.execute("SELECT @@VERSION")
    version = cursor.fetchone()[0]
    print(f"Connected successfully!")
    print(f"SQL Server Version: {version[:80]}...")
    
    cursor.execute("SELECT COUNT(*) FROM FactCrimeIncidents")
    existing_records = cursor.fetchone()[0]
    
    if existing_records > 0:
        print(f"\nFound {existing_records:,} existing records - clearing tables...")
        cursor.execute("DELETE FROM FactCrimeIncidents")
        cursor.execute("DELETE FROM DimDate")
        cursor.execute("DELETE FROM DimTime")
        cursor.execute("DELETE FROM DimCrimeType")
        cursor.execute("DELETE FROM DimLocation")
        cursor.execute("DBCC CHECKIDENT ('DimCrimeType', RESEED, 0)")
        cursor.execute("DBCC CHECKIDENT ('DimLocation', RESEED, 0)")
        cursor.execute("DBCC CHECKIDENT ('FactCrimeIncidents', RESEED, 0)")
        conn.commit()
        print("Tables cleared successfully")
    
    conn.close()
except Exception as e:
    print(f"Connection failed: {e}")
    sys.exit(1)

print(f"\n[STEP 2/6] Loading cleaned data from {DATA_FILE}...")

try:
    df = pd.read_csv(DATA_FILE)
    df['date'] = pd.to_datetime(df['date'])
    
    initial_count = len(df)
    print(f"Loaded {initial_count:,} records")
    print(f"Initial date range: {df['date'].min().date()} to {df['date'].max().date()}")
    
    today = pd.Timestamp.now().normalize()
    future_dates = df['date'] > today
    
    if future_dates.sum() > 0:
        print(f"Found {future_dates.sum():,} records with future dates - filtering...")
        df = df[df['date'] <= today]
    
    min_date = pd.Timestamp('2021-01-01')
    df = df[df['date'] >= min_date]
    
    print(f"Final dataset: {len(df):,} records")
    print(f"Date range: {df['date'].min().date()} to {df['date'].max().date()}")
    
except FileNotFoundError:
    print(f"File not found: {DATA_FILE}")
    sys.exit(1)
except Exception as e:
    print(f"Error loading data: {e}")
    sys.exit(1)

print("\n[STEP 3/6] Loading dimension tables...")

conn = pymssql.connect(**DB_CONFIG)
cursor = conn.cursor()

print("\n[3.1/4] DimDate...")
start_date = df['date'].min().normalize()
end_date = df['date'].max().normalize()

date_range = pd.date_range(start=start_date, end=end_date, freq='D')
dim_date_records = []

for d in date_range:
    dim_date_records.append((
        int(d.strftime('%Y%m%d')),
        d.date(),
        d.year,
        d.quarter,
        d.month,
        d.strftime('%B'),
        d.isocalendar().week,
        d.day,
        d.dayofweek,
        d.strftime('%A'),
        1 if d.dayofweek >= 5 else 0,
        0
    ))

cursor.executemany("""
    INSERT INTO DimDate (DateKey, FullDate, Year, Quarter, Month, MonthName, 
                         Week, DayOfMonth, DayOfWeek, DayName, IsWeekend, IsHoliday)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
""", dim_date_records)
conn.commit()
print(f"Loaded {len(dim_date_records):,} dates")

print("\n[3.2/4] DimTime...")
dim_time_records = []

for h in range(24):
    if 6 <= h < 12:
        time_of_day = 'Morning'
    elif 12 <= h < 18:
        time_of_day = 'Afternoon'
    elif 18 <= h < 22:
        time_of_day = 'Evening'
    else:
        time_of_day = 'Night'
    
    if 7 <= h < 15:
        shift = 'Day'
    elif 15 <= h < 23:
        shift = 'Evening'
    else:
        shift = 'Night'
    
    dim_time_records.append((h * 100, h, time_of_day, shift))

cursor.executemany("""
    INSERT INTO DimTime (TimeKey, Hour, TimeOfDay, ShiftPeriod)
    VALUES (%s, %s, %s, %s)
""", dim_time_records)
conn.commit()
print(f"Loaded {len(dim_time_records)} time periods")

print("\n[3.3/4] DimCrimeType...")

crime_types = df[['primary_type', 'description', 'severity_level', 'fbi_code', 'iucr']].drop_duplicates()

def get_category(crime_type):
    violent = ['Homicide', 'Criminal Sexual Assault', 'Robbery', 'Assault', 'Battery']
    property_crimes = ['Burglary', 'Theft', 'Motor Vehicle Theft', 'Criminal Damage']
    
    for v in violent:
        if v in crime_type:
            return 'Violent'
    for p in property_crimes:
        if p in crime_type:
            return 'Property'
    return 'Other'

crime_type_records = []
for _, row in crime_types.iterrows():
    category = get_category(str(row['primary_type']))
    crime_type_records.append((
        str(row['primary_type'])[:100],
        str(row['description'])[:255],
        int(row['severity_level']) if pd.notna(row['severity_level']) else 5,
        str(row['fbi_code'])[:10] if pd.notna(row['fbi_code']) else '',
        str(row['iucr'])[:10] if pd.notna(row['iucr']) else '',
        category
    ))

cursor.executemany("""
    INSERT INTO DimCrimeType (PrimaryType, Description, SeverityLevel, FBICode, IUCR, Category)
    VALUES (%s, %s, %s, %s, %s, %s)
""", crime_type_records)
conn.commit()
print(f"Loaded {len(crime_type_records):,} crime types")

cursor.execute("SELECT CrimeTypeKey, PrimaryType, Description FROM DimCrimeType")
crime_type_map = {(row[1], row[2]): row[0] for row in cursor.fetchall()}

print("\n[3.4/4] DimLocation...")

locations = df[['district', 'ward', 'beat', 'community_area', 'location_description',
                'location_category', 'latitude', 'longitude', 'has_valid_coords']].drop_duplicates()

location_records = []
for _, row in locations.iterrows():
    location_records.append((
        int(row['district']) if pd.notna(row['district']) else 0,
        int(row['ward']) if pd.notna(row['ward']) else 0,
        int(row['beat']) if pd.notna(row['beat']) else 0,
        int(row['community_area']) if pd.notna(row['community_area']) else 0,
        str(row['location_description'])[:255] if pd.notna(row['location_description']) else 'Unknown',
        str(row['location_category'])[:50] if pd.notna(row['location_category']) else 'Other',
        float(row['latitude']) if pd.notna(row['latitude']) else None,
        float(row['longitude']) if pd.notna(row['longitude']) else None,
        1 if row['has_valid_coords'] else 0
    ))

cursor.executemany("""
    INSERT INTO DimLocation (District, Ward, Beat, CommunityArea, LocationDescription,
                             LocationCategory, Latitude, Longitude, HasValidCoords)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
""", location_records)
conn.commit()
print(f"Loaded {len(location_records):,} locations")

cursor.execute("SELECT LocationKey, District, Ward, Beat FROM DimLocation")
location_map = {(row[1], row[2], row[3]): row[0] for row in cursor.fetchall()}

print(f"\nAll dimension tables loaded successfully")

print(f"\n[STEP 4/6] Preparing fact table data...")

fact_records = []
skipped = 0

for idx, row in tqdm(df.iterrows(), total=len(df), desc="Processing"):
    date_key = int(row['date'].strftime('%Y%m%d'))
    time_key = int(row['hour']) * 100 if pd.notna(row['hour']) else 0
    
    crime_key_tuple = (str(row['primary_type']), str(row['description']))
    crime_type_key = crime_type_map.get(crime_key_tuple)
    
    location_key_tuple = (
        int(row['district']) if pd.notna(row['district']) else 0,
        int(row['ward']) if pd.notna(row['ward']) else 0,
        int(row['beat']) if pd.notna(row['beat']) else 0
    )
    location_key = location_map.get(location_key_tuple)
    
    if not crime_type_key or not location_key:
        skipped += 1
        continue
    
    fact_records.append((
        str(row['id'])[:50],
        str(row['case_number'])[:50] if pd.notna(row['case_number']) else '',
        date_key,
        time_key,
        crime_type_key,
        location_key,
        1 if row['arrest'] else 0,
        1 if row['domestic'] else 0,
        1 if row['is_cleared'] else 0,
        1 if row['is_high_severity'] else 0,
        str(row['block'])[:100] if pd.notna(row['block']) else ''
    ))

print(f"\nPrepared {len(fact_records):,} records")
if skipped > 0:
    print(f"Skipped {skipped:,} records")

print(f"\n[STEP 5/6] Loading fact table in batches...")

batch_size = 5000
total_batches = (len(fact_records) + batch_size - 1) // batch_size

for i in tqdm(range(0, len(fact_records), batch_size), total=total_batches, desc="Loading"):
    batch = fact_records[i:i+batch_size]
    cursor.executemany("""
        INSERT INTO FactCrimeIncidents 
        (IncidentID, CaseNumber, DateKey, TimeKey, CrimeTypeKey, LocationKey,
         IsArrested, IsDomestic, IsCleared, IsHighSeverity, Block)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, batch)
    conn.commit()

print(f"\nLoaded {len(fact_records):,} incidents")

print(f"\n[STEP 6/6] Verifying data load...")

cursor.execute("SELECT COUNT(*) FROM DimDate")
date_count = cursor.fetchone()[0]

cursor.execute("SELECT COUNT(*) FROM DimTime")
time_count = cursor.fetchone()[0]

cursor.execute("SELECT COUNT(*) FROM DimCrimeType")
crime_count = cursor.fetchone()[0]

cursor.execute("SELECT COUNT(*) FROM DimLocation")
location_count = cursor.fetchone()[0]

cursor.execute("SELECT COUNT(*) FROM FactCrimeIncidents")
fact_count = cursor.fetchone()[0]

print("\nDATA LOAD SUMMARY")
print(f"DimDate records: {date_count:,}")
print(f"DimTime records: {time_count:,}")
print(f"DimCrimeType records: {crime_count:,}")
print(f"DimLocation records: {location_count:,}")
print(f"FactCrimeIncidents: {fact_count:,}")

cursor.execute("""
    SELECT TOP 5
        f.IncidentID,
        d.FullDate,
        t.TimeOfDay,
        c.PrimaryType,
        l.District
    FROM FactCrimeIncidents f
    JOIN DimDate d ON f.DateKey = d.DateKey
    JOIN DimTime t ON f.TimeKey = t.TimeKey
    JOIN DimCrimeType c ON f.CrimeTypeKey = c.CrimeTypeKey
    JOIN DimLocation l ON f.LocationKey = l.LocationKey
    ORDER BY d.FullDate DESC
""")

print("\nSAMPLE RECORDS (Most Recent 5)")
for row in cursor.fetchall():
    print(f"ID: {row[0]} | Date: {row[1]} | Time: {row[2]} | Crime: {row[3]} | District: {row[4]}")

conn.close()
print("\nETL COMPLETE!")