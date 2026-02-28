
SELECT 
    COUNT(*) AS TotalIncidents,
    SUM(CASE WHEN IsArrested = 1 THEN 1 ELSE 0 END) AS TotalArrests,
    CAST(SUM(CASE WHEN IsArrested = 1 THEN 1 ELSE 0 END) * 100.0 / COUNT(*) AS DECIMAL(5,2)) AS ArrestRate,
    SUM(CASE WHEN IsDomestic = 1 THEN 1 ELSE 0 END) AS DomesticIncidents,
    SUM(CASE WHEN IsHighSeverity = 1 THEN 1 ELSE 0 END) AS HighSeverityCrimes,
    COUNT(DISTINCT DateKey) AS DaysCovered
FROM FactCrimeIncidents;
GO

-- Query 1.2: Crime Volume by Year and Month
-- Trend analysis showing crime patterns over time
SELECT 
    dd.Year,
    dd.MonthName,
    dd.Month,
    COUNT(*) AS IncidentCount,
    SUM(CASE WHEN IsArrested = 1 THEN 1 ELSE 0 END) AS Arrests,
    CAST(SUM(CASE WHEN IsArrested = 1 THEN 1 ELSE 0 END) * 100.0 / COUNT(*) AS DECIMAL(5,2)) AS ArrestRate
FROM FactCrimeIncidents f
JOIN DimDate dd ON f.DateKey = dd.DateKey
GROUP BY dd.Year, dd.Month, dd.MonthName
ORDER BY dd.Year, dd.Month;
GO

-- Query 1.3: Top 10 Crime Types by Volume
-- Identifies most common crimes
SELECT TOP 10
    dct.PrimaryType,
    dct.Category,
    COUNT(*) AS IncidentCount,
    CAST(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM FactCrimeIncidents) AS DECIMAL(5,2)) AS PercentOfTotal,
    AVG(dct.SeverityLevel) AS AvgSeverity,
    SUM(CASE WHEN f.IsArrested = 1 THEN 1 ELSE 0 END) AS ArrestsCount,
    CAST(SUM(CASE WHEN f.IsArrested = 1 THEN 1 ELSE 0 END) * 100.0 / COUNT(*) AS DECIMAL(5,2)) AS ArrestRate
FROM FactCrimeIncidents f
JOIN DimCrimeType dct ON f.CrimeTypeKey = dct.CrimeTypeKey
GROUP BY dct.PrimaryType, dct.Category
ORDER BY IncidentCount DESC;
GO

-- Query 1.4: Crime by District
-- Geographic distribution of crimes
SELECT 
    dl.District,
    COUNT(*) AS TotalIncidents,
    SUM(CASE WHEN f.IsArrested = 1 THEN 1 ELSE 0 END) AS Arrests,
    CAST(SUM(CASE WHEN f.IsArrested = 1 THEN 1 ELSE 0 END) * 100.0 / COUNT(*) AS DECIMAL(5,2)) AS ArrestRate,
    AVG(dct.SeverityLevel) AS AvgSeverity,
    SUM(CASE WHEN f.IsDomestic = 1 THEN 1 ELSE 0 END) AS DomesticCases
FROM FactCrimeIncidents f
JOIN DimLocation dl ON f.LocationKey = dl.LocationKey
JOIN DimCrimeType dct ON f.CrimeTypeKey = dct.CrimeTypeKey
WHERE dl.District > 0  -- Exclude unknown districts
GROUP BY dl.District
ORDER BY TotalIncidents DESC;
GO

-- Query 1.5: Temporal Patterns - Hour of Day
-- When do crimes occur most frequently?
SELECT 
    dt.Hour,
    dt.TimeOfDay,
    dt.ShiftPeriod,
    COUNT(*) AS IncidentCount,
    AVG(dct.SeverityLevel) AS AvgSeverity,
    SUM(CASE WHEN f.IsArrested = 1 THEN 1 ELSE 0 END) AS Arrests
FROM FactCrimeIncidents f
JOIN DimTime dt ON f.TimeKey = dt.TimeKey
JOIN DimCrimeType dct ON f.CrimeTypeKey = dct.CrimeTypeKey
GROUP BY dt.Hour, dt.TimeOfDay, dt.ShiftPeriod
ORDER BY dt.Hour;
GO

