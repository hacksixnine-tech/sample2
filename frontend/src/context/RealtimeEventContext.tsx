import React, { createContext, useContext, useEffect, useState, useRef, useCallback } from 'react';
import { API_BASE_URL } from '../api/client';

export type RealtimeConnectionStatus = 'CONNECTED' | 'RECONNECTING' | 'OFFLINE';

export interface EventEnvelope {
  event_id: string;
  event_type: string;
  timestamp: string;
  source: string;
  camera_id?: string;
  district?: string;
  severity?: string;
  entity_type?: string;
  entity_id?: string;
  payload: Record<string, any>;
  created_at: string;
}

export interface NotificationItem {
  id: string;
  event_id: string;
  title: string;
  message: string;
  severity: 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW' | 'INFO';
  timestamp: string;
  camera_id?: string;
  district?: string;
  isRead: boolean;
}

interface RealtimeEventContextType {
  connectionStatus: RealtimeConnectionStatus;
  events: EventEnvelope[];
  latestEvent: EventEnvelope | null;
  notifications: NotificationItem[];
  unreadCount: number;
  isSoundEnabled: boolean;
  toggleSound: () => void;
  markAllAsRead: () => void;
  clearNotifications: () => void;
  sendTestEvent: (eventType: string, severity?: string) => Promise<void>;
  lastHeartbeat: Date | null;
}

const RealtimeEventContext = createContext<RealtimeEventContextType | undefined>(undefined);

// Web Audio API Audio Synthesizer for tactical sounds
const playTacticalChime = (severity: string) => {
  try {
    const AudioContextClass = window.AudioContext || (window as any).webkitAudioContext;
    if (!AudioContextClass) return;
    const ctx = new AudioContextClass();

    if (severity === 'CRITICAL') {
      // Prominent two-tone emergency siren chime
      const osc1 = ctx.createOscillator();
      const osc2 = ctx.createOscillator();
      const gain = ctx.createGain();

      osc1.type = 'sawtooth';
      osc2.type = 'sine';

      osc1.frequency.setValueAtTime(880, ctx.currentTime); // A5
      osc1.frequency.exponentialRampToValueAtTime(440, ctx.currentTime + 0.3);

      osc2.frequency.setValueAtTime(1200, ctx.currentTime);
      osc2.frequency.exponentialRampToValueAtTime(600, ctx.currentTime + 0.3);

      gain.gain.setValueAtTime(0.2, ctx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.01, ctx.currentTime + 0.35);

      osc1.connect(gain);
      osc2.connect(gain);
      gain.connect(ctx.destination);

      osc1.start();
      osc2.start();
      osc1.stop(ctx.currentTime + 0.35);
      osc2.stop(ctx.currentTime + 0.35);
    } else if (severity === 'HIGH') {
      // High alert chime
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();
      osc.type = 'sine';
      osc.frequency.setValueAtTime(659.25, ctx.currentTime); // E5
      osc.frequency.setValueAtTime(880, ctx.currentTime + 0.1); // A5
      gain.gain.setValueAtTime(0.15, ctx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.01, ctx.currentTime + 0.25);

      osc.connect(gain);
      gain.connect(ctx.destination);
      osc.start();
      osc.stop(ctx.currentTime + 0.25);
    }
  } catch (err) {
    // Ignore audio restriction errors
  }
};

