import React, { useState, useEffect } from 'react';
import axios from 'axios';
import Header from './components/Header';
import LocationSearch from './components/LocationSearch';
import WeatherCard from './components/WeatherCard';
import AIQuery from './components/AIQuery';
import WeatherAlerts from './components/WeatherAlerts';

function App() {
  const [weatherData, setWeatherData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [aiResponse, setAiResponse] = useState('');
  const [aiLoading, setAiLoading] = useState(false);
  const [currentLocation, setCurrentLocation] = useState({ lat: null, lon: null });

  const fetchWeather = async (state, district) => {
    setLoading(true);
    setError(null);
    setAiResponse(''); // Clear previous AI response
    try {
      const params = { state };
      if (district) params.district = district;

      // Use the API URL from environment variables, or default to /api for local proxying
      const API_BASE_URL = import.meta.env.VITE_API_URL || '/api';
      const response = await axios.get(`${API_BASE_URL}/weather/by-region`, { params });
      setWeatherData(response.data);
      setCurrentLocation({ lat: response.data.latitude, lon: response.data.longitude });
    } catch (err) {
      console.error(err);
      // Show helpful connection error if server is down
      const isLocal = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1';
      const errorMessage = !err.response 
        ? (isLocal ? 'Backend server is offline. Please run start-backend.bat.' : 'Unable to connect to the weather service. Please try again later.')
        : (err.response?.data?.detail || 'Failed to fetch weather data. Please check the location and try again.');
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const handleAiQuery = async (query) => {
    setAiLoading(true);
    try {
      const payload = { query };
      if (currentLocation.lat && currentLocation.lon) {
        payload.lat = currentLocation.lat;
        payload.lon = currentLocation.lon;
      }

      const API_BASE_URL = import.meta.env.VITE_API_URL || '/api';
      const response = await axios.post(`${API_BASE_URL}/ai/query`, payload);
      setAiResponse(response.data.answer);
    } catch (err) {
      console.error(err);
      setAiResponse('Sorry, I could not process your request at the moment.');
    } finally {
      setAiLoading(false);
    }
  };

  // Initial load - default to Delhi
  useEffect(() => {
    fetchWeather('Delhi', 'New Delhi');
  }, []);

  return (
    <div className="container">
      <Header />

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(400px, 1fr))', gap: 'var(--spacing-xl)', alignItems: 'start' }}>
        <div style={{ maxWidth: '700px', margin: '0 auto', width: '100%' }}>
          <LocationSearch onSearch={({ state, district }) => fetchWeather(state, district)} />
          <WeatherCard
            data={weatherData}
            loading={loading}
            error={error}
            localTime={weatherData?.time}
          />
          <WeatherAlerts weatherData={weatherData} />
        </div>

        <div style={{ maxWidth: '600px', margin: '0 auto', width: '100%' }}>
          <AIQuery
            onAsk={handleAiQuery}
            response={aiResponse}
            loading={aiLoading}
            weatherData={weatherData}
          />

          <div className="glass-panel" style={{ marginTop: 'var(--spacing-lg)', padding: 'var(--spacing-md)' }}>
            <h3 style={{ fontSize: '1.1rem', marginBottom: '10px' }}>About</h3>
            <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', lineHeight: '1.5' }}>
              This application uses advanced weather models to provide accurate forecasts for every district in India.
              Powered by Open-Meteo and AI.
            </p>
          </div>
        </div>
      </div>

      <footer style={{ marginTop: 'var(--spacing-xl)', textAlign: 'center', color: 'var(--text-muted)', fontSize: '0.9rem', padding: '20px 0', borderTop: '1px solid var(--glass-border)' }}>
        <p>&copy; {new Date().getFullYear()} Temp.io. Built with ❤️ for India.</p>
        <p style={{ fontSize: '0.8rem', marginTop: '8px' }}>Powered by Open-Meteo & Advanced AI</p>
        <p style={{ fontSize: '0.75rem', marginTop: '12px', opacity: 0.7 }}>
          Crafted by <a href="https://github.com/HyperPenetrator" target="_blank" rel="noopener noreferrer" style={{ color: 'var(--color-accent-tertiary)', textDecoration: 'none', fontWeight: '600' }}>HyperPenetrator</a>
        </p>
      </footer>
    </div>
  );
}

export default App;
