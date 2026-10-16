import React, { createContext, useContext, useState, useEffect } from 'react';
import {
  MetricType,
  CellProperties,
  BasinProperties,
} from '../types/contract';
import { FullDataset, loadAllContractData } from '../lib/dataLoader';

export type PageId = 'overview' | 'network' | 'robustness' | 'basins' | 'landslide' | 'method';

interface AppContextType {
  // Navigation
  activePage: PageId;
  setActivePage: (page: PageId) => void;

  // Global filters
  activeMetric: MetricType;
  setActiveMetric: (m: MetricType) => void;
  threshold: 90 | 95 | 97;
  setThreshold: (t: 90 | 95 | 97) => void;
  linkWeightMin: number;
  setLinkWeightMin: (w: number) => void;

  // Selection
  selectedCell: CellProperties | null;
  setSelectedCell: (c: CellProperties | null) => void;
  selectedBasin: BasinProperties | null;
  setSelectedBasin: (b: BasinProperties | null) => void;

  // Theme
  isDarkMode: boolean;
  toggleTheme: () => void;

  // Data
  data: FullDataset | null;
  isLoading: boolean;
  error: string | null;
  reloadData: () => void;
}

const AppContext = createContext<AppContextType | undefined>(undefined);

export const AppProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [activePage, setActivePage] = useState<PageId>('overview');
  const [activeMetric, setActiveMetric] = useState<MetricType>('betweenness');
  const [threshold, setThreshold] = useState<90 | 95 | 97>(95);
  const [linkWeightMin, setLinkWeightMin] = useState<number>(0.43);
  const [selectedCell, setSelectedCell] = useState<CellProperties | null>(null);
  const [selectedBasin, setSelectedBasin] = useState<BasinProperties | null>(null);

  const [isDarkMode, setIsDarkMode] = useState<boolean>(() => {
    return window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
  });

  const [data, setData] = useState<FullDataset | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const toggleTheme = () => {
    setIsDarkMode((prev) => !prev);
  };

  useEffect(() => {
    if (isDarkMode) {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
  }, [isDarkMode]);

  const loadData = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const full = await loadAllContractData();
      setData(full);
      // Auto-set link weight min to lowest link in thresholded dataset
      if (full.links.length > 0) {
        const minW = Math.min(...full.links.map((l) => l.weight));
        setLinkWeightMin(minW);
      }
    } catch (err: any) {
      console.error("Data load error:", err);
      setError(err.message || 'Failed to load static datasets');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  return (
    <AppContext.Provider
      value={{
        activePage,
        setActivePage,
        activeMetric,
        setActiveMetric,
        threshold,
        setThreshold,
        linkWeightMin,
        setLinkWeightMin,
        selectedCell,
        setSelectedCell,
        selectedBasin,
        setSelectedBasin,
        isDarkMode,
        toggleTheme,
        data,
        isLoading,
        error,
        reloadData: loadData,
      }}
    >
      {children}
    </AppContext.Provider>
  );
};

export const useApp = () => {
  const context = useContext(AppContext);
  if (!context) {
    throw new Error('useApp must be used within an AppProvider');
  }
  return context;
};