-- Query 1.6: Day of Week Patterns
-- Are weekends different from weekdays?
SELECT 
    dd.DayName,
    dd.IsWeekend,
    COUNT(*) AS IncidentCount,
    AVG(dct.SeverityLevel) AS AvgSeverity,
    SUM(CASE WHEN f.IsArrested = 1 THEN 1 ELSE 0 END) AS Arrests,
    CAST(SUM(CASE WHEN f.IsArrested = 1 THEN 1 ELSE 0 END) * 100.0 / COUNT(*) AS DECIMAL(5,2)) AS ArrestRate
FROM FactCrimeIncidents f
JOIN DimDate dd ON f.DateKey = dd.DateKey
JOIN DimCrimeType dct ON f.CrimeTypeKey = dct.CrimeTypeKey
GROUP BY dd.DayName, dd.DayOfWeek, dd.IsWeekend
ORDER BY dd.DayOfWeek;
GO

-- Query 1.7: Location Type Analysis
-- Where do crimes occur?
SELECT 
    dl.LocationCategory,
    COUNT(*) AS IncidentCount,
    CAST(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM FactCrimeIncidents) AS DECIMAL(5,2)) AS PercentOfTotal,
    AVG(dct.SeverityLevel) AS AvgSeverity,
    SUM(CASE WHEN f.IsArrested = 1 THEN 1 ELSE 0 END) AS Arrests
FROM FactCrimeIncidents f
JOIN DimLocation dl ON f.LocationKey = dl.LocationKey
JOIN DimCrimeType dct ON f.CrimeTypeKey = dct.CrimeTypeKey
GROUP BY dl.LocationCategory
ORDER BY IncidentCount DESC;
GO


PRINT 'Running Diagnostic Analytics Queries...';
GO

-- Query 2.1: Year-over-Year Change Analysis
-- Identifies trending crime types
WITH YearlyTrends AS (
    SELECT 
        dd.Year,
        dct.PrimaryType,
        COUNT(*) AS IncidentCount
    FROM FactCrimeIncidents f
    JOIN DimDate dd ON f.DateKey = dd.DateKey
    JOIN DimCrimeType dct ON f.CrimeTypeKey = dct.CrimeTypeKey
    GROUP BY dd.Year, dct.PrimaryType
),
YoYChange AS (
    SELECT 
        PrimaryType,
        Year,
        IncidentCount,
        LAG(IncidentCount) OVER (PARTITION BY PrimaryType ORDER BY Year) AS PrevYearCount,
        CAST((IncidentCount - LAG(IncidentCount) OVER (PARTITION BY PrimaryType ORDER BY Year)) * 100.0 / 
             NULLIF(LAG(IncidentCount) OVER (PARTITION BY PrimaryType ORDER BY Year), 0) AS DECIMAL(10,2)) AS YoYChangePercent
    FROM YearlyTrends
)
SELECT 
    PrimaryType,
    Year,
    IncidentCount,
    PrevYearCount,
    YoYChangePercent
FROM YoYChange
WHERE Year = (SELECT MAX(Year) FROM YearlyTrends)
    AND PrevYearCount IS NOT NULL
ORDER BY ABS(YoYChangePercent) DESC;
GO

-- Query 2.2: Seasonal Pattern Analysis
-- Identifies seasonal trends by quarter
SELECT 
    dct.PrimaryType,
    dd.Quarter,
    AVG(CAST(IncidentCount AS FLOAT)) AS AvgIncidentsPerDay
FROM (
    SELECT 
        f.CrimeTypeKey,
        f.DateKey,
        COUNT(*) AS IncidentCount
    FROM FactCrimeIncidents f
    GROUP BY f.CrimeTypeKey, f.DateKey
) AS DailyCounts
JOIN DimDate dd ON DailyCounts.DateKey = dd.DateKey
JOIN DimCrimeType dct ON DailyCounts.CrimeTypeKey = dct.CrimeTypeKey
WHERE dct.PrimaryType IN (
    SELECT TOP 5 PrimaryType 
    FROM DimCrimeType dct2
    JOIN FactCrimeIncidents f2 ON dct2.CrimeTypeKey = f2.CrimeTypeKey
    GROUP BY PrimaryType
    ORDER BY COUNT(*) DESC
)
GROUP BY dct.PrimaryType, dd.Quarter
ORDER BY dct.PrimaryType, dd.Quarter;
GO

