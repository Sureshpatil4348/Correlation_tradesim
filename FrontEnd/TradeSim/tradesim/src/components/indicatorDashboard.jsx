import React, { useEffect, useRef, useState, useCallback } from 'react';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend
} from 'chart.js';
import { Line } from 'react-chartjs-2';
import axios from 'axios';

// Register ChartJS components
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend
);

const styles = {
  container: {
    padding: '1.5rem',
    backgroundColor: '#f8f9fa',
  },
  error: {
    padding: '1rem',
    marginBottom: '1rem',
    borderRadius: '0.5rem',
    backgroundColor: '#fee2e2',
    border: '1px solid #ef4444',
    color: '#991b1b',
    fontSize: '0.875rem',
  },
  statusBadge: (status) => ({
    padding: '0.75rem',
    marginBottom: '1rem',
    borderRadius: '0.5rem',
    fontWeight: 500,
    textAlign: 'center',
    transition: 'all 0.3s ease',
    ...(status === 'connected' && {
      backgroundColor: '#dcfce7',
      border: '1px solid #22c55e',
      color: '#15803d',
    }),
    ...(status === 'connecting' && {
      backgroundColor: '#fef9c3',
      border: '1px solid #eab308',
      color: '#854d0e',
    }),
    ...(status === 'disconnected' && {
      backgroundColor: '#fee2e2',
      border: '1px solid #ef4444',
      color: '#991b1b',
    }),
  }),
  metricsGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))',
    gap: '1rem',
    marginBottom: '1.5rem',
  },
  metricCard: {
    backgroundColor: 'white',
    padding: '1.25rem',
    borderRadius: '0.5rem',
    boxShadow: '0 1px 3px rgba(0, 0, 0, 0.1)',
    transition: 'transform 0.2s ease',
    cursor: 'pointer',
  },
  metricCardHover: {
    transform: 'translateY(-2px)',
  },
  metricTitle: {
    fontSize: '0.875rem',
    color: '#6b7280',
    marginBottom: '0.5rem',
  },
  metricValue: {
    fontSize: '1.5rem',
    fontWeight: 600,
    color: '#111827',
    margin: 0,
  },
  metricSubtext: {
    color: '#6b7280',
    fontSize: '0.75rem',
  },
  chartSection: {
    backgroundColor: 'white',
    borderRadius: '0.5rem',
    boxShadow: '0 1px 3px rgba(0, 0, 0, 0.1)',
    overflow: 'hidden',
  },
  chartButton: {
    width: '100%',
    padding: '1rem',
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    backgroundColor: '#f8fafc',
    border: 'none',
    borderBottom: '1px solid #e2e8f0',
    cursor: 'pointer',
    transition: 'background-color 0.2s ease',
  },
  chartButtonHover: {
    backgroundColor: '#f1f5f9',
  },
  chartButtonText: {
    fontSize: '1rem',
    fontWeight: 500,
    color: '#334155',
  },
  arrow: (isVisible) => ({
    transform: isVisible ? 'rotate(180deg)' : 'rotate(0deg)',
    transition: 'transform 0.3s ease',
    fontSize: '1.25rem',
  }),
  chartContainer: (isVisible) => ({
    height: isVisible ? '600px' : '0px',
    padding: isVisible ? '1.5rem' : '0',
    transition: 'all 0.3s ease',
    overflow: 'hidden',
  }),
};

const MAX_RETRIES = 3;
const RETRY_DELAY = 5000;

