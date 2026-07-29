import React, { useState, useCallback } from 'react';
import { AuditRecord } from '../types/compliance';
import { AuditFilters } from '../services/api';
import { Search, Table2, Loader2, Inbox, RefreshCw } from 'lucide-react';

interface AuditLogTableProps {
  records: AuditRecord[];
  totalRecords: number;
  loading: boolean;
  /** Distinct from "no records": signals that the audit service itself is unreachable */
  serviceError: string | null;
  onFilter: (filters: AuditFilters) => void;
  onRefresh: () => void;
}

export const AuditLogTable: React.FC<AuditLogTableProps> = ({
  records,
  totalRecords,
  loading,
  serviceError,
  onFilter,
  onRefresh,
}) => {
  const [docFilter, setDocFilter] = useState('');
  const [serviceFilter, setServiceFilter] = useState('');
  const [eventTypeFilter, setEventTypeFilter] = useState('');

  const handleApplyFilters = useCallback(() => {
    onFilter({
      document_id: docFilter.trim() || undefined,
      service_name: serviceFilter.trim() || undefined,
      event_type: eventTypeFilter.trim() || undefined,
    });
  }, [docFilter, serviceFilter, eventTypeFilter, onFilter]);

  const handleClearFilters = useCallback(() => {
    setDocFilter('');
    setServiceFilter('');
    setEventTypeFilter('');
    onFilter({});
  }, [onFilter]);

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (e.key === 'Enter') handleApplyFilters();
    },
    [handleApplyFilters]
  );

  return (
    <div className="glass-card p-4 flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between pb-3 mb-3 border-b border-slate-200">
        <div className="flex items-center gap-2">
          <Table2 className="w-4 h-4 text-blue-600" />
          <h2 className="text-sm font-semibold text-slate-800">
            Immutable Audit Event Log
          </h2>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-xs px-2 py-0.5 rounded bg-blue-50 text-blue-700 font-mono border border-blue-100">
            {totalRecords} Records
          </span>
          <button
            onClick={onRefresh}
            disabled={loading}
            className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-blue-600 hover:bg-blue-700 active:bg-blue-800 text-white text-xs font-medium transition-all shadow-sm disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer focus:outline-none focus:ring-2 focus:ring-blue-500/40"
          >
            <RefreshCw className={`w-3 h-3 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </button>
        </div>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap items-end gap-3 mb-4 pb-3 border-b border-slate-100">
        <div className="flex flex-col gap-1">
          <label className="text-[10px] font-semibold text-slate-600 uppercase tracking-wider">
            Document ID
          </label>
          <input
            type="text"
            value={docFilter}
            onChange={(e) => setDocFilter(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="e.g., DOC-99482-A"
            className="px-2.5 py-1.5 text-xs rounded-lg border border-slate-200 bg-slate-50 text-slate-800 placeholder:text-slate-500 focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 transition-all w-40"
          />
        </div>
        <div className="flex flex-col gap-1">
          <label className="text-[10px] font-semibold text-slate-600 uppercase tracking-wider">
            Service Name
          </label>
          <input
            type="text"
            value={serviceFilter}
            onChange={(e) => setServiceFilter(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="e.g., clinical-workspace"
            className="px-2.5 py-1.5 text-xs rounded-lg border border-slate-200 bg-slate-50 text-slate-800 placeholder:text-slate-500 focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 transition-all w-44"
          />
        </div>
        <div className="flex flex-col gap-1">
          <label className="text-[10px] font-semibold text-slate-600 uppercase tracking-wider">
            Event Type
          </label>
          <input
            type="text"
            value={eventTypeFilter}
            onChange={(e) => setEventTypeFilter(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="e.g., REFERRAL_APPROVED"
            className="px-2.5 py-1.5 text-xs rounded-lg border border-slate-200 bg-slate-50 text-slate-800 placeholder:text-slate-500 focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 transition-all w-48"
          />
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={handleApplyFilters}
            disabled={loading}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-blue-600 hover:bg-blue-700 active:bg-blue-800 text-white text-xs font-medium transition-all shadow-sm disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer focus:outline-none focus:ring-2 focus:ring-blue-500/40"
          >
            <Search className="w-3 h-3" />
            Filter
          </button>
          <button
            onClick={handleClearFilters}
            disabled={loading}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-100 hover:bg-slate-200 active:bg-slate-300 text-slate-700 text-xs font-medium transition-all border border-slate-200 disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer focus:outline-none focus:ring-2 focus:ring-slate-400/30"
          >
            Clear
          </button>
        </div>
      </div>

      {/* Table body */}
      {loading ? (
        <div className="flex flex-col items-center justify-center py-16 text-slate-500 gap-3">
          <Loader2 className="w-6 h-6 text-blue-600 animate-spin" />
          <span className="text-xs font-mono">Loading audit events...</span>
        </div>
      ) : serviceError ? (
        null
      ) : records.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-16 text-slate-500 gap-2">
          <Inbox className="w-8 h-8 text-slate-400" />
          <p className="text-xs font-medium text-slate-600">
            No audit events found matching your filters.
          </p>
          <p className="text-[10px] text-slate-500">
            The audit service responded successfully — there are genuinely zero matching records.
          </p>
        </div>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-xs">
            <thead>
              <tr className="border-b border-slate-200">
                <th className="text-left py-2.5 px-3 text-slate-600 font-semibold uppercase tracking-wider text-[10px]">
                  Event ID
                </th>
                <th className="text-left py-2.5 px-3 text-slate-600 font-semibold uppercase tracking-wider text-[10px]">
                  Document ID
                </th>
                <th className="text-left py-2.5 px-3 text-slate-600 font-semibold uppercase tracking-wider text-[10px]">
                  Service
                </th>
                <th className="text-left py-2.5 px-3 text-slate-600 font-semibold uppercase tracking-wider text-[10px]">
                  Event Type
                </th>
                <th className="text-left py-2.5 px-3 text-slate-600 font-semibold uppercase tracking-wider text-[10px]">
                  HMAC Signature
                </th>
                <th className="text-left py-2.5 px-3 text-slate-600 font-semibold uppercase tracking-wider text-[10px]">
                  Timestamp
                </th>
              </tr>
            </thead>
            <tbody>
              {records.map((rec, idx) => (
                <tr
                  key={rec.event_id || idx}
                  className="border-b border-slate-100 hover:bg-blue-50/60 transition-colors cursor-pointer"
                >
                  <td className="py-2.5 px-3 font-mono text-blue-700 font-medium">
                    {rec.event_id}
                  </td>
                  <td className="py-2.5 px-3 font-mono text-slate-800">
                    {rec.document_id}
                  </td>
                  <td className="py-2.5 px-3 text-slate-700">
                    {rec.service_name}
                  </td>
                  <td className="py-2.5 px-3">
                    <span className="inline-flex items-center px-2 py-0.5 rounded bg-blue-50 text-blue-700 border border-blue-200 font-semibold text-[10px]">
                      {rec.event_type}
                    </span>
                  </td>
                  <td className="py-2.5 px-3 font-mono text-slate-600">
                    {rec.hmac_signature
                      ? `${rec.hmac_signature.substring(0, 20)}…`
                      : 'N/A'}
                  </td>
                  <td className="py-2.5 px-3 text-slate-600 font-mono">
                    {rec.created_at}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};
