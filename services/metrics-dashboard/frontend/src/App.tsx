import React, { useState, useEffect, useCallback } from 'react';
import { Header } from './components/Header';
import { KpiCardGrid } from './components/KpiCardGrid';
import { TrendCharts } from './components/TrendCharts';
import { BenchmarkDetailPanel } from './components/BenchmarkDetailPanel';
import { ErrorBanner } from './components/ErrorBanner';
import { KPISummaryResponse } from './types/metrics';
import { fetchPipelineKPIs } from './services/api';
import { RefreshCw } from 'lucide-react';

export const App: React.FC = () => {
  const [data, setData] = useState<KPISummaryResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const loadKPIs = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetchPipelineKPIs();
      setData(res);
    } catch (err: any) {
      console.error('Failed to fetch pipeline KPIs:', err);
      setError(
        'Unable to reach Metrics Dashboard service — check that the service is running and the proxy is configured.'
      );
      setData(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadKPIs();
  }, [loadKPIs]);

  const serviceStatus = loading ? 'loading' : error ? 'error' : 'connected';

  return (
    <div className="min-h-screen p-4 sm:p-6 flex flex-col max-w-7xl mx-auto space-y-6">
      <Header serviceStatus={serviceStatus} evaluatedAt={data?.evaluated_at || null} />

      {error && (
        <ErrorBanner message={error} variant="connection" />
      )}

      <div className="flex items-center justify-between pb-2 border-b border-slate-200">
        <div>
          <h2 className="text-base font-semibold text-slate-800">
            System Performance Metrics (PRD Section 13)
          </h2>
          <p className="text-xs text-slate-500">
            Real-time pipeline evaluation benchmark results
          </p>
        </div>
        <button
          onClick={loadKPIs}
          disabled={loading}
          className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-blue-600 hover:bg-blue-700 text-white text-xs font-medium transition-colors disabled:opacity-50"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          Refresh Metrics
        </button>
      </div>

      <KpiCardGrid data={data} loading={loading} />

      {!error && data && (
        <>
          <TrendCharts data={data} loading={loading} />
          <BenchmarkDetailPanel data={data} />
        </>
      )}
    </div>
  );
};

export default App;
