CREATE DATABASE IF NOT EXISTS meteodb CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE meteodb;

CREATE TABLE IF NOT EXISTS stations (
  station_id VARCHAR(32) PRIMARY KEY,
  name VARCHAR(200),
  country VARCHAR(10),
  region VARCHAR(100),
  lat DECIMAL(9,6),
  lon DECIMAL(9,6),
  elev_m DECIMAL(6,2),
  inventory JSON,
  last_updated DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS daily_obs (
  station_id VARCHAR(32) NOT NULL,
  date DATE NOT NULL,
  tavg DOUBLE NULL,
  tmin DOUBLE NULL,
  tmax DOUBLE NULL,
  prcp DOUBLE NULL,
  snwd DOUBLE NULL,
  wdir DOUBLE NULL,
  wspd DOUBLE NULL,
  wpgt DOUBLE NULL,
  tsun DOUBLE NULL,
  tavg_source VARCHAR(64),
  tmin_source VARCHAR(64),
  tmax_source VARCHAR(64),
  prcp_source VARCHAR(64),
  tsun_source VARCHAR(64),
  inserted_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (station_id, date),
  INDEX idx_date (date),
  INDEX idx_station_date (station_id, date)
);
