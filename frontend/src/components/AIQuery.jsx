import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Sparkles, Send, Bot, User, Loader, Zap, Brain, MessageCircle } from 'lucide-react';
import WidgetRenderer from './widgets/WidgetRenderer';

const AIQuery = ({ onAsk, response, loading, weatherData }) => {
    const [query, setQuery] = useState('');
    const [chatHistory, setChatHistory] = useState([]);

    const handleSubmit = (e) => {
        e.preventDefault();
        if (query.trim() && !loading) {
            setChatHistory(prev => [...prev, { role: 'user', type: 'text', text: query }]);
            onAsk(query);
            setQuery('');
        }
    };

    useEffect(() => {
        if (response && !loading) {
            setChatHistory(prev => {
                // Prevent duplicate responses if the prop hasn't changed but useEffect re-runs
                const lastMsg = prev[prev.length - 1];
                
                let parsedResponse;
                try {
                    // Try to parse if it's a JSON string
                    parsedResponse = typeof response === 'string' ? JSON.parse(response) : response;
                } catch (e) {
                    // Fallback to plain text if not valid JSON
                    parsedResponse = { role: 'assistant', type: 'text', text: response };
                }

                // If parsedResponse is just a string (some LLMs might return a string even if we want JSON)
                if (typeof parsedResponse === 'string') {
                    parsedResponse = { role: 'assistant', type: 'text', text: parsedResponse };
                }

                // Deduplication check
                if (lastMsg && lastMsg.role === 'assistant' && 
                    (lastMsg.text === parsedResponse.text || JSON.stringify(lastMsg.data) === JSON.stringify(parsedResponse.data))) {
                    return prev;
                }

                return [...prev, parsedResponse];
            });
        }
    }, [response, loading]);

    const suggestions = [
        { icon: '🌧️', text: "Will it rain today?" },
        { icon: '🌡️', text: "What's the temperature?" },
        { icon: '💨', text: "Is it windy?" },
        { icon: '☂️', text: "Should I carry an umbrella?" },
        { icon: '👕', text: "What should I wear?" }
    ];

    return (
        <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.2 }}
            className="glass-panel"
            style={{
                padding: 'var(--spacing-lg)',
                borderRadius: 'var(--radius-xl)',
                display: 'flex',
                flexDirection: 'column',
                height: '650px',
                background: 'linear-gradient(135deg, rgba(192, 132, 252, 0.08), rgba(129, 140, 248, 0.08))',
                position: 'relative',
                overflow: 'hidden'
            }}
        >
            {/* Animated Background */}
            <div style={{
                position: 'absolute',
                top: '-50%',
                left: '50%',
                transform: 'translateX(-50%)',
                width: '400px',
                height: '400px',
                background: 'radial-gradient(circle, rgba(192, 132, 252, 0.15), transparent)',
                filter: 'blur(60px)',
                pointerEvents: 'none',
                animation: 'pulse 8s ease-in-out infinite'
            }} />

            <div style={{ position: 'relative', zIndex: 1, display: 'flex', flexDirection: 'column', height: '100%' }}>
                {/* Header */}
                <div style={{
                    paddingBottom: '20px',
                    borderBottom: '2px solid var(--glass-border)',
                    marginBottom: '20px'
                }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '8px' }}>
                        <motion.div
                            animate={{
                                rotate: [0, 360],
                                scale: [1, 1.1, 1]
                            }}
                            transition={{ duration: 8, repeat: Infinity, ease: "linear" }}
                            style={{
                                background: 'linear-gradient(135deg, var(--color-accent-tertiary), var(--color-accent-secondary))',
                                borderRadius: '12px',
                                padding: '10px',
                                display: 'flex',
                                alignItems: 'center',
                                justifyContent: 'center',
                                boxShadow: '0 0 20px rgba(192, 132, 252, 0.4)'
                            }}
                        >
                            <Brain size={24} color="#fff" strokeWidth={2.5} />
                        </motion.div>

                        <div style={{ flex: 1 }}>
                            <h3 style={{
                                fontSize: '1.6rem',
                                fontWeight: '800',
                                margin: 0,
                                background: 'linear-gradient(135deg, var(--color-accent-tertiary), var(--color-accent-secondary))',
                                WebkitBackgroundClip: 'text',
                                WebkitTextFillColor: 'transparent',
                                display: 'flex',
                                alignItems: 'center',
                                gap: '8px'
                            }}>
                                AI Weather Assistant
                                <motion.div
                                    animate={{ rotate: [0, 10, -10, 0] }}
                                    transition={{ duration: 2, repeat: Infinity }}
                                >
                                    <Zap size={20} color="var(--color-accent-warning)" fill="var(--color-accent-warning)" />
                                </motion.div>
                            </h3>
                            <p style={{
                                fontSize: '0.85rem',
                                color: 'var(--text-muted)',
                                margin: 0,
                                fontWeight: '500'
                            }}>
                                {weatherData ? 'Powered by GPT-3.5 • Ask me anything!' : 'Select a location to get started'}
                            </p>
                        </div>

                        {/* AI Badge */}
                        <motion.div
                            animate={{ scale: [1, 1.05, 1] }}
                            transition={{ duration: 2, repeat: Infinity }}
                            style={{
                                padding: '6px 12px',
                                background: 'linear-gradient(135deg, rgba(192, 132, 252, 0.2), rgba(129, 140, 248, 0.2))',
                                border: '1px solid var(--color-accent-tertiary)',
                                borderRadius: 'var(--radius-sm)',
                                fontSize: '0.7rem',
                                fontWeight: '700',
                                color: 'var(--color-accent-tertiary)',
                                textTransform: 'uppercase',
                                letterSpacing: '0.05em'
                            }}
                        >
                            AI
                        </motion.div>
                    </div>
                </div>

                {/* Chat Area */}
                <div style={{
                    flex: 1,
                    overflowY: 'auto',
                    marginBottom: '16px',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: '14px',
                    padding: '4px'
                }}>
                    <AnimatePresence>
                        {chatHistory.length === 0 && !loading && (
                            <motion.div
                                initial={{ opacity: 0, y: 20 }}
                                animate={{ opacity: 1, y: 0 }}
                                exit={{ opacity: 0, y: -20 }}
                                style={{
                                    textAlign: 'center',
                                    padding: '40px 20px'
                                }}
                            >
                                <motion.div
                                    animate={{
                                        y: [0, -10, 0],
                                        rotate: [0, 5, -5, 0]
                                    }}
                                    transition={{ duration: 4, repeat: Infinity, ease: "easeInOut" }}
                                    style={{ marginBottom: '20px' }}
                                >
                                    <MessageCircle size={56} color="var(--color-accent-tertiary)" strokeWidth={1.5} />
                                </motion.div>

                                <p style={{
                                    fontSize: '1.1rem',
                                    fontWeight: '600',
                                    color: 'var(--text-secondary)',
                                    marginBottom: '24px'
                                }}>
                                    Start a conversation!
                                </p>

                                <p style={{
                                    fontSize: '0.85rem',
                                    color: 'var(--text-muted)',
                                    marginBottom: '20px',
                                    fontWeight: '500'
                                }}>
                                    Try asking:
                                </p>

                                <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', alignItems: 'center' }}>
                                    {suggestions.slice(0, 3).map((sug, i) => (
                                        <motion.button
                                            key={i}
                                            initial={{ opacity: 0, x: -20 }}
                                            animate={{ opacity: 1, x: 0 }}
                                            transition={{ delay: i * 0.1 }}
                                            onClick={() => {
                                                if (!weatherData) return;
                                                setQuery(sug.text);
                                                setTimeout(() => {
                                                    setChatHistory([{ role: 'user', type: 'text', text: sug.text }]);
                                                    onAsk(sug.text);
                                                }, 100);
                                            }}
                                            style={{
                                                width: '100%',
                                                maxWidth: '300px',
                                                padding: '12px 16px',
                                                background: 'linear-gradient(135deg, rgba(192, 132, 252, 0.1), rgba(129, 140, 248, 0.1))',
                                                border: '1px solid rgba(192, 132, 252, 0.3)',
                                                borderRadius: 'var(--radius-md)',
                                                color: 'var(--text-secondary)',
                                                fontSize: '0.9rem',
                                                fontWeight: '500',
                                                cursor: weatherData ? 'pointer' : 'not-allowed',
                                                opacity: weatherData ? 1 : 0.6,
                                                transition: 'all var(--transition-base)',
                                                display: 'flex',
                                                alignItems: 'center',
                                                gap: '10px',
                                                textAlign: 'left'
                                            }}
                                            onMouseEnter={(e) => {
                                                if (!weatherData) return;
                                                e.target.style.background = 'linear-gradient(135deg, rgba(192, 132, 252, 0.2), rgba(129, 140, 248, 0.2))';
                                                e.target.style.borderColor = 'var(--color-accent-tertiary)';
                                            }}
                                            onMouseLeave={(e) => {
                                                if (!weatherData) return;
                                                e.target.style.background = 'linear-gradient(135deg, rgba(192, 132, 252, 0.1), rgba(129, 140, 248, 0.1))';
                                                e.target.style.borderColor = 'rgba(192, 132, 252, 0.3)';
                                            }}
                                        >
                                            <span style={{ fontSize: '1.2rem' }}>{sug.icon}</span>
                                            {sug.text}
                                        </motion.button>
                                    ))}
                                </div>
                            </motion.div>
                        )}

                        {chatHistory.map((chat, index) => (
                            <motion.div
                                key={index}
                                initial={{ opacity: 0, y: 10, scale: 0.95 }}
                                animate={{ opacity: 1, y: 0, scale: 1 }}
                                transition={{ duration: 0.3 }}
                                style={{
                                    display: 'flex',
                                    gap: '12px',
                                    alignItems: 'flex-start',
                                    flexDirection: chat.role === 'user' ? 'row-reverse' : 'row'
                                }}
                            >
                                {/* Avatar */}
                                <motion.div
                                    whileHover={{ scale: 1.1, rotate: 5 }}
                                    style={{
                                        width: '40px',
                                        height: '40px',
                                        borderRadius: '12px',
                                        background: chat.role === 'user'
                                            ? 'linear-gradient(135deg, var(--color-accent-primary), var(--color-accent-secondary))'
                                            : 'linear-gradient(135deg, var(--color-accent-tertiary), var(--color-accent-secondary))',
                                        display: 'flex',
                                        alignItems: 'center',
                                        justifyContent: 'center',
                                        flexShrink: 0,
                                        boxShadow: chat.role === 'user'
                                            ? '0 4px 12px rgba(56, 189, 248, 0.3)'
                                            : '0 4px 12px rgba(192, 132, 252, 0.3)'
                                    }}
                                >
                                    {chat.role === 'user' ? (
                                        <User size={22} color="#fff" strokeWidth={2.5} />
                                    ) : (
                                        <Bot size={22} color="#fff" strokeWidth={2.5} />
                                    )}
                                </motion.div>

                                {/* Message Content */}
                                <div style={{ 
                                    display: 'flex', 
                                    flexDirection: 'column', 
                                    gap: '8px',
                                    alignItems: chat.role === 'user' ? 'flex-end' : 'flex-start',
                                    maxWidth: '85%'
                                }}>
                                    {/* Text Message */}
                                    {(chat.text || chat.message) && (
                                        <motion.div
                                            whileHover={{ scale: 1.01 }}
                                            style={{
                                                background: chat.role === 'user'
                                                    ? 'linear-gradient(135deg, rgba(56, 189, 248, 0.15), rgba(56, 189, 248, 0.08))'
                                                    : 'linear-gradient(135deg, rgba(192, 132, 252, 0.15), rgba(192, 132, 252, 0.08))',
                                                padding: '14px 18px',
                                                borderRadius: '16px',
                                                border: `1px solid ${chat.role === 'user' ? 'rgba(56, 189, 248, 0.3)' : 'rgba(192, 132, 252, 0.3)'}`,
                                                lineHeight: '1.6',
                                                boxShadow: chat.role === 'user'
                                                    ? '0 2px 8px rgba(56, 189, 248, 0.1)'
                                                    : '0 2px 8px rgba(192, 132, 252, 0.1)'
                                            }}
                                        >
                                            <p style={{
                                                margin: 0,
                                                fontSize: '0.95rem',
                                                whiteSpace: 'pre-wrap',
                                                color: 'var(--text-primary)',
                                                fontWeight: '500'
                                            }}>
                                                {chat.text || chat.message}
                                            </p>
                                        </motion.div>
                                    )}

                                    {/* Widget Rendering */}
                                    {chat.type === 'widget' && chat.widgetType && (
                                        <WidgetRenderer 
                                            widgetType={chat.widgetType} 
                                            data={chat.data} 
                                        />
                                    )}
                                </div>
                            </motion.div>
                        ))}

                        {loading && (
                            <motion.div
                                initial={{ opacity: 0, y: 10 }}
                                animate={{ opacity: 1, y: 0 }}
                                style={{
                                    display: 'flex',
                                    gap: '12px',
                                    alignItems: 'flex-start'
                                }}
                            >
                                <div style={{
                                    width: '40px',
                                    height: '40px',
                                    borderRadius: '12px',
                                    background: 'linear-gradient(135deg, var(--color-accent-tertiary), var(--color-accent-secondary))',
                                    display: 'flex',
                                    alignItems: 'center',
                                    justifyContent: 'center',
                                    boxShadow: '0 4px 12px rgba(192, 132, 252, 0.3)'
                                }}>
                                    <Bot size={22} color="#fff" strokeWidth={2.5} />
                                </div>
                                <div style={{
                                    background: 'linear-gradient(135deg, rgba(192, 132, 252, 0.15), rgba(192, 132, 252, 0.08))',
                                    padding: '14px 18px',
                                    borderRadius: '16px',
                                    border: '1px solid rgba(192, 132, 252, 0.3)',
                                    display: 'flex',
                                    gap: '10px',
                                    alignItems: 'center'
                                }}>
                                    <motion.div
                                        animate={{ rotate: 360 }}
                                        transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
                                    >
                                        <Loader size={18} color="var(--color-accent-tertiary)" strokeWidth={2.5} />
                                    </motion.div>
                                    <span style={{ fontSize: '0.95rem', color: 'var(--text-secondary)', fontWeight: '500' }}>
                                        Analyzing weather...
                                    </span>
                                </div>
                            </motion.div>
                        )}
                    </AnimatePresence>
                </div>

                {/* Input Area */}
                <form onSubmit={handleSubmit} style={{ position: 'relative' }}>
                    <input
                        type="text"
                        value={query}
                        onChange={(e) => setQuery(e.target.value)}
                        placeholder="Ask about the weather..."
                        disabled={loading || !weatherData}
                        style={{
                            width: '100%',
                            padding: '16px 60px 16px 20px',
                            background: 'rgba(255, 255, 255, 0.05)',
                            border: '2px solid var(--glass-border)',
                            borderRadius: 'var(--radius-lg)',
                            color: '#fff',
                            fontSize: '1rem',
                            fontWeight: '500',
                            transition: 'all var(--transition-base)',
                            outline: 'none'
                        }}
                        onFocus={(e) => {
                            e.target.style.borderColor = 'var(--color-accent-tertiary)';
                            e.target.style.background = 'rgba(255, 255, 255, 0.08)';
                            e.target.style.boxShadow = '0 0 0 4px rgba(192, 132, 252, 0.1)';
                        }}
                        onBlur={(e) => {
                            e.target.style.borderColor = 'var(--glass-border)';
                            e.target.style.background = 'rgba(255, 255, 255, 0.05)';
                            e.target.style.boxShadow = 'none';
                        }}
                    />
                    <motion.button
                        type="submit"
                        disabled={loading || !query.trim() || !weatherData}
                        whileHover={{ scale: query.trim() && !loading && weatherData ? 1.05 : 1 }}
                        whileTap={{ scale: query.trim() && !loading && weatherData ? 0.95 : 1 }}
                        style={{
                            position: 'absolute',
                            right: '8px',
                            top: '50%',
                            transform: 'translateY(-50%)',
                            background: loading || !query.trim() || !weatherData
                                ? 'rgba(192, 132, 252, 0.2)'
                                : 'linear-gradient(135deg, var(--color-accent-tertiary), var(--color-accent-secondary))',
                            border: 'none',
                            borderRadius: '12px',
                            width: '44px',
                            height: '44px',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            cursor: loading || !query.trim() || !weatherData ? 'not-allowed' : 'pointer',
                            opacity: loading || !query.trim() || !weatherData ? 0.4 : 1,
                            transition: 'all var(--transition-base)',
                            boxShadow: query.trim() && !loading && weatherData ? '0 4px 12px rgba(192, 132, 252, 0.4)' : 'none'
                        }}
                    >
                        <Send size={20} color="#fff" strokeWidth={2.5} />
                    </motion.button>
                </form>
            </div>

            <style>{`
        @keyframes pulse {
          0%, 100% { opacity: 1; transform: translateX(-50%) scale(1); }
          50% { opacity: 0.8; transform: translateX(-50%) scale(1.1); }
        }
      `}</style>
        </motion.div>
    );
};

export default AIQuery;
