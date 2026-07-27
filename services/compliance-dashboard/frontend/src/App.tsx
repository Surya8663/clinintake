import React, { useState, useEffect, useCallback } from 'react';
import { Header } from './components/Header';
import { AuditLogTable } from './components/AuditLogTable';
import { VaultIntegrityPanel } from './components/VaultIntegrityPanel';
import { ErrorBanner } from './components/ErrorBanner';
import { AuditRecord, VaultIntegrityResponse } from './types/compliance';
import { fetchAuditTrail, fetchVaultIntegrity, AuditFilters } from './services/api';

export const App: React.FC = () => {
  // Audit trail state
  const [records, setRecords] = useState<AuditRecord[]>([]);
  const [totalRecords, setTotalRecords] = useState<number>(0);
  const [auditLoading, setAuditLoading] = useState<boolean>(true);
  /**
   * This specifically tracks "audit-service unreachable" errors from the backend.
   * It is intentionally separate from "zero records" — a compliance reviewer must
   * see a visually distinct state for each case.
   */
  const [auditServiceError, setAuditServiceError] = useState<string | null>(null);
  /** HTTP/network-level errors (fetch itself failed — backend proxy down) */
  const [auditFetchError, setAuditFetchError] = useState<string | null>(null);

  // Vault integrity state
  const [vaultData, setVaultData] = useState<VaultIntegrityResponse | null>(null);
  const [vaultLoading, setVaultLoading] = useState<boolean>(true);
  const [vaultError, setVaultError] = useState<string | null>(null);

  // Derived overall service status for the header
  const serviceStatus: 'connected' | 'error' | 'loading' =
    auditLoading && vaultLoading ? 'loading' :
    auditServiceError || auditFetchError || vaultError ? 'error' :
    'connected';

  // Load audit trail
  const loadAuditTrail = useCallback(async (filters?: AuditFilters) => {
    setAuditLoading(true);
    setAuditServiceError(null);
    setAuditFetchError(null);

    try {
      const data = await fetchAuditTrail(filters);

      // Check if the backend returned an error field (audit-service unreachable)
      if (data.error) {
        setAuditServiceError(
          data.error === 'audit-service unreachable'
            ? 'Unable to reach Audit Service — the compliance dashboard cannot verify audit trail data. This does NOT mean the audit log is empty; the service may be temporarily unavailable.'
            : data.error === "Missing required 'audit:read' RBAC scope"
            ? 'Access denied: your session does not have the required audit:read RBAC scope.'
            : data.error
        );
        setRecords([]);
        setTotalRecords(0);
      } else {
        setRecords(data.records || []);
        setTotalRecords(data.total_records || 0);
      }
    } catch (err: any) {
      console.error('Failed to fetch audit trail:', err);
      setAuditFetchError(
        'Unable to reach the Compliance Dashboard backend — check that the service is running and the proxy is configured.'
      );
      setRecords([]);
      setTotalRecords(0);
    } finally {
      setAuditLoading(false);
    }
  }, []);

  // Load vault integrity
  const loadVaultIntegrity = useCallback(async () => {
    setVaultLoading(true);
    setVaultError(null);

    try {
      const data = await fetchVaultIntegrity();
      setVaultData(data);
    } catch (err: any) {
      console.error('Failed to verify vault integrity:', err);
      setVaultError(
        'Unable to reach the Compliance Dashboard backend for vault verification.'
      );
    } finally {
      setVaultLoading(false);
    }
  }, []);

  // Initial load
  useEffect(() => {
    loadAuditTrail();
    loadVaultIntegrity();
  }, [loadAuditTrail, loadVaultIntegrity]);

  const handleFilter = useCallback((filters: AuditFilters) => {
    loadAuditTrail(filters);
  }, [loadAuditTrail]);

  const handleRefresh = useCallback(() => {
    loadAuditTrail();
    loadVaultIntegrity();
  }, [loadAuditTrail, loadVaultIntegrity]);

  return (
    <div className="min-h-screen p-4 sm:p-6 flex flex-col max-w-7xl mx-auto">
      <Header serviceStatus={serviceStatus} />

      {/* Error banners — prominently positioned above all content */}
      {auditFetchError && (
        <div className="mb-4">
          <ErrorBanner message={auditFetchError} variant="connection" />
        </div>
      )}
      {auditServiceError && (
        <div className="mb-4">
          <ErrorBanner message={auditServiceError} variant="connection" />
        </div>
      )}

      <div className="space-y-6 flex-1">
        {/* Vault integrity panel */}
        <VaultIntegrityPanel
          data={vaultData}
          loading={vaultLoading}
          error={vaultError}
        />

        {/* Audit log table */}
        <AuditLogTable
          records={records}
          totalRecords={totalRecords}
          loading={auditLoading}
          serviceError={auditServiceError || auditFetchError}
          onFilter={handleFilter}
          onRefresh={handleRefresh}
        />
      </div>
    </div>
  );
};

export default App;