-- Query 2.3: Arrest Rate Analysis by Crime Type and Time
-- Why are some crimes cleared more than others?
SELECT 
    dct.PrimaryType,
    dt.TimeOfDay,
    COUNT(*) AS TotalIncidents,
    SUM(CASE WHEN f.IsArrested = 1 THEN 1 ELSE 0 END) AS Arrests,
    CAST(SUM(CASE WHEN f.IsArrested = 1 THEN 1 ELSE 0 END) * 100.0 / COUNT(*) AS DECIMAL(5,2)) AS ArrestRate
FROM FactCrimeIncidents f
JOIN DimCrimeType dct ON f.CrimeTypeKey = dct.CrimeTypeKey
JOIN DimTime dt ON f.TimeKey = dt.TimeKey
WHERE dct.PrimaryType IN (
    SELECT TOP 10 PrimaryType 
    FROM DimCrimeType dct2
    JOIN FactCrimeIncidents f2 ON dct2.CrimeTypeKey = f2.CrimeTypeKey
    GROUP BY PrimaryType
    ORDER BY COUNT(*) DESC
)
GROUP BY dct.PrimaryType, dt.TimeOfDay
HAVING COUNT(*) >= 100  -- Minimum sample size
ORDER BY dct.PrimaryType, dt.TimeOfDay;
GO

-- Query 2.4: Crime Correlation Analysis
-- Which crime types occur together in same districts?
WITH DistrictCrimes AS (
    SELECT 
        dl.District,
        dct.PrimaryType,
        COUNT(*) AS CrimeCount
    FROM FactCrimeIncidents f
    JOIN DimLocation dl ON f.LocationKey = dl.LocationKey
    JOIN DimCrimeType dct ON f.CrimeTypeKey = dct.CrimeTypeKey
    WHERE dl.District > 0
    GROUP BY dl.District, dct.PrimaryType
    HAVING COUNT(*) >= 10
)
SELECT 
    dc1.PrimaryType AS Crime1,
    dc2.PrimaryType AS Crime2,
    COUNT(DISTINCT dc1.District) AS DistrictsWithBoth,
    AVG(dc1.CrimeCount) AS AvgCount_Crime1,
    AVG(dc2.CrimeCount) AS AvgCount_Crime2
FROM DistrictCrimes dc1
JOIN DistrictCrimes dc2 ON dc1.District = dc2.District 
    AND dc1.PrimaryType < dc2.PrimaryType  -- Avoid duplicates
GROUP BY dc1.PrimaryType, dc2.PrimaryType
HAVING COUNT(DISTINCT dc1.District) >= 15  -- Significant co-occurrence
ORDER BY DistrictsWithBoth DESC;
GO

-- Query 2.5: Domestic Violence Pattern Analysis
-- Understanding domestic crime patterns
SELECT 
    dct.PrimaryType,
    dd.DayName,
    dt.TimeOfDay,
    COUNT(*) AS DomesticIncidents,
    CAST(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (PARTITION BY dct.PrimaryType) AS DECIMAL(5,2)) AS PercentOfCrimeType,
    SUM(CASE WHEN f.IsArrested = 1 THEN 1 ELSE 0 END) AS Arrests
FROM FactCrimeIncidents f
JOIN DimCrimeType dct ON f.CrimeTypeKey = dct.CrimeTypeKey
JOIN DimDate dd ON f.DateKey = dd.DateKey
JOIN DimTime dt ON f.TimeKey = dt.TimeKey
WHERE f.IsDomestic = 1
    AND dct.PrimaryType IN ('Battery', 'Assault', 'Criminal Damage')
