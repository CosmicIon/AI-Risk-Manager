import { Bell, Search, User } from 'lucide-react';

export default function Header() {
  return (
    <header className="header">
      <div className="header-search">
        <Search size={18} className="search-icon" />
        <input 
          type="text" 
          placeholder="Search Case ID, ARN, or Customer..." 
          className="search-input"
        />
      </div>
      
      <div className="header-actions">
        <div className="tenant-badge">
          CosmicIon FinServe
        </div>
        
        <button className="icon-btn notification-btn">
          <Bell size={20} />
          <span className="notification-dot"></span>
        </button>
        
        <div className="user-profile">
          <div className="avatar">
            <User size={18} />
          </div>
          <div className="user-info">
            <span className="user-name">Risk Analyst</span>
            <span className="user-role">Admin</span>
          </div>
        </div>
      </div>
    </header>
  );
}
