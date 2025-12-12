# ⭐ Weather Forecasting Using SARIMAX & Prophet  
### HCLTech Hackathon Project – Daily Weather Modeling & Forecasting

---

## 📌 Project Overview
This project builds a robust weather forecasting system using daily meteorological data from a SQLite database. Two advanced time-series models are implemented and compared:

- **SARIMAX** (Seasonal ARIMA with eXogenous regressors)  
- **Prophet** (with external regressors)  

**Key Features**:
- Uses precipitation (`prcp`) and wind speed (`wspd`) as external regressors
- Generates accurate **30-day future temperature forecasts**
- Comprehensive data cleaning, visualization, and model evaluation

---

## 📂 Dataset Description

### `daily_obs` table
Daily weather observations with columns:
- `tavg`, `tmin`, `tmax` (temperature in °C)
- `prcp` (precipitation in mm)
- `wspd` (wind speed in km/h)
- `station_id`, `date`

### `stations` table
Station metadata:
- `station_id`
- Station name and location details

---

## 🛠️ Data Preprocessing

1. Loaded data from `meteodb.db` using `sqlite3`
2. Cleaned station names with regex
3. Fixed `station_id` formatting (removed `.csv` suffix)
4. Converted `date` to datetime and extracted year/month/day
5. Merged observations with station metadata
6. Removed incomplete year (2020)
7. Handled missing values via interpolation (for `tavg`, `prcp`, `wspd`)
8. Dropped remaining rows with NA
9. Sorted chronologically for time-series analysis

---

## 📊 Visualization
Generated three insightful time-series plots:
- Daily Average Temperature (`tavg`)
- Daily Precipitation (`prcp`)
- Daily Wind Speed (`wspd`)

Revealed clear trends, noise, and mild weekly seasonality.

---

## 🔮 Modeling Approach
Forecasted **average temperature (`tavg`)** using two models:

### 1️⃣ SARIMAX (Winner Model)

**Why SARIMAX excels for this data**:
- Effectively captures short-term dependencies
- Incorporates external regressors directly
- Handles mild weekly seasonality without over-smoothing

**Best Parameters**:

order = (1, 0, 1)
seasonal_order = (1, 0, 1, 7)  # Weekly seasonality
**Best Parameters**:

order = (1, 0, 1)
seasonal_order = (1, 0, 1, 7)  # Weekly seasonality

Metric,Value
RMSE,1.87
MAE,1.57
MAPE,8.72%

2️⃣ Prophet (with Regressors)
Configured with:

ds → date
y → tavg
Additional regressors: prcp, wspd

## Performance Metrics:

MetricValueRMSE 8.03
MAE 7.88
MAPE 43.49%

Underperformed due to:

Overly smooth trend assumption
Less flexibility with strong regressor-driven patterns

## 📦 Project Structure

project/
├── meteodb.db                
├── forecast.py or notebook.ipynb
├── README.md
├── plots/
└── models/                  

## Libraries Used

pandas
numpy
matplotlib
sqlite3
prophet
statsmodels
scikit-learn
meteostat API
