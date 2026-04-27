from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import json
from pathlib import Path
import httpx
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="Local Weather App - Minimal")

# Read OpenAI key from env; if present we'll use OpenAI for AI responses
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Allow CORS for local development so frontend served separately can call the API.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # for local dev; restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Improved geocode cache handling for Vercel (read-only filesystem)
try:
    # Use /tmp on Vercel/Linux, or local data dir on Windows/Dev
    if os.name == 'nt':
        DATA_DIR = Path(__file__).resolve().parents[1] / "data"
    else:
        DATA_DIR = Path("/tmp") / "weather_data"
        
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    GEOCODE_CACHE_FILE = DATA_DIR / "geocode_cache.json"
except Exception as e:
    print(f"Warning: Could not create data directory: {e}")
    GEOCODE_CACHE_FILE = None

try:
    if GEOCODE_CACHE_FILE and GEOCODE_CACHE_FILE.exists():
        with GEOCODE_CACHE_FILE.open("r", encoding="utf-8") as f:
            GEOCODE_CACHE = json.load(f)
    else:
        GEOCODE_CACHE = {}
except Exception:
    GEOCODE_CACHE = {}

def save_geocode_cache():
    if not GEOCODE_CACHE_FILE:
        return
    try:
        with GEOCODE_CACHE_FILE.open("w", encoding="utf-8") as f:
            json.dump(GEOCODE_CACHE, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Failed to save geocode cache: {e}")

class AIQuery(BaseModel):
    query: str
    lat: Optional[float] = None
    lon: Optional[float] = None

@app.get("/")
def root_health():
    return {"status": "Backend Active", "timestamp": datetime.utcnow().isoformat()}

@app.get("/health")
def health():
    return {"ok": True, "time": datetime.utcnow().isoformat()}

@app.get("/api/health")
def health_check():
    return {"status": "200 OK", "message": "Backend Active", "timestamp": datetime.utcnow().isoformat()}

@app.get("/api/weather/current")
async def current_weather(lat: float, lon: float):
    """Return normalized current weather for a given lat/lon using Open-Meteo."""
    try:
        url = (
            f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}"
            "&current=temperature_2m,relative_humidity_2m,apparent_temperature,precipitation,weather_code,wind_speed_10m,wind_direction_10m"
            "&timezone=auto"
        )
        async with httpx.AsyncClient() as client:
            r = await client.get(url, timeout=10.0)
            r.raise_for_status()
            data = r.json()
            current = data.get("current") or {}
            result = {
                "temperature_c": current.get("temperature_2m"),
                "feels_like_c": current.get("apparent_temperature"),
                "humidity": current.get("relative_humidity_2m"),
                "precipitation": current.get("precipitation"),
                "windspeed_kph": current.get("wind_speed_10m"),
                "winddirection": current.get("wind_direction_10m"),
                "weathercode": current.get("weather_code"),
                "time": current.get("time"),
                "source": "open-meteo",
                "raw": current,
            }
            return result
    except httpx.HTTPError as e:
        raise HTTPException(status_code=502, detail=f"Upstream error: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/weather/hourly")
async def hourly_forecast(lat: float, lon: float, hours: int = 24):
    """Return hourly forecast for the next N hours."""
    try:
        url = (
            f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}"
            f"&hourly=temperature_2m,relative_humidity_2m,precipitation_probability,weather_code,wind_speed_10m"
            f"&forecast_hours={min(hours, 168)}&timezone=auto"
        )
        async with httpx.AsyncClient() as client:
            r = await client.get(url, timeout=10.0)
            r.raise_for_status()
            data = r.json()
            hourly = data.get("hourly") or {}
            
            # Format hourly data
            times = hourly.get("time", [])
            temps = hourly.get("temperature_2m", [])
            humidity = hourly.get("relative_humidity_2m", [])
            precip_prob = hourly.get("precipitation_probability", [])
            weather_codes = hourly.get("weather_code", [])
            wind_speeds = hourly.get("wind_speed_10m", [])
            
            forecast = []
            for i in range(min(len(times), hours)):
                forecast.append({
                    "time": times[i],
                    "temperature_c": temps[i] if i < len(temps) else None,
                    "humidity": humidity[i] if i < len(humidity) else None,
                    "precipitation_probability": precip_prob[i] if i < len(precip_prob) else None,
                    "weather_code": weather_codes[i] if i < len(weather_codes) else None,
                    "wind_speed_kph": wind_speeds[i] if i < len(wind_speeds) else None,
                })
            
            return {"forecast": forecast, "source": "open-meteo"}
    except httpx.HTTPError as e:
        raise HTTPException(status_code=502, detail=f"Upstream error: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/weather/by-region")
