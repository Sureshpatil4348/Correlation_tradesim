  // /App.js
import React, { useState, useEffect } from 'react';
import Navbar from './components/navbar';
import LoginForm from './components/loginForm';
import useStore from './stores/useStore';  // Import Zustand store to check login state
import Sidebar from './components/sidebar';
import Dashboard from './components/pages/dashboard';
import Strategies from './components/pages/strategies';
import Indicators from './components/pages/indicators';
import Analytics from './components/pages/analytics';
import Settings from './components/pages/settings';
import Loader from './components/loader';
const App = () => {
  // Check if the user is logged in
  const { isLoggedIn, setIsLoggedIn, isLoading } = useStore((state) => state);
  const {setAccountInfo} = useStore((state) => state);
  const { selectedPage } = useStore((state) => state);

  useEffect(() => {
    const checkLoginStatus = async () => {
      try {
        const response = await fetch('http://localhost:5001/mt5/status');
        const data = await response.json();

        if (data.status === 'logged_in') {
          const accountInfo = {
            account_number: data.account_number,
            balance: data.balance,
            equity: data.equity,
          };
          setAccountInfo(accountInfo);
          setIsLoggedIn(true);
        } else {
          setIsLoggedIn(false);
        }
      } catch (error) {
        console.error('Error fetching login status:', error);
      }
    };

    checkLoginStatus();
  }, []);

  return (
    <div style={{ position: 'relative', marginTop: '50px', display:'flex', flexDirection:'column', alignItems:'center', width:'100vw' }}>
      <Navbar />
      {!isLoggedIn ? (
        <LoginForm />  // Show login form if not logged in
      ) : (
        <>
        <Sidebar />
        { selectedPage === 'Dashboard' && <Dashboard />}
        { selectedPage === 'Strategies' && <Strategies />}
        { selectedPage === 'Indicators' && <Indicators />}
        { selectedPage === 'Analytics' && <Analytics />}
        { selectedPage === 'Settings' && <Settings />}
        </>
      )}
      {isLoading && (
          <div style={{marginLeft: '0px', position: 'absolute', width: '100vw', top: '0', left: '0', display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100%', backgroundColor: 'rgba(0, 0, 0, 0.5)', zIndex: 9999, minHeight: '100vh'}}>
              <Loader />
          </div>
      )}
    </div>
  );
};

export default App;
