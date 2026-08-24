import React, { useRef, useState, useEffect, useCallback } from 'react';
import Hls from 'hls.js';
import { Camera, StreamProtocol, CameraStatus } from '../../types';
import {
  Wifi,
  WifiOff,
  AlertCircle,
  Play,
  Pause,
  Volume2,
  VolumeX,
  RefreshCw,
  Maximize2,
  Camera as CameraIcon,
  Loader2,
  Activity,
  Sliders,
  Settings2,
  Shield,
  Layers,
} from 'lucide-react';

export type PlayerState =
  | 'CONNECTING'
  | 'LIVE'
  | 'BUFFERING'
  | 'OFFLINE'
  | 'ERROR'
  | 'RECONNECTING'
  | 'SOURCE_CONFIG_REQUIRED'
  | 'TEST_STREAM';

export interface CameraPlayerProps {
  camera: Camera;
  streamUrl?: string;
  protocol?: StreamProtocol;
  status: CameraStatus;
  fps?: number;
  quality?: 'EXCELLENT' | 'GOOD' | 'POOR' | 'OFFLINE';
  isAutoPlay?: boolean;
}

const MAX_RECONNECT_ATTEMPTS = 5;

export const CameraPlayer: React.FC<CameraPlayerProps> = ({
  camera,
  streamUrl,
  protocol = 'HLS',
  status: initialStatus,
  fps = 25,
  quality = 'GOOD',
  isAutoPlay = true,
}) => {
  const videoRef = useRef<HTMLVideoElement>(null);
  const hlsRef = useRef<Hls | null>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  const [playerState, setPlayerState] = useState<PlayerState>('CONNECTING');
  const [isPlaying, setIsPlaying] = useState<boolean>(isAutoPlay);
  const [isMuted, setIsMuted] = useState<boolean>(true);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [reconnectAttempt, setReconnectAttempt] = useState<number>(0);
  const [latencyMs, setLatencyMs] = useState<number>(65);
  const [currentFps, setCurrentFps] = useState<number>(fps);
  const [resolvedStreamUrl, setResolvedStreamUrl] = useState<string>('');
  const [sourceType, setSourceType] = useState<string>('GATEWAY');
  const [selectedProfile, setSelectedProfile] = useState<string>('MEDIUM');
  const [isTestMode, setIsTestMode] = useState<boolean>(false);
  const [isFitContain, setIsFitContain] = useState<boolean>(true);

  // 1. Fetch normalized browser-compatible stream endpoint from PHANTOM Backend
  useEffect(() => {
    let isMounted = true;

    const resolveStreamFromBackend = async () => {
      try {
        setPlayerState('CONNECTING');
        const camId = camera.id || camera.camera_code || 'CAM-001';
        const response = await fetch(`/api/v1/cameras/${encodeURIComponent(camId)}/stream?profile=${selectedProfile}`);

        if (response.ok) {
          const resData = await response.json();
          if (isMounted && resData.success && resData.data) {
            const data = resData.data;
            const playUrl = data.browser_playback_url || data.hls_stream_url;
            setResolvedStreamUrl(playUrl);
            setSourceType(data.source_type || data.provider || 'GATEWAY');
            if (data.status === 'SOURCE_CONFIG_REQUIRED') {
              setPlayerState('SOURCE_CONFIG_REQUIRED');
              return;
            }
            if (data.mode === 'TEST_STREAM_ACTIVE') {
              setIsTestMode(true);
            }
            if (data.latency_ms) setLatencyMs(Math.round(data.latency_ms));
            if (data.fps) setCurrentFps(data.fps);
          }
        } else {
          // Fallback to local gateway route
          if (isMounted) {
            setResolvedStreamUrl(`/api/v1/streams/${encodeURIComponent(camId)}/live.m3u8`);
          }
        }
      } catch (err) {
        // Safe gateway default
        const camId = camera.id || camera.camera_code || 'CAM-001';
        if (isMounted) {
          setResolvedStreamUrl(`/api/v1/streams/${encodeURIComponent(camId)}/live.m3u8`);
        }
      }
    };

    if (streamUrl) {
      setResolvedStreamUrl(streamUrl);
    } else {
      resolveStreamFromBackend();
    }

    return () => {
      isMounted = false;
    };
  }, [camera.id, camera.camera_code, streamUrl, selectedProfile]);

  const destroyHls = useCallback(() => {
    if (hlsRef.current) {
      hlsRef.current.destroy();
      hlsRef.current = null;
    }
  }, []);

  // 2. Initialize Hls.js / Video Engine
  const initializePlayer = useCallback(() => {
    const video = videoRef.current;
    if (!video || !resolvedStreamUrl) {
      return;
    }

    destroyHls();
    setPlayerState('CONNECTING');
    setErrorMessage(null);

    const isHls = resolvedStreamUrl.endsWith('.m3u8') || resolvedStreamUrl.includes('/streams/');

    if (isHls && Hls.isSupported()) {
      const hls = new Hls({
        enableWorker: true,
        lowLatencyMode: true,
        backBufferLength: 20,
        maxBufferLength: 10,
        maxMaxBufferLength: 20,
        liveSyncDurationCount: 3,
        liveMaxLatencyDurationCount: 6,
        manifestLoadingTimeOut: 8000,
        manifestLoadingMaxRetry: 4,
        manifestLoadingRetryDelay: 1000,
        levelLoadingTimeOut: 8000,
        fragLoadingTimeOut: 10000,
      });

      hlsRef.current = hls;
      hls.loadSource(resolvedStreamUrl);
      hls.attachMedia(video);

      hls.on(Hls.Events.MANIFEST_PARSED, () => {
        setPlayerState(isTestMode ? 'TEST_STREAM' : 'LIVE');
        setReconnectAttempt(0);
        if (isAutoPlay) {
          video.play().catch(() => {
            // Autoplay with sound restricted by browser policy -> mute and retry
            video.muted = true;
            setIsMuted(true);
            video.play().catch(() => {});
          });
        }
      });

      hls.on(Hls.Events.FRAG_LOADED, () => {
        if (playerState !== 'LIVE' && playerState !== 'TEST_STREAM') {
          setPlayerState(isTestMode ? 'TEST_STREAM' : 'LIVE');
        }
      });

      hls.on(Hls.Events.ERROR, (_event, data) => {
        if (data.details === 'bufferStalledError') {
          setPlayerState('BUFFERING');
          return;
        }
        if (data.fatal) {
          switch (data.type) {
            case Hls.ErrorTypes.NETWORK_ERROR:
              handleNetworkError(hls);
              break;
            case Hls.ErrorTypes.MEDIA_ERROR:
              hls.recoverMediaError();
              break;
            default:
              destroyHls();
              setPlayerState('ERROR');
              setErrorMessage('Live CCTV Stream feed interrupted. Retrying via Gateway...');
              scheduleReconnect();
              break;
          }
        }
      });
    } else if (video.canPlayType('application/vnd.apple.mpegurl')) {
      // Native Safari iOS / macOS HLS support
      video.src = resolvedStreamUrl;
      video.addEventListener('loadedmetadata', () => {
        setPlayerState(isTestMode ? 'TEST_STREAM' : 'LIVE');
        if (isAutoPlay) video.play().catch(() => {});
      });
      video.addEventListener('error', () => {
        setPlayerState('ERROR');
        scheduleReconnect();
      });
    } else {
      // Direct MP4 / HTTP progressive playback
      video.src = resolvedStreamUrl;
      video.load();
      video.addEventListener('playing', () => setPlayerState('LIVE'));
      video.addEventListener('error', () => {
        setPlayerState('ERROR');
        scheduleReconnect();
      });
    }
  }, [resolvedStreamUrl, isAutoPlay, isTestMode, destroyHls]);

  const handleNetworkError = (hls: Hls) => {
    if (reconnectAttempt < MAX_RECONNECT_ATTEMPTS) {
      setPlayerState('RECONNECTING');
      setReconnectAttempt((prev) => prev + 1);
      setTimeout(() => {
        hls.startLoad();
      }, 1500);
    } else {
      destroyHls();
      setPlayerState('OFFLINE');
      setErrorMessage('CCTV stream signal lost. Stream Gateway attempting upstream reconnect.');
    }
  };

  const scheduleReconnect = () => {
    if (reconnectAttempt < MAX_RECONNECT_ATTEMPTS) {
      setPlayerState('RECONNECTING');
      setReconnectAttempt((prev) => prev + 1);
      setTimeout(() => {
        initializePlayer();
      }, 2000 * Math.min(reconnectAttempt + 1, 3));
    } else {
      setPlayerState('OFFLINE');
      setErrorMessage('Camera stream offline. External CCTV source connection timed out.');
    }
  };

  useEffect(() => {
    if (resolvedStreamUrl && playerState !== 'SOURCE_CONFIG_REQUIRED') {
      initializePlayer();
    }
    return () => {
      destroyHls();
    };
  }, [resolvedStreamUrl, initializePlayer, destroyHls]);

  const handlePlayToggle = () => {
    const video = videoRef.current;
    if (!video) return;
    if (isPlaying) {
      video.pause();
      setIsPlaying(false);
    } else {
      video.play().catch(() => {});
      setIsPlaying(true);
    }
  };

  const handleMuteToggle = () => {
    const video = videoRef.current;
    if (!video) return;
    video.muted = !isMuted;
    setIsMuted(!isMuted);
  };

  const handleRefresh = () => {
    setReconnectAttempt(0);
    initializePlayer();
  };

  const handleFullscreen = () => {
    if (containerRef.current) {
      if (!document.fullscreenElement) {
        containerRef.current.requestFullscreen().catch(() => {});
      } else {
        document.exitFullscreen().catch(() => {});
      }
    }
  };

  const handleCaptureSnapshot = () => {
    const video = videoRef.current;
    if (!video) return;
    try {
      const canvas = document.createElement('canvas');
      canvas.width = video.videoWidth || 1280;
      canvas.height = video.videoHeight || 720;
      const ctx = canvas.getContext('2d');
      if (ctx) {
        ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
        const link = document.createElement('a');
        link.download = `EVIDENCE_${camera.camera_code || 'CAM'}_${Date.now()}.png`;
        link.href = canvas.toDataURL('image/png');
        link.click();
      }
    } catch {
      // Fallback
    }
  };

  return (
    <div className="camera-player-container relative" ref={containerRef}>
      {/* HTML5 Video Element with Full-Frame 100% Uncropped display */}
      <video
        ref={videoRef}
        className={`w-full h-full ${isFitContain ? 'object-contain' : 'object-cover'} bg-black`}
        playsInline
        muted={isMuted}
        autoPlay={isAutoPlay}
      />

      {/* Tactical HUD Header */}
      <div className="player-hud-top">
        <div className="hud-badge-left">
          <span className="hud-cam-code">{camera.camera_code || camera.name}</span>
          <span className="hud-district">{camera.district || 'GUJARAT POLICE'}</span>
        </div>

        <div className="hud-badge-right">
          {/* Live / Status Indicator */}
          {playerState === 'LIVE' && (
            <span className="status-badge-pill badge-live animate-pulse">
              <span className="live-dot" /> LIVE
            </span>
          )}
          {playerState === 'TEST_STREAM' && (
            <span className="status-badge-pill badge-test">
              <Layers size={11} className="mr-1" /> TEST FEED
            </span>
          )}
          {playerState === 'CONNECTING' && (
            <span className="status-badge-pill badge-connecting">
              <Loader2 size={11} className="animate-spin mr-1" /> CONNECTING
            </span>
          )}
          {playerState === 'RECONNECTING' && (
            <span className="status-badge-pill badge-warning">
              <RefreshCw size={11} className="animate-spin mr-1" /> RECONNECTING ({reconnectAttempt}/{MAX_RECONNECT_ATTEMPTS})
            </span>
          )}
          {playerState === 'SOURCE_CONFIG_REQUIRED' && (
            <span className="status-badge-pill badge-alert">
              <AlertCircle size={11} className="mr-1" /> CONFIG REQUIRED
            </span>
          )}
          {playerState === 'OFFLINE' && (
            <span className="status-badge-pill badge-offline">
              <WifiOff size={11} className="mr-1" /> NO SIGNAL
            </span>
          )}

          {/* Framing Mode Indicator */}
          <span className="status-badge-pill" style={{ background: 'rgba(15, 23, 42, 0.7)', border: '1px solid rgba(0, 240, 255, 0.3)', color: '#00f0ff', fontSize: '10px' }}>
            {isFitContain ? '100% FULL FRAME' : 'ZOOM FILL'}
          </span>

          {/* FPS & Latency Telemetry */}
          {(playerState === 'LIVE' || playerState === 'TEST_STREAM') && (
            <span className="hud-telemetry">
              {currentFps} FPS | {latencyMs}ms
            </span>
          )}
        </div>
      </div>

      {/* State Overlays */}
      {playerState === 'CONNECTING' && (
        <div className="player-overlay-state">
          <Loader2 size={36} className="text-cyan animate-spin mb-2" />
          <span className="overlay-msg">ESTABLISHING STREAM GATEWAY LINK...</span>
          <span className="overlay-sub">Resolving low-latency HLS pipeline</span>
        </div>
      )}

      {playerState === 'SOURCE_CONFIG_REQUIRED' && (
        <div className="player-overlay-state overlay-warning">
          <AlertCircle size={36} className="text-amber-400 mb-2" />
          <span className="overlay-msg">CCTV SOURCE CONFIGURATION REQUIRED</span>
          <span className="overlay-sub">
            Add live RTSP / HLS endpoint in <code>camera_sources.yaml</code> or external catalog.
          </span>
          <button onClick={handleRefresh} className="btn-retry-stream mt-3">
            <RefreshCw size={14} className="mr-1" /> Retry Stream Discovery
          </button>
        </div>
      )}

      {playerState === 'OFFLINE' && (
        <div className="player-overlay-state overlay-offline">
          <WifiOff size={36} className="text-slate-500 mb-2" />
          <span className="overlay-msg">CAMERA FEED OFFLINE</span>
          <span className="overlay-sub">{errorMessage || 'Upstream video feed is not transmitting.'}</span>
          <button onClick={handleRefresh} className="btn-retry-stream mt-3">
            <RefreshCw size={14} className="mr-1" /> Reconnect
          </button>
        </div>
      )}

      {playerState === 'ERROR' && (
        <div className="player-overlay-state overlay-error">
          <AlertCircle size={36} className="text-rose-500 mb-2" />
          <span className="overlay-msg">STREAM TRANSMISSION INTERRUPTED</span>
          <span className="overlay-sub">{errorMessage || 'Codec synchronization failed.'}</span>
          <button onClick={handleRefresh} className="btn-retry-stream mt-3">
            <RefreshCw size={14} className="mr-1" /> Retry Connection
          </button>
        </div>
      )}

      {/* Tactical Player Controls Bar */}
      <div className="player-controls-bar">
        <div className="controls-left">
          <button onClick={handlePlayToggle} className="ctrl-btn" title={isPlaying ? 'Pause Feed' : 'Play Feed'}>
            {isPlaying ? <Pause size={15} /> : <Play size={15} />}
          </button>

          <button onClick={handleMuteToggle} className="ctrl-btn" title={isMuted ? 'Unmute Audio' : 'Mute Audio'}>
            {isMuted ? <VolumeX size={15} /> : <Volume2 size={15} />}
          </button>

          <button onClick={handleRefresh} className="ctrl-btn" title="Refresh & Resync Stream">
            <RefreshCw size={15} />
          </button>

          <button onClick={handleCaptureSnapshot} className="ctrl-btn" title="Capture Evidentiary Snapshot">
            <CameraIcon size={15} />
          </button>

          {/* Aspect Ratio Framing Toggle (FIT 100% Uncropped vs FILL Zoomed) */}
          <button
            onClick={() => setIsFitContain(!isFitContain)}
            className="ctrl-btn"
            title={isFitContain ? 'Current: 100% Full Uncropped Frame (Contain). Click to Fill.' : 'Current: Zoomed Fill (Cover). Click for 100% Full Uncropped Frame.'}
            style={{ fontSize: '11px', fontWeight: 600, padding: '2px 6px', color: isFitContain ? '#00f0ff' : '#94a3b8' }}
          >
            {isFitContain ? 'FIT (100%)' : 'FILL (ZOOM)'}
          </button>
        </div>

        <div className="controls-right">
          {/* Quality Profile Selector */}
          <select
            value={selectedProfile}
            onChange={(e) => setSelectedProfile(e.target.value)}
            className="ctrl-profile-select"
            title="Bandwidth Profile"
          >
            <option value="LOW">LOW (480p)</option>
            <option value="MEDIUM">MED (720p)</option>
            <option value="HIGH">HIGH (1080p)</option>
            <option value="BURST_TRACKING">BURST (60fps)</option>
          </select>

          <button onClick={handleFullscreen} className="ctrl-btn" title="Fullscreen">
            <Maximize2 size={15} />
          </button>
        </div>
      </div>
    </div>
  );
};
