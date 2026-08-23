import React from 'react';
import {
  LayoutDashboard,
  Tv,
  Camera,
  Car,
  ListOrdered,
  BellRing,
  FileSpreadsheet,
  Compass,
  MapPin,
  Route,
  PieChart,
  Activity,
  Server,
  FileText,
  Building2,
  Users,
  Sliders,
  Settings,
  Layers,
} from 'lucide-react';

export type NavView =
  | 'dashboard'
  | 'live_monitoring'
  | 'camera_registry'
  | 'anpr_vehicles'
  | 'watchlists'
  | 'alerts'
  | 'incidents'
  | 'investigations'
  | 'gis_map'
  | 'vehicle_tracking'
  | 'coverage_gaps'
  | 'stream_health'
  | 'system_health'
  | 'audit_logs'
  | 'departments'
  | 'users_roles'
  | 'integrations'
  | 'system_settings';

interface SidebarProps {
  activeView: NavView;
  onNavigate: (view: NavView) => void;
  alertCount?: number;
}

interface NavItem {
  id: NavView;
  label: string;
  icon: React.ElementType;
  badge?: string | number;
  badgeType?: 'live' | 'alert' | 'count';
}

interface NavSection {
  title: string;
  items: NavItem[];
}

export const Sidebar: React.FC<SidebarProps> = ({ activeView, onNavigate, alertCount = 0 }) => {
  const sections: NavSection[] = [
    {
      title: 'COMMAND',
      items: [
        { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
        { id: 'live_monitoring', label: 'Live Monitoring', icon: Tv, badge: '4-WALL', badgeType: 'live' },
        { id: 'camera_registry', label: 'Camera Registry', icon: Camera },
      ],
    },
    {
      title: 'INTELLIGENCE',
      items: [
        { id: 'anpr_vehicles', label: 'ANPR & Vehicles', icon: Car },
        { id: 'watchlists', label: 'Watchlists', icon: ListOrdered },
        {
          id: 'alerts',
          label: 'Alerts',
          icon: BellRing,
          badge: alertCount > 0 ? alertCount : undefined,
          badgeType: 'alert',
        },
        { id: 'incidents', label: 'Incidents', icon: FileSpreadsheet },
        { id: 'investigations', label: 'Investigations', icon: Compass },
      ],
    },
    {
      title: 'GIS',
      items: [
        { id: 'gis_map', label: 'CCTV Map', icon: MapPin },
        { id: 'vehicle_tracking', label: 'Vehicle Tracking', icon: Route },
        { id: 'coverage_gaps', label: 'Coverage & Gaps', icon: PieChart },
      ],
    },
    {
      title: 'OPERATIONS',
      items: [
        { id: 'stream_health', label: 'Stream Health', icon: Activity },
        { id: 'system_health', label: 'System Health', icon: Server },
        { id: 'audit_logs', label: 'Audit Logs', icon: FileText },
      ],
    },
    {
      title: 'ADMIN',
      items: [
        { id: 'departments', label: 'Departments', icon: Building2 },
        { id: 'users_roles', label: 'Users & Roles', icon: Users },
        { id: 'integrations', label: 'Integrations', icon: Layers },
        { id: 'system_settings', label: 'System Settings', icon: Settings },
      ],
    },
  ];

  return (
    <aside className="global-sidebar" aria-label="Surveillance Navigation">
      <div className="sidebar-scroll">
        {sections.map((section) => (
          <div key={section.title} className="sidebar-section">
            <h3 className="section-title">{section.title}</h3>
            <ul className="nav-items-list">
              {section.items.map((item) => {
                const Icon = item.icon;
                const isActive = activeView === item.id;
                return (
                  <li key={item.id}>
                    <button
                      onClick={() => onNavigate(item.id)}
                      className={`nav-item-btn ${isActive ? 'active' : ''}`}
                      aria-current={isActive ? 'page' : undefined}
                    >
                      <Icon size={16} className="nav-icon" />
                      <span className="nav-label">{item.label}</span>

                      {item.badge !== undefined && (
                        <span className={`nav-badge badge-${item.badgeType || 'count'}`}>
                          {item.badge}
                        </span>
                      )}
                    </button>
                  </li>
                );
              })}
            </ul>
          </div>
        ))}
      </div>

      {/* Sidebar Clearances Tag */}
      <div className="sidebar-clearance-footer">
        <div className="clearance-indicator">
          <span className="clearance-dot"></span>
          <span className="clearance-text">CLEARANCE LEVEL 5</span>
        </div>
      </div>
    </aside>
  );
};
