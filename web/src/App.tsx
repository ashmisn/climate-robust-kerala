import React from 'react';
import { AppProvider, useApp } from './state/AppContext';
import { Navbar } from './components/Navbar';
import { Sidebar } from './components/Sidebar';
import { DetailDrawer } from './components/DetailDrawer';

import { Overview } from './pages/Overview';
import { NetworkExplorer } from './pages/NetworkExplorer';
import { RobustnessPage } from './pages/RobustnessPage';
import { BasinsPage } from './pages/BasinsPage';
import { LandslidePage } from './pages/LandslidePage';
import { MethodPage } from './pages/MethodPage';

import { Loader2, AlertCircle } from 'lucide-react';

const DashboardContent: React.FC = () => {
  const { activePage, isLoading, error, reloadData } = useApp();

  if (isLoading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[calc(100vh-4rem)] p-6 space-y-4">
        <Loader2 className="w-10 h-10 animate-spin text-emerald-600" />
        <p className="text-sm font-medium text-slate-600 dark:text-slate-300">
          Loading spatial climate datasets from static data contract...
        </p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[calc(100vh-4rem)] p-6 space-y-4">
        <div className="p-4 bg-red-50 dark:bg-red-950/40 border border-red-500/20 rounded-xl text-center max-w-md space-y-3">
          <AlertCircle className="w-8 h-8 text-red-500 mx-auto" />
          <h3 className="font-bold text-red-900 dark:text-red-200">Failed to Load Datasets</h3>
          <p className="text-xs text-red-700 dark:text-red-300">{error}</p>
          <button
            onClick={reloadData}
            className="px-4 py-2 bg-red-600 hover:bg-red-700 text-white text-xs font-semibold rounded-lg shadow-sm"
          >
            Retry Loading
          </button>
        </div>
      </div>
    );
  }

  const renderPage = () => {
    switch (activePage) {
      case 'overview':
        return <Overview />;
      case 'network':
        return <NetworkExplorer />;
      case 'robustness':
        return <RobustnessPage />;
      case 'basins':
        return <BasinsPage />;
      case 'landslide':
        return <LandslidePage />;
      case 'method':
        return <MethodPage />;
      default:
        return <Overview />;
    }
  };

  return (
    <div className="flex-1 overflow-y-auto min-h-[calc(100vh-4rem)]">
      {renderPage()}
      <DetailDrawer />
    </div>
  );
};

export const App: React.FC = () => {
  return (
    <AppProvider>
      <div className="min-h-screen flex flex-col bg-slate-50 dark:bg-slate-950 transition-colors">
        <Navbar />
        <div className="flex-1 flex flex-col md:flex-row">
          <Sidebar />
          <DashboardContent />
        </div>
      </div>
    </AppProvider>
  );
};

export default App;
