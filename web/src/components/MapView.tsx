import React, { useEffect, useRef, useState } from 'react';
import L from 'leaflet';
import { useApp } from '../state/AppContext';
import { CellFeature } from '../types/contract';
import { interpolateColor, VIRIDIS_RAMP, VULNERABILITY_RAMP, formatMetricName } from '../lib/colors';
import { Eye, EyeOff, Layers, MapPin, Compass } from 'lucide-react';

interface MapViewProps {
  showLinksDefault?: boolean;
  showLandslidesDefault?: boolean;
  showBasinsDefault?: boolean;
  highlightCellId?: string | null;
  removedCellIds?: Set<string>;
  heightClass?: string;
}

export type BasemapType = 'canvas' | 'satellite' | 'topo';

export const MapView: React.FC<MapViewProps> = ({
  showLinksDefault = true,
  showLandslidesDefault = false,
  showBasinsDefault = false,
  highlightCellId = null,
  removedCellIds = new Set(),
  heightClass = "h-[540px]"
}) => {
  const mapContainerRef = useRef<HTMLDivElement>(null);
  const mapInstanceRef = useRef<L.Map | null>(null);
  
  const basemapBaseRef = useRef<L.TileLayer | null>(null);
  const basemapLabelsRef = useRef<L.TileLayer | null>(null);
  const basinsLayerRef = useRef<L.LayerGroup | null>(null);
  const cellsLayerRef = useRef<L.LayerGroup | null>(null);
  const linksLayerRef = useRef<L.LayerGroup | null>(null);
  const landslidesLayerRef = useRef<L.LayerGroup | null>(null);

  const [basemapType, setBasemapType] = useState<BasemapType>('canvas');
  const [showLinks, setShowLinks] = useState<boolean>(showLinksDefault);
  const [showLandslides, setShowLandslides] = useState<boolean>(showLandslidesDefault);
  const [showBasins, setShowBasins] = useState<boolean>(showBasinsDefault);

  const {
    data,
    activeMetric,
    linkWeightMin,
    selectedCell,
    setSelectedCell,
    setSelectedBasin,
    isDarkMode
  } = useApp();

  // Initialize Map
  useEffect(() => {
    if (!mapContainerRef.current || mapInstanceRef.current) return;

    const map = L.map(mapContainerRef.current, {
      center: [10.35, 76.45],
      zoom: 7.6,
      zoomSnap: 0.2,
      zoomDelta: 0.5,
      zoomControl: true,
      attributionControl: false
    });

    mapInstanceRef.current = map;
    basinsLayerRef.current = L.layerGroup().addTo(map);
    cellsLayerRef.current = L.layerGroup().addTo(map);
    linksLayerRef.current = L.layerGroup().addTo(map);
    landslidesLayerRef.current = L.layerGroup().addTo(map);

    return () => {
      map.remove();
      mapInstanceRef.current = null;
    };
  }, []);

  // Update Free, Watermark-Free Esri / Open Basemap
  useEffect(() => {
    if (!mapInstanceRef.current) return;
    const map = mapInstanceRef.current;

    // Remove existing tile layers
    if (basemapBaseRef.current) {
      map.removeLayer(basemapBaseRef.current);
      basemapBaseRef.current = null;
    }
    if (basemapLabelsRef.current) {
      map.removeLayer(basemapLabelsRef.current);
      basemapLabelsRef.current = null;
    }

    let baseUrl = '';
    let labelsUrl: string | null = null;

    if (basemapType === 'satellite') {
      baseUrl = 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}';
      labelsUrl = 'https://services.arcgisonline.com/ArcGIS/rest/services/Reference/World_Boundaries_and_Places/MapServer/tile/{z}/{y}/{x}';
    } else if (basemapType === 'topo') {
      baseUrl = 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Topo_Map/MapServer/tile/{z}/{y}/{x}';
    } else {
      // Clean Minimalist Canvas (Dark or Light)
      if (isDarkMode) {
        baseUrl = 'https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Base/MapServer/tile/{z}/{y}/{x}';
        labelsUrl = 'https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Reference/MapServer/tile/{z}/{y}/{x}';
      } else {
        baseUrl = 'https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Light_Gray_Base/MapServer/tile/{z}/{y}/{x}';
        labelsUrl = 'https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Light_Gray_Reference/MapServer/tile/{z}/{y}/{x}';
      }
    }

    const baseLayer = L.tileLayer(baseUrl, {
      maxZoom: 18,
      attribution: 'Esri, USGS, NOAA'
    }).addTo(map);
    baseLayer.bringToBack();
    basemapBaseRef.current = baseLayer;

    if (labelsUrl) {
      const labelsLayer = L.tileLayer(labelsUrl, {
        maxZoom: 18,
        pane: 'overlayPane',
        opacity: 0.85
      }).addTo(map);
      basemapLabelsRef.current = labelsLayer;
    }
  }, [basemapType, isDarkMode]);

  // Compute Min and Max for the active metric across cells
  const metricRange = React.useMemo(() => {
    if (!data?.cells.features) return { min: 0, max: 1 };
    const values = data.cells.features.map((f) => (f.properties as any)[activeMetric] || 0);
    const min = Math.min(...values);
    const max = Math.max(...values);
    return { min, max: max === min ? min + 1 : max };
  }, [data, activeMetric]);

  // Render Basins Outline Layer
  useEffect(() => {
    if (!mapInstanceRef.current || !basinsLayerRef.current || !data?.basins) return;
    const layerGroup = basinsLayerRef.current;
    layerGroup.clearLayers();

    if (!showBasins) return;

    data.basins.features.forEach((feature) => {
      const props = feature.properties;
      const geojsonLayer = L.geoJSON(feature as any, {
        style: {
          color: isDarkMode ? '#38bdf8' : '#0284c7',
          weight: 2,
          opacity: 0.8,
          fillOpacity: 0.05,
          fillColor: '#0284c7',
          dashArray: '4, 4'
        }
      });

      geojsonLayer.bindTooltip(
        `<div class="text-xs font-sans">
          <strong>Basin:</strong> ${props.name} (${props.basin_id})<br/>
          <span>Cells: ${props.n_cells} | Impact Rank: #${props.impact_rank}</span>
        </div>`,
        { sticky: true }
      );

      geojsonLayer.on('click', () => {
        setSelectedBasin(props);
      });

      layerGroup.addLayer(geojsonLayer);
    });
  }, [data, showBasins, isDarkMode, setSelectedBasin]);

  // Render Cells
  useEffect(() => {
    if (!mapInstanceRef.current || !cellsLayerRef.current || !data?.cells) return;
    const layerGroup = cellsLayerRef.current;
    layerGroup.clearLayers();

    const ramp = activeMetric === 'landslide_density' ? VULNERABILITY_RAMP : VIRIDIS_RAMP;

    data.cells.features.forEach((feature) => {
      const props = feature.properties;
      const isRemoved = removedCellIds.has(props.cell_id);
      const isSelected = selectedCell?.cell_id === props.cell_id || highlightCellId === props.cell_id;

      const rawVal = (props as any)[activeMetric] ?? 0;
      const fillColor = isRemoved
        ? '#94a3b8'
        : interpolateColor(rawVal, metricRange.min, metricRange.max, ramp);

      const coords = feature.geometry.coordinates[0];
      // Leaflet uses [lat, lon], GeoJSON uses [lon, lat]
      const latLngs = coords.map(([lon, lat]) => [lat, lon] as [number, number]);

      const polygon = L.polygon(latLngs, {
        fillColor,
        fillOpacity: isRemoved ? 0.2 : isSelected ? 0.9 : basemapType === 'satellite' ? 0.55 : 0.7,
        color: isSelected ? '#10b981' : isRemoved ? '#64748b' : isDarkMode ? '#1e293b' : '#cbd5e1',
        weight: isSelected ? 3 : 1,
        dashArray: isRemoved ? '4, 4' : undefined
      });

      polygon.bindTooltip(
        `<div class="text-xs font-sans">
          <strong>${props.cell_id}</strong> (${props.basin_name || props.basin_id})<br/>
          <span class="text-slate-500">${formatMetricName(activeMetric)}:</span>
          <strong>${typeof rawVal === 'number' ? rawVal.toFixed(4) : rawVal}</strong>
        </div>`,
        { sticky: true }
      );

      polygon.on('click', () => {
        setSelectedCell(props);
      });

      layerGroup.addLayer(polygon);
    });
  }, [data, activeMetric, metricRange, selectedCell, highlightCellId, removedCellIds, setSelectedCell, isDarkMode, basemapType]);

  // Render Links
  useEffect(() => {
    if (!mapInstanceRef.current || !linksLayerRef.current || !data) return;
    const layerGroup = linksLayerRef.current;
    layerGroup.clearLayers();

    if (!showLinks) return;

    // Build coordinate lookup table for cells
    const cellCoords = new Map<string, [number, number]>();
    data.cells.features.forEach((f) => {
      cellCoords.set(f.properties.cell_id, [f.properties.lat, f.properties.lon]);
    });

    data.links.forEach((link) => {
      if (link.weight < linkWeightMin) return;

      const src = cellCoords.get(link.source);
      const tgt = cellCoords.get(link.target);
      if (!src || !tgt) return;

      // Link opacity mapped to weight
      const opacity = Math.min(0.85, Math.max(0.18, (link.weight - 0.3) / 0.5));

      const polyline = L.polyline([src, tgt], {
        color: isDarkMode ? '#38bdf8' : '#0284c7',
        weight: Math.max(1, link.weight * 2.8),
        opacity: opacity,
      });

      polyline.bindTooltip(
        `<div class="text-xs">
          <strong>Link:</strong> ${link.source} ↔ ${link.target}<br/>
          <strong>ES Score Q:</strong> ${link.weight.toFixed(4)}
        </div>`
      );

      layerGroup.addLayer(polyline);
    });
  }, [data, showLinks, linkWeightMin, isDarkMode]);

  // Render Landslide Points
  useEffect(() => {
    if (!mapInstanceRef.current || !landslidesLayerRef.current || !data?.landslidePoints) return;
    const layerGroup = landslidesLayerRef.current;
    layerGroup.clearLayers();

    if (!showLandslides) return;

    data.landslidePoints.forEach((pt) => {
      const circle = L.circleMarker([pt.lat, pt.lon], {
        radius: 3.5,
        fillColor: '#ef4444',
        color: '#ffffff',
        weight: 1,
        fillOpacity: 0.85
      });
      circle.bindTooltip(
        `<div class="text-xs">
          <strong>2018 Landslide Event</strong><br/>
          Lat: ${pt.lat.toFixed(3)}°, Lon: ${pt.lon.toFixed(3)}°
        </div>`
      );
      layerGroup.addLayer(circle);
    });
  }, [data, showLandslides]);

  return (
    <div className={`relative rounded-xl overflow-hidden border border-slate-200 dark:border-slate-800 shadow-xs ${heightClass}`}>
      {/* Map DOM */}
      <div ref={mapContainerRef} className="w-full h-full" />

      {/* Top-Right Layer Toggles & Controls */}
      <div className="absolute top-3 right-3 z-[1000] flex flex-col gap-2 bg-white/95 dark:bg-slate-900/95 backdrop-blur-md p-2.5 rounded-xl border border-slate-200 dark:border-slate-800 shadow-lg text-xs">
        
        {/* Basemap Switcher */}
        <div className="pb-1.5 border-b border-slate-200 dark:border-slate-800">
          <div className="text-[10px] uppercase font-bold text-slate-400 mb-1 flex items-center gap-1">
            <Compass className="w-3 h-3 text-emerald-500" />
            Basemap
          </div>
          <div className="grid grid-cols-3 gap-1 bg-slate-100 dark:bg-slate-800/80 p-0.5 rounded-md">
            <button
              onClick={() => setBasemapType('canvas')}
              className={`px-1.5 py-0.5 rounded text-[11px] transition-all font-medium ${
                basemapType === 'canvas'
                  ? 'bg-white dark:bg-slate-700 text-emerald-600 dark:text-emerald-400 shadow-xs'
                  : 'text-slate-500 hover:text-slate-800 dark:hover:text-slate-200'
              }`}
            >
              Canvas
            </button>
            <button
              onClick={() => setBasemapType('satellite')}
              className={`px-1.5 py-0.5 rounded text-[11px] transition-all font-medium ${
                basemapType === 'satellite'
                  ? 'bg-white dark:bg-slate-700 text-emerald-600 dark:text-emerald-400 shadow-xs'
                  : 'text-slate-500 hover:text-slate-800 dark:hover:text-slate-200'
              }`}
            >
              Satellite
            </button>
            <button
              onClick={() => setBasemapType('topo')}
              className={`px-1.5 py-0.5 rounded text-[11px] transition-all font-medium ${
                basemapType === 'topo'
                  ? 'bg-white dark:bg-slate-700 text-emerald-600 dark:text-emerald-400 shadow-xs'
                  : 'text-slate-500 hover:text-slate-800 dark:hover:text-slate-200'
              }`}
            >
              Topo
            </button>
          </div>
        </div>

        {/* Feature Overlays */}
        <div className="flex flex-col gap-1">
          <div className="text-[10px] uppercase font-bold text-slate-400 mb-0.5 flex items-center gap-1">
            <Layers className="w-3 h-3 text-sky-500" />
            Overlays
          </div>

          <button
            onClick={() => setShowLinks(!showLinks)}
            className={`flex items-center justify-between gap-2 px-2 py-1 rounded transition-colors ${
              showLinks
                ? 'bg-sky-50 dark:bg-sky-950/60 text-sky-700 dark:text-sky-300 font-medium border border-sky-200 dark:border-sky-800/50'
                : 'text-slate-500 hover:bg-slate-100 dark:hover:bg-slate-800'
            }`}
          >
            <span className="flex items-center gap-1.5">
              {showLinks ? <Eye className="w-3.5 h-3.5 text-sky-500" /> : <EyeOff className="w-3.5 h-3.5" />}
              Network Links
            </span>
            <span className="w-2 h-2 rounded-full bg-sky-400"></span>
          </button>

          <button
            onClick={() => setShowLandslides(!showLandslides)}
            className={`flex items-center justify-between gap-2 px-2 py-1 rounded transition-colors ${
              showLandslides
                ? 'bg-red-50 dark:bg-red-950/60 text-red-700 dark:text-red-300 font-medium border border-red-200 dark:border-red-800/50'
                : 'text-slate-500 hover:bg-slate-100 dark:hover:bg-slate-800'
            }`}
          >
            <span className="flex items-center gap-1.5">
              {showLandslides ? <Eye className="w-3.5 h-3.5 text-red-500" /> : <EyeOff className="w-3.5 h-3.5" />}
              2018 Landslides
            </span>
            <span className="w-2 h-2 rounded-full bg-red-500"></span>
          </button>

          <button
            onClick={() => setShowBasins(!showBasins)}
            className={`flex items-center justify-between gap-2 px-2 py-1 rounded transition-colors ${
              showBasins
                ? 'bg-emerald-50 dark:bg-emerald-950/60 text-emerald-700 dark:text-emerald-300 font-medium border border-emerald-200 dark:border-emerald-800/50'
                : 'text-slate-500 hover:bg-slate-100 dark:hover:bg-slate-800'
            }`}
          >
            <span className="flex items-center gap-1.5">
              {showBasins ? <Eye className="w-3.5 h-3.5 text-emerald-500" /> : <EyeOff className="w-3.5 h-3.5" />}
              River Basins
            </span>
            <span className="w-2 h-2 rounded-full bg-emerald-500"></span>
          </button>
        </div>

      </div>

      {/* Bottom Color Ramp Legend */}
      <div className="absolute bottom-3 left-3 z-[1000] bg-white/95 dark:bg-slate-900/95 backdrop-blur-md px-3 py-2 rounded-xl border border-slate-200 dark:border-slate-800 shadow-lg text-[11px]">
        <div className="font-semibold text-slate-700 dark:text-slate-200 mb-1 flex items-center justify-between gap-4">
          <span>{formatMetricName(activeMetric)}</span>
          <span className="text-[10px] text-slate-400 font-mono">Q &gt; {linkWeightMin.toFixed(2)}</span>
        </div>
        <div className="flex items-center gap-1.5">
          <span className="font-mono text-slate-500">{metricRange.min.toFixed(3)}</span>
          <div className="flex h-2.5 w-32 rounded-xs overflow-hidden shadow-xs">
            {(activeMetric === 'landslide_density' ? VULNERABILITY_RAMP : VIRIDIS_RAMP).map((c, i) => (
              <div key={i} className="flex-1" style={{ backgroundColor: c }} />
            ))}
          </div>
          <span className="font-mono text-slate-500">{metricRange.max.toFixed(3)}</span>
        </div>
      </div>
    </div>
  );
};
