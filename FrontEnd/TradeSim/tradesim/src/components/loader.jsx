import React from 'react';

const Loader = () => {
    return (
        <div style={{display: 'flex', justifyContent: 'flex-start', alignItems: 'flex-start', height: '100vh'}}>
            <div style={{border: '16px solid #f3f3f3', borderRadius: '50%', borderTop: '16px solid #3498db', width: '60px', height: '60px', animation: 'spin 2s linear infinite'}}></div>
        </div>
    );
};

export default Loader;