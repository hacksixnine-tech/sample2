import React, { createContext, useContext, useState } from 'react';

export type UserRole = 'SYSTEM_ADMIN' | 'POLICE_OFFICER' | 'INVESTIGATOR' | 'VIEWER';

export interface UserProfile {
  id: string;
  username: string;
  full_name: string;
  role: UserRole;
  badge_number: string;
  department: string;
  clearance_level: number;
}

interface AuthContextType {
  user: UserProfile;
  operationalMode: string;
  setOperationalMode: (mode: string) => void;
  logout: () => void;
}

const DEFAULT_USER: UserProfile = {
  id: 'usr-84920',
  username: 'cmd.vance',
  full_name: 'Cmdr. K. Vance',
  role: 'SYSTEM_ADMIN',
  badge_number: 'GJ-POL-8492',
  department: 'Statewide Surveillance Command',
  clearance_level: 5,
};

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user] = useState<UserProfile>(DEFAULT_USER);
  const [operationalMode, setOperationalMode] = useState<string>('ACTIVE_SURVEILLANCE');

  const logout = () => {
    localStorage.removeItem('phantom_auth_token');
    alert('Operator session locked. Re-authenticate to access Level 5 Matrix.');
  };

  return (
    <AuthContext.Provider value={{ user, operationalMode, setOperationalMode, logout }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
};
