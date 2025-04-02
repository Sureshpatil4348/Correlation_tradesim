// /components/Navbar.jsx
import React from 'react';
import useStore from '../stores/useStore';

const Navbar = () => {
    const isLoggedIn = useStore((state) => state.isLoggedIn);
    const accountInfo = useStore((state) => state.accountInfo);
    const logout = useStore((state) => state.logout);

  return (
    <div
      style={{
        backgroundColor: '#333',
        height: '50px',
        color: 'white',
        padding: '0px 20px',
        width: '100vw',
        position: 'fixed',
        top: 0,
        left: 0,
        zIndex: 1000,
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
      }}
    >
      <h3 style={{ margin: 0 }}>BotMudra TradeSim</h3>
      {isLoggedIn ? (
        <div style={{ display: 'flex', alignItems: 'center', marginRight: '40px' }}>
          <p style={{ margin: 0, paddingRight: '10px' }}>
            <strong>Account:</strong> {accountInfo?.account_number || accountInfo?.login}
          </p>
          <p style={{ margin: 0, paddingRight: '10px' }}>
            <strong>Balance:</strong> {accountInfo?.balance}
          </p>
          <button
            onClick={logout}  // Logout function from the store
            style={{
              padding: '5px 10px',
              backgroundColor: 'red',
              color: '#fff',
              border: 'none',
              cursor: 'pointer',
            }}
          >
            Logout
          </button>
        </div>
      ) : (
        <p style={{ marginRight: '40px' }}>Please log in to view account details</p>
      )}
    </div>
  );
};

export default Navbar;