GROUP BY dct.PrimaryType, dd.DayName, dd.DayOfWeek, dt.TimeOfDay
ORDER BY dct.PrimaryType, dd.DayOfWeek, dt.TimeOfDay;
GO

-- Query 2.6: High-Risk Location Identification
-- Which specific beats have highest crime density?
SELECT TOP 20
    dl.District,
    dl.Beat,
    COUNT(*) AS IncidentCount,
    AVG(dct.SeverityLevel) AS AvgSeverity,
    SUM(CASE WHEN f.IsHighSeverity = 1 THEN 1 ELSE 0 END) AS HighSeverityCrimes,
    SUM(CASE WHEN f.IsArrested = 1 THEN 1 ELSE 0 END) AS Arrests,
    CAST(SUM(CASE WHEN f.IsArrested = 1 THEN 1 ELSE 0 END) * 100.0 / COUNT(*) AS DECIMAL(5,2)) AS ArrestRate
FROM FactCrimeIncidents f
JOIN DimLocation dl ON f.LocationKey = dl.LocationKey
JOIN DimCrimeType dct ON f.CrimeTypeKey = dct.CrimeTypeKey
WHERE dl.District > 0 AND dl.Beat > 0
GROUP BY dl.District, dl.Beat
ORDER BY IncidentCount DESC;
GO


PRINT 'Creating aggregated views for predictive modeling...';
GO

-- Query 3.1: Daily Crime Statistics by District
-- Time series data for forecasting
SELECT 
    dd.FullDate,
    dd.Year,
    dd.Month,
    dd.DayOfWeek,
    dd.IsWeekend,
    dl.District,
    COUNT(*) AS DailyIncidents,
    AVG(dct.SeverityLevel) AS AvgSeverity,
    SUM(CASE WHEN f.IsArrested = 1 THEN 1 ELSE 0 END) AS DailyArrests,
    SUM(CASE WHEN f.IsDomestic = 1 THEN 1 ELSE 0 END) AS DomesticIncidents
FROM FactCrimeIncidents f
JOIN DimDate dd ON f.DateKey = dd.DateKey
JOIN DimLocation dl ON f.LocationKey = dl.LocationKey
JOIN DimCrimeType dct ON f.CrimeTypeKey = dct.CrimeTypeKey
WHERE dl.District > 0
GROUP BY dd.FullDate, dd.Year, dd.Month, dd.DayOfWeek, dd.IsWeekend, dl.District
ORDER BY dd.FullDate, dl.District;
GO

-- Query 3.2: Hourly Patterns by Location Type
-- Feature engineering for ML models
SELECT 
    dt.Hour,
    dt.TimeOfDay,
    dl.LocationCategory,
    dct.Category AS CrimeCategory,
    COUNT(*) AS IncidentCount,
    AVG(dct.SeverityLevel) AS AvgSeverity
FROM FactCrimeIncidents f
JOIN DimTime dt ON f.TimeKey = dt.TimeKey
JOIN DimLocation dl ON f.LocationKey = dl.LocationKey
JOIN DimCrimeType dct ON f.CrimeTypeKey = dct.CrimeTypeKey
GROUP BY dt.Hour, dt.TimeOfDay, dl.LocationCategory, dct.Category
HAVING COUNT(*) >= 10
ORDER BY dt.Hour, dl.LocationCategory;
GO

-- ====================================
-- SECTION 4: PRESCRIPTIVE ANALYTICS
-- "What Should We Do?"
-- ====================================

PRINT 'Running Prescriptive Analytics Queries...';
GO