export const RealtimeEventProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [connectionStatus, setConnectionStatus] = useState<RealtimeConnectionStatus>('OFFLINE');
  const [events, setEvents] = useState<EventEnvelope[]>([]);
  const [latestEvent, setLatestEvent] = useState<EventEnvelope | null>(null);
  const [notifications, setNotifications] = useState<NotificationItem[]>([]);
  const [lastHeartbeat, setLastHeartbeat] = useState<Date | null>(null);
  const [isSoundEnabled, setIsSoundEnabled] = useState<boolean>(() => {
    return localStorage.getItem('phantom_sound_enabled') !== 'false';
  });

  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<any>(null);
  const reconnectAttemptsRef = useRef<number>(0);
  const seenEventIdsRef = useRef<Set<string>>(new Set());
  const lastEventTimestampRef = useRef<string | null>(null);

  const toggleSound = useCallback(() => {
    setIsSoundEnabled((prev) => {
      const next = !prev;
      localStorage.setItem('phantom_sound_enabled', String(next));
      return next;
    });
  }, []);

  const markAllAsRead = useCallback(() => {
    setNotifications((prev) => prev.map((n) => ({ ...n, isRead: true })));
  }, []);

  const clearNotifications = useCallback(() => {
    setNotifications([]);
  }, []);

  // Process incoming event envelope
  const handleEventEnvelope = useCallback((env: EventEnvelope) => {
    if (!env || !env.event_id) return;

    // Deduplication check
    if (seenEventIdsRef.current.has(env.event_id)) {
      return;
    }
    seenEventIdsRef.current.add(env.event_id);
    if (seenEventIdsRef.current.size > 2000) {
      // Prevent memory bloat
      const firstItems = Array.from(seenEventIdsRef.current).slice(0, 500);
      firstItems.forEach((id) => seenEventIdsRef.current.delete(id));
    }

    lastEventTimestampRef.current = env.timestamp;
    setLatestEvent(env);
    setEvents((prev) => [env, ...prev.slice(0, 199)]);

    // Notification synthesis
    const sev = (env.severity || 'INFO').toUpperCase() as any;
    const title = env.payload?.title || env.event_type.replace(/_/g, ' ');
    const msg =
      env.payload?.message ||
      env.payload?.description ||
      (env.payload?.plate_number ? `Plate: ${env.payload.plate_number}` : 'Operational event recorded.');

    const newNotif: NotificationItem = {
      id: env.event_id,
      event_id: env.event_id,
      title,
      message: msg,
      severity: ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW', 'INFO'].includes(sev) ? sev : 'INFO',
      timestamp: env.timestamp,
      camera_id: env.camera_id,
      district: env.district,
      isRead: false,
    };

    setNotifications((prev) => [newNotif, ...prev.slice(0, 99)]);

    // Play tactical sound if sound is on and high severity
    if (isSoundEnabled && (sev === 'CRITICAL' || sev === 'HIGH')) {
      playTacticalChime(sev);
    }
  }, [isSoundEnabled]);

  // Connect WebSocket
  const connectWebSocket = useCallback(() => {
    if (wsRef.current && (wsRef.current.readyState === WebSocket.OPEN || wsRef.current.readyState === WebSocket.CONNECTING)) {
      return;
    }

    setConnectionStatus('RECONNECTING');

    // Build ws URL from API_BASE_URL
    const wsBase = API_BASE_URL.replace(/^http/, 'ws');
    const wsUrl = `${wsBase}/events/ws`;

    try {
      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      ws.onopen = () => {
        setConnectionStatus('CONNECTED');
        reconnectAttemptsRef.current = 0;
        setLastHeartbeat(new Date());

        // Recover missed events if we have a last known timestamp
        if (lastEventTimestampRef.current) {
          fetch(`${API_BASE_URL}/events/history?since=${encodeURIComponent(lastEventTimestampRef.current)}`)
            .then((r) => r.json())
            .then((res) => {
              if (res && res.success && res.data?.events) {
                res.data.events.forEach((e: EventEnvelope) => handleEventEnvelope(e));
              }
            })
            .catch(() => {});
        }
      };

      ws.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data);
          if (message.type === 'HEARTBEAT') {
            setLastHeartbeat(new Date());
            // Reply with ping
            ws.send(JSON.stringify({ type: 'PING' }));
          } else if (message.type === 'PONG') {
            setLastHeartbeat(new Date());
          } else if (message.type === 'EVENT' && message.data) {
            handleEventEnvelope(message.data);
          } else if (message.type === 'ALERT_NOTIFICATION' && message.data) {
            // Backwards compatibility with /alerts/ws
            handleEventEnvelope({
              event_id: message.data.alert_id || message.data.id || String(Date.now()),
              event_type: 'ALERT_CREATED',
              timestamp: new Date().toISOString(),
              source: 'alert-engine',
              severity: message.data.severity || 'HIGH',
              camera_id: message.data.camera_id,
              payload: message.data,
              created_at: new Date().toISOString(),
            });
          }
        } catch (err) {
          // Ignore json parse error
        }
      };

      ws.onerror = () => {
        // Handled by onclose
      };

      ws.onclose = () => {
        setConnectionStatus('OFFLINE');
        wsRef.current = null;

        // Exponential backoff reconnect: 1s, 2s, 4s, 8s, max 30s
        const backoffMs = Math.min(1000 * Math.pow(2, reconnectAttemptsRef.current), 30000);
        reconnectAttemptsRef.current += 1;

        if (reconnectTimeoutRef.current) {
          clearTimeout(reconnectTimeoutRef.current);
        }
        reconnectTimeoutRef.current = setTimeout(() => {
          connectWebSocket();
        }, backoffMs);
      };
    } catch (err) {
      setConnectionStatus('OFFLINE');
    }
  }, [handleEventEnvelope]);

  useEffect(() => {
    connectWebSocket();

    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [connectWebSocket]);

  const sendTestEvent = useCallback(async (eventType: string, severity = 'CRITICAL') => {
    try {
      const res = await fetch(`${API_BASE_URL}/events/test-event`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          event_type: eventType,
          severity,
          entity_id: 'GJ05AB1234',
          camera_id: 'CAM-014 (Surat Ring Road)',
          district: 'Surat',
          payload: {
            title: `Live ${eventType.replace(/_/g, ' ')}`,
            message: `Real-time test broadcast for ${eventType} (Vehicle: GJ05AB1234).`,
            plate_number: 'GJ05AB1234',
            camera_name: 'CAM-014 (Surat Ring Road)',
            district: 'Surat',
            severity,
          },
        }),
      });
      const json = await res.json();
      if (json.success && json.data) {
        handleEventEnvelope(json.data);
      }
    } catch (err) {
      console.error('Failed to trigger test event:', err);
    }
  }, [handleEventEnvelope]);

  const unreadCount = notifications.filter((n) => !n.isRead).length;

  return (
    <RealtimeEventContext.Provider
      value={{
        connectionStatus,
        events,
        latestEvent,
        notifications,
        unreadCount,
        isSoundEnabled,
        toggleSound,
        markAllAsRead,
        clearNotifications,
        sendTestEvent,
        lastHeartbeat,
      }}
    >
      {children}
    </RealtimeEventContext.Provider>
  );
};

export const useRealtimeEvents = () => {
  const context = useContext(RealtimeEventContext);
  if (!context) {
    throw new Error('useRealtimeEvents must be used within a RealtimeEventProvider');
  }
  return context;
};
