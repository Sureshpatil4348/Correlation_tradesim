import React, { useState } from 'react';
import useStore from '../stores/useStore';  // Import Zustand store

const LoginForm = () => {
  const [account, setAccount] = useState('');
  const [password, setPassword] = useState('');
  const [server, setServer] = useState('');
  // Get the login action from Zustand store
  const login = useStore((state) => state.login);
  
  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const response = await fetch('http://localhost:5001/mt5/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
        },
        body: JSON.stringify({
          account: Number(account),
          password: password,
          server: server,
        }),
      });

      const data = await response.json();
      if (response.ok) {
        console.log('Login successful');
        // Save account info to the Zustand store
        login(data.account_info);
        setAccount('');
        setPassword('');
        setServer('');
      } else {
        console.error('Login failed', data.message);
      }
    } catch (error) {
      console.error('Error logging in:', error);
    }
  };

  return (
    <div
      style={{
        width: '500px',
        margin: '50px auto',
        padding: '20px',
        border: '1px solid #ccc',
        borderRadius: '8px',
      }}
    >
      <form onSubmit={handleSubmit} style={{ width: '100%', display:'flex', flexDirection:'column', alignItems:'center' }}>
        <h2 style={{ textAlign: 'center', fontWeight: 'bold', marginBottom: '20px' }}>BotMudra TradeSim</h2>
        <div style={{ display:'flex', flexDirection:'column', alignItems:'flex-start', width:'90%'}}>

        <div style={{ marginBottom: '10px', width:'100%'}}>
          <label htmlFor="account" style={{ display: 'block', fontWeight: '600', marginBottom: '5px' }}>
            MT5 Username
          </label>
          <input
            placeholder="Enter your MT5 username"
            id="account"
            type="number"
            value={account}
            onChange={(e) => setAccount(e.target.value)}
            style={{ width: '95%', padding: '8px' }}
            required
          />
        </div>

        <div style={{ marginBottom: '10px', width:'100%' }}>
          <label htmlFor="password" style={{ display: 'block', fontWeight: '600', marginBottom: '5px' }}>
            MT5 Password
          </label>
          <input
            placeholder="Enter your MT5 password"
            id="password"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            style={{ width: '95%', padding: '8px' }}
            required
          />
        </div>

        <div style={{ marginBottom: '10px', width:'100%' }}>
          <label htmlFor="server" style={{ display: 'block', fontWeight: '600', marginBottom: '5px' }}>
            MT5 Server
          </label>
          <input
            placeholder="Eg. Exness-server"
            id="server"
            type="text"
            value={server}
            onChange={(e) => setServer(e.target.value)}
            style={{ width: '95%', padding: '8px' }}
            required
          />
        </div>
        </div>

        <button
          type="submit"
          style={{
            width: '95%',
            padding: '10px',
            backgroundColor: 'black',
            color: '#fff',
            border: 'none',
            borderRadius: '4px',
            marginTop: '10px',
          }}
        >
          Login
        </button>
      </form>
    </div>
  );
};

export default LoginForm;