// Color scales and styling utilities for Kerala Climate Network

export const VIRIDIS_RAMP = [
  '#440154', // dark purple
  '#482878',
  '#3e4a89',
  '#31688e',
  '#26828e',
  '#1f9e89',
  '#35b779',
  '#6ece58',
  '#b5de2b',
  '#fde725'  // bright yellow
];

export const VULNERABILITY_RAMP = [
  '#fef2f2', // light red
  '#fee2e2',
  '#fecaca',
  '#fca5a5',
  '#f87171',
  '#ef4444',
  '#dc2626',
  '#b91c1c',
  '#991b1b',
  '#7f1d1d'
];

export const TEAL_RAMP = [
  '#f0fdfa',
  '#ccfbf1',
  '#99f6e4',
  '#5eead4',
  '#2dd4bf',
  '#14b8a6',
  '#0d9488',
  '#0f766e',
  '#115e59',
  '#134e4a'
];

/**
 * Maps a numerical value to a hex color given a range and color ramp.
 */
export function interpolateColor(value: number, min: number, max: number, ramp: string[] = VIRIDIS_RAMP): string {
  if (min === max || isNaN(value)) {
    return ramp[Math.floor(ramp.length / 2)];
  }
  const norm = Math.max(0, Math.min(1, (value - min) / (max - min)));
  const index = Math.min(ramp.length - 1, Math.floor(norm * ramp.length));
  return ramp[index];
}

export function formatMetricName(metric: string): string {
  switch (metric) {
    case 'betweenness':
      return 'Betweenness Centrality';
    case 'degree':
      return 'Degree Centrality';
    case 'clustering':
      return 'Clustering Coeff.';
    case 'eigenvector':
      return 'Eigenvector Centrality';
    case 'landslide_density':
      return 'Landslide Density (pts/km²)';
    case 'mean_slope':
      return 'Mean Slope (deg)';
    case 'max_slope':
      return 'Max Slope (deg)';
    case 'extreme_days_aug2018':
      return 'Aug 2018 Extreme Days';
    default:
      return metric.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());
  }
}
