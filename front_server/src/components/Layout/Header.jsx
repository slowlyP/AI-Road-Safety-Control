import React, { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import '../../styles/common.css';

const Header = ({ isLoggedIn, isAdmin, userName }) => {
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const location = useLocation();

  const toggleMenu = () => {
    setIsMenuOpen(!isMenuOpen);
  };

  return (
    <header className="site-header" id="siteHeader">
      <div className="header-inner">
        <Link to="/" className="logo">
          <span className="logo-badge">404</span>
          <span className="logo-text">R·N·F <strong>AI</strong></span>
        </Link>

        <nav className={`main-nav ${isMenuOpen ? 'is-active' : ''}`} id="mainNav">
          <ul className="nav-list">
            <li><a href="/#intro">소개</a></li>
            <li><a href="/#feature">기능</a></li>
            <li><a href="/#tech">기술</a></li>
            <li><a href="/#alert">알림</a></li>
            <li><Link to="/realtime-monitor">탐지 현황</Link></li>
            <li><Link to="/cctv">CCTV 보기</Link></li>
            <li><Link to="/report/create" className="highlight-link">신고하기</Link></li>
            <li><Link to="/board">자유게시판</Link></li>

            {isAdmin && (
              <li>
                <Link to="/admin/dashboard" className="admin-link">
                  대시보드
                </Link>
              </li>
            )}
          </ul>
        </nav>

        <div className="header-actions">
          {isLoggedIn ? (
            <>
              <span className="user-name">{userName}님</span>
              <Link to="/mypage" className="btn btn-outline">마이페이지</Link>
              <Link to="/logout" className="btn btn-primary">로그아웃</Link>
            </>
          ) : (
            <>
              <Link to="/login" className="btn btn-outline">로그인</Link>
              <Link to="/signup" className="btn btn-primary">회원가입</Link>
            </>
          )}
        </div>

        <button 
          className={`menu-toggle ${isMenuOpen ? 'is-active' : ''}`} 
          id="menuToggle" 
          onClick={toggleMenu}
          aria-label="모바일 메뉴 열기"
        >
          <span></span>
          <span></span>
          <span></span>
        </button>
      </div>
    </header>
  );
};

export default Header;
