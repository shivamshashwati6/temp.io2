import React from 'react';
import { motion } from 'framer-motion';
import { Wind } from 'lucide-react';

const getAqiColor = (aqi) => {
    if (aqi <= 50) return '#10b981'; // Good (Green)
    if (aqi <= 100) return '#f59e0b'; // Moderate (Yellow/Orange)
    if (aqi <= 150) return '#f97316'; // Unhealthy for Sensitive (Orange)
    if (aqi <= 200) return '#ef4444'; // Unhealthy (Red)
    if (aqi <= 300) return '#7e22ce'; // Very Unhealthy (Purple)
    return '#7f1d1d'; // Hazardous (Maroon)
};

const AqiDialWidget = ({ data }) => {
    const { aqi, category } = data;
    const color = getAqiColor(aqi);
    
    // Calculate rotation for the dial (0 to 180 degrees)
    // Assuming max AQI for scale is 500
    const percentage = Math.min(aqi / 500, 1);

    return (
        <motion.div
            initial={{ opacity: 0, scale: 0.9, y: 10 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            className="glass-panel p-6 w-full max-w-sm overflow-hidden"
            style={{
                background: 'linear-gradient(135deg, rgba(255, 255, 255, 0.1), rgba(255, 255, 255, 0.05))',
                border: '1px solid rgba(255, 255, 255, 0.2)',
            }}
        >
            <div className="flex items-center gap-2 mb-6">
                <Wind size={20} className="text-slate-400" />
                <h4 className="text-sm font-bold text-slate-300 uppercase tracking-widest">Air Quality Index</h4>
            </div>

            <div className="relative flex flex-col items-center">
                <div className="relative w-48 h-24 overflow-hidden">
                    {/* Semi-circle background */}
                    <svg className="w-48 h-48 -rotate-180 transform" viewBox="0 0 100 100">
                        <circle
                            cx="50"
                            cy="50"
                            r="45"
                            fill="none"
                            stroke="rgba(255,255,255,0.1)"
                            strokeWidth="10"
                            strokeDasharray="141.37"
                            strokeDashoffset="141.37"
                        />
                        <motion.circle
                            cx="50"
                            cy="50"
                            r="45"
                            fill="none"
                            stroke={color}
                            strokeWidth="10"
                            strokeDasharray="282.7"
                            initial={{ strokeDashoffset: 282.7 }}
                            animate={{ strokeDashoffset: 282.7 - (percentage * 141.35) }}
                            transition={{ duration: 1.5, ease: "easeOut" }}
                            className="drop-shadow-[0_0_8px_rgba(255,255,255,0.3)]"
                        />
                    </svg>
                    
                    <div className="absolute bottom-0 left-0 right-0 flex flex-col items-center">
                        <span className="text-3xl font-black text-white">{aqi}</span>
                        <span className="text-[10px] font-bold uppercase tracking-tighter" style={{ color }}>
                            {category}
                        </span>
                    </div>
                </div>

                <div className="w-full mt-6 grid grid-cols-6 gap-1 h-1.5 rounded-full overflow-hidden opacity-50">
                    <div className="bg-[#10b981]" />
                    <div className="bg-[#f59e0b]" />
                    <div className="bg-[#f97316]" />
                    <div className="bg-[#ef4444]" />
                    <div className="bg-[#7e22ce]" />
                    <div className="bg-[#7f1d1d]" />
                </div>
            </div>
            
            <div className="absolute top-0 right-0 p-4 opacity-10">
                <Wind size={80} />
            </div>
        </motion.div>
    );
};

export default AqiDialWidget;