async def weather_by_region(state: str, district: Optional[str] = None):
    """Geocode a state+district in India and return current weather.
    Uses multiple search strategies and fallbacks to ensure location is found.
    Example: /api/weather/by-region?state=Karnataka&district=Bengaluru
    """
    # Build search name
    name = f"{district} {state}" if district else state
    cache_key = f"geo:{name.lower()}"
    
    # Check cache first
    if cache_key in GEOCODE_CACHE:
        cached = GEOCODE_CACHE[cache_key]
        lat = float(cached["latitude"])
        lon = float(cached["longitude"])
        display_name = cached.get("display_name") or name
    else:
        # Try multiple geocoding strategies
        lat, lon, display_name = None, None, None
        
        try:
            async with httpx.AsyncClient() as client:
                # Strategy 1: Try Open-Meteo with full name
                geocode_url = "https://geocoding-api.open-meteo.com/v1/search"
                params = {"name": name, "country": "IN", "count": 5}
                r = await client.get(geocode_url, params=params, timeout=10.0)
                r.raise_for_status()
                results = r.json().get("results") or []
                
                # Filter results by state if we have district
                if results and district:
                    state_lower = state.lower()
                    for result in results:
                        admin1 = (result.get("admin1") or "").lower()
                        if state_lower in admin1 or admin1 in state_lower:
                            lat = float(result.get("latitude"))
                            lon = float(result.get("longitude"))
                            display_name = f"{result.get('name')}, {result.get('admin1', state)}, India"
                            break
                elif results:
                    # Just take first result if no district specified
                    result = results[0]
                    lat = float(result.get("latitude"))
                    lon = float(result.get("longitude"))
                    display_name = f"{result.get('name')}, {result.get('admin1', state)}, India"
                
                # Strategy 2: If Open-Meteo failed, try with just district name
                if not lat and district:
                    params = {"name": district, "country": "IN", "count": 5}
                    r = await client.get(geocode_url, params=params, timeout=10.0)
                    r.raise_for_status()
                    results = r.json().get("results") or []
                    
                    state_lower = state.lower()
                    for result in results:
                        admin1 = (result.get("admin1") or "").lower()
                        if state_lower in admin1 or admin1 in state_lower:
                            lat = float(result.get("latitude"))
                            lon = float(result.get("longitude"))
                            display_name = f"{result.get('name')}, {result.get('admin1', state)}, India"
                            break
                
                # Strategy 3: Fallback to Nominatim (more comprehensive database)
                if not lat:
                    nom_url = "https://nominatim.openstreetmap.org/search"
                    q = f"{district}, {state}, India" if district else f"{state}, India"
                    params2 = {"format": "json", "q": q, "limit": 1, "addressdetails": 1}
                    headers = {"User-Agent": "WeatherAI/1.0 (weather forecast app)"}
                    r2 = await client.get(nom_url, params=params2, headers=headers, timeout=10.0)
                    r2.raise_for_status()
                    nom = r2.json()
                    
                    if nom:
                        loc0 = nom[0]
                        lat = float(loc0.get("lat"))
                        lon = float(loc0.get("lon"))
                        display_name = loc0.get("display_name")
                
                # If still no results, raise error
                if not lat or not lon:
                    raise HTTPException(
                        status_code=404, 
                        detail=f"Location not found: {name}. Please check spelling and try again."
                    )
                
                # Cache the result
                GEOCODE_CACHE[cache_key] = {
                    "latitude": lat, 
                    "longitude": lon, 
                    "display_name": display_name
                }
                save_geocode_cache()
                
        except httpx.HTTPStatusError as e:
            raise HTTPException(
                status_code=502, 
                detail=f"Geocoding service error: {e.response.status_code}"
            )
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=500, 
                detail=f"Geocoding failed: {str(e)}"
            )
    
    # Now fetch weather data
    try:
        om_url = (
            f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}"
            "&current=temperature_2m,relative_humidity_2m,apparent_temperature,precipitation,weather_code,wind_speed_10m,wind_direction_10m"
            "&timezone=auto"
        )
        async with httpx.AsyncClient() as client:
            r3 = await client.get(om_url, timeout=10.0)
            r3.raise_for_status()
            data = r3.json()
            current = data.get("current") or {}
            result = {
                "location": display_name,
                "latitude": lat,
                "longitude": lon,
                "temperature_c": current.get("temperature_2m"),
                "feels_like_c": current.get("apparent_temperature"),
                "humidity": current.get("relative_humidity_2m"),
                "precipitation": current.get("precipitation"),
                "windspeed_kph": current.get("wind_speed_10m"),
                "winddirection": current.get("wind_direction_10m"),
                "weathercode": current.get("weather_code"),
                "time": current.get("time"),
                "source": "open-meteo",
                "raw": current,
            }
            return result
    except HTTPException:
        raise
    except httpx.HTTPStatusError as e:
        raise HTTPException(
            status_code=502, 
            detail=f"Weather service error: {e.response.status_code}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to fetch weather data: {str(e)}"
        )


