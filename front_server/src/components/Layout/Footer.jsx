import React from 'react';
import '../../styles/common.css';

const Footer = ({ isAdmin }) => {
  return (
    <footer className="site-footer" id="contact">
      <div className="footer-inner">
        <div className="footer-brand">
          <div className="footer-logo">
            <span className="logo-badge">404</span>
            <span className="logo-text">R·N·F <strong>AI</strong></span>
          </div>

          <p className="footer-desc">
            AI 기반 도로 낙하물 탐지 시스템으로
            도로 위 위험 요소를 빠르게 감지하고
            사용자 신고와 관리자 대응을 지원합니다.
          </p>

          <div className="footer-tech">
            <span>React</span>
            <span>YOLO</span>
            <span>MySQL</span>
            <span>AI Vision</span>
          </div>
        </div>

        <div className="footer-links">
          <h4>서비스</h4>
          <ul>
            <li><a href="/#intro">서비스 소개</a></li>
            <li><a href="/#feature">핵심 기능</a></li>
            <li><a href="/#tech">기술 구조</a></li>
            <li><a href="/#alert">위험도 등급</a></li>
            <li><a href="/realtime-monitor">실시간 탐지 현황</a></li>
            <li><a href="/report/create">낙하물 신고</a></li>

            {isAdmin && (
              <li>
                <a className="admin-footer-link" href="/admin/dashboard">
                  관리자 대시보드
                </a>
              </li>
            )}
          </ul>
        </div>

        <div className="footer-resources">
          <h4 className="footer-title">Project Archive</h4>
          <ul className="resource-list">
            <li><a href="https://github.com/lms-mini-project/AI-accident-detection" target="_blank" rel="noreferrer">Team GitHub</a></li>
            <li><a href="https://www.notion.so/doreen1004/AI-31fbec735c378068834eec617ff1a984" target="_blank" rel="noreferrer">Project Notion</a></li>
            <li><a href="https://doha.atlassian.net/jira/software/projects/AI/summary" target="_blank" rel="noreferrer">Jira Board</a></li>
          </ul>

          <h4 className="footer-title" style={{ marginTop: '35px' }}>Project Info</h4>
          <div className="info-content">
            <p><strong>개발 기간:</strong> 2026.03.09 ~ 2026.04.06</p>
            <p><strong>팀 명칭:</strong> 404 R·N·F AI Team</p>
            <p><strong>문의:</strong> <a href="mailto:jihun22400669@gmail.com">jihun22400669@gmail.com</a></p>
          </div>
        </div>
      </div>

      <div className="footer-bottom">
        <p>© 2026 404 R·N·F AI — Road Hazard Detection System</p>
      </div>
    </footer>
  );
};

export default Footer;
