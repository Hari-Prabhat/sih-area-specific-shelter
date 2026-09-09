import { ClimateData } from '../utils/thermalEngine';

export const climatePresets: ClimateData[] = [
  { location: "Leh, Ladakh", altitude: 3500, ambientTempMin: -25, ambientTempMax: 30, avgAmbientTemp: 5, solarIrradiance: 2000, avgSunshineHours: 7.9, windSpeed: 6.5, humidity: 25, cloudFreeDays: 320 },
  { location: "Kargil, Ladakh", altitude: 2676, ambientTempMin: -28, ambientTempMax: 28, avgAmbientTemp: 3, solarIrradiance: 1950, avgSunshineHours: 7.5, windSpeed: 5.8, humidity: 30, cloudFreeDays: 300 },
  { location: "Siachen Glacier Area", altitude: 5400, ambientTempMin: -45, ambientTempMax: 5, avgAmbientTemp: -20, solarIrradiance: 2100, avgSunshineHours: 8.5, windSpeed: 12.0, humidity: 15, cloudFreeDays: 330 },
  { location: "Manali, Himachal Pradesh", altitude: 2050, ambientTempMin: -15, ambientTempMax: 28, avgAmbientTemp: 10, solarIrradiance: 1800, avgSunshineHours: 7.0, windSpeed: 4.5, humidity: 45, cloudFreeDays: 260 },
  { location: "Shimla, Himachal Pradesh", altitude: 2276, ambientTempMin: -8, ambientTempMax: 28, avgAmbientTemp: 12, solarIrradiance: 1750, avgSunshineHours: 6.8, windSpeed: 3.8, humidity: 55, cloudFreeDays: 240 },
  { location: "Srinagar, J&K", altitude: 1585, ambientTempMin: -8, ambientTempMax: 33, avgAmbientTemp: 13, solarIrradiance: 1700, avgSunshineHours: 6.5, windSpeed: 3.2, humidity: 60, cloudFreeDays: 220 },
  { location: "Gangtok, Sikkim", altitude: 1650, ambientTempMin: 2, ambientTempMax: 24, avgAmbientTemp: 14, solarIrradiance: 1600, avgSunshineHours: 5.5, windSpeed: 2.8, humidity: 75, cloudFreeDays: 150 },
  { location: "Darjeeling, West Bengal", altitude: 2045, ambientTempMin: 1, ambientTempMax: 22, avgAmbientTemp: 12, solarIrradiance: 1550, avgSunshineHours: 5.2, windSpeed: 3.5, humidity: 78, cloudFreeDays: 130 },
  { location: "Delhi (NCR)", altitude: 216, ambientTempMin: 2, ambientTempMax: 46, avgAmbientTemp: 25, solarIrradiance: 1900, avgSunshineHours: 8.0, windSpeed: 3.0, humidity: 55, cloudFreeDays: 280 },
  { location: "Jaisalmer, Rajasthan", altitude: 200, ambientTempMin: 5, ambientTempMax: 50, avgAmbientTemp: 28, solarIrradiance: 2100, avgSunshineHours: 10.0, windSpeed: 4.0, humidity: 20, cloudFreeDays: 350 },
  { location: "Mumbai, Maharashtra", altitude: 14, ambientTempMin: 18, ambientTempMax: 36, avgAmbientTemp: 27, solarIrradiance: 1650, avgSunshineHours: 7.0, windSpeed: 4.2, humidity: 75, cloudFreeDays: 180 },
  { location: "Chennai, Tamil Nadu", altitude: 6, ambientTempMin: 20, ambientTempMax: 38, avgAmbientTemp: 29, solarIrradiance: 1800, avgSunshineHours: 7.5, windSpeed: 3.8, humidity: 72, cloudFreeDays: 200 },
  { location: "Guwahati, Assam", altitude: 55, ambientTempMin: 6, ambientTempMax: 36, avgAmbientTemp: 22, solarIrradiance: 1600, avgSunshineHours: 5.8, windSpeed: 2.0, humidity: 80, cloudFreeDays: 160 },
  { location: "Custom Location", altitude: 0, ambientTempMin: 0, ambientTempMax: 30, avgAmbientTemp: 15, solarIrradiance: 1800, avgSunshineHours: 7.0, windSpeed: 3.0, humidity: 50, cloudFreeDays: 250 },
];
