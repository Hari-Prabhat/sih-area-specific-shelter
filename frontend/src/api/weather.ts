export interface GeocodingResult {
  id: number;
  name: string;
  latitude: number;
  longitude: number;
  elevation?: number;
  country?: string;
  country_code?: string;
  admin1?: string;
  admin2?: string;
  timezone?: string;
  population?: number;
  postcodes?: string[];
}

export interface GeocodingResponse {
  results?: GeocodingResult[];
  generationtime_ms?: number;
}

export interface CurrentWeather {
  temperature_2m: number;
  relative_humidity_2m: number;
  precipitation: number;
  wind_speed_10m: number;
  weather_code: number;
  is_day: number;
  time: string;
}

export interface CurrentWeatherResponse {
  latitude: number;
  longitude: number;
  elevation: number;
  timezone: string;
  current: CurrentWeather;
  current_units: {
    temperature_2m: string;
    relative_humidity_2m: string;
    precipitation: string;
    wind_speed_10m: string;
    weather_code: string;
    is_day: string;
    time: string;
  };
}

const GEOCODING_BASE = "https://geocoding-api.open-meteo.com/v1";
const FORECAST_BASE = "https://api.open-meteo.com/v1";

export async function searchLocation(
  city: string,
  count: number = 5
): Promise<GeocodingResult[]> {
  if (!city || !city.trim()) {
    return [];
  }

  const params = new URLSearchParams({
    name: city.trim(),
    count: String(count),
    language: "en",
    format: "json",
  });

  try {
    const response = await fetch(`${GEOCODING_BASE}/search?${params.toString()}`);
    if (!response.ok) {
      throw new Error(`Geocoding API error: ${response.status} ${response.statusText}`);
    }
    const data: GeocodingResponse = await response.json();
    return data.results ?? [];
  } catch (err: unknown) {
    if (err instanceof Error) {
      if (err.message.includes("Failed to fetch") || err.message.includes("NetworkError")) {
        throw new Error("Network error. Please check your internet connection.");
      }
      throw err;
    }
    throw new Error("Unknown error while searching location.");
  }
}

export async function getCurrentWeather(
  latitude: number,
  longitude: number
): Promise<CurrentWeatherResponse> {
  const params = new URLSearchParams({
    latitude: String(latitude),
    longitude: String(longitude),
    current: [
      "temperature_2m",
      "relative_humidity_2m",
      "precipitation",
      "wind_speed_10m",
      "weather_code",
      "is_day",
    ].join(","),
    wind_speed_unit: "kmh",
    timezone: "auto",
  });

  try {
    const response = await fetch(`${FORECAST_BASE}/forecast?${params.toString()}`);
    if (!response.ok) {
      throw new Error(`Weather API error: ${response.status} ${response.statusText}`);
    }
    const data: CurrentWeatherResponse = await response.json();
    return data;
  } catch (err: unknown) {
    if (err instanceof Error) {
      if (err.message.includes("Failed to fetch") || err.message.includes("NetworkError")) {
        throw new Error("Network error. Please check your internet connection.");
      }
      throw err;
    }
    throw new Error("Unknown error while fetching weather.");
  }
}

export type WeatherConditionKey =
  | "sunny"
  | "partlyCloudy"
  | "cloudy"
  | "foggy"
  | "drizzle"
  | "rainy"
  | "snowy"
  | "rainShowers"
  | "thunderstorm"
  | "unknown";

export function weatherCodeToCondition(code: number): WeatherConditionKey {
  if (code === 0) return "sunny";
  if (code === 1 || code === 2) return "partlyCloudy";
  if (code === 3) return "cloudy";
  if (code === 45 || code === 48) return "foggy";
  if (code >= 51 && code <= 57) return "drizzle";
  if (code >= 61 && code <= 67) return "rainy";
  if (code >= 71 && code <= 77) return "snowy";
  if (code >= 80 && code <= 82) return "rainShowers";
  if (code >= 95 && code <= 99) return "thunderstorm";
  return "unknown";
}
