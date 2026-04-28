import React from 'react';
import '../../styles/common.css';

const TeamSidebar = ({ activeMember }) => {
  const members = [
    { id: 'kdh', name: '김도하', github: 'https://github.com/DDORINY', img: '/images/team/kdh.png' },
    { id: 'smg', name: '송명근', github: 'https://github.com/slowlyP', img: '/images/team/smg.png' },
    { id: 'lhj', name: '임효정', github: 'https://github.com/ggug0125-ui', img: '/images/team/lhj.png' },
    { id: 'kdk', name: '김도균', github: 'https://github.com/Dogyun-Kim57', img: '/images/team/kdk.png' }
  ];

  return (
    <aside className="team-sidebar">
      <strong>404RNF</strong>
      {members.map(member => (
        <div 
          key={member.id}
          className={`team-profile ${activeMember === member.id ? 'is-active' : ''}`}
          onClick={() => window.open(member.github)}
          style={{ cursor: 'pointer' }}
        >
          <img src={member.img} alt={member.name} />
          <div>
            <strong>{member.name}</strong>
          </div>
        </div>
      ))}
    </aside>
  );
};

export default TeamSidebar;
