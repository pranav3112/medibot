import React from 'react';
import './HamburgerButton.css';

interface HamburgerButtonProps {
  onClick: () => void;
  isOpen: boolean;
}

const HamburgerButton: React.FC<HamburgerButtonProps> = ({ onClick, isOpen }) => {
  return (
    <button 
      className={`hamburger-button ${isOpen ? 'hamburger-open' : ''}`} 
      onClick={onClick} 
      aria-label={isOpen ? "Close menu" : "Open menu"}
    >
      <div className="hamburger-line hamburger-line-1"></div>
      <div className="hamburger-line hamburger-line-2"></div>
      <div className="hamburger-line hamburger-line-3"></div>
    </button>
  );
};

export default HamburgerButton;