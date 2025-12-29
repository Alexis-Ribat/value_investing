/**
 * Governance Component
 * 3-zone responsive layout:
 * Zone 1 (Top-Left): Donut chart - Ownership breakdown
 * Zone 2 (Top-Right): Horizontal bar chart - Top 5 institutional holders
 * Zone 3 (Bottom - Full Width): Table - Insider roster
 */

import React, { useEffect, useState } from 'react';
import { GovernanceData, DonutChartData, BarChartData } from '../types/governance';
import {
  fetchGovernanceDataWithCache,
  calculateDonutChartData,
  calculateBarChartData,
  formatPercentage,
  formatShares,
  truncateName,
} from '../services/governanceService';
import './GovernanceComponent.css';

interface GovernanceComponentProps {
  ticker: string;
  onLoading?: (loading: boolean) => void;
  onError?: (error: string | null) => void;
}

/**
 * Donut Chart Component (Canvas-based)
 */
const DonutChart: React.FC<{ data: DonutChartData[] }> = ({ data }) => {
  const canvasRef = React.useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    if (!canvasRef.current || data.length === 0) return;

    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const dpr = window.devicePixelRatio || 1;
    const size = 250;
    canvas.width = size * dpr;
    canvas.height = size * dpr;
    ctx.scale(dpr, dpr);

    const centerX = size / 2;
    const centerY = size / 2;
    const radius = 80;
    const donutWidth = 25;

    let startAngle = -Math.PI / 2;

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

      startAngle += sliceAngle;
    });
  }, [data]);

  return (
    <div className="donut-wrapper">
      <canvas ref={canvasRef} className="donut-chart" />
    </div>
  );
};

/**
 * Horizontal Bar Chart Component
 */
const HorizontalBarChart: React.FC<{ data: BarChartData[] }> = ({ data }) => {
  const maxPercentage = Math.max(...data.map((d) => d.percentage), 1);

  return (
    <div className="bar-chart">
      {data.map((item, idx) => (
        <div key={idx} className="bar-item">
          <div className="bar-label">{item.name}</div>
          <div className="bar-container">
            <div
              className="bar-fill"
              style={{
                width: `${(item.percentage / maxPercentage) * 100}%`,
                backgroundColor: ['#d4af37', '#2e5da3', '#5a6c7d', '#00cc96', '#ff4b4b'][idx],
              }}
            />
          </div>
          <div className="bar-value">{item.percentage.toFixed(2)}%</div>
        </div>
      ))}
    </div>
  );
};

/**
 * Main Governance Component
 */
export const GovernanceComponent: React.FC<GovernanceComponentProps> = ({
  ticker,
  onLoading,
  onError,
}) => {
  const [data, setData] = useState<GovernanceData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadData = async () => {
      setLoading(true);
      onLoading?.(true);

      try {
        const governanceData = await fetchGovernanceDataWithCache(ticker);

        if (!governanceData) {
          setError(`No governance data available for ${ticker}`);
          onError?.(`No governance data available for ${ticker}`);
          setData(null);
        } else {
          setError(null);
          onError?.(null);
          setData(governanceData);
        }
      } catch (err) {
        const errorMessage =
          err instanceof Error ? err.message : 'Failed to load governance data';
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
    return <div className="governance-container loading">Loading governance data...</div>;
  }

  if (error || !data) {
    return (
      <div className="governance-container error">
        <p>{error || 'No data available'}</p>
      </div>
    );
  }

  const donutData = calculateDonutChartData(data.majorHolders);
  const barData = calculateBarChartData(data.institutionalHolders);
  const insiderRosterSorted = [...data.insiderRoster].sort(
    (a, b) => b.sharesHeld - a.sharesHeld,
  );

  return (
    <div className="governance-container">
      {/* Top Row: Two Cards */}
      <div className="governance-grid-top">
        {/* Zone 1: Ownership Distribution */}
        <div className="card zone-donut">
          <h4 className="card-title">Ownership Distribution</h4>
          <DonutChart data={donutData} />
          <div className="chart-legend">
            {donutData.map((item) => (
              <div key={item.label} className="legend-item">
                <div
                  className="legend-color"
                  style={{ backgroundColor: item.color }}
                />
                <span className="legend-label">{item.label}</span>
                <span className="legend-value">{item.value.toFixed(1)}%</span>
              </div>
            ))}
          </div>
        </div>

        {/* Zone 2: Top Investors */}
        <div className="card zone-bars">
          <h4 className="card-title">Top Institutional Holders</h4>
          <HorizontalBarChart data={barData} />
        </div>
      </div>

      {/* Zone 3: Insider Roster Table */}
      <div className="card zone-table">
        <h4 className="card-title">Management & Insiders</h4>
        <div className="table-wrapper">
          <table className="insider-table">
            <thead>
              <tr>
                <th>Name</th>
                <th>Position</th>
                <th>Shares Held</th>
              </tr>
            </thead>
            <tbody>
              {insiderRosterSorted.map((insider, idx) => (
                <tr key={idx}>
                  <td className="cell-name">{insider.name}</td>
                  <td className="cell-position">{insider.position}</td>
                  <td className="cell-shares">{formatShares(insider.sharesHeld)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default GovernanceComponent;
