import React, { useState } from 'react';
import axios from 'axios';

const Settings = () => {
    const [symbol, setSymbol] = useState('');
    const [timeframe, setTimeframe] = useState(15);
    const [loading, setLoading] = useState(false);
    const [results, setResults] = useState(null);
    const [error, setError] = useState(null);

    const timeframes = [
        { value: 1, label: '1 minute (M1)' },
        { value: 5, label: '5 minutes (M5)' },
        { value: 15, label: '15 minutes (M15)' },
        { value: 30, label: '30 minutes (M30)' },
        { value: 60, label: '1 hour (H1)' },
        { value: 240, label: '4 hours (H4)' },
        { value: 1440, label: '1 day (D1)' }
    ];

    const checkDataAvailability = async (e) => {
        e.preventDefault();
        setLoading(true);
        setResults(null);
        setError(null);
        
        try {
            const response = await axios.get('http://localhost:5001/mt5/available-data-range', {
                params: {
                    symbol,
                    timeframe: parseInt(timeframe)
                }
            });
            
            setResults(response.data);
        } catch (err) {
            setError(err.response?.data || { error: "Connection error. Please check if MT5 is running." });
        } finally {
            setLoading(false);
        }
    };

    return (
        <div style={{ marginLeft: '10vw', display: 'flex', flexDirection: 'column', padding: '20px' }}>
            <div style={{ display: 'flex', flexDirection: 'row', justifyContent: 'space-between', width: '100%', padding: '10px', height: '60px', alignItems: 'center' }}>
                <h2>Settings</h2>
            </div>
            
            <div style={{ border: '1px solid #ccc', borderRadius: '5px', padding: '20px', marginBottom: '20px' }}>
                <h3>Data Availability Checker</h3>
                <p style={{ color: 'grey' }}>Check how much historical data is available for a specific currency pair</p>
                
                <form onSubmit={checkDataAvailability} style={{ marginTop: '15px' }}>
                    <div style={{ display: 'flex', flexDirection: 'row', gap: '15px', flexWrap: 'wrap' }}>
                        <div style={{ display: 'flex', flexDirection: 'column', minWidth: '200px' }}>
                            <label style={{ marginBottom: '5px', fontWeight: '500' }}>Currency Symbol</label>
                            <input 
                                type="text" 
                                placeholder="Enter symbol (e.g., EURUSD)" 
                                value={symbol} 
                                onChange={(e) => setSymbol(e.target.value)}
                                style={{ 
                                    padding: '8px 12px', 
                                    borderRadius: '4px', 
                                    border: '1px solid #ccc', 
                                    fontSize: '14px' 
                                }}
                                required
                            />
                        </div>
                        
                        <div style={{ display: 'flex', flexDirection: 'column', minWidth: '200px' }}>
                            <label style={{ marginBottom: '5px', fontWeight: '500' }}>Timeframe</label>
                            <select 
                                value={timeframe} 
                                onChange={(e) => setTimeframe(e.target.value)}
                                style={{ 
                                    padding: '8px 12px', 
                                    borderRadius: '4px', 
                                    border: '1px solid #ccc', 
                                    fontSize: '14px',
                                    background: 'white' 
                                }}
                            >
                                {timeframes.map(tf => (
                                    <option key={tf.value} value={tf.value}>{tf.label}</option>
                                ))}
                            </select>
                        </div>
                        
                        <div style={{ display: 'flex', flexDirection: 'column', justifyContent: 'flex-end' }}>
                            <button 
                                type="submit" 
                                disabled={loading || !symbol} 
                                style={{ 
                                    padding: '8px 16px', 
                                    backgroundColor: loading || !symbol ? 'grey' : 'green',
                                    color: 'white', 
                                    border: 'none', 
                                    borderRadius: '4px',
                                    cursor: loading || !symbol ? 'not-allowed' : 'pointer',
                                    height: '36px'
                                }}
                            >
                                {loading ? 'Checking...' : 'Check Availability'}
                            </button>
                        </div>
                    </div>
                </form>
                
                {/* Results display */}
                {results && results.status === "success" && (
                    <div style={{ marginTop: '20px', padding: '15px', backgroundColor: '#f0f9f0', borderRadius: '5px', border: '1px solid #d0e9d0' }}>
                        <h4 style={{ margin: '0 0 10px 0', color: 'green' }}>Data Available for {results.symbol}</h4>
                        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
                            <div>
                                <p style={{ margin: '5px 0', fontWeight: '500' }}>Date Range:</p>
                                <p style={{ margin: '5px 0' }}>From: {results.data_range?.start}</p>
                                <p style={{ margin: '5px 0' }}>To: {results.data_range?.end}</p>
                            </div>
                            <div>
                                <p style={{ margin: '5px 0', fontWeight: '500' }}>Details:</p>
                                <p style={{ margin: '5px 0' }}>Timeframe: {timeframes.find(tf => tf.value === parseInt(timeframe))?.label}</p>
                                <p style={{ margin: '5px 0' }}>Total Bars: {results.total_bars || 'N/A'}</p>
                            </div>
                        </div>
                    </div>
                )}
                {results && results.status === "error" && (
                    <div style={{ marginTop: '20px', padding: '15px', backgroundColor: '#fff0f0', borderRadius: '5px', border: '1px solid #e9d0d0' }}>
                        <h4 style={{ margin: '0 0 10px 0', color: '#d32f2f' }}>Error</h4>
                        <p style={{ margin: '5px 0' }}>{results.error || "Unknown error occurred"}</p>
                    </div>
                )}
                
                {/* Error display */}
                {error && (
                    <div style={{ marginTop: '20px', padding: '15px', backgroundColor: '#fff0f0', borderRadius: '5px', border: '1px solid #e9d0d0' }}>
                        <h4 style={{ margin: '0 0 10px 0', color: '#d32f2f' }}>Error</h4>
                        <p style={{ margin: '5px 0' }}>{error.error || error.detail || "Unknown error occurred"}</p>
                        {error.available_symbols && (
                            <div>
                                <p style={{ margin: '10px 0 5px 0', fontWeight: '500' }}>Available symbols:</p>
                                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '5px' }}>
                                    {error.available_symbols.map(sym => (
                                        <span 
                                            key={sym} 
                                            style={{ 
                                                padding: '3px 8px', 
                                                backgroundColor: '#f5f5f5', 
                                                borderRadius: '3px',
                                                cursor: 'pointer',
                                                fontSize: '13px'
                                            }}
                                            onClick={() => setSymbol(sym)}
                                        >
                                            {sym}
                                        </span>
                                    ))}
                                </div>
                            </div>
                        )}
                    </div>
                )}
            </div>
        </div>
    );
};

export default Settings;
