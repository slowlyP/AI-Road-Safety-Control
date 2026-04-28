import React, { useEffect } from 'react';
import '../styles/main.css';

const Home = () => {
  useEffect(() => {
    const revealItems = document.querySelectorAll(".reveal");
    const observer = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.classList.add("show");
        }
      });
    }, {
      threshold: 0.15
    });

    revealItems.forEach((item) => observer.observe(item));

    return () => {
      revealItems.forEach((item) => observer.unobserve(item));
    };
  }, []);

  return (
    <>
      <section className="hero-section" id="intro">
        <div className="hero-overlay"></div>

        <div className="hero-content reveal">
          <div className="hero-badge">● 실시간 도로 낙하물 탐지 시스템</div>

          <h1 className="hero-title">
            주행 중 낙하물<br />
            <span>0.5초</span> 안에 감지합니다
          </h1>

          <p className="hero-desc">
            AI 카메라가 전방 도로의 낙하물·장애물을 실시간으로 탐지하고,<br />
            사용자 신고와 관리자 처리 흐름을 하나로 연결하여
            더 빠르고 안전한 도로 환경을 지원합니다.
          </p>

          <div className="hero-actions">
            <a href="/report/create" className="btn btn-primary hero-btn">
              신고하기
            </a>
            <a href="#tech" className="btn btn-outline hero-btn">
              시스템 흐름 보기
            </a>
          </div>

          <div className="hero-stats">
            <div className="stat-card reveal">
              <strong>0.5초</strong>
              <span>평균 탐지 속도</span>
            </div>
            <div className="stat-card reveal">
              <strong>90.4%</strong>
              <span>탐지 정확도</span>
            </div>
            <div className="stat-card reveal">
              <strong>실시간</strong>
              <span>빠른 긴급 처리</span>
            </div>
          </div>
        </div>

        <div className="hero-scroll">
          <a href="#feature">SCROLL</a>
        </div>
      </section>

      <section className="main-section feature-section" id="feature">
        <div className="section-inner">
          <div className="section-head reveal">
            <p className="section-label">핵심 기능</p>
            <h2>도로 위 위험 요소를<br />빠르게 감지하고 대응합니다</h2>
            <p className="section-subtext">
              신고 등록부터 탐지, 위험도 분류, 관리자 처리까지<br />
              하나의 서비스 흐름으로 연결되는 기능을 제공합니다.
            </p>
          </div>

          <div className="feature-grid">
            <article className="feature-card reveal">
              <div className="feature-icon">📷</div>
              <h3>AI 낙하물 탐지</h3>
              <p>
                이미지 및 영상 데이터를 기반으로<br />도로 위 낙하물과 장애물을<br />
                자동 인식하고 빠르게 탐지합니다.
              </p>
            </article>

            <article className="feature-card reveal">
              <div className="feature-icon">🚨</div>
              <h3>실시간 위험 알림</h3>
              <p>
                탐지 결과를 기반으로 위험도를 분석하여<br />
                즉각적인 경고와<br /> 후속 대응이 가능하도록 지원합니다.
              </p>
            </article>

            <article className="feature-card reveal">
              <div className="feature-icon">📝</div>
              <h3>신고 등록 및 추적</h3>
              <p>
                사용자는 사진·영상과 위치 정보를 등록하고<br />
                신고 접수부터 처리 완료까지<br /> 상태를 확인할 수 있습니다.
              </p>
            </article>
          </div>
        </div>
      </section>

      <section className="main-section tech-section" id="tech">
        <div className="section-inner">
          <div className="section-head reveal">
            <p className="section-label">기술 구성</p>
            <h2>탐지부터 기록과 관리까지<br /> 하나의 흐름으로 연결됩니다</h2>
            <p className="section-subtext">
              사용자의 신고 데이터와 AI 탐지 결과를 기반으로<br />
              관리자 대시보드에서 통합 관리가 가능합니다.
            </p>
          </div>

          <div className="flow-grid">
            <div className="flow-card reveal">
              <span className="flow-step">01</span>
              <strong>신고 등록</strong>
              <p>사용자가 낙하물 위치와 내용을 입력합니다.</p>
            </div>

            <div className="flow-card reveal">
              <span className="flow-step">02</span>
              <strong>파일 업로드</strong>
              <p>사진 또는 영상 파일을 함께 등록합니다.</p>
            </div>

            <div className="flow-card reveal">
              <span className="flow-step">03</span>
              <strong>AI 탐지</strong>
              <p>객체 탐지 모델이 낙하물 여부를 분석합니다.</p>
            </div>

            <div className="flow-card reveal">
              <span className="flow-step">04</span>
              <strong>위험도 분석</strong>
              <p>낮음, 주의, 위험, 긴급 등급으로 분류합니다.</p>
            </div>

            <div className="flow-card reveal">
              <span className="flow-step">05</span>
              <strong>실시간 알림</strong>
              <p>관리자와 시스템 사용자에게 위험 정보를 전달합니다.</p>
            </div>

            <div className="flow-card reveal">
              <span className="flow-step">06</span>
              <strong>관리자 처리</strong>
              <p>대시보드에서 신고 확인과 상태 변경을 수행합니다.</p>
            </div>
          </div>
        </div>
      </section>

      <section className="main-section alert-section" id="alert">
        <div className="section-inner">
          <div className="section-head reveal">
            <p className="section-label">위험도 등급</p>
            <h2>위험 상황을 등급별로<br /> 빠르게 확인할 수 있습니다</h2>
            <p className="section-subtext">
              AI 탐지 결과와 신고 내용을 바탕으로
              우선 대응이 필요한 상황을 직관적으로 구분합니다.
            </p>
          </div>

          <div className="alert-grid">
            <div className="alert-card low reveal">
              <span className="alert-name">낮음</span>
              <p>경미한 장애물 또는 비교적 영향이<br /> 적은 상황</p>
            </div>

            <div className="alert-card caution reveal">
              <span className="alert-name">주의</span>
              <p>차량 주행에 영향을 줄 수 있어<br /> 확인이 필요한 상황</p>
            </div>

            <div className="alert-card danger reveal">
              <span className="alert-name">위험</span>
              <p>즉각적인 조치가<br /> 필요한 도로 위 위험 상황</p>
            </div>

            <div className="alert-card emergency reveal">
              <span className="alert-name">긴급</span>
              <p>대형 사고로 이어질 수 있어<br /> 최우선 대응이 필요한 상황</p>
            </div>
          </div>
        </div>
      </section>

      <section className="main-section service-section" id="service">
        <div className="section-inner">
          <div className="section-head reveal">
            <p className="section-label">서비스 가치</p>
            <h2>더 빠른 탐지와 더 정확한 대응으로<br /> 도로 안전을 개선합니다</h2>
            <p className="section-subtext">
              사용자 신고, AI 분석, 관리자 처리 흐름을 통합하여<br />
              실제 도로 안전 관리에 활용 가능한 서비스를 목표로 합니다.
            </p>
          </div>

          <div className="service-grid">
            <div className="service-card reveal">
              <h3>사용자 중심 신고 시스템</h3>
              <p>
                위치, 설명, 파일을 손쉽게 등록하여<br /> 누구나 빠르게 도로 이상 상황을 공유할 수 있습니다.
              </p>
            </div>

            <div className="service-card reveal">
              <h3>관리자 대시보드 통합 관리</h3>
              <p>
                접수 상태, 위험도, 처리 현황을 시각적으로 확인하고<br /> 운영 효율을 높일 수 있습니다.
              </p>
            </div>

            <div className="service-card reveal">
              <h3>AI 기반 확장 가능 구조</h3>
              <p>
                향후 실시간 영상 분석, 자동 알림,<br /> 탐지 로그 관리까지<br /> 단계적으로 확장할 수 있습니다.
              </p>
            </div>
          </div>
        </div>
      </section>
    </>
  );
};

export default Home;