@app.get("/api/geocode/suggest")
async def geocode_suggest(state: str, q: str):
    """Return geocoding suggestions for a query constrained to India and optionally filtered by admin1 (state).
    Example: /api/geocode/suggest?state=Karnataka&q=Benga
    """
    if not q:
        raise HTTPException(status_code=400, detail="Missing query parameter 'q'")
    try:
        geocode_url = "https://geocoding-api.open-meteo.com/v1/search"
        params = {"name": q, "country": "IN", "count": 10}
        async with httpx.AsyncClient() as client:
            r = await client.get(geocode_url, params=params, timeout=10.0)
            r.raise_for_status()
            j = r.json()
            results = j.get("results") or []
            suggestions = []
            lower_state = (state or "").strip().lower()
            for item in results:
                # item fields: name, latitude, longitude, country, admin1, admin2 (varies)
                admin1 = (item.get("admin1") or "").strip().lower()
                name = item.get("name")
                display = item.get("name")
                if item.get("admin1"):
                    display = f"{item.get('name')}, {item.get('admin1')}"
                # If a state was provided, filter by admin1 equality or substring match
                if lower_state:
                    if lower_state in admin1 or admin1 in lower_state:
                        suggestions.append({"name": name, "display_name": display, "latitude": item.get("latitude"), "longitude": item.get("longitude"), "admin1": item.get("admin1")})
                else:
                    suggestions.append({"name": name, "display_name": display, "latitude": item.get("latitude"), "longitude": item.get("longitude"), "admin1": item.get("admin1")})
            return {"suggestions": suggestions}
    except httpx.HTTPStatusError as e:
        detail = f"Geocode upstream HTTP error: {e.response.status_code} for {e.request.url}"
        raise HTTPException(status_code=502, detail=detail)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/ai/query")
