import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import MainLayout from './components/Layout/MainLayout';
import Home from './pages/Home';
import RealtimeMonitor from './pages/RealtimeMonitor';
import CctvDashboard from './pages/CctvDashboard';
import ReportCreate from './pages/ReportCreate';
import BoardList from './pages/BoardList';
import Login from './pages/Login';
import Signup from './pages/Signup';

function App() {
  // 실제로는 API 호출을 통해 로그인 상태를 관리해야 함
  const mockUser = {
    isLoggedIn: false,
    isAdmin: false,
    userName: ""
  };

  return (
    <Router>
      <MainLayout 
        isLoggedIn={mockUser.isLoggedIn} 
        isAdmin={mockUser.isAdmin} 
        userName={mockUser.userName}
        activeMember="kdh" // 예시로 김도하 선택
      >
        <Routes>
          <Route path="/" element={<Home />} />
          {/* 다른 페이지들도 추후 여기에 추가 */}
          <Route path="/realtime-monitor" element={<RealtimeMonitor />} />
          <Route path="/cctv" element={<CctvDashboard />} />
          <Route path="/report/create" element={<ReportCreate />} />
          <Route path="/board" element={<BoardList />} />
          <Route path="/login" element={<Login />} />
          <Route path="/signup" element={<Signup />} />
        </Routes>
      </MainLayout>
    </Router>
  );
}

export default App;
