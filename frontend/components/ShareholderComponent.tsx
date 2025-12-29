/**
 * Shareholder Component
 * Displays institutional holders table and ownership distribution chart
 * Responsive: 2 columns on desktop, stacked on mobile
 */

import React, { useEffect, useState } from 'react';
import { ShareholderData, ShareholderChartData } from '../types/shareholder';
import {
  fetchShareholdersWithCache,
  calculateChartData,
  formatCurrencyValue,
  formatShares,
} from '../services/shareholderService';
import './ShareholderComponent.css';

interface ShareholderComponentProps {
  ticker: string;
  onLoading?: (loading: boolean) => void;
  onError?: (error: string | null) => void;
}

/**
 * Simple Pie/Donut Chart Component (using HTML Canvas)
 * Can be replaced with Recharts, Chart.js, or D3 if preferred
 */
interface PieChartProps {
  data: ShareholderChartData[];
  currency?: string;
}

const PieChart: React.FC<PieChartProps> = ({ data, currency = 'USD' }) => {
  const canvasRef = React.useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    if (!canvasRef.current || data.length === 0) return;

    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    // Set canvas size
    const dpr = window.devicePixelRatio || 1;
    const size = 300;
    canvas.width = size * dpr;
    canvas.height = size * dpr;
    ctx.scale(dpr, dpr);

    const centerX = size / 2;
    const centerY = size / 2;
    const radius = 100;
    const donutWidth = 30;

    let startAngle = -Math.PI / 2;

    // Draw pie slices
    data.forEach((item) => {
      const sliceAngle = (item.value / 100) * 2 * Math.PI;

      // Draw donut slice
      ctx.fillStyle = item.color;
      ctx.beginPath();
      ctx.arc(centerX, centerY, radius, startAngle, startAngle + sliceAngle);
      ctx.arc(
        centerX,
        centerY,
        radius - donutWidth,
        startAngle + sliceAngle,
        startAngle,
        true,
      );
      ctx.fill();

      // Draw label
      const labelAngle = startAngle + sliceAngle / 2;
      const labelX = centerX + Math.cos(labelAngle) * (radius - donutWidth / 2);
      const labelY = centerY + Math.sin(labelAngle) * (radius - donutWidth / 2);

      ctx.fillStyle = '#fff';
      ctx.font = 'bold 12px Arial';
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      ctx.fillText(`${item.value.toFixed(1)}%`, labelX, labelY);

      startAngle += sliceAngle;
    });
  }, [data]);

  return (
    <div className="pie-chart-container">
      <canvas ref={canvasRef} className="pie-chart" />
      <div className="pie-chart-legend">
        {data.map((item) => (
          <div key={item.label} className="legend-item">
            <div
              className="legend-color"
              style={{ backgroundColor: item.color }}
            />
            <span>{item.label}</span>
            <span className="legend-value">{item.value.toFixed(1)}%</span>
          </div>
        ))}
      </div>
    </div>
  );
};

/**
 * Main Shareholder Component
 */
export const ShareholderComponent: React.FC<ShareholderComponentProps> = ({
  ticker,
  onLoading,
  onError,
}) => {
  const [data, setData] = useState<ShareholderData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadData = async () => {
      setLoading(true);
      onLoading?.(true);

      try {
        const shareholderData = await fetchShareholdersWithCache(ticker);

        if (!shareholderData) {
          setError(`No shareholder data available for ${ticker}`);
          onError?.(`No shareholder data available for ${ticker}`);
          setData(null);
        } else {
          setError(null);
          onError?.(null);
          setData(shareholderData);
        }
      } catch (err) {
        const errorMessage =
          err instanceof Error ? err.message : 'Failed to load shareholder data';
        setError(errorMessage);
        onError?.(errorMessage);
        setData(null);
      } finally {
        setLoading(false);
        onLoading?.(false);
      }
    };

    loadData();
  }, [ticker, onLoading, onError]);

  if (loading) {
    return <div className="shareholder-container loading">Loading shareholder data...</div>;
  }

  if (error || !data) {
    return (
      <div className="shareholder-container error">
        <p>{error || 'No data available'}</p>
      </div>
    );
  }

  const chartData = calculateChartData(data.majorHoldersBreakdown);
  const currency = data.currency || 'USD';

  return (
    <div className="shareholder-container">
      <h3 className="section-title">Major Shareholders</h3>

      <div className="shareholder-content">
        {/* Left Column: Institutional Holders Table */}
        <div className="column column-table">
          <h4 className="column-header">Top Institutional Holders</h4>
          <div className="table-wrapper">
            <table className="shareholders-table">
              <thead>
                <tr>
                  <th>Holder</th>
                  <th>Shares</th>
                  <th>Value</th>
                  <th>% Held</th>
                </tr>
              </thead>
              <tbody>
                {data.topInstitutionalHolders.map((holder, index) => (
                  <tr key={index} className="table-row">
                    <td className="cell-name">{holder.holder}</td>
                    <td className="cell-number">{formatShares(holder.shares)}</td>
                    <td className="cell-number">
                      {formatCurrencyValue(holder.value, currency)}
                    </td>
                    <td className="cell-number">{holder.pctHeld.toFixed(2)}%</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {data.lastUpdated && (
            <p className="data-updated">
              Last updated: {new Date(data.lastUpdated).toLocaleDateString()}
            </p>
          )}
        </div>

        {/* Right Column: Ownership Distribution Chart */}
        <div className="column column-chart">
          <h4 className="column-header">Ownership Distribution</h4>
          <PieChart data={chartData} currency={currency} />
        </div>
      </div>
    </div>
  );
};

export default ShareholderComponent;
