import React from 'react';
import { Maximize2, Camera as CameraIcon, RefreshCw, ZoomIn, ZoomOut } from 'lucide-react';

interface CameraControlsProps {
  onFullscreen?: () => void;
  onSnapshot?: () => void;
  onReload?: () => void;
  onZoomIn?: () => void;
  onZoomOut?: () => void;
  isPtz?: boolean;
}

export const CameraControls: React.FC<CameraControlsProps> = ({
  onFullscreen,
  onSnapshot,
  onReload,
  onZoomIn,
  onZoomOut,
  isPtz = false,
}) => {
  return (
    <div className="cam-controls-bar">
      {isPtz && (
        <div className="ptz-quick-controls">
          <button onClick={onZoomIn} className="cam-ctrl-btn" title="Zoom In (+)">
            <ZoomIn size={13} />
          </button>
          <button onClick={onZoomOut} className="cam-ctrl-btn" title="Zoom Out (-)">
            <ZoomOut size={13} />
          </button>
        </div>
      )}

      <div className="action-buttons-group">
        <button onClick={onReload} className="cam-ctrl-btn" title="Reconnect Stream">
          <RefreshCw size={13} />
        </button>

        <button onClick={onSnapshot} className="cam-ctrl-btn" title="Save Forensic Snapshot">
          <CameraIcon size={13} />
        </button>

        <button onClick={onFullscreen} className="cam-ctrl-btn" title="Expand Fullscreen (F)">
          <Maximize2 size={13} />
        </button>
      </div>
    </div>
  );
};
