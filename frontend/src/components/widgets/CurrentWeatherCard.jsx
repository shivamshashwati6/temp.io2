import React from 'react';
import { motion } from 'framer-motion';
import { Thermometer, Wind, Droplets, Sun, Cloud, CloudRain, CloudLightning, CloudSnow, CloudFog } from 'lucide-react';

const WeatherIcon = ({ condition, size = 48 }) => {
    const iconProps = { size, className: "text-accent-primary" };
    const lowerCondition = condition?.toLowerCase() || '';

    if (lowerCondition.includes('rain')) return <CloudRain {...iconProps} />;
    if (lowerCondition.includes('cloud')) return <Cloud {...iconProps} />;
    if (lowerCondition.includes('thunder')) return <CloudLightning {...iconProps} />;
    if (lowerCondition.includes('snow')) return <CloudSnow {...iconProps} />;
    if (lowerCondition.includes('mist') || lowerCondition.includes('fog')) return <CloudFog {...iconProps} />;
    return <Sun {...iconProps} />;
};

const CurrentWeatherCard = ({ data }) => {
    const { temp, condition, humidity, windSpeed, location } = data;

    return (
        <motion.div
            initial={{ opacity: 0, scale: 0.9, y: 10 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            className="glass-panel p-6 w-full max-w-sm overflow-hidden group"
            style={{
                background: 'linear-gradient(135deg, rgba(255, 255, 255, 0.1), rgba(255, 255, 255, 0.05))',
                border: '1px solid rgba(255, 255, 255, 0.2)',
                boxShadow: '0 8px 32px 0 rgba(0, 0, 0, 0.37)',
            }}
        >
            <div className="flex justify-between items-start mb-4">
                <div>
                    <h4 className="text-xl font-bold text-white mb-1">{location}</h4>
                    <p className="text-sm text-slate-300 font-medium">{condition}</p>
                </div>
                <div className="bg-white/10 p-3 rounded-2xl backdrop-blur-md border border-white/10 group-hover:scale-110 transition-transform duration-300">
                    <WeatherIcon condition={condition} />
                </div>
            </div>

            <div className="flex items-end gap-2 mb-6">
                <span className="text-5xl font-black text-white tracking-tighter">
                    {temp}°
                </span>
                <span className="text-lg font-bold text-slate-400 mb-2">C</span>
            </div>

            <div className="grid grid-cols-2 gap-4">
                <div className="flex items-center gap-3 bg-white/5 p-3 rounded-xl border border-white/5">
                    <div className="text-sky-400">
                        <Droplets size={20} />
                    </div>
                    <div>
                        <p className="text-[10px] uppercase tracking-wider text-slate-400 font-bold">Humidity</p>
                        <p className="text-sm font-bold text-white">{humidity}%</p>
                    </div>
                </div>
                <div className="flex items-center gap-3 bg-white/5 p-3 rounded-xl border border-white/5">
                    <div className="text-teal-400">
                        <Wind size={20} />
                    </div>
                    <div>
                        <p className="text-[10px] uppercase tracking-wider text-slate-400 font-bold">Wind</p>
                        <p className="text-sm font-bold text-white">{windSpeed} km/h</p>
                    </div>
                </div>
            </div>

            <div className="absolute -bottom-12 -right-12 w-32 h-32 bg-sky-500/10 blur-3xl rounded-full pointer-events-none" />
            <div className="absolute -top-12 -left-12 w-32 h-32 bg-purple-500/10 blur-3xl rounded-full pointer-events-none" />
        </motion.div>
    );
};

export default CurrentWeatherCard;
