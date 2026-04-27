"""
Test script to verify all WeatherAI backend endpoints
Run this after starting the backend server
"""
import httpx
import sys
from datetime import datetime

BASE_URL = "http://localhost:8000"

def test_health():
    """Test health endpoint"""
    print("\n[TEST 1] Health Check")
    print("-" * 50)
    try:
        response = httpx.get(f"{BASE_URL}/api/health", timeout=5.0)
        if response.status_code == 200:
            data = response.json()
            print(f"  [PASS] Status: {response.status_code}")
            print(f"  [PASS] Response: {data}")
            return True
        else:
            print(f"  [FAIL] Failed with status: {response.status_code}")
            return False
    except Exception as e:
        print(f"  [FAIL] Error: {e}")
        return False

def test_weather_by_region():
    """Test weather by region endpoint"""
    print("\n[TEST 2] Weather by Region (Delhi)")
    print("-" * 50)
    try:
        params = {"state": "Delhi", "district": "New Delhi"}
        response = httpx.get(f"{BASE_URL}/api/weather/by-region", params=params, timeout=10.0)
        if response.status_code == 200:
            data = response.json()
            print(f"  [PASS] Status: {response.status_code}")
            print(f"  [PASS] Location: {data.get('location')}")
            print(f"  [PASS] Temperature: {data.get('temperature_c')}°C")
            print(f"  [PASS] Humidity: {data.get('humidity')}%")
            print(f"  [PASS] Feels Like: {data.get('feels_like_c')}°C")
            print(f"  [PASS] Wind Speed: {data.get('windspeed_kph')} km/h")
            print(f"  [PASS] Weather Code: {data.get('weathercode')}")
            return True
        else:
            print(f"  [FAIL] Failed with status: {response.status_code}")
            print(f"  Response: {response.text}")
            return False
    except Exception as e:
        print(f"  [FAIL] Error: {e}")
        return False

def test_weather_current():
    """Test current weather by coordinates"""
    print("\n[TEST 3] Current Weather (Mumbai coordinates)")
    print("-" * 50)
    try:
        params = {"lat": 19.0760, "lon": 72.8777}
        response = httpx.get(f"{BASE_URL}/api/weather/current", params=params, timeout=10.0)
        if response.status_code == 200:
            data = response.json()
            print(f"  [PASS] Status: {response.status_code}")
            print(f"  [PASS] Temperature: {data.get('temperature_c')}°C")
            print(f"  [PASS] Humidity: {data.get('humidity')}%")
            print(f"  [PASS] Precipitation: {data.get('precipitation')} mm")
            print(f"  [PASS] Wind Speed: {data.get('windspeed_kph')} km/h")
            return True
        else:
            print(f"  [FAIL] Failed with status: {response.status_code}")
            return False
    except Exception as e:
        print(f"  [FAIL] Error: {e}")
        return False

def test_hourly_forecast():
    """Test hourly forecast endpoint"""
    print("\n[TEST 4] Hourly Forecast (Bangalore, 12 hours)")
    print("-" * 50)
    try:
        params = {"lat": 12.9716, "lon": 77.5946, "hours": 12}
        response = httpx.get(f"{BASE_URL}/api/weather/hourly", params=params, timeout=10.0)
        if response.status_code == 200:
            data = response.json()
            forecast = data.get('forecast', [])
            print(f"  [PASS] Status: {response.status_code}")
            print(f"  [PASS] Forecast hours received: {len(forecast)}")
            if forecast:
                print(f"  [PASS] First hour: {forecast[0].get('time')}")
                print(f"  - Temperature: {forecast[0].get('temperature_c')}°C")
                print(f"  - Humidity: {forecast[0].get('humidity')}%")
                print(f"  - Precipitation Probability: {forecast[0].get('precipitation_probability')}%")
            return True
        else:
            print(f"  [FAIL] Failed with status: {response.status_code}")
            return False
    except Exception as e:
        print(f"  [FAIL] Error: {e}")
        return False

def test_ai_query():
    """Test AI query endpoint"""
    print("\n[TEST 5] AI Query")
    print("-" * 50)
    try:
        payload = {
            "query": "Will it rain today?",
            "lat": 28.6139,
            "lon": 77.2090
        }
        response = httpx.post(f"{BASE_URL}/api/ai/query", json=payload, timeout=15.0)
        if response.status_code == 200:
            data = response.json()
            print(f"  [PASS] Status: {response.status_code}")
            print(f"  [PASS] Mode: {data.get('mode')}")
            print(f"  [PASS] Answer: {data.get('answer')[:100]}...")
            return True
        else:
            print(f"  [FAIL] Failed with status: {response.status_code}")
            return False
    except Exception as e:
        print(f"  [FAIL] Error: {e}")
        return False

def test_geocode_suggest():
    """Test geocode suggestions"""
    print("\n[TEST 6] Geocode Suggestions")
    print("-" * 50)
    try:
        params = {"state": "Karnataka", "q": "Bang"}
        response = httpx.get(f"{BASE_URL}/api/geocode/suggest", params=params, timeout=10.0)
        if response.status_code == 200:
            data = response.json()
            suggestions = data.get('suggestions', [])
            print(f"  [PASS] Status: {response.status_code}")
            print(f"  [PASS] Suggestions found: {len(suggestions)}")
            for i, sug in enumerate(suggestions[:3], 1):
                print(f"  {i}. {sug.get('display_name')}")
            return True
        else:
            print(f"  [FAIL] Failed with status: {response.status_code}")
            return False
    except Exception as e:
        print(f"  [FAIL] Error: {e}")
        return False

def main():
    print("=" * 50)
    print("WeatherAI Backend Test Suite")
    print(f"Testing server at: {BASE_URL}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)
    
    tests = [
        test_health,
        test_weather_by_region,
        test_weather_current,
        test_hourly_forecast,
        test_ai_query,
        test_geocode_suggest,
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"\n✗ Test failed with exception: {e}")
            results.append(False)
    
    # Summary
    print("\n" + "=" * 50)
    print("TEST SUMMARY")
    print("=" * 50)
    passed = sum(results)
    total = len(results)
    print(f"Passed: {passed}/{total}")
    print(f"Failed: {total - passed}/{total}")
    
    if passed == total:
        print("\n[PASS] All tests passed! Backend is working correctly.")
        sys.exit(0)
    else:
        print("\n[FAIL] Some tests failed. Please check the output above.")
        sys.exit(1)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nTests interrupted by user.")
        sys.exit(1)