-- Query 4.1: High-Priority Districts for Resource Allocation
-- Recommends districts needing more resources
WITH DistrictMetrics AS (
    SELECT 
        dl.District,
        COUNT(*) AS TotalIncidents,
        AVG(dct.SeverityLevel) AS AvgSeverity,
        SUM(CASE WHEN f.IsArrested = 1 THEN 1 ELSE 0 END) AS Arrests,
        CAST(SUM(CASE WHEN f.IsArrested = 1 THEN 1 ELSE 0 END) * 100.0 / COUNT(*) AS DECIMAL(5,2)) AS ArrestRate,
        SUM(CASE WHEN f.IsHighSeverity = 1 THEN 1 ELSE 0 END) AS HighSeverityCrimes
    FROM FactCrimeIncidents f
    JOIN DimLocation dl ON f.LocationKey = dl.LocationKey
    JOIN DimCrimeType dct ON f.CrimeTypeKey = dct.CrimeTypeKey
    WHERE dl.District > 0
    GROUP BY dl.District
),
Percentiles AS (
    SELECT 
        PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY TotalIncidents) OVER () AS P75_Incidents,
        PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY AvgSeverity) OVER () AS P75_Severity,
        PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY ArrestRate) OVER () AS P25_ArrestRate
    FROM DistrictMetrics
)
SELECT DISTINCT
    dm.District,
    dm.TotalIncidents,
    dm.AvgSeverity,
    dm.ArrestRate,
    dm.HighSeverityCrimes,
    CASE 
        WHEN dm.TotalIncidents > p.P75_Incidents 
            AND dm.AvgSeverity > p.P75_Severity 
            AND dm.ArrestRate < p.P25_ArrestRate 
        THEN 'Critical - Immediate Action'
        WHEN dm.TotalIncidents > p.P75_Incidents 
            OR dm.AvgSeverity > p.P75_Severity 
        THEN 'High Priority'
        ELSE 'Standard'
    END AS PriorityLevel,
    CASE 
        WHEN dm.ArrestRate < p.P25_ArrestRate THEN 'Increase detective resources'
        WHEN dm.TotalIncidents > p.P75_Incidents THEN 'Increase patrol presence'
        WHEN dm.AvgSeverity > p.P75_Severity THEN 'Deploy specialized units'
        ELSE 'Maintain current levels'
    END AS Recommendation
FROM DistrictMetrics dm
CROSS JOIN Percentiles p
ORDER BY 
    CASE 
        WHEN dm.TotalIncidents > p.P75_Incidents 
            AND dm.AvgSeverity > p.P75_Severity 
            AND dm.ArrestRate < p.P25_ArrestRate 
        THEN 1
        WHEN dm.TotalIncidents > p.P75_Incidents 
            OR dm.AvgSeverity > p.P75_Severity 
        THEN 2
        ELSE 3
    END,
    dm.TotalIncidents DESC;
GO

-- Query 4.2: Optimal Patrol Schedule Recommendations
-- When and where to deploy patrols
WITH HourlyHotspots AS (
    SELECT 
        dl.District,
        dt.Hour,
        dt.TimeOfDay,
        dt.ShiftPeriod,
        COUNT(*) AS IncidentCount,
        AVG(dct.SeverityLevel) AS AvgSeverity,
        SUM(CASE WHEN f.IsArrested = 1 THEN 1 ELSE 0 END) AS Arrests
    FROM FactCrimeIncidents f
    JOIN DimLocation dl ON f.LocationKey = dl.LocationKey
    JOIN DimTime dt ON f.TimeKey = dt.TimeKey
    JOIN DimCrimeType dct ON f.CrimeTypeKey = dct.CrimeTypeKey
    WHERE dl.District > 0
    GROUP BY dl.District, dt.Hour, dt.TimeOfDay, dt.ShiftPeriod
)
SELECT TOP 30
    District,
    Hour,
    TimeOfDay,
    ShiftPeriod,
    IncidentCount,
    AvgSeverity,
    Arrests,
    CAST(IncidentCount * AvgSeverity AS DECIMAL(10,2)) AS RiskScore,
    CASE 
        WHEN IncidentCount > 50 AND AvgSeverity > 6 THEN '4-5 officers'
        WHEN IncidentCount > 30 OR AvgSeverity > 6 THEN '2-3 officers'
        ELSE '1-2 officers'
    END AS RecommendedPatrolSize
FROM HourlyHotspots
ORDER BY (IncidentCount * AvgSeverity) DESC;
GO

