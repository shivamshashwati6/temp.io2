import asyncio
import httpx

async def test_geocode():
    name = "Nalbari Assam"
    print(f"Testing geocode for: {name}")
    
    # Test Open-Meteo
    url = "https://geocoding-api.open-meteo.com/v1/search"
    params = {"name": name, "country": "IN", "count": 1}
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(url, params=params)
            print(f"Open-Meteo Status: {resp.status_code}")
            print(f"Open-Meteo Body: {resp.text}")
    except Exception as e:
        print(f"Open-Meteo Error: {e}")

    # Test Nominatim
    url2 = "https://nominatim.openstreetmap.org/search"
    params2 = {"format": "json", "q": "Nalbari, Assam, India", "limit": 1}
    headers = {"User-Agent": "TestScript/1.0"}
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(url2, params=params2, headers=headers)
            print(f"Nominatim Status: {resp.status_code}")
            print(f"Nominatim Body: {resp.text}")
    except Exception as e:
        print(f"Nominatim Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_geocode())
