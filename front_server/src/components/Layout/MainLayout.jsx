import React from 'react';
import Header from './Header';
import Footer from './Footer';
import TeamSidebar from './TeamSidebar';
import '../../styles/common.css';

const MainLayout = ({ children, isLoggedIn, isAdmin, userName, activeMember }) => {
  return (
    <div className="app-container">
      <Header isLoggedIn={isLoggedIn} isAdmin={isAdmin} userName={userName} />
      
      <main className="page-wrapper">
        <div className="page-with-team-sidebar">
          <TeamSidebar activeMember={activeMember} />
          <div className="page-content-area">
            {children}
          </div>
        </div>
      </main>

      <Footer isAdmin={isAdmin} />
      
      {isLoggedIn && isAdmin && (
        <div id="realtime-alert-toast-container" className="realtime-alert-toast-container"></div>
      )}
    </div>
  );
};

export default MainLayout;
