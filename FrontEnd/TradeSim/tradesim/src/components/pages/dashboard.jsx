import React, { useState, useEffect } from 'react';
import useStore from '../../stores/useStore';

const Dashboard = () => {
    const { accountInfo, setAccountInfo, startActiveStrategy, setStartActiveStrategy, setIsLoading } = useStore((state) => state);
    const [trades, setTrades] = useState([]);
    const [history, setHistory] = useState([]);
    const [totalProfit, setTotalProfit] = useState(0);
    const {strategies, setStrategies} = useStore((state) => state);

    const fetchTrades = async () => {
        try {
            const response = await fetch("http://localhost:5001/mt5/trades");
            const data = await response.json();
            if (data.positions.length > 0) {
                if (strategies.find(strategy => Number(strategy.magicNumber) === data.positions[0]?.magic)) {
                    setStrategies(strategies.map(strategy => Number(strategy.magicNumber) === data.positions[0].magic && strategy.status === "inactive" ? {...strategy, status: "active"} : {...strategy, status: strategy.status}));
                    setStartActiveStrategy(true)
                }
            }
            setTrades(data);
        } catch (error) {
            console.error("Error fetching trades:", error);
        }
    }


    useEffect(() => {
        const fetchAccountInfo = async () => {
            const response = await fetch("http://localhost:5001/mt5/account");
            const data = await response.json();
            setAccountInfo(data);   
        };
        const fetchHistory = async () => {
            setIsLoading(true);
            try {
                const response = await fetch("http://localhost:5001/mt5/history");
                const data = await response.json();
                
                // Calculate total profit from trades array
                const totalProfitCalc = data.reduce((acc, item) => {
                    // Sum up profits from all trades in the trades array
                    return acc + item.trades.reduce((tradeAcc, trade) => tradeAcc + (trade.profit || 0), 0);
                }, 0);
                
                setHistory(data);
                setTotalProfit(totalProfitCalc);
            } catch (error) {
                console.error("Error fetching history:", error);
            } finally {
                setIsLoading(false);
            }
        };
        fetchAccountInfo();
        fetchHistory();
        fetchTrades();
        const interval = setInterval(fetchTrades, 1000);
        return () => clearInterval(interval);
    }, []);

    
    return (
        <div style={{ marginLeft: '10vw', display: 'flex', flexDirection: 'column', width: '80vw', height: '100vh' }}>
            <div style={{ display: 'flex', flexDirection: 'row', justifyContent: 'space-between', width: '100%', padding: '10px', height: '60px', alignItems: 'center' }}>
                <h2>Dashboard</h2>
                <div style={{ color: 'green', border: '1px solid green', padding: '5px', borderRadius: '5px' }}>Connected to MT5 ({accountInfo.account_number ? accountInfo.account_number : accountInfo.login})</div>
            </div>
            <div style={{display: 'flex', flexDirection: 'row', justifyContent: 'space-between', width: '100%', padding: '10px'}}>
                <div style={{width: '30%', border: '1px solid #ccc', borderRadius: '5px', padding: '10px'}}>
                    <h3>Active Trades</h3>
                    <div style={{color: 'gray', fontSize: '12px'}}>Currently open positions</div>
                    <div style={{color: 'green', fontSize: '30px'}}>{trades?.positions?.length}</div>
                    <div style={{color: totalProfit > 0 ? 'green' : 'red', fontSize: '15px'}}><span style={{fontWeight: 'bold', color: 'gray', fontSize: '12px'}}>Strategies Running:</span> {strategies.filter(strategy => strategy.status === "active").length}/{strategies.length} </div>
                    {strategies.map(strategy => (
                        <div key={strategy.magicNumber} style={{color: 'gray', fontSize: '12px', display: 'flex', flexDirection: 'row', justifyContent: 'space-between', width: '100%'}}>
                            <span style={{width: '25%', fontWeight: 'bold', color: 'gray', fontSize: '12px'}}>{strategy.name}</span>
                            <span style={{width: '25%', color: strategy.status === "active" ? 'green' : 'red', textAlign: 'center'}}>{strategy.status}</span>
                            <span style={{width: '25%', color: 'gray', fontSize: '12px'}}>
                                Trades Running: {trades?.positions?.filter(trade => trade?.magic === Number(strategy.magicNumber))?.length || 0}
                            </span>
                            <span style={{width: '25%', color: 'gray', fontSize: '12px'}}>
                                Past Trades: {history?.filter(item => 
                                    item?.trades?.length > 0 && 
                                    item?.trades[0]?.magic === Number(strategy.magicNumber)
                                )?.length || 0}
                            </span>
                        </div>
                    ))}
                </div>
                <div style={{width: '30%', border: '1px solid #ccc', borderRadius: '5px', padding: '10px'}}>
                    <h3>Win Rate</h3>
                    <div style={{color: 'gray', fontSize: '12px'}}>Overall trading performance</div>
                    <div style={{color: 'green', fontSize: '30px'}}>
                        {(history?.filter(item => item?.trades?.length > 0)?.reduce((acc, item) => {
                            const lastTrade = item?.trades?.[item.trades.length - 1];
                            return acc + ((lastTrade?.profit || 0) > 0 ? 1 : 0);
                        }, 0) / (history?.filter(item => item?.trades?.length > 0)?.length || 1) * 100).toFixed(2)}%
                    </div>
                    <div style={{color: totalProfit > 0 ? 'green' : 'red', fontSize: '15px'}}>
                        <span style={{fontWeight: 'bold', color: 'gray', fontSize: '12px'}}>Total Winning Trades:</span> 
                        {history?.filter(item => item?.trades?.length > 0)?.reduce((acc, item) => {
                            const lastTrade = item?.trades?.[item.trades.length - 1];
                            return acc + ((lastTrade?.profit || 0) > 0 ? 1 : 0);
                        }, 0)}/{history?.filter(item => item?.trades?.length > 0)?.length || 0}
                    </div>
                </div>
                <div style={{width: '30%', border: '1px solid #ccc', borderRadius: '5px', padding: '10px'}}>
                    <h3>Total Profit</h3>
                    <div style={{color: 'gray', fontSize: '12px'}}>Cumulative trading result</div>
                    <div style={{color: trades?.positions?.reduce((acc, trade) => acc + trade.profit, 0).toFixed(2) > 0 ? 'green' : 'red', fontSize: '30px'}}>${trades?.positions?.reduce((acc, trade) => acc + trade.profit, 0).toFixed(2)}</div>
                    <div style={{color: totalProfit > 0 ? 'green' : 'red', fontSize: '15px'}}>
                        <span style={{marginRight: '10px'}}><span style={{fontWeight: 'bold', color: 'gray', fontSize: '12px'}}>Total Profit till date:</span> ${totalProfit.toFixed(2)}</span>
                    </div>
                    <div style={{color: totalProfit > 0 ? 'green' : 'red', fontSize: '15px'}}>
                        <span><span style={{fontWeight: 'bold', color: 'gray', fontSize: '12px'}}>Total Equity:</span> ${accountInfo.equity.toFixed(2)}</span>
                    </div>
                    <div style={{color: 'black', fontSize: '12px'}}><span><span style={{fontWeight: 'bold', color: 'gray', fontSize: '12px'}}>Balance:</span> ${accountInfo.balance.toFixed(2)}</span></div>
                </div>
            </div>
            <div style={{display: 'flex', flexDirection: 'column', justifyContent: 'space-between', width: '100%', border: '1px solid #ccc', borderRadius: '5px', margin: '10px'}}>
                <h3 style={{padding: '10px'}}>Live Trades</h3>
                <div style={{padding: '10px', color: 'gray', fontSize: '12px'}}>Last trading activity</div>
                <div style={{padding: '10px'}}>
                    <table style={{width: '100%', border: '1px solid #ccc', borderRadius: '5px'}}>
                        <tbody>
                        <tr style={{color: 'grey', borderBottom: '1px solid #ccc'}}>
                            <td style={{width: '10%', paddingLeft: '10px', textAlign: 'left', borderBottom: trades?.positions?.length > 0 ? '1px solid #ccc' : 'none'}}>Symbol</td>
                            <td style={{width: '10%', textAlign: 'center', borderBottom: trades?.positions?.length > 0 ? '1px solid #ccc' : 'none'}}>Type</td>
                            <td style={{width: '10%', textAlign: 'center', borderBottom: trades?.positions?.length > 0 ? '1px solid #ccc' : 'none'}}>Magic Number</td>
                            <td style={{width: '10%', textAlign: 'center', borderBottom: trades?.positions?.length > 0 ? '1px solid #ccc' : 'none'}}>Open Time</td>
                            <td style={{width: '10%', textAlign: 'center', borderBottom: trades?.positions?.length > 0 ? '1px solid #ccc' : 'none'}}>Open Price</td>
                            <td style={{width: '10%', textAlign: 'center', borderBottom: trades?.positions?.length > 0 ? '1px solid #ccc' : 'none'}}>Current Price</td>
                            <td style={{width: '10%', textAlign: 'center', borderBottom: trades?.positions?.length > 0 ? '1px solid #ccc' : 'none'}}>Lots</td>
                            <td style={{width: '10%', textAlign: 'center', borderBottom: trades?.positions?.length > 0 ? '1px solid #ccc' : 'none'}}>Profit</td>
                            <td style={{width: '10%', textAlign: 'right', paddingRight: '10px', borderBottom: trades?.positions?.length > 0 ? '1px solid #ccc' : 'none'}}>Strategy Name</td>
                        </tr>
                        {trades.positions?.map((trade, index) => (
                            <tr key={trade.id} style={{height: '40px', borderBottom: index !== trades.positions.length - 1 ? '1px solid #ccc' : 'none'}}>
                                <td style={{width: '10%', textAlign: 'left', paddingLeft: '10px', borderBottom: index !== trades.positions.length - 1 ? '1px solid #ccc' : 'none'}}>{trade.symbol}</td>
                                <td style={{width: '10%', textAlign: 'center', color: trade.type === 0 ? 'green' : 'red', borderBottom: index !== trades.positions.length - 1 ? '1px solid #ccc' : 'none'}}>{trade.type === 0 ? 'Buy' : 'Sell'}</td>
                                <td style={{width: '10%', textAlign: 'center', borderBottom: index !== trades.positions.length - 1 ? '1px solid #ccc' : 'none'}}>{trade.magic}</td>
                                <td style={{width: '10%', textAlign: 'center', borderBottom: index !== trades.positions.length - 1 ? '1px solid #ccc' : 'none'}}>{new Date(trade.time * 1000).toISOString().split('T')[0] + ' ' + new Date(trade.time * 1000).toISOString().split('T')[1].split('.')[0]}</td>
                                <td style={{width: '10%', textAlign: 'center', borderBottom: index !== trades.positions.length - 1 ? '1px solid #ccc' : 'none'}}>{trade.price_open.toFixed(5)}</td>
                                <td style={{width: '10%', textAlign: 'center', borderBottom: index !== trades.positions.length - 1 ? '1px solid #ccc' : 'none'}}>{trade.price_current.toFixed(5)}</td>
                                <td style={{width: '10%', textAlign: 'center', borderBottom: index !== trades.positions.length - 1 ? '1px solid #ccc' : 'none'}}>{trade.volume}</td>
                                <td style={{width: '10%', textAlign: 'center', color: trade.profit > 0 ? 'green' : 'red', borderBottom: index !== trades.positions.length - 1 ? '1px solid #ccc' : 'none'}}>{trade.profit}</td>                                    
                                <td style={{width: '10%', textAlign: 'right', paddingRight: '10px', borderBottom: index !== trades.positions.length - 1 ? '1px solid #ccc' : 'none'}}>{strategies.find(strategy => Number(strategy.magicNumber) === trade.magic)?.name}</td>
                            </tr>
                        ))}
                        </tbody>
                    </table>
                </div>
            </div>
            <div style={{display: 'flex', flexDirection: 'column', justifyContent: 'space-between', width: '100%', border: '1px solid #ccc', borderRadius: '5px', margin: '10px'}}>
                <h3 style={{padding: '10px'}}>Recent Trades</h3>
                <div style={{padding: '10px', color: 'gray', fontSize: '12px'}}>Last trading activity</div>
                <div style={{padding: '10px'}}>
                    <table style={{width: '100%', border: '1px solid #ccc', borderRadius: '5px'}}>
                        <tbody>
                        <tr style={{color: 'grey', borderBottom: '1px solid #ccc'}}>
                            <td style={{width: '10%', paddingLeft: '10px', textAlign: 'left', borderBottom: trades.length > 0 ? '1px solid #ccc' : 'none'}}>Symbol</td>
                            <td style={{width: '10%', textAlign: 'center', borderBottom: trades.length > 0 ? '1px solid #ccc' : 'none'}}>Type</td>
                            <td style={{width: '10%', textAlign: 'center', borderBottom: trades.length > 0 ? '1px solid #ccc' : 'none'}}>Magic Number</td>
                            <td style={{width: '10%', textAlign: 'center', borderBottom: trades.length > 0 ? '1px solid #ccc' : 'none'}}>Open Time</td>
                            <td style={{width: '10%', textAlign: 'center', borderBottom: trades.length > 0 ? '1px solid #ccc' : 'none'}}>Open Price</td>
                            <td style={{width: '10%', textAlign: 'center', borderBottom: trades.length > 0 ? '1px solid #ccc' : 'none'}}>Close Time</td>
                            <td style={{width: '10%', textAlign: 'center', borderBottom: trades.length > 0 ? '1px solid #ccc' : 'none'}}>Close Price</td>
                            <td style={{width: '10%', textAlign: 'center', borderBottom: trades.length > 0 ? '1px solid #ccc' : 'none'}}>Lots</td>
                            <td style={{width: '10%', textAlign: 'center', borderBottom: trades.length > 0 ? '1px solid #ccc' : 'none'}}>Profit</td>
                            <td style={{width: '10%', textAlign: 'center', borderBottom: trades.length > 0 ? '1px solid #ccc' : 'none'}}>Comment</td>
                            <td style={{width: '10%', textAlign: 'right', paddingRight: '10px', borderBottom: trades.length > 0 ? '1px solid #ccc' : 'none'}}>Strategy Name</td>
                        </tr>
                        {history.map((item, index) => {
                            // Get first and last trade for entry/exit info
                            const entryTrade = item.trades[0];
                            const exitTrade = item.trades[item.trades.length - 1];
                            
                            return (
                                <tr key={item?.position?.ticket || entryTrade?.ticket || index} style={{height: '40px', borderBottom: index !== history.length - 1 ? '1px solid #ccc' : 'none'}}>
                                    <td style={{width: '10%', textAlign: 'left', paddingLeft: '10px', borderBottom: index !== history.length - 1 ? '1px solid #ccc' : 'none'}}>
                                        {item?.position?.symbol || entryTrade?.symbol}
                                    </td>
                                    <td style={{width: '10%', textAlign: 'center', color: entryTrade?.type === 0 ? 'green' : 'red', borderBottom: index !== history.length - 1 ? '1px solid #ccc' : 'none'}}>
                                        {entryTrade?.type === 0 ? 'Buy' : 'Sell'}
                                    </td>
                                    <td style={{width: '10%', textAlign: 'center', borderBottom: index !== history.length - 1 ? '1px solid #ccc' : 'none'}}>
                                        {entryTrade?.magic}
                                    </td>
                                    <td style={{width: '10%', textAlign: 'center', borderBottom: index !== history.length - 1 ? '1px solid #ccc' : 'none'}}>
                                        {entryTrade?.time ? new Date(entryTrade.time * 1000).toISOString().split('T')[0] + ' ' + new Date(entryTrade.time * 1000).toISOString().split('T')[1].split('.')[0] : ''}
                                    </td>
                                    <td style={{width: '10%', textAlign: 'center', borderBottom: index !== history.length - 1 ? '1px solid #ccc' : 'none'}}>
                                        {entryTrade?.price?.toFixed(5)}
                                    </td>
                                    <td style={{width: '10%', textAlign: 'center', borderBottom: index !== history.length - 1 ? '1px solid #ccc' : 'none'}}>
                                        {exitTrade?.time ? new Date(exitTrade.time * 1000).toISOString().split('T')[0] + ' ' + new Date(exitTrade.time * 1000).toISOString().split('T')[1].split('.')[0] : ''}
                                    </td>
                                    <td style={{width: '10%', textAlign: 'center', borderBottom: index !== history.length - 1 ? '1px solid #ccc' : 'none'}}>
                                        {exitTrade?.price?.toFixed(5)}
                                    </td>
                                    <td style={{width: '10%', textAlign: 'center', borderBottom: index !== history.length - 1 ? '1px solid #ccc' : 'none'}}>
                                        {entryTrade?.volume}
                                    </td>
                                    <td style={{width: '10%', textAlign: 'center', color: exitTrade?.profit > 0 ? 'green' : 'red', borderBottom: index !== history.length - 1 ? '1px solid #ccc' : 'none'}}>
                                        {exitTrade?.profit}
                                    </td>
                                    <td style={{width: '10%', textAlign: 'center', borderBottom: index !== history.length - 1 ? '1px solid #ccc' : 'none'}}>
                                        {entryTrade?.comment}
                                    </td>
                                    <td style={{width: '10%', textAlign: 'right', paddingRight: '10px', borderBottom: index !== history.length - 1 ? '1px solid #ccc' : 'none'}}>
                                        {strategies.find(strategy => Number(strategy.magicNumber) === entryTrade?.magic)?.name}
                                    </td>
                                </tr>
                            );
                        })}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    );
};

export default Dashboard;
