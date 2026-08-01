import React from 'react';
import { AlertTriangle, WifiOff } from 'lucide-react';

interface ErrorBannerProps {
  /** The error message to display */
  message: string;
  /**
   * Distinguishes between "service unreachable" (connection) vs. other errors (generic).
   * A compliance reviewer must see a visually distinct state for "audit-service unreachable"
   * vs. a genuinely empty audit log.
   */
  variant: 'connection' | 'generic';
}

export const ErrorBanner: React.FC<ErrorBannerProps> = ({ message, variant }) => {
  const isConnection = variant === 'connection';

  return (
    <div
      className={`p-4 rounded-xl border flex items-center gap-3 text-xs ${
        isConnection
          ? 'bg-amber-50 border-amber-200 text-amber-800'
          : 'bg-rose-50 border-rose-200 text-rose-800'
      }`}
    >
      {isConnection ? (
        <WifiOff className="w-5 h-5 text-amber-600 shrink-0" />
      ) : (
        <AlertTriangle className="w-5 h-5 text-rose-600 shrink-0" />
      )}
      <div className="flex-1">
        <p className="font-semibold">
          {isConnection ? 'Audit Service Unreachable' : 'Error'}
        </p>
        <p className="mt-0.5 leading-relaxed">{message}</p>
      </div>
    </div>
  );
};
