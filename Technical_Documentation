## Model Performance Analysis

### Crime Type Classifier Results

The Random Forest model was trained on 677,967 incidents and tested on 169,492 incidents, representing an 80-20 split. The model achieved 88% overall accuracy with the following per-class performance:

Assault: Perfect performance with 100% precision, recall, and F1 score across 22,234 test cases. The model never misclassifies assaults and catches all assault incidents.

Battery: High recall (100%) but moderate precision (68%) across 43,836 test cases. The model successfully identifies all battery incidents but sometimes incorrectly predicts other crimes as battery. This suggests battery shares characteristics with other crime types.

Criminal Damage: Perfect performance with 100% precision, recall, and F1 score across 28,012 test cases. Property damage crimes have distinct patterns that enable perfect classification.

Motor Vehicle Theft: Poor performance with 43% precision and only 1% recall across 20,498 test cases. The model struggles to identify vehicle thefts, likely because they occur across varied times and locations without clear patterns in the available features.

Theft: Perfect performance with 100% precision, recall, and F1 score across 54,912 test cases. General theft crimes are easily distinguished from other categories.

Feature importance analysis revealed that severity level dominates predictions at 98.6% importance. Hour of day contributes 1.0%, while month, day of week, and weekend flag each contribute less than 0.5%. This indicates that crime types have very distinct severity profiles. For example, assault and battery consistently score as high severity, while theft varies more widely.

The model's weighted F1 score of 83% reflects strong overall performance despite challenges with motor vehicle theft. For operational use, the model reliably predicts most crime types but should not be relied upon for vehicle theft classification without additional features like location type or vehicle-related keywords.

### Crime Volume Forecaster Results

The Gradient Boosting model was trained on 1,476 days of historical data and tested on 370 days representing the most recent period. Key performance metrics include:

R-squared of 62% indicates the model explains 62% of variance in daily crime counts. The remaining 38% represents random variation that cannot be predicted from historical patterns alone.

RMSE of 51 crimes per day means predictions are typically off by about 51 incidents. Given that average daily crime volume is approximately 650 incidents, this represents roughly 8% error in relative terms.

MAPE of 21% shows that predictions average 21% deviation from actual values. This is higher than RMSE percentage due to the impact of low-crime days where small absolute errors create large percentage errors.

The model uses 12 features including calendar information (day of year, day of week, month, week number, weekend flag), lag features (crime counts from 1, 7, 14, and 30 days prior), and rolling statistics (7-day and 30-day moving averages and standard deviations).

Analysis of predictions over time shows the model successfully captures:
- Weekly patterns with higher crime on weekends
- Seasonal trends with higher crime in summer months  
- General upward or downward trends over multi-month periods

The model struggles with:
- Sudden spikes from special events or incidents
- Holiday periods that disrupt normal patterns
- The first few days after a major trend change

For operational planning, the model provides reliable estimates of expected daily workload. A prediction of 650 crimes with 51 RMSE suggests actual volume will likely fall between 600 and 700. This enables appropriate staffing decisions even if the exact number varies.

### Hotspot Detector Results

The DBSCAN clustering algorithm processed 100,000 recent crime incidents with valid geographic coordinates. Using an epsilon parameter of 0.01 degrees (approximately 1 kilometer at Chicago's latitude) and minimum samples of 20, the algorithm identified spatial patterns.

Primary Hotspot (Cluster 0): Located at 41.85 degrees North, 87.67 degrees West, this cluster contains 99,536 incidents representing 99.5% of all clustered crimes. Average severity is 5.2 on a 10-point scale. This location corresponds to downtown Chicago and the surrounding urban core. The massive concentration indicates this is the primary area for crime activity, driven by high population density, commercial activity, foot traffic, and nightlife.

Secondary Hotspot (Cluster 1): Located at 41.98 degrees North, 87.90 degrees West, this cluster contains 436 incidents with average severity 4.7. This represents a much smaller but still significant concentration, likely a neighborhood commercial district or transportation hub.

Only 28 incidents (0.03%) were classified as outliers not belonging to any cluster. This extremely low outlier rate indicates that crime is highly concentrated geographically rather than randomly distributed.

The clustering results have important operational implications. Since 99.5% of analyzed crimes occur in just two geographic areas, patrol resources concentrated in these hotspots could impact the vast majority of incidents. The downtown hotspot alone accounts for essentially all clustered crime activity.

However, the secondary hotspot with only 436 incidents suggests the algorithm's parameters may need tuning. The large difference in cluster sizes (99,536 vs 436) indicates potential for identifying more medium-sized clusters by adjusting epsilon or minimum samples parameters. Additional clusters of 1,000 to 10,000 incidents each would provide more granular targeting for patrol deployment.

The clustering methodology can be applied to any time period or crime subset. For example, analyzing only nighttime incidents or specific crime types might reveal different spatial patterns requiring different intervention strategies.
