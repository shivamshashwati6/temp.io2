"""
Test script specifically for Nalbari, Assam geocoding issue
"""
import httpx
import asyncio

async def test_nalbari():
    print("=" * 60)
    print("Testing Nalbari, Assam Geocoding")
    print("=" * 60)
    
    # Test the actual endpoint
    base_url = "http://localhost:8000"
    
    print("\n[TEST] Fetching weather for Nalbari, Assam...")
    try:
        async with httpx.AsyncClient() as client:
            params = {"state": "Assam", "district": "Nalbari"}
            response = await client.get(
                f"{base_url}/api/weather/by-region",
                params=params,
                timeout=15.0
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"\n✓ SUCCESS!")
                print(f"  Location: {data.get('location')}")
                print(f"  Coordinates: {data.get('latitude')}, {data.get('longitude')}")
                print(f"  Temperature: {data.get('temperature_c')}°C")
                print(f"  Humidity: {data.get('humidity')}%")
                print(f"  Feels Like: {data.get('feels_like_c')}°C")
                print(f"  Wind Speed: {data.get('windspeed_kph')} km/h")
                print(f"  Weather Code: {data.get('weathercode')}")
                return True
            else:
                print(f"\n✗ FAILED with status: {response.status_code}")
                print(f"  Response: {response.text}")
                return False
                
    except httpx.ConnectError:
        print("\n✗ ERROR: Cannot connect to backend server")
        print("  Make sure the backend is running on http://localhost:8000")
        return False
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        return False

async def test_geocoding_strategies():
    """Test different geocoding strategies"""
    print("\n" + "=" * 60)
    print("Testing Geocoding Strategies")
    print("=" * 60)
    
    # Strategy 1: Open-Meteo with full name
    print("\n[Strategy 1] Open-Meteo: 'Nalbari Assam'")
    try:
        async with httpx.AsyncClient() as client:
            r = await client.get(
                "https://geocoding-api.open-meteo.com/v1/search",
                params={"name": "Nalbari Assam", "country": "IN", "count": 5},
                timeout=10.0
            )
            results = r.json().get("results") or []
            print(f"  Results: {len(results)}")
            if results:
                for i, res in enumerate(results[:3], 1):
                    print(f"  {i}. {res.get('name')}, {res.get('admin1', 'N/A')}")
    except Exception as e:
        print(f"  Error: {e}")
    
    # Strategy 2: Open-Meteo with just district
    print("\n[Strategy 2] Open-Meteo: 'Nalbari'")
    try:
        async with httpx.AsyncClient() as client:
            r = await client.get(
                "https://geocoding-api.open-meteo.com/v1/search",
                params={"name": "Nalbari", "country": "IN", "count": 5},
                timeout=10.0
            )
            results = r.json().get("results") or []
            print(f"  Results: {len(results)}")
            if results:
                for i, res in enumerate(results[:3], 1):
                    admin1 = res.get('admin1', 'N/A')
                    print(f"  {i}. {res.get('name')}, {admin1}")
                    if 'assam' in admin1.lower():
                        print(f"     ✓ Match found for Assam!")
    except Exception as e:
        print(f"  Error: {e}")
    
    # Strategy 3: Nominatim
    print("\n[Strategy 3] Nominatim: 'Nalbari, Assam, India'")
    try:
        async with httpx.AsyncClient() as client:
            r = await client.get(
                "https://nominatim.openstreetmap.org/search",
                params={"format": "json", "q": "Nalbari, Assam, India", "limit": 3},
                headers={"User-Agent": "WeatherAI/1.0 Test"},
                timeout=10.0
            )
            results = r.json()
            print(f"  Results: {len(results)}")
            if results:
                for i, res in enumerate(results[:3], 1):
                    print(f"  {i}. {res.get('display_name')}")
                    print(f"     Coords: {res.get('lat')}, {res.get('lon')}")
    except Exception as e:
        print(f"  Error: {e}")

async def main():
    # Test geocoding strategies first
    await test_geocoding_strategies()
    
    # Then test the actual endpoint
    print("\n")
    success = await test_nalbari()
    
    print("\n" + "=" * 60)
    if success:
        print("✓ Nalbari, Assam is now working!")
    else:
        print("✗ Test failed - check backend logs")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())
