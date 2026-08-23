// PHANTOM CCTV Platform // Production TypeScript Definitions

export type SystemStatus = 'healthy' | 'degraded' | 'unhealthy' | 'unavailable';

export interface HealthResponse {
  status: string;
  timestamp: string;
  environment: string;
  version: string;
}

export interface ReadinessResponse {
  status: 'ready' | 'not_ready';
  timestamp: string;
  database: {
    connected: boolean;
    postgres_version?: string;
    postgis_version?: string;
    latency_ms?: number;
    error?: string;
  };
}

export interface SystemInfo {
  application: string;
  version: string;
  environment: string;
  api_prefix: string;
  timestamp: string;
  active_modules: string[];
}

export type CameraStatus = 'ONLINE' | 'OFFLINE' | 'DEGRADED' | 'MAINTENANCE' | 'UNKNOWN';
export type StreamProtocol = 'RTSP' | 'HLS' | 'WEBRTC' | 'ONVIF' | 'HTTP';
export type CameraType = 'FIXED' | 'PTZ' | 'DOME' | 'THERMAL' | 'ANPR' | 'MULTI_SENSOR';

export interface CameraStream {
  id?: string;
  camera_id: string;
  protocol: StreamProtocol;
  stream_url: string;
  resolution?: string;
  fps?: number;
  is_active: boolean;
  bitrate_kbps?: number;
}

export interface StreamSessionResponse {
  provider: string;
  camera_id: string;
  browser_playback_url: string;
  protocol: StreamProtocol;
  webrtc_fallback_url?: string;
  is_direct_browser_supported: boolean;
  session_id: string;
  timestamp: string;
}

export interface StreamHealthTelemetry {
  camera_id: string;
  status: 'LIVE' | 'OFFLINE';
  http_status: number;
  latency_ms?: number;
  fps: number;
  codec?: string;
  resolution?: string;
  last_frame_timestamp?: string;
  provider?: string;
  error?: string;
}

export interface Camera {
  id: string;
  camera_code: string;
  name: string;
  department_id?: string;
  department_name?: string;
  district?: string;
  taluka?: string;
  city?: string;
  latitude: number;
  longitude: number;
  camera_type: CameraType;
  status: CameraStatus;
  ip_address?: string;
  is_ptz_capable: boolean;
  ai_enabled: boolean;
  location_description?: string;
  last_heartbeat?: string;
  fps?: number;
  streams?: CameraStream[];
}

export interface District {
  id: string;
  district_code: string;
  name: string;
  state: string;
  zone?: string;
  headquarters?: string;
  centroid_lat: number;
  centroid_lng: number;
  camera_count?: number;
  is_active: boolean;
}

export interface Department {
  id: string;
  code: string;
  name: string;
  description?: string;
  contact_email?: string;
  contact_phone?: string;
  is_active: boolean;
  total_cameras?: number;
}

export interface CoverageGapsAnalysis {
  statewide_summary: CameraCoverage;
  district_density: Array<{
    district: string;
    total_cameras: number;
    online_cameras: number;
    offline_cameras: number;
    avg_lat: number;
    avg_lng: number;
    coverage_density_level: 'HIGH' | 'MEDIUM' | 'LOW';
  }>;
  offline_hotspots: Array<{
    district: string;
    city: string;
    location_name: string;
    latitude: number;
    longitude: number;
    offline_count: number;
  }>;
  low_coverage_zones: Array<any>;
  calculation_methodology: string;
  timestamp: string;
}

export interface BulkImportResult {
  total_rows: number;
  successful: number;
  failed: number;
  errors: Array<{
    row: number;
    field?: string;
    error: string;
    data?: any;
  }>;
  imported_camera_codes: string[];
}

export interface CameraCoverage {
  total_cameras: number;
  operational_cameras: number;
  offline_cameras: number;
  maintenance_cameras: number;
  departments_count: number;
  districts_count: number;
  by_department: Record<string, number>;
  by_district: Record<string, number>;
  online_percentage?: number;
}

export type AlertSeverity = 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW' | 'INFO';
export type AlertStatus = 'NEW' | 'ACKNOWLEDGED' | 'IN_PROGRESS' | 'RESOLVED' | 'DISMISSED';

export interface Alert {
  id: string;
  alert_code: string;
  title: string;
  description?: string;
  severity: AlertSeverity;
  status: AlertStatus;
  event_type: string;
  camera_id?: string;
  camera_name?: string;
  district?: string;
  location?: string;
  confidence: number;
  entity_id?: string;
  entity_type?: string;
  created_at: string;
  acknowledged_at?: string;
  resolved_at?: string;
  assigned_to?: string;
  notes?: string;
}

export interface ANPRRecord {
  id: string;
  plate_number: string;
  raw_plate_text?: string;
  confidence: number;
  vehicle_type?: string;
  vehicle_color?: string;
  vehicle_make?: string;
  camera_id: string;
  camera_name: string;
  district?: string;
  latitude?: number;
  longitude?: number;
  speed_kmh?: number;
  matched_watchlist: boolean;
  watchlist_type?: string;
  timestamp: string;
  snapshot_url?: string;
}

export interface WatchlistEntry {
  id: string;
  watchlist_type: 'STOLEN_VEHICLE' | 'SUSPECT_VEHICLE' | 'WANTED_PERSON' | 'VIP' | 'CUSTOM';
  identifier_value: string;
  reason: string;
  severity: AlertSeverity;
  fir_number?: string;
  requesting_agency?: string;
  valid_from: string;
  valid_until?: string;
  is_active: boolean;
  created_at: string;
}

export interface Incident {
  id: string;
  incident_number: string;
  title: string;
  severity: AlertSeverity;
  status: 'OPEN' | 'UNDER_INVESTIGATION' | 'ESCALATED' | 'CLOSED';
  lead_investigator?: string;
  district?: string;
  alerts_count: number;
  evidence_count: number;
  created_at: string;
  summary: string;
  primary_camera_id?: string;
}

export interface AuditLog {
  id: string;
  action: string;
  user_id: string;
  username: string;
  ip_address: string;
  timestamp: string;
  details?: Record<string, unknown>;
  severity?: string;
}

export interface ApiResponse<T> {
  success: boolean;
  data: T;
  request_id?: string;
  message?: string;
}

export interface PaginatedResponse<T> {
  success: boolean;
  data: T[];
  meta: {
    total_count: number;
    page: number;
    page_size: number;
    total_pages: number;
  };
}
