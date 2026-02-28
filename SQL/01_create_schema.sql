CREATE TABLE DimDate (
    DateKey INT PRIMARY KEY,
    FullDate DATE NOT NULL,
    Year INT,
    Quarter INT,
    Month INT,
    MonthName VARCHAR(20),
    Week INT,
    DayOfMonth INT,
    DayOfWeek INT,
    DayName VARCHAR(20),
    IsWeekend BIT,
    IsHoliday BIT DEFAULT 0
);


CREATE TABLE DimTime (
    TimeKey INT PRIMARY KEY,
    Hour INT,
    TimeOfDay VARCHAR(20),  
    ShiftPeriod VARCHAR(20)  
);


CREATE TABLE DimCrimeType (
    CrimeTypeKey INT PRIMARY KEY IDENTITY(1,1),
    PrimaryType VARCHAR(100) NOT NULL,
    Description VARCHAR(255),
    SeverityLevel INT,
    FBICode VARCHAR(10),
    IUCR VARCHAR(10),
    Category VARCHAR(50)  
);


CREATE TABLE DimLocation (
    LocationKey INT PRIMARY KEY IDENTITY(1,1),
    District INT,
    Ward INT,
    Beat INT,
    CommunityArea INT,
    LocationDescription VARCHAR(255),
    LocationCategory VARCHAR(50),  
    Latitude DECIMAL(10, 8),
    Longitude DECIMAL(11, 8),
    HasValidCoords BIT DEFAULT 0
);


CREATE TABLE FactCrimeIncidents (
    IncidentKey BIGINT PRIMARY KEY IDENTITY(1,1),
    IncidentID VARCHAR(50) UNIQUE NOT NULL,
    CaseNumber VARCHAR(50),
    
    
    DateKey INT FOREIGN KEY REFERENCES DimDate(DateKey),
    TimeKey INT FOREIGN KEY REFERENCES DimTime(TimeKey),
    CrimeTypeKey INT FOREIGN KEY REFERENCES DimCrimeType(CrimeTypeKey),
    LocationKey INT FOREIGN KEY REFERENCES DimLocation(LocationKey),
    
    
    IsArrested BIT DEFAULT 0,
    IsDomestic BIT DEFAULT 0,
    IsCleared BIT DEFAULT 0,
    IsHighSeverity BIT DEFAULT 0,
    
    
    Block VARCHAR(100),
    CreatedDate DATETIME DEFAULT GETDATE(),
    UpdatedDate DATETIME DEFAULT GETDATE()
);


CREATE TABLE AggCrimeStatistics (
    StatKey INT PRIMARY KEY IDENTITY(1,1),
    DateKey INT,
    CrimeTypeKey INT,
    LocationKey INT,
    IncidentCount INT,
    ArrestCount INT,
    ClearanceRate DECIMAL(5,2),
    AvgSeverity DECIMAL(5,2),
    CalculatedDate DATETIME DEFAULT GETDATE()
);

CREATE TABLE AggHotspots (
    HotspotKey INT PRIMARY KEY IDENTITY(1,1),
    LocationKey INT,
    Year INT,
    Month INT,
    IncidentCount INT,
    RiskScore DECIMAL(8,2),
    RiskLevel VARCHAR(20), 
    CalculatedDate DATETIME DEFAULT GETDATE()
);


CREATE INDEX IX_FactCrime_Date ON FactCrimeIncidents(DateKey);
CREATE INDEX IX_FactCrime_CrimeType ON FactCrimeIncidents(CrimeTypeKey);
CREATE INDEX IX_FactCrime_Location ON FactCrimeIncidents(LocationKey);
CREATE INDEX IX_FactCrime_Arrest ON FactCrimeIncidents(IsArrested);


CREATE INDEX IX_DimDate_Year ON DimDate(Year);
CREATE INDEX IX_DimDate_Month ON DimDate(Month);
CREATE INDEX IX_DimLocation_District ON DimLocation(District);
CREATE INDEX IX_DimCrimeType_Severity ON DimCrimeType(SeverityLevel);

