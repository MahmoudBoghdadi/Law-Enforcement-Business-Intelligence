-- Export 1: Daily crime statistics (for time series)
SELECT 
    dd.FullDate AS Date,
    dd.Year,
    dd.Month,
    dd.MonthName,
    dd.DayOfWeek,
    dd.DayName,
    dd.IsWeekend,
    dl.District,
    dct.PrimaryType AS CrimeType,
    dct.Category AS CrimeCategory,
    COUNT(*) AS IncidentCount,
    SUM(CASE WHEN f.IsArrested = 1 THEN 1 ELSE 0 END) AS Arrests,
    AVG(dct.SeverityLevel) AS AvgSeverity
FROM FactCrimeIncidents f
JOIN DimDate dd ON f.DateKey = dd.DateKey
JOIN DimLocation dl ON f.LocationKey = dl.LocationKey
JOIN DimCrimeType dct ON f.CrimeTypeKey = dct.CrimeTypeKey
GROUP BY dd.FullDate, dd.Year, dd.Month, dd.MonthName, dd.DayOfWeek, dd.DayName, dd.IsWeekend, dl.District, dct.PrimaryType, dct.Category
ORDER BY dd.FullDate;
GO

-- Export 2: Geographic data (for maps)
SELECT 
    dl.District,
    dl.Beat,
    dl.LocationCategory,
    dl.Latitude,
    dl.Longitude,
    dct.PrimaryType,
    COUNT(*) AS IncidentCount,
    AVG(dct.SeverityLevel) AS AvgSeverity
FROM FactCrimeIncidents f
JOIN DimLocation dl ON f.LocationKey = dl.LocationKey
JOIN DimCrimeType dct ON f.CrimeTypeKey = dct.CrimeTypeKey
WHERE dl.HasValidCoords = 1
GROUP BY dl.District, dl.Beat, dl.LocationCategory, dl.Latitude, dl.Longitude, dct.PrimaryType
HAVING COUNT(*) >= 5
ORDER BY IncidentCount DESC;
GO