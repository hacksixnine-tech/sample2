import React, { useState } from 'react';
import { Camera } from '../../types';
import { CameraPlayer } from './CameraPlayer';
import { CameraMetadata } from './CameraMetadata';
import { CameraControls } from './CameraControls';
import { CameraStatusBadge } from './CameraStatusBadge';

export interface CameraCardProps {
  camera: Camera;
  onSelect?: (camera: Camera) => void;
  isFocused?: boolean;
}

export const CameraCard: React.FC<CameraCardProps> = ({ camera, onSelect, isFocused = false }) => {
  const [isFullscreen, setIsFullscreen] = useState(false);

  const primaryStream = camera.streams && camera.streams.length > 0 ? camera.streams[0] : undefined;

  const handleFullscreen = () => {
    setIsFullscreen(!isFullscreen);
  };

  const handleSnapshot = () => {
    alert(`Snapshot captured for ${camera.camera_code} (${camera.name}). Preserved in forensic vault.`);
  };

  return (
    <div
      className={`camera-card-wrapper ${isFocused ? 'focused' : ''} ${isFullscreen ? 'fullscreen-mode' : ''}`}
      onClick={() => onSelect && onSelect(camera)}
    >
      {/* Top Card Header */}
      <div className="camera-card-header">
        <div className="header-left">
          <CameraStatusBadge status={camera.status} />
          <span className="card-cam-id">{camera.camera_code}</span>
        </div>
        <CameraControls
          onFullscreen={handleFullscreen}
          onSnapshot={handleSnapshot}
          isPtz={camera.is_ptz_capable}
        />
      </div>

      {/* Video Player Abstraction */}
      <div className="camera-card-player-wrap">
        <CameraPlayer
          camera={camera}
          streamUrl={primaryStream?.stream_url}
          protocol={primaryStream?.protocol || 'HLS'}
          status={camera.status}
          fps={camera.fps || 25}
          quality={camera.status === 'ONLINE' ? 'EXCELLENT' : 'OFFLINE'}
        />
      </div>

      {/* Camera Metadata Bar */}
      <CameraMetadata camera={camera} />
    </div>
  );
};
