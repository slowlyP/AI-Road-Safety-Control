import React from 'react';
import { Link } from 'react-router-dom';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:5001';

const BoardList = () => {
  return (
    <div style={{ padding: '40px 20px', maxWidth: '800px', margin: '0 auto', textAlign: 'center', minHeight: '60vh', display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'center' }}>
      <div style={{ marginBottom: '30px' }}>
        <span className="logo-badge" style={{ 
          display: 'inline-block',
          background: 'linear-gradient(135deg, #ff6b00, #ff4d4d)',
          color: 'white',
          padding: '4px 12px',
          borderRadius: '20px',
          fontWeight: 'bold',
          marginBottom: '15px'
        }}>안내</span>
        <h2 style={{ fontSize: '28px', color: '#fff', marginBottom: '15px' }}>자유게시판 시스템 업데이트 중</h2>
        <p style={{ color: '#a0aec0', lineHeight: '1.6', fontSize: '16px' }}>
          현재 자유게시판을 React 기반의 새로운 인터페이스로 이전하는 작업이 진행 중입니다.<br/>
          빠른 시일 내에 더 빠르고 편리한 게시판으로 찾아뵙겠습니다.
        </p>
      </div>

      <div style={{ 
        background: '#1a2235', 
        border: '1px solid #4a5568', 
        borderRadius: '12px', 
        padding: '30px',
        width: '100%',
        maxWidth: '500px'
      }}>
        <p style={{ color: '#e2e8f0', marginBottom: '20px' }}>기존 게시판을 임시로 이용하시겠습니까?</p>
        <a 
          href={`${API_BASE_URL}/board/`}
          target="_blank"
          rel="noopener noreferrer"
          style={{
            display: 'inline-block',
            background: '#3182ce',
            color: 'white',
            padding: '12px 24px',
            borderRadius: '8px',
            textDecoration: 'none',
            fontWeight: '600',
            transition: 'background 0.2s'
          }}
          onMouseOver={(e) => e.target.style.background = '#2b6cb0'}
          onMouseOut={(e) => e.target.style.background = '#3182ce'}
        >
          기존 게시판 열기 (새 탭)
        </a>
      </div>
    </div>
  );
};

export default BoardList;
