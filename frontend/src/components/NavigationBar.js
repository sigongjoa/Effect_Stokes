import React from 'react';
import { Link } from 'react-router-dom';

const NavigationBar = () => {
  return (
    <nav style={{
      backgroundColor: '#282c34',
      padding: '10px 20px',
      display: 'flex',
      justifyContent: 'center',
      gap: '20px',
      borderBottom: '1px solid #61dafb'
    }}>
      <Link to="/preview" style={{
        color: 'white',
        textDecoration: 'none',
        fontSize: '1.2em',
        padding: '5px 10px',
        borderRadius: '5px',
        transition: 'background-color 0.3s ease'
      }} onMouseOver={e => e.currentTarget.style.backgroundColor = '#61dafb'} onMouseOut={e => e.currentTarget.style.backgroundColor = 'transparent'}>
        Preview
      </Link>
      <Link to="/full-pipeline" style={{
        color: 'white',
        textDecoration: 'none',
        fontSize: '1.2em',
        padding: '5px 10px',
        borderRadius: '5px',
        transition: 'background-color 0.3s ease'
      }} onMouseOver={e => e.currentTarget.style.backgroundColor = '#61dafb'} onMouseOut={e => e.currentTarget.style.backgroundColor = 'transparent'}>
        Full Pipeline
      </Link>
    </nav>
  );
};

export default NavigationBar;
