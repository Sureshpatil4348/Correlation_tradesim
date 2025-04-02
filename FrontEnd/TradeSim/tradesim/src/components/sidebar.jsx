import React, { useState } from 'react';
import useStore from '../stores/useStore';

const Sidebar = () => {
    const { selectedPage, setSelectedPage } = useStore((state) => state);
    return (
        <div style={{ position: 'fixed', top: 0, left: 0, width: '10vw', height: '100vh', backgroundColor: 'rgba(216, 216, 216, 0.5)', zIndex:1000, marginTop: '50px' }}>
            <ul style={{ listStyleType: 'none', padding: 0, margin: 0 }}>
                <li style={{ padding: '10px', cursor: 'pointer', borderRadius: '5px', color: selectedPage === 'Dashboard' ? 'black' : 'grey', fontWeight: selectedPage === 'Dashboard' ? '600' : '300' }} onClick={() => setSelectedPage('Dashboard')}>Dashboard</li>
                <li style={{ padding: '10px', cursor: 'pointer', borderRadius: '5px', color: selectedPage === 'Strategies' ? 'black' : 'grey', fontWeight: selectedPage === 'Strategies' ? '600' : '300' }} onClick={() => setSelectedPage('Strategies')}>Strategies</li>
                <li style={{ padding: '10px', cursor: 'pointer', borderRadius: '5px', color: selectedPage === 'Indicators' ? 'black' : 'grey', fontWeight: selectedPage === 'Indicators' ? '600' : '300' }} onClick={() => setSelectedPage('Indicators')}>Indicators</li>
                <li style={{ padding: '10px', cursor: 'pointer', borderRadius: '5px', color: selectedPage === 'Analytics' ? 'black' : 'grey', fontWeight: selectedPage === 'Analytics' ? '600' : '300' }} onClick={() => setSelectedPage('Analytics')}>Analytics</li>
                <li style={{ padding: '10px', cursor: 'pointer', borderRadius: '5px', color: selectedPage === 'Settings' ? 'black' : 'grey', fontWeight: selectedPage === 'Settings' ? '600' : '300' }} onClick={() => setSelectedPage('Settings')}>Settings</li>
            </ul>
        </div>
    );
};

export default Sidebar;