-- Query 4.3: Crime Prevention Strategy Recommendations
-- Targeted interventions by crime type and location
SELECT 
    dct.PrimaryType,
    dl.LocationCategory,
    COUNT(*) AS IncidentCount,
    CAST(SUM(CASE WHEN f.IsArrested = 1 THEN 1 ELSE 0 END) * 100.0 / COUNT(*) AS DECIMAL(5,2)) AS CurrentArrestRate,
    CASE 
        WHEN dct.PrimaryType LIKE '%Theft%' AND dl.LocationCategory = 'Street' 
            THEN 'Install security cameras and increase bike/pedestrian patrols'
        WHEN dct.PrimaryType LIKE '%Theft%' AND dl.LocationCategory = 'Commercial' 
            THEN 'Business outreach program and alarm system subsidies'
        WHEN dct.PrimaryType LIKE '%Battery%' AND dl.LocationCategory = 'Residence' 
            THEN 'Domestic violence intervention and community mediation programs'
        WHEN dct.PrimaryType LIKE '%Burglary%' 
            THEN 'Neighborhood watch activation and property marking campaigns'
        WHEN dct.PrimaryType LIKE '%Vehicle%' 
            THEN 'Anti-theft device education and parking lot security audits'
        WHEN dct.PrimaryType LIKE '%Robbery%' 
            THEN 'Enhanced lighting in high-risk areas and targeted patrols'
        ELSE 'Community engagement and visibility patrols'
    END AS PreventionStrategy,
    CASE 
        WHEN SUM(CASE WHEN f.IsArrested = 1 THEN 1 ELSE 0 END) * 100.0 / COUNT(*) < 20 
            THEN 'Focus on investigation and evidence collection training'
        ELSE 'Maintain current enforcement approach'
    END AS EnforcementRecommendation
FROM FactCrimeIncidents f
JOIN DimCrimeType dct ON f.CrimeTypeKey = dct.CrimeTypeKey
JOIN DimLocation dl ON f.LocationKey = dl.LocationKey
GROUP BY dct.PrimaryType, dl.LocationCategory
HAVING COUNT(*) >= 100
ORDER BY IncidentCount DESC;
GO

-- Query 4.4: Resource Reallocation Matrix
-- Shows which districts are over/under-resourced
WITH ResourceNeeds AS (
    SELECT 
        dl.District,
        COUNT(*) AS TotalIncidents,
        AVG(dct.SeverityLevel) AS AvgSeverity,
        (COUNT(*) * AVG(dct.SeverityLevel)) / 
            (SELECT SUM(COUNT(*) * AVG(dct.SeverityLevel)) 
             FROM FactCrimeIncidents f2
             JOIN DimLocation dl2 ON f2.LocationKey = dl2.LocationKey
             JOIN DimCrimeType dct2 ON f2.CrimeTypeKey = dct2.CrimeTypeKey
             WHERE dl2.District > 0
             GROUP BY dl2.District) * 100 AS NeededResourcePercent
    FROM FactCrimeIncidents f
    JOIN DimLocation dl ON f.LocationKey = dl.LocationKey
    JOIN DimCrimeType dct ON f.CrimeTypeKey = dct.CrimeTypeKey
    WHERE dl.District > 0
    GROUP BY dl.District
)
SELECT 
    District,
    TotalIncidents,
    CAST(AvgSeverity AS DECIMAL(5,2)) AS AvgSeverity,
    CAST(NeededResourcePercent AS DECIMAL(5,2)) AS RecommendedAllocationPercent,
    CAST((100.0 / (SELECT COUNT(DISTINCT District) FROM ResourceNeeds)) AS DECIMAL(5,2)) AS CurrentAllocationPercent,
    CAST((NeededResourcePercent - (100.0 / (SELECT COUNT(DISTINCT District) FROM ResourceNeeds))) AS DECIMAL(5,2)) AS AllocationChange,
    CASE 
        WHEN (NeededResourcePercent - (100.0 / (SELECT COUNT(DISTINCT District) FROM ResourceNeeds))) > 2 
            THEN 'Increase resources'
        WHEN (NeededResourcePercent - (100.0 / (SELECT COUNT(DISTINCT District) FROM ResourceNeeds))) < -2 
            THEN 'Reduce resources'
        ELSE 'Maintain current'
    END AS Action
FROM ResourceNeeds
ORDER BY AllocationChange DESC;
GO
