import React, { useEffect, useState } from 'react';
import useStore from '../../stores/useStore';
import html2canvas from 'html2canvas';
import { jsPDF } from 'jspdf';
import axios from 'axios';
const Analytics = () => {
    const { strategyToBackTest, setStrategyToBackTest, accountInfo, setIsLoading } = useStore((state) => state);
    const [startDate, setStartDate] = useState('');
    const [endDate, setEndDate] = useState('');
    const [backtestData, setBacktestData] = useState([]);
    const [reportData, setReportData] = useState(false);
    const [dataRange, setDataRange] = useState([]);
    const [hasCalledApi, setHasCalledApi] = useState(false);

    useEffect(() => {
        const fetchDataSequentially = async () => {
            try {
                // Check if we've already made the calls
                if (hasCalledApi) return;
                
                setHasCalledApi(true); // Set flag before making calls
                
                // First currency pair
                await checkDataRange(strategyToBackTest?.currencyPairs[0], strategyToBackTest?.timeFrame);
                // Second currency pair - only called after first one completes
                await checkDataRange(strategyToBackTest?.currencyPairs[1], strategyToBackTest?.timeFrame);
            } catch (error) {
                console.error('Error fetching data ranges:', error);
            }
        };
        
        if (strategyToBackTest?.currencyPairs?.length > 0 && !hasCalledApi) {
            fetchDataSequentially();
        }
    }, [strategyToBackTest?.currencyPairs, hasCalledApi]);

    // Example API call
    const checkDataRange = async (symbol, timeframe) => {
        setIsLoading(true);
        try {
            const response = await axios.get(`http://localhost:5001/mt5/available-data-range`, {
                params: {
                    symbol,
                    timeframe
                }
            });
            
            setDataRange((prev) => {
                // Check if data for this symbol already exists
                const symbolExists = prev.some(item => item.symbol === response.data.symbol);
                
                // If symbol exists, don't add it again
                if (symbolExists) {
                    return prev;
                }
                
                // If symbol doesn't exist, add it to the array
                return [...prev, response.data];
            });
            setIsLoading(false);
        } catch (error) {
            console.error('Error checking data range:', error);
            throw error;
        }
    };

    const isStrategyComplete = (strategy) => {
        console.log("Strategy is", strategy);
        if (strategy === null) {
            console.log("Strategy is null");
            return false;
        }
        return Object.entries(strategy).every(([key, value]) => {
            // Skip checking the status key
            if (key === "status") {
                return true;
            }
            
            if (Array.isArray(value)) {
                console.log("Value is an array");
                return value.every(v => v !== '' && v !== null && v !== undefined);
            }
            console.log("Value is not an array");
            return value !== '' && value !== null && value !== undefined;
        });
    }
    const startBacktest = () => {
        if (startDate === '' || endDate === '' || startDate > endDate) {
            return;
        }

        setStrategyToBackTest({
            ...strategyToBackTest,
            startDate: startDate.split('-').map(Number),
            endDate: endDate.split('-').map(Number)
        });

        const fetchBacktestData = async () => {
            setIsLoading(true);
            const response = await fetch("http://localhost:5001/mt5/backtest-strategy/", {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({...strategyToBackTest, startDate: startDate, endDate: endDate})
            });
            const responseData = await response.json();
            if (!responseData.error) {
                setBacktestData(responseData);
                setIsLoading(false);
                setReportData(true);
            } else {
                setIsLoading(false);
                setReportData(false);
                alert(responseData.error);
            }
        }
        fetchBacktestData();
    }

    const generateReport = async () => {
        setIsLoading(true);
        const element = document.getElementById('report-container');
        
        // Get the full scroll height of the element
        const height = Math.max(
            element.scrollHeight,
            element.offsetHeight,
            element.clientHeight
        );

        // Configure html2canvas with full height and scale
        const canvas = await html2canvas(element, {
            height: height,
            windowHeight: height,
            scrollY: -window.scrollY,
            scale: 2,
            useCORS: true,
            logging: false,
            onclone: (document) => {
                document.getElementById('report-container').style.height = `${height}px`;
            }
        });

        const imgData = canvas.toDataURL('image/png');
        
        // Create A4 PDF
        const pdf = new jsPDF('p', 'mm', 'a4');
        const pageWidth = pdf.internal.pageSize.getWidth();
        const pageHeight = pdf.internal.pageSize.getHeight();

        // Calculate dimensions
        const imgWidth = canvas.width;
        const imgHeight = canvas.height;
        
        // Calculate the number of pages needed
        const pagesCount = Math.ceil(imgHeight / (canvas.width * (pageHeight / pageWidth)));
        
        // Split the image across pages
        for (let page = 0; page < pagesCount; page++) {
            if (page > 0) {
                pdf.addPage();
            }
            
            pdf.addImage(
                imgData,
                'PNG',
                0,
                -(page * pageHeight),
                pageWidth,
                (imgHeight * pageWidth) / imgWidth,
                '',
                'FAST'
            );
        }

        const fileName = `${strategyToBackTest?.name}-${startDate}-${endDate}-MN-${strategyToBackTest?.magicNumber}-${strategyToBackTest?.currencyPairs[0]}-${strategyToBackTest?.currencyPairs[1]}.pdf`;
        pdf.save(fileName);
        setIsLoading(false);
    }

    return (
        <div style={{ marginLeft: '10vw', display: 'flex', flexDirection: 'column'}}>
            <div id="report-container" style={{display: 'flex', flexDirection: 'column', width: '100%', height: '100%' }}>
            <div style={{ display: 'flex', flexDirection: 'row', justifyContent: 'space-between', width: '100%', padding: '10px', height: '60px', alignItems: 'center' }}>
                <h2>Analytics</h2>
                <div style={{ color: 'green', border: '1px solid green', padding: '5px', borderRadius: '5px' }}>Connected to MT5 ({accountInfo.account_number ? accountInfo.account_number : accountInfo.login})</div>
            </div>
            <div style={{ display: 'flex', flexDirection: 'row', justifyContent: 'space-between', width: '100%', padding: '10px', height: '60px', alignItems: 'center' }}>
                <div style={{ display: 'flex', flexDirection: 'row', justifyContent: 'space-between', width: '100%', padding: '10px', height: '60px', alignItems: 'center', border: '1px solid #ccc', borderRadius: '5px' }}>
                    <table style={{ width: '100%' }}>
                        <thead>
                            <tr>
                                    <th style={{borderBottom: '1px solid #ccc', fontWeight: '500', color: 'grey'}}>Currency Pair</th>
                                    <th style={{borderBottom: '1px solid #ccc', fontWeight: '500', color: 'grey'}}>Correlation Window</th>
                                    <th style={{borderBottom: '1px solid #ccc', fontWeight: '500', color: 'grey'}}>RSI</th>
                                    <th style={{borderBottom: '1px solid #ccc', fontWeight: '500', color: 'grey'}}>Lot Size</th>
                                    <th style={{borderBottom: '1px solid #ccc', fontWeight: '500', color: 'grey'}}>Overbought</th>
                                    <th style={{borderBottom: '1px solid #ccc', fontWeight: '500', color: 'grey'}}>Oversold</th>
                                    <th style={{borderBottom: '1px solid #ccc', fontWeight: '500', color: 'grey'}}>Timeframe</th>
                                    <th style={{borderBottom: '1px solid #ccc', fontWeight: '500', color: 'grey'}}>Entry Threshold</th>
                                    <th style={{borderBottom: '1px solid #ccc', fontWeight: '500', color: 'grey'}}>Exit Threshold</th>
                                    <th style={{borderBottom: '1px solid #ccc', fontWeight: '500', color: 'grey'}}>Starting Balance</th>
                                    <th style={{borderBottom: '1px solid #ccc', fontWeight: '500', color: 'grey'}}>Magic Number</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr>
                                <td style={{ textAlign: 'center' }}>{strategyToBackTest?.currencyPairs?.join(' & ')}</td>
                                <td style={{ textAlign: 'center' }}>{strategyToBackTest?.correlationWindow}</td>
                                <td style={{ textAlign: 'center' }}>{strategyToBackTest?.rsiPeriod}</td>
                                <td style={{ textAlign: 'center' }}><span>{strategyToBackTest?.currencyPairs[0]}: {strategyToBackTest?.lotSize[0]}</span> <br /> <span>{strategyToBackTest?.currencyPairs[1]}: {strategyToBackTest?.lotSize[1]}</span></td>
                                <td style={{ textAlign: 'center' }}>{strategyToBackTest?.rsiOverbought}</td>
                                <td style={{ textAlign: 'center' }}>{strategyToBackTest?.rsiOversold}</td>
                                <td style={{ textAlign: 'center' }}>{strategyToBackTest?.timeFrame}</td>
                                <td style={{ textAlign: 'center' }}>{strategyToBackTest?.entryThreshold}</td>
                                <td style={{ textAlign: 'center' }}>{strategyToBackTest?.exitThreshold}</td>
                                    <td style={{ textAlign: 'center' }}>{strategyToBackTest?.startingBalance}</td>
                                    <td style={{ textAlign: 'center' }}>{strategyToBackTest?.magicNumber}</td>
                            </tr>
                        </tbody>
                    </table>
                
                </div>
            </div>
            <div style={{ display: 'flex', flexDirection: 'row', justifyContent: 'space-between', width: '100%', padding: '10px', height: '60px', alignItems: 'center' }}>
                <h2>Performance Analytics</h2>
                <div style={{ color: 'grey', border: '1px solid green', padding: '5px', borderRadius: '5px' }}><span style={{ fontWeight: '500', color: 'grey' }}>Name: </span>{strategyToBackTest?.name}</div>
            </div>
            <div style={{ display: 'flex', flexDirection: 'row', justifyContent: 'space-between', width: '100%', padding: '10px', height: '60px', alignItems: 'center' }}>
            {dataRange?.map((range, index) => (
                    <div key={index} style={{ color: 'grey', border: '1px solid green', padding: '5px', borderRadius: '5px' }}>
                        <div style={{ fontWeight: '500', color: 'grey' }}>Data Range: {range.symbol}</div>
                        <div style={{ color: 'grey' }}>{new Date(range.data_range?.start).toLocaleDateString()} to {new Date(range.data_range?.end).toLocaleDateString()}</div>
                    </div>
                ))}
            </div>
            <div style={{ display: 'flex', flexDirection: 'row', justifyContent: 'space-between', width: '100%', padding: '10px 10px', height: '60px', alignItems: 'center' }}>
                <button style={{ width: '200px', height: '40px', backgroundColor: !isStrategyComplete(strategyToBackTest) || startDate === '' || endDate === '' || startDate > endDate ? 'grey' : 'green', border: 'none', borderRadius: '5px', color: 'white', cursor: !isStrategyComplete(strategyToBackTest) || startDate === '' || endDate === '' || startDate > endDate ? 'not-allowed' : 'pointer' }} disabled={!isStrategyComplete(strategyToBackTest) || startDate === '' || endDate === '' || startDate > endDate} onClick={() => startBacktest()}>Start Backtest</button>
                    <button disabled={!reportData} onClick={() => generateReport()} style={{ cursor: !reportData ? 'not-allowed' : 'pointer', backgroundColor: !reportData ? 'grey' : 'green', border: 'none', borderRadius: '5px', color: 'white', width: '200px', height: '40px' }}>Generate Report</button>
            </div>
            <div style={{ display: 'flex', flexDirection: 'row', justifyContent: 'space-between', width: '100%', padding: '0px 10px', height: '60px', alignItems: 'center' }}>
                <div style={{ display: 'flex', flexDirection: 'row', justifyContent: 'space-between', width: '40%', padding: '0px 10px', height: '60px', alignItems: 'center', border: '1px solid #ccc', borderRadius: '5px' }}>
                    <div style={{ display: 'flex', flexDirection: 'row', width: '50%', padding: '0px 10px', height: '60px', alignItems: 'center' }}>
                        <div style={{ fontWeight: '500', paddingRight: '5px' }}>From: </div>
                        <div>
                                <input style={{border: '1px solid #ccc', borderRadius: '5px', fontSize: '14px'}} type="date" value={startDate} onChange={(e) => setStartDate(e.target.value)} />
                            </div>
                    </div>
                    
                    <div style={{ display: 'flex', flexDirection: 'row', width: '50%', padding: '0px 10px', height: '60px', alignItems: 'center' }}>
                        <div style={{ fontWeight: '500', paddingRight: '5px' }}>To: </div>
                        <div>
                                <input style={{border: '1px solid #ccc', borderRadius: '5px', fontSize: '14px'}} type="date" value={endDate} onChange={(e) => setEndDate(e.target.value)} />
                            </div>
                    </div>
                </div>
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', justifyContent: 'space-between', width: '100%', padding: '20px 10px', alignItems: 'flex-start' }}>
                <h3>Metrics (Depending on initial balance)</h3>
                <div style={{ width: '100%', border: '1px solid #ccc', borderRadius: '5px'}}>
                    <table style={{ width: '100%' }}>
                        <thead>
                            <tr>
                                <th style={{borderBottom: backtestData.metrics ? '1px solid #ccc' : 'none', fontWeight: '500', color: 'grey'}}>Initial Balance</th>
                                <th style={{borderBottom: backtestData.metrics ? '1px solid #ccc' : 'none', fontWeight: '500', color: 'grey'}}>Net Profit Percentage</th>
                                <th style={{borderBottom: backtestData.metrics ? '1px solid #ccc' : 'none', fontWeight: '500', color: 'grey'}}>Net Profit Dollars</th>
                                <th style={{borderBottom: backtestData.metrics ? '1px solid #ccc' : 'none', fontWeight: '500', color: 'grey'}}>Max Drawdown</th>
                                <th style={{borderBottom: backtestData.metrics ? '1px solid #ccc' : 'none', fontWeight: '500', color: 'grey'}}>Max Drawdown Percentage</th>
                                <th style={{borderBottom: backtestData.metrics ? '1px solid #ccc' : 'none', fontWeight: '500', color: 'grey'}}>Profit Factor</th>
                                <th style={{borderBottom: backtestData.metrics ? '1px solid #ccc' : 'none', fontWeight: '500', color: 'grey'}}>Sharpe Ratio</th>
                                <th style={{borderBottom: backtestData.metrics ? '1px solid #ccc' : 'none', fontWeight: '500', color: 'grey'}}>Final Balance</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr>
                                <td style={{textAlign: 'center'}}>{backtestData.metrics && "$" + strategyToBackTest?.startingBalance}</td>
                                <td style={{textAlign: 'center'}}>{backtestData.metrics && backtestData?.metrics?.net_profit_percentage.toFixed(2) + "%"}</td>
                                <td style={{textAlign: 'center'}}>{"$" + backtestData.metrics && backtestData?.metrics?.net_profit_dollars.toFixed(2)}</td>
                                <td style={{textAlign: 'center'}}>{"$" + backtestData.metrics && backtestData?.metrics?.max_drawdown_dollars.toFixed(2)}</td>
                                <td style={{textAlign: 'center'}}>{backtestData.metrics && backtestData?.metrics?.max_drawdown_percentage.toFixed(2) + "%"}</td>
                                <td style={{textAlign: 'center'}}>{backtestData.metrics && backtestData?.metrics?.profit_factor.toFixed(2)}</td>
                                <td style={{textAlign: 'center'}}>{backtestData.metrics && backtestData?.metrics?.sharpe_ratio.toFixed(2)}</td>
                                <td style={{textAlign: 'center'}}>{"$" + backtestData.metrics && backtestData?.metrics?.final_balance.toFixed(2)}</td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', justifyContent: 'space-between', width: '100%', padding: '20px 10px', alignItems: 'flex-start' }}>
                <h3>Metrics (Depending on backtest data)</h3>
                <div style={{ width: '100%', border: '1px solid #ccc', borderRadius: '5px'}}>
                    <table style={{ width: '100%' }}>
                        <thead>
                            <tr>
                                <th style={{borderBottom: backtestData.metrics ? '1px solid #ccc' : 'none', fontWeight: '500', color: 'grey'}}>Total Trades</th>
                                <th style={{borderBottom: backtestData.metrics ? '1px solid #ccc' : 'none', fontWeight: '500', color: 'grey'}}>Total Winning Trades</th>
                                <th style={{borderBottom: backtestData.metrics ? '1px solid #ccc' : 'none', fontWeight: '500', color: 'grey'}}>Total Losing Trades</th>
                                <th style={{borderBottom: backtestData.metrics ? '1px solid #ccc' : 'none', fontWeight: '500', color: 'grey'}}>Win Rate</th>
                                <th style={{borderBottom: backtestData.metrics ? '1px solid #ccc' : 'none', fontWeight: '500', color: 'grey'}}>Avg Trade Duration</th>
                                <th style={{borderBottom: backtestData.metrics ? '1px solid #ccc' : 'none', fontWeight: '500', color: 'grey'}}>Avg Trade Profit</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr>
                                <td style={{textAlign: 'center'}}>{backtestData?.metrics?.total_trades}</td>
                                <td style={{textAlign: 'center'}}>{backtestData?.metrics?.winning_trades}</td>
                                <td style={{textAlign: 'center'}}>{backtestData?.metrics?.losing_trades}</td>
                                <td style={{textAlign: 'center'}}>{backtestData.metrics && backtestData?.metrics?.win_rate.toFixed(2)*100 + "%"}</td>
                                <td style={{textAlign: 'center'}}>{backtestData?.metrics?.avg_trade_duration.toFixed(2)}</td>
                                <td style={{textAlign: 'center'}}>{backtestData.trades && "$"+backtestData?.trades?.reduce((acc, trade) => acc + trade.total_profit, 0).toFixed(5)}</td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', justifyContent: 'space-between', width: '100%', padding: '20px 10px', alignItems: 'flex-start' }}>
                <h3>Trades</h3>
                <div style={{ width: '100%', border: '1px solid #ccc', borderRadius: '5px'}}>
                    <table style={{ width: '100%' }}>
                        <thead>
                            <tr>
                                    <th style={{borderBottom: backtestData.trades ? '1px solid #ccc' : 'none', fontWeight: '500', color: 'grey'}}>Entry Time</th>
                                    <th style={{borderBottom: '1px solid #ccc', fontWeight: '500', color: 'grey'}}>Exit Time</th>
                                    <th style={{borderBottom: '1px solid #ccc', fontWeight: '500', color: 'grey'}}>Long Pair</th>
                                    <th style={{borderBottom: '1px solid #ccc', fontWeight: '500', color: 'grey'}}>Short Pair</th>
                                    <th style={{borderBottom: '1px solid #ccc', fontWeight: '500', color: 'grey'}}>Long Entry Price</th>
                                    <th style={{borderBottom: '1px solid #ccc', fontWeight: '500', color: 'grey'}}>Long Exit Price</th>
                                    <th style={{borderBottom: '1px solid #ccc', fontWeight: '500', color: 'grey'}}>Short Entry Price</th>
                                    <th style={{borderBottom: '1px solid #ccc', fontWeight: '500', color: 'grey'}}>Short Exit Price</th>
                                    <th style={{borderBottom: '1px solid #ccc', fontWeight: '500', color: 'grey'}}>Total Profit</th>
                            </tr>
                        </thead>
                        <tbody>
                            {backtestData?.trades?.map((trade, index) => (
                                <tr key={index}>
                                    <td style={{textAlign: 'center'}}>{trade.entry_time.split('T').join(" ")}</td>
                                    <td style={{textAlign: 'center'}}>{trade.exit_time.split('T').join(" ")}</td>
                                    <td style={{textAlign: 'center'}}>{trade.long_pair}</td>
                                    <td style={{textAlign: 'center'}}>{trade.short_pair}</td>
                                        <td style={{textAlign: 'center'}}>{trade.long_entry_price.toFixed(5)}</td>
                                        <td style={{textAlign: 'center'}}>{trade.long_exit_price.toFixed(5)}</td>
                                        <td style={{textAlign: 'center'}}>{trade.short_entry_price.toFixed(5)}</td>
                                        <td style={{textAlign: 'center'}}>{trade.short_exit_price.toFixed(5)}</td>
                                        <td style={{textAlign: 'center'}}>{trade.total_profit.toFixed(5)}</td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </div>
            {backtestData?.correlation_timeline_plot !== null && backtestData?.correlation_timeline_plot !== undefined && <div style={{ display: 'flex', flexDirection: 'column', justifyContent: 'space-between', width: '100%', padding: '20px 10px', alignItems: 'flex-start' }}>
                <h3>Correlation Timeline</h3>
                    <div style={{ width: '100%', border: '1px solid #ccc', borderRadius: '5px', display: 'flex', justifyContent: 'center', alignItems: 'center'}}>
                    <img src={`data:image/png;base64,${backtestData?.correlation_timeline_plot}`} alt="Chart" style={{ maxHeight: '500px', objectFit: 'contain' }} />                
                </div>
            </div>}
                <div style={{ display: 'flex', flexDirection: 'row', justifyContent: 'space-between', width: '100%', padding: '20px 10px', alignItems: 'flex-start'}}>
                    <div style={{display: 'flex', flexDirection: 'row', justifyContent: 'space-between', width: '100%', padding: '20px 10px', alignItems: 'flex-start', border: '1px solid #ccc', borderRadius: '5px'}}>
                        {backtestData?.correlation_vs_profit_plot !== null && backtestData?.correlation_vs_profit_plot !== undefined && <div style={{ width: '50%', padding: '20px 10px', alignItems: 'flex-start' }}>
                <h3>Correlation vs Profit</h3>
                            <div style={{ width: '100%', display: 'flex', justifyContent: 'center', alignItems: 'center', marginLeft: '10px'}}>
                                <img src={`data:image/png;base64,${backtestData?.correlation_vs_profit_plot}`} alt="Chart" style={{ maxHeight: '400px', objectFit: 'contain' }} />                
                </div>
            </div>}
                        {backtestData?.equity_curve_plot !== null && backtestData?.equity_curve_plot !== undefined && <div style={{ width: '50%', padding: '20px 10px', alignItems: 'flex-start' }}>
                <h3>Equity Curve</h3>
                            <div style={{ width: '100%', display: 'flex', justifyContent: 'center', alignItems: 'center', marginLeft: '10px'}}>
                                <img src={`data:image/png;base64,${backtestData?.equity_curve_plot}`} alt="Chart" style={{ maxHeight: '400px', objectFit: 'contain' }} />                
                </div>
            </div>}
                    </div>
                </div>
            </div>
        </div>
    );
};  

export default Analytics;