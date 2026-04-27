import React from 'react';
import CurrentWeatherCard from './CurrentWeatherCard';
import AqiDialWidget from './AqiDialWidget';
import TrendGraphWidget from './TrendGraphWidget';

const WidgetRenderer = ({ widgetType, data }) => {
    switch (widgetType) {
        case 'CURRENT_WEATHER':
            return <CurrentWeatherCard data={data} />;
        case 'AQI_DIAL':
            return <AqiDialWidget data={data} />;
        case 'TREND_GRAPH':
            return <TrendGraphWidget data={data} />;
        default:
            return null;
    }
};

export default WidgetRenderer;
