import useStore from '../../stores/useStore';
import IndicatorDashboard from '../indicatorDashboard';

const Indicators = () => {

    const { accountInfo, strategies } = useStore((state) => state);

    const srtategiesForIndicator = strategies.filter((strategy) => strategy.status === 'active');

    return (
        <div style={{ marginLeft: '10vw', display: 'flex', flexDirection: 'column', width: '80vw', height: '100vh' }}>
            <div style={{ display: 'flex', flexDirection: 'row', justifyContent: 'space-between', width: '100%', padding: '10px', height: '60px', alignItems: 'center' }}>
                <h2>Indicator</h2>
                <div style={{ color: 'green', border: '1px solid green', padding: '5px', borderRadius: '5px' }}>Connected to MT5 ({accountInfo.account_number ? accountInfo.account_number : accountInfo.login})</div>
            </div>
            {srtategiesForIndicator.map((strategy) => (
                <div style={{display: 'flex', flexDirection: 'column', justifyContent: 'space-between', width: '100%', padding: '10px', border: '1px solid gray', borderRadius: '5px', marginBottom: '10px'}}>
                    <div style={{display: 'flex', flexDirection: 'row', justifyContent: 'space-between', width: '100%', padding: '10px'}}>
                        <div style={{display: 'flex', flexDirection: 'row', justifyContent: 'space-between', width: '100%', padding: '10px'}}>
                            <h3>{strategy.name} - {strategy.currencyPairs[0]} & {strategy.currencyPairs[1]}</h3>
                        </div>
                    </div>
                    <div>
                        <IndicatorDashboard strategyParams={strategy} />
                    </div>
                </div>
            ))}
        </div>
    );
};      

export default Indicators;
