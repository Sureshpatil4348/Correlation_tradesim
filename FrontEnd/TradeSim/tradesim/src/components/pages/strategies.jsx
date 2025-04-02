import React, { useState, useEffect } from 'react';
import useStore from '../../stores/useStore';

const Strategies = () => {
    const { accountInfo } = useStore((state) => state);
    const {strategies, setStrategies} = useStore((state) => state);
    const {setSelectedPage} = useStore((state) => state);
    const [selectedButton, setSelectedButton] = useState('list');
    const [createStrategy, setCreateStrategy] = useState(false);
    const [strategyName, setStrategyName] = useState('');
    const [selectedStrategy, setSelectedStrategy] = useState(null);
    const {strategyToBackTest, setStrategyToBackTest, setIsLoading, startActiveStrategy} = useStore((state) => state);

    useEffect(() => {
        if (strategies.length > 0 && strategies.filter(strategy => strategy.status === 'active').length > 0 && startActiveStrategy) {
            console.log('Running strategy', strategies.filter(strategy => strategy.status === 'active'));
            strategies.filter(strategy => strategy.status === 'active').forEach(strategy => {
                runStrategy(strategy);
            });
        }
    }, []);

    const [formData, setFormData] = useState({
        id: null,
        name: '',
        currencyPairs: ['', ''],
        lotSize: [0, 0],
        timeFrame: '',
        magicNumber: '',
        tradeComment: '',
        rsiPeriod: '',
        correlationWindow: '',
        rsiOverbought: 0,
        rsiOversold: 0,
        entryThreshold: 0,
        exitThreshold: 0,
        startingBalance: 0,
    });

    const defaultStrategy = {
        id: null,
        name: '',
        currencyPairs: ['', ''],
        lotSize: [0, 0],
        timeFrame: '',
        magicNumber: '',
        tradeComment: '',
        rsiPeriod: 14,
        correlationWindow: 50,
        rsiOverbought: 70,
        rsiOversold: 30,
        entryThreshold: 0,
        exitThreshold: 0,
        startingBalance: 0,
      };

    const addNewStrategy = () => {
        const completeStrategy = { ...defaultStrategy, name: strategyName, id: strategies.length + 1 };
        setStrategies([...strategies, completeStrategy]);
        setCreateStrategy(false);
    }

    const editSelectedStrategy = (strategy) => {
        setSelectedStrategy(strategy);
        setSelectedButton('edit');
        setFormData(strategy);
    }

    const saveStrategyParameters = (e) => {
        e.preventDefault();
        const completeStrategy = selectedStrategy
            ? { ...defaultStrategy, ...formData, id: selectedStrategy.id }
            : { ...defaultStrategy, ...formData, id: strategies.length + 1 };
      
        if (selectedStrategy) {
          setStrategies(strategies.map((strategy) => strategy.id === selectedStrategy.id ? completeStrategy : strategy));
        } else {
          setStrategies([...strategies, completeStrategy]);
        }
        setSelectedButton('list');
        setSelectedStrategy(null);
        setStrategyToBackTest(null);
      };

      const deleteStrategy = (id) => {
        setStrategies(strategies.filter((strategy) => strategy.id !== id));
      };

      const runStrategy = async (strategy) => {
        const response = await fetch("http://localhost:5001/mt5/start-strategy/", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(strategy),
            });
            const data = await response.json();
            if (data.status === 'success') {
                setStrategies(strategies.map((s) => s.id === strategy.id ? {...s, status: 'active'} : s));
            } else {
                alert('Error starting strategy');
            }
      }

      const stopStrategy = async (strategy) => {
        setIsLoading(true);
        const response = await fetch("http://localhost:5001/mt5/stop-strategy/", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(strategy),
        });
        const data = await response.json();
        if (data.status === 'stopped') {
            setStrategies(strategies.map((s) => s.id === strategy.id ? {...s, status: 'inactive'} : s));
        } else {
            alert('Error stopping strategy');
        }
        setIsLoading(false);
      }

      const backTestStrategy = (strategy) => {
        setSelectedPage('Analytics');
        setStrategyToBackTest(strategy);
      }

      const isStrategyComplete = (strategy) => {
        return Object.values(strategy).every(value => {
            if (Array.isArray(value)) {
                return value.every(v => v !== '' && v !== null && v !== undefined);
            }
            return value !== '' && value !== null && value !== undefined;
        });
      }

    return (
        <div style={{ marginLeft: '10vw', display: 'flex', flexDirection: 'column', width: '80vw', height: '100vh' }}>
            <div style={{ display: 'flex', flexDirection: 'row', justifyContent: 'space-between', width: '100%', padding: '10px', height: '60px', alignItems: 'center' }}>
                <h2>Strategy Management</h2>
                <div style={{ color: 'green', border: '1px solid green', borderRadius: '5px', padding: '5px' }}>Connected to MT5 ({accountInfo.account_number ? accountInfo.account_number : accountInfo.login})</div>
            </div>
            <div style={{display: 'flex', flexDirection: 'row', justifyContent: 'space-between', width: '100%', padding: '10px', height: '60px', alignItems: 'center' }}>
                <div style={{display: 'flex', flexDirection: 'row', borderRadius: '5px', backgroundColor: 'rgba(216, 216, 216, 0.5)', width: '100%', height: '80%', alignItems: 'center', justifyContent: 'center'}}>
                    <button style={{height: '80%', outline: 'none', width: '49.6%', borderRadius: '5px', cursor: 'pointer', color: selectedButton === 'list' ? 'black' : 'grey', backgroundColor: selectedButton === 'list' ? 'white' : 'transparent'}} onClick={() => setSelectedButton('list')}>Strategy List</button>
                    <button style={{height: '80%', outline: 'none', width: '49.6%', borderRadius: '5px', cursor: 'pointer', color: selectedButton === 'create' || selectedButton === 'edit' ? 'black' : 'grey', backgroundColor: selectedButton === 'create' || selectedButton === 'edit' ? 'white' : 'transparent'}} onClick={() => setSelectedButton('create')}>Create/Edit Strategy</button>
                </div>
            </div>
            {selectedButton === 'list' ? <div style={{width: '100%', border: '1px solid #ccc', borderRadius: '5px', margin: '10px'}}> 
                <h3 style={{paddingLeft: '10px'}}>Strategy Management</h3>
                <div style={{paddingLeft: '10px', color: 'gray', fontSize: '12px'}}>Add, configure, and activate multiple trading strategies</div>
                {!createStrategy ? <button style={{margin: '10px 0px 10px 10px', padding: '10px', borderRadius: '5px', border: '1px solid #ccc', cursor: 'pointer', backgroundColor: 'black', color: 'white'}} onClick={() => setCreateStrategy(true)}>Add new Strategy</button> : null}
                {createStrategy ? <div style={{padding: '10px'}}>
                    <div style={{display: 'flex', flexDirection: 'column', justifyContent: 'space-between'}}  >
                        <h4>Strategy Name</h4>
                        <div style={{display: 'flex', flexDirection: 'row'}}  >
                            <input type="text" placeholder="Enter strategy name" style={{width: '80%', borderRadius: '5px', border: '1px solid #ccc', padding: '15px'}} onChange={(e) => setStrategyName(e.target.value)} />
                            <button style={{padding: '10px', borderRadius: '5px', border: '1px solid #ccc', cursor: 'pointer', backgroundColor: 'black', color: 'white', width: '10%'}} onClick={() => addNewStrategy()}>Save</button>
                            <button style={{padding: '10px', borderRadius: '5px', border: '1px solid #ccc', cursor: 'pointer', backgroundColor: 'grey', color: 'white', width: '10%'}} onClick={() => setCreateStrategy(false)}>Cancel</button>
                        </div>
                    </div>
                </div> : null}
                <div style={{padding: '10px'}}>
                    <table style={{width: '100%', border: '1px solid #ccc', borderRadius: '5px'}}>
                        <tbody>
                        <tr style={{color: 'grey'}}>
                            <td style={{width: '20%', textAlign: 'left', paddingLeft: '10px', borderBottom: strategies.length > 0 ? '1px solid #ccc' : 'none'}}>Strategy Name</td>
                            <td style={{width: '20%', textAlign: 'left', borderBottom: strategies.length > 0 ? '1px solid #ccc' : 'none'}}>Currency pairs</td>
                            <td style={{width: '20%', textAlign: 'left', borderBottom: strategies.length > 0 ? '1px solid #ccc' : 'none'}}>Status</td>
                            <td style={{width: '20%', textAlign: 'right', paddingRight: '10px', borderBottom: strategies.length > 0 ? '1px solid #ccc' : 'none'}}>Actions</td>
                        </tr>
                        {strategies.map((strategy, index) => (
                            <tr key={strategy.id} style={{height: '40px'}}>
                                <td style={{width: '20%', textAlign: 'left', paddingLeft: '10px', borderBottom: index !== strategies.length - 1 ? '1px solid #ccc' : 'none'}}>{strategy.name}</td>
                                <td style={{width: '20%', textAlign: 'left', borderBottom: index !== strategies.length - 1 ? '1px solid #ccc' : 'none'}}>{strategy?.currencyPairs?.[0] !== '' && strategy?.currencyPairs?.[1] !== '' ? strategy?.currencyPairs?.join(' & ') : 'N/A'}</td>
                                <td style={{width: '20%', textAlign: 'left', borderBottom: index !== strategies.length - 1 ? '1px solid #ccc' : 'none'}}>{strategy.status === 'active' ? <div style={{color: 'green'}}>Active</div> : <div style={{color: 'red'}}>Inactive</div>}</td>
                                <td style={{width: '20%', textAlign: 'right', paddingRight: '10px', borderBottom: index !== strategies.length - 1 ? '1px solid #ccc' : 'none'}}>
                                    <button style={{marginRight: '5px', padding: '5px', fontSize: '12px', borderRadius: '5px', border: '1px solid #ccc', cursor: 'pointer'}} onClick={() => editSelectedStrategy(strategy)}>Edit</button>
                                    <button style={{marginRight: '5px', padding: '5px', fontSize: '12px', borderRadius: '5px', border: '1px solid #ccc', cursor: !isStrategyComplete(strategy) ? 'not-allowed' : 'pointer'}} disabled={!isStrategyComplete(strategy)} onClick={() => strategy.status === 'active' ? stopStrategy(strategy) : runStrategy(strategy)}>{strategy.status === 'active' ? <div style={{color: 'red'}}>Stop</div> : <div style={{color: !isStrategyComplete(strategy) ? 'grey' : 'green'}}>Run</div>}</button>
                                    <button style={{marginRight: '5px', padding: '5px', fontSize: '12px', borderRadius: '5px', border: '1px solid #ccc', cursor: !isStrategyComplete(strategy) ? 'not-allowed' : 'pointer'}} onClick={() => backTestStrategy(strategy)} disabled={!isStrategyComplete(strategy)}>BackTest</button>
                                    <button style={{padding: '5px', fontSize: '12px', borderRadius: '5px', border: '1px solid #ccc', cursor: 'pointer'}} onClick={() => deleteStrategy(strategy.id)}>Delete</button>
                                </td>
                            </tr>
                        ))}
                        </tbody>
                    </table>
                </div>
            </div> : 
            <div style={{width: '100%', border: '1px solid #ccc', borderRadius: '5px', margin: '10px'}}>
                <h3 style={{paddingLeft: '10px'}}>Strategy Parameters</h3>
                <div style={{paddingLeft: '10px', color: 'gray', fontSize: '12px'}}>Comfigure the strategy: {selectedStrategy?.name}</div>
                <form style={{padding: '10px', display: 'flex', flexDirection: 'column', maxHeight: '600px', flexWrap: 'wrap'}} onSubmit={(e) => saveStrategyParameters(e)}>
                    <div style={{display: 'flex', flexDirection: 'column', justifyContent: 'space-between', width: '49%', marginBottom: '10px'}}>
                        <label style={{paddingBottom: '5px', fontSize: '14px', fontWeight: '500'}}>Strategy Name</label>
                        <input type="text" placeholder="Enter strategy name" style={{borderRadius: '5px', border: '1px solid #ccc', padding: '10px', fontSize: '12px'}} value={formData?.name} onChange={(e) => setFormData({...formData, name: e.target.value})} />
                    </div>
                    <div style={{display: 'flex', flexDirection: 'column', justifyContent: 'space-between', width: '49%', marginBottom: '10px'}}>
                        <label style={{paddingBottom: '5px', fontSize: '14px', fontWeight: '500'}}>Currency pair 1</label>
                        <input type="text" placeholder="Enter currency pairs" style={{borderRadius: '5px', border: '1px solid #ccc', padding: '10px', fontSize: '12px'}} value={formData?.currencyPairs?.[0]} onChange={(e) => setFormData({...formData, currencyPairs: [e.target.value, formData?.currencyPairs?.[1]]})} />
                    </div>
                    <div style={{display: 'flex', flexDirection: 'column', justifyContent: 'space-between', width: '49%', marginBottom: '10px'}}>
                        <label style={{paddingBottom: '5px', fontSize: '14px', fontWeight: '500'}}>Lot Size for pair 1</label>
                        <input type="number" step="any" placeholder="Enter lot size" style={{borderRadius: '5px', border: '1px solid #ccc', padding: '10px', fontSize: '12px'}} value={formData?.lotSize?.[0]} onChange={(e) => setFormData({...formData, lotSize: [e.target.value, formData?.lotSize?.[1]]})} />
                    </div>
                    <div style={{display: 'flex', flexDirection: 'column', justifyContent: 'space-between', width: '49%', marginBottom: '10px'}}>
                        <label style={{paddingBottom: '5px', fontSize: '14px', fontWeight: '500'}}>Currency pair 2</label>
                        <input type="text" placeholder="Enter currency pairs" style={{borderRadius: '5px', border: '1px solid #ccc', padding: '10px', fontSize: '12px'}} value={formData?.currencyPairs?.[1]} onChange={(e) => setFormData({...formData, currencyPairs: [formData?.currencyPairs?.[0], e.target.value]})} />
                    </div>
                    <div style={{display: 'flex', flexDirection: 'column', justifyContent: 'space-between', width: '49%', marginBottom: '10px'}}>
                        <label style={{paddingBottom: '5px', fontSize: '14px', fontWeight: '500'}}>Lot Size for pair 2</label>
                        <input type="number" step="any" placeholder="Enter lot size" style={{borderRadius: '5px', border: '1px solid #ccc', padding: '10px', fontSize: '12px'}} value={formData?.lotSize?.[1]} onChange={(e) => setFormData({...formData, lotSize: [formData?.lotSize?.[0], e.target.value]})} />
                    </div>
                    <div style={{display: 'flex', flexDirection: 'column', justifyContent: 'space-between', width: '49%', marginBottom: '10px'}}>
                        <label style={{paddingBottom: '5px', fontSize: '14px', fontWeight: '500'}}>Time Frame</label>
                        <select style={{borderRadius: '5px', border: '1px solid #ccc', padding: '10px', fontSize: '12px'}} value={formData?.timeFrame} onChange={(e) => setFormData({...formData, timeFrame: Number(e.target.value)})}>
                            <option value="1">M1</option>
                            <option value="5">M5</option>
                            <option value="15">M15</option>
                            <option value="30">M30</option>
                            <option value="60">H1</option>
                            <option value="240">H4</option>
                            <option value="1440">D1</option>
                            <option value="10080">W1</option>
                            <option value="43200">MN</option>
                        </select>
                    </div>
                    <div style={{display: 'flex', flexDirection: 'column', justifyContent: 'space-between', width: '49%', marginBottom: '10px'}}>
                        <label style={{paddingBottom: '5px', fontSize: '14px', fontWeight: '500'}}>Magic Number</label>
                        <input type="number" step="any" placeholder="Enter magic number" style={{borderRadius: '5px', border: '1px solid #ccc', padding: '10px', fontSize: '12px'}} value={formData?.magicNumber} onChange={(e) => setFormData({...formData, magicNumber: e.target.value})} />
                        <div style={{paddingTop: '5px', fontSize: '12px', color: 'gray'}}>Unique identifier for trades from this strategy</div>
                    </div>
                    <div style={{display: 'flex', flexDirection: 'column', justifyContent: 'space-between', width: '49%', marginBottom: '10px'}}>
                        <label style={{paddingBottom: '5px', fontSize: '14px', fontWeight: '500'}}>Trade Comment</label>
                        <input type="text" placeholder="Enter trade comment" style={{borderRadius: '5px', border: '1px solid #ccc', padding: '10px', fontSize: '12px'}} value={formData?.tradeComment} onChange={(e) => setFormData({...formData, tradeComment: e.target.value})} />
                        <div style={{paddingTop: '5px', fontSize: '12px', color: 'gray'}}>Comment that will be attached to each trade</div>
                    </div>
                    <div style={{display: 'flex', flexDirection: 'column', justifyContent: 'space-between', width: '49%', marginBottom: '10px'}}>
                        <label style={{paddingBottom: '5px', fontSize: '14px', fontWeight: '500'}}>RSI Period: {formData?.rsiPeriod ? formData?.rsiPeriod : '14'}</label>
                        <input type="range" min="3" max="50" style={{width: '100%'}} value={formData?.rsiPeriod ? formData?.rsiPeriod : '14'} onChange={(e) => setFormData({...formData, rsiPeriod: Number(e.target.value)})} />
                    </div>
                    <div style={{display: 'flex', flexDirection: 'column', justifyContent: 'space-between', width: '49%', marginBottom: '10px'}}>
                        <label style={{paddingBottom: '5px', fontSize: '14px', fontWeight: '500'}}>Correlation Window: {formData?.correlationWindow ? formData?.correlationWindow : '10'}</label>
                        <input type="range" min="5" max="100" style={{width: '100%'}} value={formData?.correlationWindow ? formData?.correlationWindow : '10'} onChange={(e) => setFormData({...formData, correlationWindow: Number(e.target.value)})} />
                    </div>
                    <div style={{display: 'flex', flexDirection: 'row', justifyContent: 'space-between', marginBottom: '10px', width: '49%'}}>
                        <div style={{width: '49%', display: 'flex', flexDirection: 'column', justifyContent: 'space-between'}}>
                            <label style={{paddingBottom: '5px', fontSize: '14px', fontWeight: '500'}}>RSI Overbought</label>
                            <input type="number" step="any" style={{borderRadius: '5px', border: '1px solid #ccc', padding: '10px', fontSize: '12px'}} value={formData?.rsiOverbought} onChange={(e) => setFormData({...formData, rsiOverbought: Number(e.target.value)})} />
                        </div>
                        <div style={{width: '49%', display: 'flex', flexDirection: 'column', justifyContent: 'space-between'}}>
                            <label style={{paddingBottom: '5px', fontSize: '14px', fontWeight: '500'}}>RSI Oversold</label>
                            <input type="number" step="any" style={{borderRadius: '5px', border: '1px solid #ccc', padding: '10px', fontSize: '12px'}} value={formData?.rsiOversold} onChange={(e) => setFormData({...formData, rsiOversold: Number(e.target.value)})} />
                        </div>
                    </div>
                    <div style={{display: 'flex', flexDirection: 'row', justifyContent: 'space-between', marginBottom: '10px', width: '49%'}}>
                        <div style={{width: '49%', display: 'flex', flexDirection: 'column', justifyContent: 'space-between'}}>
                            <label style={{paddingBottom: '5px', fontSize: '14px', fontWeight: '500'}}>Entry Threshold</label>
                            <input type="number" step="any" style={{borderRadius: '5px', border: '1px solid #ccc', padding: '10px', fontSize: '12px'}} value={formData?.entryThreshold} onChange={(e) => setFormData({...formData, entryThreshold: Number(e.target.value)})} />
                        </div>
                        <div style={{width: '49%', display: 'flex', flexDirection: 'column', justifyContent: 'space-between'}}>
                            <label style={{paddingBottom: '5px', fontSize: '14px', fontWeight: '500'}}>Exit Threshold</label>
                            <input type="number" step="any" style={{borderRadius: '5px', border: '1px solid #ccc', padding: '10px', fontSize: '12px'}} value={formData?.exitThreshold} onChange={(e) => setFormData({...formData, exitThreshold: Number(e.target.value)})} />
                        </div>
                    </div>
                    <div style={{display: 'flex', flexDirection: 'column', justifyContent: 'space-between', width: '49%', marginBottom: '10px'}}>
                        <label style={{paddingBottom: '5px', fontSize: '14px', fontWeight: '500'}}>Starting Balance</label>
                        <input type="number" step="any" style={{borderRadius: '5px', border: '1px solid #ccc', padding: '10px', fontSize: '12px'}} value={formData?.startingBalance} onChange={(e) => setFormData({...formData, startingBalance: Number(e.target.value)})} />
                    </div>
                    <div style={{display: 'flex', flexDirection: 'row', justifyContent: 'flex-end', marginBottom: '10px', width: '49%'}}>
                        <button style={{width: '220px', fontSize: '14px', padding: '10px', borderRadius: '5px', border: '1px solid #ccc', cursor: 'pointer', backgroundColor: 'black', color: 'white'}} type="submit">Save Strategy Parameters</button>
                    </div>
                </form>
            </div>
            }
        </div>
    );
};  

export default Strategies;
