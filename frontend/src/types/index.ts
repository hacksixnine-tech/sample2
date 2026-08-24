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

export interface SightingDetail {
  sighting_id?: string;
  camera_id: string;
  camera_name?: string;
  source_camera_id?: string;
  district?: string;
  location_name?: string;
  latitude?: number;
  longitude?: number;
  timestamp: string;
  plate_confidence?: number;
  vehicle_confidence?: number;
  evidence_reference?: string;
  alert_reference?: string;
  frame_reference?: string;
  is_demo?: boolean;
  transition_distance_meters?: number;
  transition_time_seconds?: number;
  estimated_speed_kmph?: number;
  speed_label?: string;
  anomaly_flag?: string;
  matched_watchlist?: boolean;
  watchlist_type?: string;
  alert_id?: string;
  incident_id?: string;
}

export interface VehicleMovementHistory {
  vehicle_id: string;
  normalized_plate: string;
  raw_plate: string;
  vehicle_type?: string;
  first_seen?: string;
  last_seen?: string;
  sighting_count: number;
  unique_camera_count: number;
  unique_district_count: number;
  sort_order: 'asc' | 'desc';
  sightings: SightingDetail[];
}

export interface VehicleSummary {
  vehicle_id: string;
  normalized_plate: string;
  raw_plate: string;
  vehicle_type?: string;
  make?: string;
  model?: string;
  color?: string;
  owner_name?: string;
  first_seen?: string;
  last_seen?: string;
  total_sightings: number;
  unique_cameras: number;
  unique_districts: number;
  watchlist_matches_count: number;
  alerts_count: number;
  watchlist_status: 'CLEAR' | 'MATCH';
  highest_risk_level?: AlertSeverity;
  investigation_status: 'OPEN' | 'UNDER_REVIEW' | 'WATCH' | 'RESOLVED' | 'ARCHIVED';
  average_transition_speed_kmph?: number;
  speed_disclaimer: string;
  is_demo?: boolean;
}

export interface RoutePoint {
  sequence: number;
  camera_id: string;
  camera_name?: string;
  source_camera_id?: string;
  district?: string;
  city?: string;
  latitude: number;
  longitude: number;
  timestamp: string;
  straight_line_distance_prev_meters?: number;
  time_delta_prev_seconds?: number;
  geographic_speed_kmph?: number;
  speed_label?: string;
  anomaly_flag?: string;
}

export interface VehicleRoute {
  vehicle_id: string;
  normalized_plate: string;
  route_type: string;
  point_count: number;
  first_seen?: string;
  last_seen?: string;
  total_geographic_distance_meters: number;
  unique_camera_count: number;
  unique_district_count: number;
  points: RoutePoint[];
  anomalies_detected: Array<{
    anomaly_type: string;
    severity: string;
    description: string;
    camera_id?: string;
    timestamp?: string;
    speed_kmph?: number;
  }>;
}

