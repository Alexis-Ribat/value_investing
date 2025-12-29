/**
 * Governance Component Example Page
 */

import React, { useState } from 'react';
import GovernanceComponent from '../components/GovernanceComponent';

export default function GovernanceExamplePage() {
  const [ticker, setTicker] = useState('AAPL');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleTickerChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    setTicker(e.target.value);
  };

  return (
    <div style={styles.container}>
      <h1 style={styles.title}>Management & Capital - Governance</h1>

      <div style={styles.controls}>
        <label htmlFor="ticker-select" style={styles.label}>
          Select Stock:
        </label>
        <select
          id="ticker-select"
          value={ticker}
          onChange={handleTickerChange}
          style={styles.select}
        >
          <option value="AAPL">Apple (AAPL)</option>
          <option value="MC.PA">LVMH (MC.PA)</option>
        </select>
      </div>

      {isLoading && <p style={styles.status}>Loading...</p>}
      {error && <p style={styles.error}>{error}</p>}

      <GovernanceComponent
        key={ticker}
        ticker={ticker}
        onLoading={setIsLoading}
        onError={setError}
      />
    </div>
  );
}

const styles = {
  container: {
    padding: '24px',
    maxWidth: '1400px',
    margin: '0 auto',
    backgroundColor: '#0a0e27',
    minHeight: '100vh',
    color: '#ffffff',
  } as React.CSSProperties,
  title: {
    margin: '0 0 24px 0',
    fontSize: '24px',
    fontWeight: '600',
  } as React.CSSProperties,
  controls: {
    marginBottom: '24px',
    display: 'flex',
    gap: '12px',
    alignItems: 'center',
  } as React.CSSProperties,
  label: {
    fontSize: '14px',
    fontWeight: '500',
  } as React.CSSProperties,
  select: {
    padding: '8px 12px',
    borderRadius: '4px',
    border: '1px solid #2a3055',
    fontSize: '14px',
    backgroundColor: '#141829',
    color: '#ffffff',
    cursor: 'pointer',
  } as React.CSSProperties,
  status: {
    fontSize: '14px',
    color: '#a8afc7',
  } as React.CSSProperties,
  error: {
    fontSize: '14px',
    color: '#ff4b4b',
  } as React.CSSProperties,
};
