/**
 * Example Page: Shareholder Component Usage
 */

import React, { useState } from 'react';
import ShareholderComponent from '../components/ShareholderComponent';

export default function ExamplePage() {
  const [ticker, setTicker] = useState('AAPL');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleTickerChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    setTicker(e.target.value);
  };

  return (
    <div style={{ padding: '24px', maxWidth: '1200px', margin: '0 auto' }}>
      <h1>Shareholder Data Component Example</h1>

      <div
        style={{
          marginBottom: '24px',
          display: 'flex',
          gap: '12px',
          alignItems: 'center',
        }}
      >
        <label htmlFor="ticker-select">Select Stock:</label>
        <select
          id="ticker-select"
          value={ticker}
          onChange={handleTickerChange}
          style={{
            padding: '8px 12px',
            borderRadius: '4px',
            border: '1px solid #ddd',
            fontSize: '14px',
          }}
        >
          <option value="AAPL">Apple (AAPL)</option>
          <option value="MC.PA">LVMH (MC.PA)</option>
        </select>
      </div>

      {isLoading && <p>Loading...</p>}
      {error && <p style={{ color: 'red' }}>{error}</p>}

      <ShareholderComponent
        key={ticker}
        ticker={ticker}
        onLoading={setIsLoading}
        onError={setError}
      />
    </div>
  );
}
