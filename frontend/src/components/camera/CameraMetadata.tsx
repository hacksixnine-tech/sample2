import React from 'react';
import { Camera } from '../../types';
import { MapPin, Building, Cpu, Radio } from 'lucide-react';

export const CameraMetadata: React.FC<{ camera: Camera }> = ({ camera }) => {
  return (
    <div className="cam-metadata-panel">
      <div className="cam-meta-row main">
        <span className="cam-code">{camera.camera_code}</span>
        <span className="cam-name">{camera.name}</span>
      </div>

      <div className="cam-meta-row sub">
        <div className="cam-meta-item" title="District / Jurisdiction">
          <MapPin size={11} className="text-cyan" />
          <span>{camera.district || 'Statewide Area'}</span>
        </div>

        <div className="cam-meta-item" title="Department">
          <Building size={11} className="text-muted" />
          <span>{camera.department_name || 'Home Dept / Police'}</span>
        </div>

        <div className="cam-meta-item" title="AI Analytics Status">
          <Cpu size={11} className={camera.ai_enabled ? 'text-healthy' : 'text-muted'} />
          <span>{camera.ai_enabled ? 'AI INFERENCE ACTIVE' : 'RAW STREAM'}</span>
        </div>

        <div className="cam-meta-item" title="PTZ Capability">
          <Radio size={11} className={camera.is_ptz_capable ? 'text-cyan' : 'text-muted'} />
          <span>{camera.is_ptz_capable ? 'PTZ ACTIVE' : 'FIXED'}</span>
        </div>
      </div>
    </div>
  );
};