const IndicatorDashboard = ({ strategyParams }) => {
  const [indicatorData, setIndicatorData] = useState({
    correlation: 0,
    rsi1: 0,
    rsi2: 0,
    pair1: '',
    pair2: '',
  });

  const [chartData, setChartData] = useState({
    correlation: [],
    rsi: [],
    labels: [],
  });

  const [connectionStatus, setConnectionStatus] = useState('disconnected');
  const [error, setError] = useState(null);
  const [retryCount, setRetryCount] = useState(0);
  const wsRef = useRef(null);
  const retryTimeoutRef = useRef(null);
  const streamInitiatedRef = useRef(false);
  const strategyIdRef = useRef(null);

  const [hoveredCard, setHoveredCard] = useState(null);
  const [isChartVisible, setIsChartVisible] = useState(false);
  const [isButtonHovered, setIsButtonHovered] = useState(false);

  // Add ref for chart instance
  const chartRef = useRef(null);

  const startStream = useCallback(async () => {
    if (streamInitiatedRef.current && strategyIdRef.current === strategyParams.id) {
      return;
    }

    try {
      const response = await axios.post('http://localhost:5002/start-stream/', 
        {
          ...strategyParams,
          lotSize: strategyParams.lotSize.map(String),
          magicNumber: String(strategyParams.magicNumber)
        },
        {
          headers: { 'Content-Type': 'application/json' },
          withCredentials: true
        }
      );
      
      if (response.data.websocket_url) {
        streamInitiatedRef.current = true;
        strategyIdRef.current = strategyParams.id;
        connectWebSocket(response.data.websocket_url);
      }
    } catch (error) {
      const errorMessage = error.response?.data?.detail?.message || 
                          error.response?.data?.detail ||
                          'Failed to start indicator stream';
      setError(errorMessage);
      setConnectionStatus('error');
    }
  }, [strategyParams.id]);

  const connectWebSocket = useCallback((wsUrl) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      console.log('WebSocket already connected');
      return;
    }

    try {
      if (wsRef.current) {
        wsRef.current.close();
      }

      setConnectionStatus('connecting');
      console.log('Connecting to:', wsUrl);
      wsRef.current = new WebSocket(wsUrl);

      wsRef.current.onopen = () => {
        console.log('WebSocket connected');
        setConnectionStatus('connected');
        setError(null);
        setRetryCount(0);
      };

      wsRef.current.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          if (data.error) {
            setError(data.error);
            return;
          }

          // Update current values
          if (data.correlation !== undefined) {
            const timestamp = new Date(data.timestamp).toLocaleTimeString();
            
            setIndicatorData(prev => ({
              correlation: typeof data.correlation === 'number' ? data.correlation.toFixed(3) : data.correlation,
              rsi1: formatValue(data.rsi_values?.[Object.keys(data.current_prices)[0]]),
              rsi2: formatValue(data.rsi_values?.[Object.keys(data.current_prices)[1]]),
              pair1: Object.keys(data.current_prices)[0] || '',
              pair2: Object.keys(data.current_prices)[1] || '',
              thresholds: data.thresholds
            }));

            // Update chart data
            setChartData(prev => {
              const newCorrelation = [...prev.correlation, data.correlation];
              const rsi1 = data.rsi_values?.[Object.keys(data.current_prices)[0]];
              const rsi2 = data.rsi_values?.[Object.keys(data.current_prices)[1]];
              const avgRsi = (rsi1 && rsi2) ? (rsi1 + rsi2) / 2 : null;
              const newRsi = [...prev.rsi, avgRsi];
              const newLabels = [...prev.labels, timestamp];

              // Keep last 100 points
              const maxPoints = 100;
              return {
                correlation: newCorrelation.slice(-maxPoints),
                rsi: newRsi.slice(-maxPoints),
                labels: newLabels.slice(-maxPoints),
              };
            });
          }
        } catch (err) {
          console.error('Error processing message:', err);
        }
      };

      wsRef.current.onclose = (event) => {
        console.log('WebSocket closed:', event);
        setConnectionStatus('disconnected');
        
        if (retryCount < MAX_RETRIES) {
          console.log(`Retrying connection (${retryCount + 1}/${MAX_RETRIES})...`);
          setRetryCount(prev => prev + 1);
          retryTimeoutRef.current = setTimeout(() => startStream(), RETRY_DELAY);
        } else {
          setError('Maximum retry attempts reached');
        }
      };

      wsRef.current.onerror = (error) => {
        console.error('WebSocket error:', error);
        setError('WebSocket connection error');
        setConnectionStatus('error');
      };

    } catch (err) {
      console.error('Error setting up WebSocket:', err);
      setError('Failed to setup WebSocket connection');
      setConnectionStatus('error');
    }
  }, []);

  useEffect(() => {
    if (!strategyParams) {
      setError('No strategy parameters provided');
      return;
    }

    startStream();

    // Cleanup function
    return () => {
      // Destroy chart instance
      if (chartRef.current) {
        chartRef.current.destroy();
      }
      // Cleanup WebSocket
      if (wsRef.current) {
        wsRef.current.close();
      }
      if (retryTimeoutRef.current) {
        clearTimeout(retryTimeoutRef.current);
      }
      streamInitiatedRef.current = false;
      strategyIdRef.current = null;
    };
  }, [strategyParams.id]);

  const formatValue = (value) => {
    return typeof value === 'number' ? value.toFixed(2) : value || 'N/A';
  };

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    interaction: {
      mode: 'index',
      intersect: false,
    },
    plugins: {
      title: {
        display: true,
        text: 'Trading Indicators',
        font: {
          size: 16,
          weight: 'bold',
        },
        padding: 20,
      },
      legend: {
        position: 'top',
        labels: {
          usePointStyle: true,
          padding: 15,
          font: {
            size: 12,
          },
        },
      },
      tooltip: {
        backgroundColor: 'rgba(255, 255, 255, 0.9)',
        titleColor: '#333',
        bodyColor: '#666',
        borderColor: '#ddd',
        borderWidth: 1,
        padding: 10,
        callbacks: {
          label: function(context) {
            let label = context.dataset.label || '';
            if (label) {
              label += ': ';
            }
            if (context.parsed.y !== null) {
              label += context.parsed.y.toFixed(3);
            }
            return label;
          }
        }
      }
    },
    scales: {
      y: {
        type: 'linear',
        display: true,
        position: 'left',
        min: -1,
        max: 1,
        title: {
          display: true,
          text: 'Correlation',
          font: {
            weight: 'bold',
          },
        },
        grid: {
          color: 'rgba(0, 0, 0, 0.05)',
        },
      },
      y1: {
        type: 'linear',
        display: true,
        position: 'right',
        min: 0,
        max: 100,
        title: {
          display: true,
          text: 'RSI',
          font: {
            weight: 'bold',
          },
        },
        grid: {
          display: false,
        },
      },
        },
  };

  const getChartData = () => {
    const thresholds = indicatorData.thresholds || {
      entry: 0.7,
      exit: 0.3,
      rsi_overbought: 70,
      rsi_oversold: 30
    };

    return {
      labels: chartData.labels,
      datasets: [
        {
          label: 'Correlation',
          data: chartData.correlation,
          borderColor: 'rgb(75, 192, 192)',
          yAxisID: 'y',
        },
        {
          label: 'RSI',
          data: chartData.rsi,
          borderColor: 'rgb(255, 99, 132)',
          yAxisID: 'y1',
        },
        {
          label: 'Entry Threshold',
          data: Array(chartData.labels.length).fill(thresholds.entry),
          borderColor: 'rgba(0, 255, 0, 0.5)',
          borderDash: [5, 5],
          yAxisID: 'y',
        },
        {
          label: 'Exit Threshold',
          data: Array(chartData.labels.length).fill(thresholds.exit),
          borderColor: 'rgba(255, 0, 0, 0.5)',
          borderDash: [5, 5],
          yAxisID: 'y',
        },
        {
          label: 'RSI Overbought',
          data: Array(chartData.labels.length).fill(thresholds.rsi_overbought),
          borderColor: 'rgba(255, 165, 0, 0.5)',
          borderDash: [5, 5],
          yAxisID: 'y1',
        },
        {
          label: 'RSI Oversold',
          data: Array(chartData.labels.length).fill(thresholds.rsi_oversold),
          borderColor: 'rgba(255, 165, 0, 0.5)',
          borderDash: [5, 5],
          yAxisID: 'y1',
        }
      ]
    };
  };

  return (
    <div style={styles.container}>
      {error && (
        <div style={styles.error}>
          <strong>Error: </strong>{error}
        </div>
      )}

      <div style={styles.statusBadge(connectionStatus)}>
        Status: {connectionStatus.charAt(0).toUpperCase() + connectionStatus.slice(1)}
      </div>

      <div style={styles.metricsGrid}>
        <div 
          style={{
            ...styles.metricCard,
            ...(hoveredCard === 'correlation' && styles.metricCardHover)
          }}
          onMouseEnter={() => setHoveredCard('correlation')}
          onMouseLeave={() => setHoveredCard(null)}
        >
          <h3 style={styles.metricTitle}>Correlation</h3>
          <p style={styles.metricValue}>{indicatorData.correlation}</p>
          <small style={styles.metricSubtext}>
            {indicatorData.pair1} vs {indicatorData.pair2}
          </small>
        </div>

        <div 
          style={{
            ...styles.metricCard,
            ...(hoveredCard === 'rsi1' && styles.metricCardHover)
          }}
          onMouseEnter={() => setHoveredCard('rsi1')}
          onMouseLeave={() => setHoveredCard(null)}
        >
          <h3 style={styles.metricTitle}>RSI {indicatorData.pair1}</h3>
          <p style={styles.metricValue}>{indicatorData.rsi1}</p>
        </div>

        <div 
          style={{
            ...styles.metricCard,
            ...(hoveredCard === 'rsi2' && styles.metricCardHover)
          }}
          onMouseEnter={() => setHoveredCard('rsi2')}
          onMouseLeave={() => setHoveredCard(null)}
        >
          <h3 style={styles.metricTitle}>RSI {indicatorData.pair2}</h3>
          <p style={styles.metricValue}>{indicatorData.rsi2}</p>
        </div>
      </div>

      <div style={styles.chartSection}>
        <button 
          style={{
            ...styles.chartButton,
            ...(isButtonHovered && styles.chartButtonHover)
          }}
          onClick={() => setIsChartVisible(!isChartVisible)}
          onMouseEnter={() => setIsButtonHovered(true)}
          onMouseLeave={() => setIsButtonHovered(false)}
        >
          <span style={styles.chartButtonText}>
            {isChartVisible ? 'Hide Chart' : 'Show Chart'}
          </span>
          <span style={styles.arrow(isChartVisible)}>▼</span>
        </button>
        
        <div style={styles.chartContainer(isChartVisible)}>
          <Line 
            ref={chartRef}
            options={chartOptions} 
            data={getChartData()} 
            redraw={false}
          />
        </div>
      </div>
    </div>
  );
};

export default IndicatorDashboard; 