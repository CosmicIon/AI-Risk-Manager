'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { 
  LayoutDashboard, 
  ShieldAlert, 
  Undo2, 
  FileSearch, 
  Network, 
  Activity, 
  Settings 
} from 'lucide-react';

const navItems = [
  { name: 'Dashboard', href: '/', icon: LayoutDashboard },
  { name: 'Chargebacks', href: '/chargebacks', icon: FileSearch },
  { name: 'Returns', href: '/returns', icon: Undo2 },
  { name: 'Fraud Alerts', href: '/fraud', icon: ShieldAlert },
  { name: 'Abuse Rings', href: '/rings', icon: Network },
  { name: 'Evaluation', href: '/evaluation', icon: Activity },
  { name: 'Settings', href: '/settings', icon: Settings },
];

export default function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="sidebar">
      <div className="sidebar-logo">
        <ShieldAlert size={28} className="logo-icon" />
        <h2>AI Risk Manager</h2>
      </div>
      
      <nav className="sidebar-nav">
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = pathname === item.href || (item.href !== '/' && pathname.startsWith(item.href));
          
          return (
            <Link 
              key={item.name} 
              href={item.href} 
              className={`nav-item ${isActive ? 'active' : ''}`}
            >
              <Icon size={20} />
              <span>{item.name}</span>
            </Link>
          );
        })}
      </nav>
      
      <div className="sidebar-footer">
        <p className="version-info">v1.0.0-rc.1</p>
        <span className="status-dot" title="All systems operational" />
      </div>
    </aside>
  );
}
