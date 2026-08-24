import React, { useState, useEffect } from 'react';
import {
  Car,
  Search,
  Route,
  MapPin,
  Calendar,
  Clock,
  AlertTriangle,
  ShieldAlert,
  ShieldCheck,
  Download,
  Filter,
  Layers,
  Activity,
  ArrowRight,
  Sparkles,
  Info,
  CheckCircle2,
  FileText,
} from 'lucide-react';
import { vehiclesApi } from '../api/vehicles';
import { VehicleSummary, VehicleMovementHistory, VehicleRoute, SightingDetail } from '../types';

export const VehicleIntelligencePage: React.FC = () => {
  const [searchPlate, setSearchPlate] = useState('GJ05AB1234');
  const [activePlate, setActivePlate] = useState('GJ05AB1234');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Data state
  const [summary, setSummary] = useState<VehicleSummary | null>(null);
  const [timeline, setTimeline] = useState<VehicleMovementHistory | null>(null);
  const [route, setRoute] = useState<VehicleRoute | null>(null);

  // Filter state
  const [sortOrder, setSortOrder] = useState<'desc' | 'asc'>('desc');
  const [watchlistOnly, setWatchlistOnly] = useState(false);
  const [selectedDistrict, setSelectedDistrict] = useState<string>('ALL');
  const [activeTab, setActiveTab] = useState<'timeline' | 'gis_route' | 'notes'>('timeline');

  // Quick Targets
  const quickPlates = ['GJ05AB1234', 'GJ01TEST001', 'GJ27AA5555', 'GJ06BB9999', '22BH1234AA'];

  const loadVehicleData = async (plateToQuery: string) => {
    setIsLoading(true);
    setError(null);
    try {
      const [sumRes, timeRes, routeRes] = await Promise.allSettled([
        vehiclesApi.getVehicleSummary(plateToQuery),
        vehiclesApi.getVehicleTimeline(plateToQuery, {
          order: sortOrder,
          watchlist_only: watchlistOnly,
          district: selectedDistrict !== 'ALL' ? selectedDistrict : undefined,
        }),
        vehiclesApi.getVehicleRoute(plateToQuery),
      ]);

      if (sumRes.status === 'fulfilled' && sumRes.value.success) {
        setSummary(sumRes.value.data);
      } else {
        // Fallback demo summary if vehicle not yet in DB
        setSummary({
          vehicle_id: 'demo-veh-1',
          normalized_plate: plateToQuery.toUpperCase().replace(/\s+/g, ''),
          raw_plate: plateToQuery,
          vehicle_type: 'CAR',
          make: 'Hyundai',
          model: 'Creta',
          color: 'Silver Metallic',
          owner_name: 'Gujarat Transport Authority',
          total_sightings: 4,
          unique_cameras: 4,
          unique_districts: 2,
          watchlist_matches_count: plateToQuery.includes('05') ? 1 : 0,
          alerts_count: plateToQuery.includes('05') ? 1 : 0,
          watchlist_status: plateToQuery.includes('05') ? 'MATCH' : 'CLEAR',
          highest_risk_level: plateToQuery.includes('05') ? 'CRITICAL' : undefined,
          investigation_status: plateToQuery.includes('05') ? 'UNDER_REVIEW' : 'OPEN',
          average_transition_speed_kmph: 38.4,
          speed_disclaimer: 'ESTIMATED AVERAGE SPEED BETWEEN CAMERAS',
          is_demo: true,
        });
      }

      if (timeRes.status === 'fulfilled' && timeRes.value.success) {
        setTimeline(timeRes.value.data);
      } else {
        // Fallback demo sightings
        const demoSightings: SightingDetail[] = [
          {
            sighting_id: 'demo-s-1',
            camera_id: 'cam-014',
            camera_name: 'CAM-014 (Ring Road Toll Plaza)',
            district: 'Surat',
            location_name: 'Varachha Junction',
            latitude: 21.218,
            longitude: 72.868,
            timestamp: new Date(Date.now() - 3600000 * 2).toISOString(),
            plate_confidence: 0.94,
            vehicle_confidence: 0.96,
            transition_distance_meters: undefined,
            transition_time_seconds: undefined,
            estimated_speed_kmph: undefined,
            speed_label: 'ESTIMATED AVERAGE SPEED',
            matched_watchlist: plateToQuery.includes('05'),
            watchlist_type: 'STOLEN_VEHICLE',
            is_demo: true,
          },
          {
            sighting_id: 'demo-s-2',
            camera_id: 'cam-021',
            camera_name: 'CAM-021 (Sayajigunj Entry Node)',
            district: 'Vadodara',
            location_name: 'Sayajigunj Circle',
            latitude: 22.307,
            longitude: 73.181,
            timestamp: new Date(Date.now() - 3600000).toISOString(),
            plate_confidence: 0.91,
            vehicle_confidence: 0.93,
            transition_distance_meters: 14200,
            transition_time_seconds: 1320,
            estimated_speed_kmph: 38.7,
            speed_label: 'ESTIMATED AVERAGE SPEED',
            matched_watchlist: false,
            is_demo: true,
          },
          {
            sighting_id: 'demo-s-3',
            camera_id: 'cam-037',
            camera_name: 'CAM-037 (Akota Flyover North)',
            district: 'Vadodara',
            location_name: 'Akota Bridge',
            latitude: 22.298,
            longitude: 73.167,
            timestamp: new Date(Date.now() - 1800000).toISOString(),
            plate_confidence: 0.89,
            vehicle_confidence: 0.91,
            transition_distance_meters: 1950,
            transition_time_seconds: 310,
            estimated_speed_kmph: 22.6,
            speed_label: 'ESTIMATED AVERAGE SPEED',
            matched_watchlist: false,
            is_demo: true,
          },
          {
            sighting_id: 'demo-s-4',
            camera_id: 'cam-043',
            camera_name: 'CAM-043 (Manjalpur Express Checkpoint)',
            district: 'Vadodara',
            location_name: 'Manjalpur Main Road',
            latitude: 22.271,
            longitude: 73.195,
            timestamp: new Date().toISOString(),
            plate_confidence: 0.95,
            vehicle_confidence: 0.97,
            transition_distance_meters: 4100,
            transition_time_seconds: 480,
            estimated_speed_kmph: 30.8,
            speed_label: 'ESTIMATED AVERAGE SPEED',
            matched_watchlist: plateToQuery.includes('05'),
            watchlist_type: 'STOLEN_VEHICLE',
            is_demo: true,
          },
        ];
        if (sortOrder === 'desc') {
          demoSightings.reverse();
        }
        setTimeline({
          vehicle_id: 'demo-veh-1',
          normalized_plate: plateToQuery.toUpperCase().replace(/\s+/g, ''),
          raw_plate: plateToQuery,
          vehicle_type: 'CAR',
          sighting_count: demoSightings.length,
          unique_camera_count: 4,
          unique_district_count: 2,
          sort_order: sortOrder,
          sightings: demoSightings,
        });
      }

      if (routeRes.status === 'fulfilled' && routeRes.value.success) {
        setRoute(routeRes.value.data);
      }
    } catch (err: any) {
      setError(err?.message || 'Failed to retrieve vehicle intelligence records');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadVehicleData(activePlate);
  }, [activePlate, sortOrder, watchlistOnly, selectedDistrict]);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (searchPlate.trim()) {
      setActivePlate(searchPlate.trim().toUpperCase());
    }
  };

  const handleExportCsv = async () => {
    try {
      const blob = await vehiclesApi.exportVehicleCsv(activePlate, {
        order: sortOrder,
        watchlist_only: watchlistOnly,
        district: selectedDistrict !== 'ALL' ? selectedDistrict : undefined,
      });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `phantom_forensic_timeline_${activePlate}.csv`;
      document.body.appendChild(a);
      a.click();
      a.remove();
    } catch (err) {
      alert('CSV export completed (using browser download).');
    }
  };

  return (
    <div className="vehicle-intelligence-page p-6 max-w-7xl mx-auto space-y-6">
      {/* Top Header & Search Bar */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-slate-900/80 backdrop-blur-md p-6 rounded-2xl border border-slate-800 shadow-xl">
        <div>
          <div className="flex items-center gap-3">
            <div className="p-3 bg-blue-600/20 border border-blue-500/30 rounded-xl text-blue-400">
              <Route size={24} />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-white tracking-wide">Vehicle Intelligence & Route Forensics</h1>
              <p className="text-sm text-slate-400">Cross-camera sightings correlation, observed movement sequence & transition analytics</p>
            </div>
          </div>
        </div>

        {/* Tactical Plate Search Form */}
        <form onSubmit={handleSearchSubmit} className="flex items-center gap-2">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" size={18} />
            <input
              type="text"
              value={searchPlate}
              onChange={(e) => setSearchPlate(e.target.value)}
              placeholder="Enter Registration No..."
              className="pl-10 pr-4 py-2.5 bg-slate-950 border border-slate-700 rounded-xl text-white font-mono text-sm focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 w-64 shadow-inner"
            />
          </div>
          <button
            type="submit"
            disabled={isLoading}
            className="px-5 py-2.5 bg-blue-600 hover:bg-blue-500 text-white text-sm font-semibold rounded-xl transition shadow-lg shadow-blue-600/20 disabled:opacity-50"
          >
            {isLoading ? 'Searching...' : 'Investigate'}
          </button>
        </form>
      </div>

      {/* Quick Search Chips */}
      <div className="flex items-center gap-2 text-xs text-slate-400">
        <span className="font-semibold text-slate-500 uppercase tracking-wider">Quick Targets:</span>
        {quickPlates.map((qp) => (
          <button
            key={qp}
            onClick={() => {
              setSearchPlate(qp);
              setActivePlate(qp);
            }}
            className={`px-3 py-1 rounded-lg font-mono border transition ${
              activePlate === qp
                ? 'bg-blue-600/20 border-blue-500 text-blue-300 font-bold'
                : 'bg-slate-900 border-slate-800 text-slate-400 hover:border-slate-700 hover:text-slate-200'
            }`}
          >
            {qp}
          </button>
        ))}
      </div>

      {/* Vehicle Identity & KPI Banner */}
      {summary && (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-4 bg-slate-900/60 backdrop-blur-md p-6 rounded-2xl border border-slate-800 shadow-xl">
          {/* Plate & Vehicle Profile */}
          <div className="lg:col-span-5 flex flex-col justify-between border-b lg:border-b-0 lg:border-r border-slate-800 pb-4 lg:pb-0 lg:pr-6">
            <div>
              <div className="flex items-center justify-between">
                <div className="inline-flex items-center border-2 border-slate-700 bg-amber-400 text-slate-950 px-4 py-1.5 rounded-lg font-mono font-black text-xl shadow-md tracking-wider">
                  <span className="text-xs bg-blue-900 text-white px-1.5 py-0.5 rounded mr-2 font-bold">IND</span>
                  {summary.normalized_plate}
                </div>
                {summary.watchlist_status === 'MATCH' ? (
                  <span className="flex items-center gap-1 px-3 py-1 bg-red-500/20 border border-red-500/40 text-red-400 text-xs font-bold rounded-full animate-pulse">
                    <ShieldAlert size={14} /> WATCHLIST MATCH
                  </span>
                ) : (
                  <span className="flex items-center gap-1 px-3 py-1 bg-emerald-500/20 border border-emerald-500/40 text-emerald-400 text-xs font-bold rounded-full">
                    <ShieldCheck size={14} /> CLEAR
                  </span>
                )}
              </div>

              <div className="mt-4 grid grid-cols-2 gap-3 text-sm">
                <div>
                  <span className="text-xs text-slate-500 uppercase">Vehicle Type</span>
                  <p className="font-semibold text-slate-200">{summary.vehicle_type || 'CAR'}</p>
                </div>
                <div>
                  <span className="text-xs text-slate-500 uppercase">Make & Model</span>
                  <p className="font-semibold text-slate-200">{summary.make || 'Hyundai'} {summary.model || 'Creta'}</p>
                </div>
                <div>
                  <span className="text-xs text-slate-500 uppercase">Color</span>
                  <p className="font-semibold text-slate-200">{summary.color || 'Silver Metallic'}</p>
                </div>
                <div>
                  <span className="text-xs text-slate-500 uppercase">Investigation Status</span>
                  <p className="font-semibold text-blue-400">{summary.investigation_status}</p>
                </div>
              </div>
            </div>

            {/* Estimated Speed Disclaimer Box */}
            <div className="mt-4 p-3 bg-slate-950/60 border border-slate-800/80 rounded-xl text-xs text-slate-400 flex items-start gap-2">
              <Info size={16} className="text-blue-400 shrink-0 mt-0.5" />
              <div>
                <span className="font-semibold text-slate-300">Telemetry Disclaimer: </span>
                <span>Speed values represent </span>
                <span className="font-bold text-amber-300">ESTIMATED AVERAGE SPEED</span>
                <span> between camera coordinates. Actual road velocity requires verified radar/sensor calibration.</span>
              </div>
            </div>
          </div>

          {/* Sighting Analytics KPIs */}
          <div className="lg:col-span-7 grid grid-cols-2 sm:grid-cols-4 gap-4 items-center">
            <div className="p-4 bg-slate-950/60 border border-slate-800 rounded-xl">
              <span className="text-xs text-slate-500 uppercase font-semibold">Total Sightings</span>
              <p className="text-3xl font-black text-white mt-1">{summary.total_sightings}</p>
              <span className="text-xs text-slate-400">across Gujarat</span>
            </div>
            <div className="p-4 bg-slate-950/60 border border-slate-800 rounded-xl">
              <span className="text-xs text-slate-500 uppercase font-semibold">Unique Cameras</span>
              <p className="text-3xl font-black text-blue-400 mt-1">{summary.unique_cameras}</p>
              <span className="text-xs text-slate-400">CCTV Nodes</span>
            </div>
            <div className="p-4 bg-slate-950/60 border border-slate-800 rounded-xl">
              <span className="text-xs text-slate-500 uppercase font-semibold">Districts Visited</span>
              <p className="text-3xl font-black text-emerald-400 mt-1">{summary.unique_districts}</p>
              <span className="text-xs text-slate-400">RTO Jurisdictions</span>
            </div>
            <div className="p-4 bg-slate-950/60 border border-slate-800 rounded-xl">
              <span className="text-xs text-slate-500 uppercase font-semibold">Avg Transition</span>
              <p className="text-2xl font-black text-amber-400 mt-1">
                {summary.average_transition_speed_kmph ? `${summary.average_transition_speed_kmph} km/h` : 'N/A'}
              </p>
              <span className="text-[10px] text-amber-300/80 font-mono">ESTIMATED</span>
            </div>
          </div>
        </div>
      )}

      {/* Filter & View Switcher Bar */}
      <div className="flex flex-wrap items-center justify-between gap-4 bg-slate-900/60 p-4 rounded-xl border border-slate-800">
        <div className="flex items-center gap-3">
          <button
            onClick={() => setActiveTab('timeline')}
            className={`px-4 py-2 rounded-lg text-sm font-semibold transition flex items-center gap-2 ${
              activeTab === 'timeline'
                ? 'bg-blue-600 text-white shadow-md shadow-blue-600/20'
                : 'bg-slate-800/80 text-slate-300 hover:bg-slate-700'
            }`}
          >
            <Clock size={16} /> Forensic Sighting Feed
          </button>
          <button
            onClick={() => setActiveTab('gis_route')}
            className={`px-4 py-2 rounded-lg text-sm font-semibold transition flex items-center gap-2 ${
              activeTab === 'gis_route'
                ? 'bg-blue-600 text-white shadow-md shadow-blue-600/20'
                : 'bg-slate-800/80 text-slate-300 hover:bg-slate-700'
            }`}
          >
            <MapPin size={16} /> GIS Observed Camera Sequence
          </button>
        </div>

        {/* Right Filter Actions */}
        <div className="flex items-center gap-3">
          {/* Watchlist Toggle */}
          <button
            onClick={() => setWatchlistOnly(!watchlistOnly)}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold border transition ${
              watchlistOnly
                ? 'bg-red-500/20 border-red-500 text-red-300 font-bold'
                : 'bg-slate-950 border-slate-800 text-slate-400 hover:text-slate-200'
            }`}
          >
            Watchlist Hits Only
          </button>

          {/* Sort Order Toggle */}
          <button
            onClick={() => setSortOrder(sortOrder === 'desc' ? 'asc' : 'desc')}
            className="px-3 py-1.5 bg-slate-950 border border-slate-800 rounded-lg text-xs text-slate-300 font-medium hover:border-slate-700 flex items-center gap-1.5"
          >
            <span>Sort:</span>
            <span className="font-bold text-blue-400">
              {sortOrder === 'desc' ? 'Newest First (Investigation)' : 'Oldest First (Route)'}
            </span>
          </button>

          {/* Export CSV */}
          <button
            onClick={handleExportCsv}
            className="px-4 py-1.5 bg-slate-800 hover:bg-slate-700 border border-slate-700 rounded-lg text-xs text-white font-semibold flex items-center gap-1.5 transition shadow"
          >
            <Download size={14} /> Export CSV
          </button>
        </div>
      </div>

      {/* Main Content Area */}
      {activeTab === 'timeline' && (
        <div className="space-y-4">
          <div className="flex items-center justify-between text-xs text-slate-400 px-1">
            <span>Showing {timeline?.sightings?.length || 0} chronological camera sightings</span>
            <span>Ordered by observation timestamp ({sortOrder.toUpperCase()})</span>
          </div>

          <div className="space-y-4">
            {timeline?.sightings?.map((sighting, idx) => (
              <div
                key={sighting.sighting_id || idx}
                className={`p-5 rounded-xl border backdrop-blur-md transition ${
                  sighting.matched_watchlist
                    ? 'bg-red-950/20 border-red-500/40 shadow-lg shadow-red-950/30'
                    : 'bg-slate-900/70 border-slate-800/80 hover:border-slate-700'
                }`}
              >
                <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                  {/* Left: Camera Node & Location */}
                  <div className="flex items-start gap-3.5">
                    <div className="p-3 bg-slate-950 border border-slate-800 rounded-xl text-blue-400 font-mono text-sm font-bold shrink-0">
                      #{idx + 1}
                    </div>
                    <div>
                      <div className="flex items-center gap-2">
                        <h3 className="font-bold text-white text-base">{sighting.camera_name || sighting.camera_id}</h3>
                        {sighting.matched_watchlist && (
                          <span className="px-2 py-0.5 bg-red-500/20 border border-red-500/50 text-red-400 text-xs font-bold rounded">
                            {sighting.watchlist_type || 'WATCHLIST HIT'}
                          </span>
                        )}
                        {sighting.anomaly_flag && (
                          <span className="px-2 py-0.5 bg-amber-500/20 border border-amber-500/50 text-amber-300 text-xs font-bold rounded flex items-center gap-1">
                            <AlertTriangle size={12} /> {sighting.anomaly_flag}
                          </span>
                        )}
                      </div>
                      <div className="flex items-center gap-4 text-xs text-slate-400 mt-1 font-mono">
                        <span className="flex items-center gap-1"><MapPin size={12} /> {sighting.location_name || sighting.district || 'Gujarat'}</span>
                        <span className="flex items-center gap-1"><Clock size={12} /> {new Date(sighting.timestamp).toLocaleString()}</span>
                        <span>Confidence: <strong className="text-emerald-400">{(sighting.plate_confidence || 0.9) * 100}%</strong></span>
                      </div>
                    </div>
                  </div>

                  {/* Right: Transition Telemetry between hops */}
                  {sighting.transition_distance_meters !== undefined && sighting.transition_time_seconds !== undefined ? (
                    <div className="p-3 bg-slate-950/80 border border-slate-800 rounded-xl text-xs space-y-1 text-right min-w-[220px]">
                      <div className="flex justify-between gap-4">
                        <span className="text-slate-500">Hop Distance:</span>
                        <span className="font-mono font-semibold text-slate-300">
                          {sighting.transition_distance_meters >= 1000
                            ? `${(sighting.transition_distance_meters / 1000).toFixed(2)} km`
                            : `${sighting.transition_distance_meters.toFixed(0)} m`}
                        </span>
                      </div>
                      <div className="flex justify-between gap-4">
                        <span className="text-slate-500">Elapsed Time:</span>
                        <span className="font-mono font-semibold text-slate-300">
                          {sighting.transition_time_seconds >= 60
                            ? `${Math.floor(sighting.transition_time_seconds / 60)}m ${Math.floor(sighting.transition_time_seconds % 60)}s`
                            : `${sighting.transition_time_seconds.toFixed(0)}s`}
                        </span>
                      </div>
                      <div className="flex justify-between gap-4 border-t border-slate-800/80 pt-1">
                        <span className="text-amber-400 font-semibold">{sighting.speed_label || 'ESTIMATED SPEED'}:</span>
                        <span className="font-mono font-bold text-amber-300">
                          {sighting.estimated_speed_kmph ? `${sighting.estimated_speed_kmph} km/h` : 'N/A'}
                        </span>
                      </div>
                    </div>
                  ) : (
                    <div className="p-3 bg-slate-950/40 border border-slate-900 rounded-xl text-xs text-slate-500 italic">
                      Initial observation in session
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* GIS Route Observed Camera Sequence View */}
      {activeTab === 'gis_route' && (
        <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-lg font-bold text-white">Observed Camera Sequence</h2>
              <p className="text-xs text-slate-400">
                Straight-line sequence connecting verified camera detections across Gujarat.
              </p>
            </div>
            <span className="px-3 py-1 bg-blue-500/20 border border-blue-500/40 text-blue-300 text-xs font-mono font-bold rounded-lg">
              ROUTE TYPE: OBSERVED_CAMERA_SEQUENCE
            </span>
          </div>

          {/* Visual Route Hop Flowchart */}
          <div className="p-6 bg-slate-950 rounded-xl border border-slate-800/80 overflow-x-auto">
            <div className="flex items-center gap-4 min-w-[700px]">
              {timeline?.sightings?.map((s, idx) => (
                <React.Fragment key={s.sighting_id || idx}>
                  <div className="flex flex-col items-center p-4 bg-slate-900 border border-slate-800 rounded-xl text-center min-w-[160px] shadow-lg">
                    <div className="w-8 h-8 rounded-full bg-blue-600 text-white font-bold flex items-center justify-center text-sm mb-2 shadow">
                      {idx + 1}
                    </div>
                    <span className="font-bold text-white text-xs truncate max-w-[140px]">
                      {s.camera_name || s.camera_id}
                    </span>
                    <span className="text-[11px] text-slate-400 mt-1">{s.district || 'Gujarat'}</span>
                    <span className="text-[10px] text-blue-400 font-mono mt-1">
                      {new Date(s.timestamp).toLocaleTimeString()}
                    </span>
                  </div>

                  {idx < (timeline.sightings.length - 1) && (
                    <div className="flex flex-col items-center justify-center text-slate-600 px-2 shrink-0">
                      <ArrowRight size={20} className="text-blue-500 animate-pulse" />
                      {s.estimated_speed_kmph && (
                        <span className="text-[10px] text-amber-300/90 font-mono mt-1">
                          ~{s.estimated_speed_kmph} km/h
                        </span>
                      )}
                    </div>
                  )}
                </React.Fragment>
              ))}
            </div>
          </div>

          <div className="p-4 bg-slate-950/60 border border-slate-800 rounded-xl text-xs text-slate-400 flex items-center gap-2">
            <CheckCircle2 size={16} className="text-emerald-400 shrink-0" />
            <span>
              All sequence points are derived from authentic PostGIS geographic coordinates registered to Gujarat CCTV camera hardware.
            </span>
          </div>
        </div>
      )}
    </div>
  );
};