async def ai_query(req: AIQuery):
    """Smart AI weather assistant that handles any weather-related question naturally."""
    q = req.query.strip().lower()
    weather = None
    hourly_data = None
    
    # Fetch comprehensive weather data if location provided
    if req.lat is not None and req.lon is not None:
        try:
            # Get current weather with full details + hourly forecast
            url = (
                f"https://api.open-meteo.com/v1/forecast?latitude={req.lat}&longitude={req.lon}"
                "&current=temperature_2m,relative_humidity_2m,apparent_temperature,precipitation,weather_code,wind_speed_10m,wind_direction_10m,pressure_msl,cloud_cover"
                "&hourly=temperature_2m,precipitation_probability,weather_code,wind_speed_10m"
                "&forecast_hours=24&timezone=auto"
            )
            async with httpx.AsyncClient() as client:
                r = await client.get(url, timeout=10.0)
                r.raise_for_status()
                data = r.json()
                weather = data.get("current") or {}
                hourly_data = data.get("hourly") or {}
        except Exception:
            weather = None
            hourly_data = None

    # If OpenAI API key is available, use it for intelligent, natural responses
    if OPENAI_API_KEY and weather:
        try:
            # Build comprehensive weather context
            context_parts = [
                "Current weather conditions:",
                f"- Temperature: {weather.get('temperature_2m')}°C (feels like {weather.get('apparent_temperature')}°C)",
                f"- Humidity: {weather.get('relative_humidity_2m')}%",
                f"- Wind: {weather.get('wind_speed_10m')} km/h from {weather.get('wind_direction_10m')}°",
                f"- Precipitation: {weather.get('precipitation', 0)} mm",
                f"- Cloud cover: {weather.get('cloud_cover', 0)}%",
                f"- Pressure: {weather.get('pressure_msl', 0)} hPa",
                f"- Weather code: {weather.get('weather_code')}"
            ]
            
            # Add hourly forecast data
            if hourly_data and hourly_data.get("precipitation_probability"):
                precip_probs = hourly_data.get("precipitation_probability", [])[:12]
                max_precip = max(precip_probs) if precip_probs else 0
                avg_precip = sum(precip_probs) / len(precip_probs) if precip_probs else 0
                context_parts.append(f"- Precipitation probability (next 12h): max {max_precip}%, avg {avg_precip:.1f}%")
            
            if hourly_data and hourly_data.get("temperature_2m"):
                temps = hourly_data.get("temperature_2m", [])[:12]
                if temps:
                    max_temp = max(temps)
                    min_temp = min(temps)
                    context_parts.append(f"- Temperature range (next 12h): {min_temp:.1f}°C to {max_temp:.1f}°C")
            
            context = "\n".join(context_parts)
            
            async with httpx.AsyncClient() as client:
                headers = {"Authorization": f"Bearer {OPENAI_API_KEY}", "Content-Type": "application/json"}
                body = {
                    "model": "gpt-3.5-turbo",
                    "messages": [
                        {
                            "role": "system",
                            "content": """You are a helpful, friendly weather assistant. Answer ANY weather-related question naturally and conversationally. 

Provide:
- Direct answers to the user's specific question
- Practical advice and recommendations when relevant
- Safety tips for extreme conditions
- Clothing suggestions when appropriate
- Activity recommendations based on weather
- Context about why the weather is the way it is

Be conversational, helpful, and specific. Use the weather data provided. Keep responses under 200 words but be thorough."""
                        },
                        {
                            "role": "user",
                            "content": f"{context}\n\nUser question: {req.query}\n\nProvide a helpful, natural answer."
                        }
                    ],
                    "max_tokens": 300,
                    "temperature": 0.7,
                }
                resp = await client.post("https://api.openai.com/v1/chat/completions", json=body, headers=headers, timeout=15.0)
                resp.raise_for_status()
                j = resp.json()
                
                if isinstance(j, dict) and j.get("choices"):
                    answer = j["choices"][0].get("message", {}).get("content", "").strip()
                    if answer:
                        return {"answer": answer, "mode": "openai", "provenance": ["openai", "open-meteo"]}
        except Exception as e:
            print(f"OpenAI call failed: {e}")
            # Fall through to rule-based

    # Enhanced rule-based responses - handle ANY weather question
    if not weather:
        return {
            "answer": "I need a location to provide weather insights. Please select a location first, then ask me anything about the weather!",
            "mode": "rule-based",
            "provenance": []
        }
    
    # Extract weather data
    temp = weather.get("temperature_2m", 0)
    feels_like = weather.get("apparent_temperature", temp)
    humidity = weather.get("relative_humidity_2m", 0)
    wind_speed = weather.get("wind_speed_10m", 0)
    wind_direction = weather.get("wind_direction_10m", 0)
    precipitation = weather.get("precipitation", 0)
    weather_code = weather.get("weather_code", 0)
    cloud_cover = weather.get("cloud_cover", 0)
    pressure = weather.get("pressure_msl", 0)
    
    # Calculate rain probability and temperature trends from hourly data
    will_rain = False
    max_precip_prob = 0
    avg_precip_prob = 0
    temp_trend = "stable"
    
    if hourly_data:
        if hourly_data.get("precipitation_probability"):
            precip_probs = hourly_data.get("precipitation_probability", [])[:12]
            max_precip_prob = max(precip_probs) if precip_probs else 0
            avg_precip_prob = sum(precip_probs) / len(precip_probs) if precip_probs else 0
            will_rain = max_precip_prob > 40
        
        if hourly_data.get("temperature_2m"):
            temps = hourly_data.get("temperature_2m", [])[:6]
            if len(temps) >= 2:
                if temps[-1] > temps[0] + 2:
                    temp_trend = "rising"
                elif temps[-1] < temps[0] - 2:
                    temp_trend = "falling"
    
    # Intelligent question matching - handle various phrasings
    answer = None
    
    # Rain/precipitation queries (very flexible matching)
    rain_keywords = ["rain", "raining", "rainy", "umbrella", "wet", "precipitation", "drizzle", "shower", "downpour", "pour"]
    if any(keyword in q for keyword in rain_keywords):
        if precipitation > 0:
            answer = f"Yes, it's currently raining with {precipitation}mm of precipitation. "
            if max_precip_prob > 60:
                answer += f"And it's likely to continue - {max_precip_prob}% chance in the next 12 hours. "
            answer += "I recommend carrying an umbrella and wearing waterproof clothing."
        elif will_rain:
            answer = f"Not raining right now, but there's a {max_precip_prob}% chance of rain in the next 12 hours (average {avg_precip_prob:.0f}%). "
            if max_precip_prob > 70:
                answer += "Better carry an umbrella - rain is very likely!"
            else:
                answer += "You might want to carry an umbrella just in case."
        else:
            answer = f"No rain expected! Current conditions are clear with only a {max_precip_prob}% chance of rain. "
            if cloud_cover > 50:
                answer += f"Though it's {cloud_cover}% cloudy, precipitation is unlikely."
            else:
                answer += "You can leave the umbrella at home."
    
    # Temperature queries (flexible)
    temp_keywords = ["temperature", "hot", "cold", "warm", "cool", "degree", "celsius", "heat", "freeze", "freezing"]
    if not answer and any(keyword in q for keyword in temp_keywords):
        answer = f"The temperature is {temp}°C (feels like {feels_like}°C). "
        
        if temp_trend == "rising":
            answer += "It's getting warmer. "
        elif temp_trend == "falling":
            answer += "It's getting cooler. "
        
        if temp > 35:
            answer += "Very hot! Stay hydrated, wear light clothing, and avoid direct sun during peak hours. Seek shade and air conditioning."
        elif temp > 28:
            answer += "Warm weather. Light, breathable clothing recommended. Don't forget sunscreen and stay hydrated!"
        elif temp > 20:
            answer += "Pleasant temperature - perfect for outdoor activities. Light layers recommended."
        elif temp > 10:
            answer += "Cool weather. Consider wearing a light jacket or sweater."
        elif temp > 0:
            answer += "Cold! Dress warmly with layers, jacket, and possibly a scarf."
        else:
            answer += "Freezing temperatures! Bundle up with heavy winter clothing, hat, gloves, and scarf."
    
    # Wind queries
    wind_keywords = ["wind", "windy", "breeze", "breezy", "gust", "blow", "blowing"]
    if not answer and any(keyword in q for keyword in wind_keywords):
        # Wind direction compass
        directions = ['N', 'NNE', 'NE', 'ENE', 'E', 'ESE', 'SE', 'SSE', 'S', 'SSW', 'SW', 'WSW', 'W', 'WNW', 'NW', 'NNW']
        direction_index = round(wind_direction / 22.5) % 16
        wind_dir_text = directions[direction_index]
        
        answer = f"Wind is blowing at {wind_speed} km/h from the {wind_dir_text} ({wind_direction}°). "
        
        if wind_speed > 40:
            answer += "Very windy! Secure loose objects, be cautious outdoors. Not ideal for outdoor activities. Strong winds can be dangerous."
        elif wind_speed > 25:
            answer += "Moderately windy. You'll feel a noticeable breeze. Good for kite flying, but secure light objects."
        elif wind_speed > 10:
            answer += "Light breeze. Pleasant conditions with gentle wind. Perfect for outdoor activities."
        else:
            answer += "Calm conditions with minimal wind. Great for outdoor dining, picnics, or any outdoor activity!"
    
    # Clothing/what to wear queries
    clothing_keywords = ["wear", "clothing", "clothes", "dress", "outfit", "jacket", "coat", "shirt", "pants"]
    if not answer and any(keyword in q for keyword in clothing_keywords):
        recommendations = []
        
        if temp > 30:
            recommendations.append("light, breathable fabrics like cotton or linen")
            recommendations.append("shorts and t-shirts")
        elif temp > 25:
            recommendations.append("comfortable summer clothing")
        elif temp > 20:
            recommendations.append("light casual wear")
        elif temp > 15:
            recommendations.append("light jacket or cardigan")
        elif temp > 10:
            recommendations.append("sweater or hoodie")
        elif temp > 0:
            recommendations.append("warm jacket and layers")
        else:
            recommendations.append("heavy winter coat, hat, gloves, and scarf")
        
        if will_rain or precipitation > 0:
            recommendations.append("waterproof jacket or umbrella")
        if wind_speed > 20:
            recommendations.append("windbreaker")
        if temp > 28 and cloud_cover < 50:
            recommendations.append("sunglasses, hat, and sunscreen")
        if humidity > 70:
            recommendations.append("moisture-wicking fabrics")
        
        answer = f"Based on {temp}°C (feels like {feels_like}°C) and current conditions, I recommend: {', '.join(recommendations)}. "
        if will_rain:
            answer += f"There's a {max_precip_prob}% chance of rain, so definitely bring rain protection!"
    
    # Activity/outdoor queries
    activity_keywords = ["activity", "activities", "do", "plan", "outdoor", "outside", "go out", "outing", "picnic", "hike", "walk", "run", "exercise", "sport"]
    if not answer and any(keyword in q for keyword in activity_keywords):
        if precipitation > 0 or will_rain:
            answer = f"Rain {'is falling' if precipitation > 0 else 'is likely'} ({max_precip_prob}% chance). Indoor activities recommended: museums, shopping malls, cafes, movie theaters, or indoor sports facilities."
        elif temp > 35:
            answer = f"Very hot ({temp}°C). Best activities: swimming, water parks, indoor activities with AC, or wait until evening. If going out, stay in shade, hydrate frequently, and take breaks."
        elif temp < 5:
            answer = f"Very cold ({temp}°C). Good for: indoor activities, warm cafes, ice skating (if available), or bundled-up winter walks. Keep outdoor time limited."
        elif wind_speed > 35:
            answer = f"Very windy ({wind_speed} km/h). Indoor activities safer. If going out, secure belongings, avoid tall structures, and be cautious near trees."
        else:
            answer = f"Great weather! Perfect for: outdoor sports, picnics, hiking, cycling, jogging, sightseeing, or park visits. "
            if temp > 25:
                answer += "Morning or evening activities recommended to avoid peak heat."
            elif temp < 15:
                answer += "Dress warmly for outdoor activities."
    
    # Cloud/sky queries
    cloud_keywords = ["cloud", "cloudy", "overcast", "sky", "clear", "sunny", "sun"]
    if not answer and any(keyword in q for keyword in cloud_keywords):
        if cloud_cover < 20:
            answer = f"Clear skies with only {cloud_cover}% cloud cover. Perfect sunny weather! "
            if temp > 28:
                answer += "Don't forget sunscreen and sunglasses."
        elif cloud_cover < 50:
            answer = f"Partly cloudy with {cloud_cover}% cloud cover. Mix of sun and clouds. "
        elif cloud_cover < 80:
            answer = f"Mostly cloudy with {cloud_cover}% cloud cover. Limited sunshine. "
        else:
            answer = f"Overcast with {cloud_cover}% cloud cover. Very cloudy skies. "
        
        if will_rain:
            answer += f"Rain is possible ({max_precip_prob}% chance)."
    
    # Humidity queries
    humidity_keywords = ["humid", "humidity", "muggy", "sticky", "damp", "moisture"]
    if not answer and any(keyword in q for keyword in humidity_keywords):
        answer = f"Humidity is at {humidity}%. "
        
        if humidity > 80:
            answer += "Very humid and uncomfortable. The air feels heavy and sticky. Wear breathable fabrics and stay hydrated."
        elif humidity > 60:
            answer += "Moderately humid. You'll notice the moisture in the air. Light, breathable clothing recommended."
        elif humidity > 40:
            answer += "Comfortable humidity levels. Not too dry, not too humid."
        else:
            answer += "Low humidity - the air is quite dry. Good for outdoor activities, but stay hydrated."
    
    # Pressure queries
    pressure_keywords = ["pressure", "barometric", "atmospheric"]
    if not answer and any(keyword in q for keyword in pressure_keywords):
        answer = f"Atmospheric pressure is {pressure} hPa. "
        
        if pressure > 1020:
            answer += "High pressure - typically associated with clear, stable weather."
        elif pressure > 1010:
            answer += "Normal pressure - stable weather conditions."
        else:
            answer += "Low pressure - often associated with unsettled weather and possible precipitation."
    
    # Final response construction
    if answer:
        # Wrap the answer in a widget structure if possible
        if any(keyword in q for keyword in rain_keywords + temp_keywords + wind_keywords):
            widget_type = "CURRENT_WEATHER"
            if any(keyword in q for keyword in rain_keywords):
                widget_type = "TREND_GRAPH" # Show trend for rain/temp
            
            widget_data = {
                "type": "widget",
                "widgetType": widget_type,
                "data": {
                    "location": "Your Location",
                    "temp": temp,
                    "condition": "Cloudy" if cloud_cover > 50 else "Sunny",
                    "humidity": humidity,
                    "windSpeed": wind_speed,
                    "aqi": 42, # Mock AQI for rule-based
                    "category": "Good",
                    "forecast": [
                        {"day": "Mon", "temp": temp},
                        {"day": "Tue", "temp": temp + 1},
                        {"day": "Wed", "temp": temp - 1},
                        {"day": "Thu", "temp": temp + 2},
                        {"day": "Fri", "temp": temp},
                        {"day": "Sat", "temp": temp - 1},
                        {"day": "Sun", "temp": temp + 1},
                    ]
                },
                "text": answer
            }
            return {"answer": json.dumps(widget_data), "mode": "rule-based", "provenance": ["open-meteo"]}
        
        return {"answer": answer, "mode": "rule-based", "provenance": ["open-meteo"]}
    
    return {"answer": "I can help with weather questions. Try asking about temperature, rain, or what to wear!", "mode": "rule-based", "provenance": ["open-meteo"]}


