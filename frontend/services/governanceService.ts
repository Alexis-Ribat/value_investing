/**
 * Governance Data Service
 * Handles fetching and processing governance data from Yahoo Finance
 */

import { GovernanceData, DonutChartData, BarChartData } from '../types/governance';

/**
 * Mock governance data for testing
 */
export const mockGovernanceData: Record<string, GovernanceData> = {
  AAPL: {
    majorHolders: {
      insidersPercent: 0.07,
      institutionsPercent: 61.04,
    },
    institutionalHolders: [
      { holder: 'Vanguard Group', shares: 1235000000 },
      { holder: 'Blackrock Inc', shares: 1102000000 },
      { holder: 'Berkshire Hathaway', shares: 916000000 },
      { holder: 'State Street', shares: 641000000 },
      { holder: 'Fidelity Investments', shares: 482000000 },
    ],
    insiderRoster: [
      { name: 'Tim Cook', position: 'Chief Executive Officer', sharesHeld: 3525221 },
      { name: 'Luca Maestri', position: 'Chief Financial Officer', sharesHeld: 160000 },
      { name: 'Katherine Adams', position: 'General Counsel', sharesHeld: 25000 },
      { name: 'Craig Federighi', position: 'SVP Software Engineering', sharesHeld: 400000 },
      { name: 'John Ternus', position: 'SVP Hardware Engineering', sharesHeld: 120000 },
    ],
    lastUpdated: new Date().toISOString(),
  },
  'MC.PA': {
    majorHolders: {
      insidersPercent: 49.3,
      institutionsPercent: 2.18,
    },
    institutionalHolders: [
      { holder: 'Christian Dior SE', shares: 209504613 },
      { holder: 'Arnault Family', shares: 35669321 },
      { holder: 'OFI Invest Asset', shares: 697528 },
      { holder: 'Rothschild & Co', shares: 426829 },
      { holder: 'State Street Global', shares: 369770 },
    ],
    insiderRoster: [
      { name: 'Bernard Arnault', position: 'Chairman & CEO', sharesHeld: 35669321 },
      { name: 'Delphine Arnault', position: 'CEO Christian Dior', sharesHeld: 5000000 },
      { name: 'Alexandre Arnault', position: 'Exec Board Member', sharesHeld: 2500000 },
      { name: 'Antoine Arnault', position: 'Exec Board Member', sharesHeld: 1200000 },
      { name: 'Frédéric Arnault', position: 'Watchmaker', sharesHeld: 800000 },
    ],
    lastUpdated: new Date().toISOString(),
  },
};

/**
 * Fetch governance data for a given ticker
 */
export async function fetchGovernanceData(ticker: string): Promise<GovernanceData | null> {
  try {
    // TODO: Replace with actual API call to backend
    // return await fetch(`/api/governance/${ticker}`).then(r => r.json());

    // For now, return mock data if available
    return mockGovernanceData[ticker] || null;
  } catch (error) {
    console.error(`Failed to fetch governance data for ${ticker}:`, error);
    return null;
  }
}

/**
 * Calculate donut chart data from major holders
 */
export function calculateDonutChartData(majorHolders: {
  insidersPercent: number;
  institutionsPercent: number;
}): DonutChartData[] {
  const publicPercent = Math.max(
    0,
    100 - majorHolders.insidersPercent - majorHolders.institutionsPercent,
  );

  const data: DonutChartData[] = [];

  if (majorHolders.insidersPercent > 0) {
    data.push({
      label: 'Insiders',
      value: majorHolders.insidersPercent,
      color: '#d4af37', // Gold
    });
  }

  if (majorHolders.institutionsPercent > 0) {
    data.push({
      label: 'Institutions',
      value: majorHolders.institutionsPercent,
      color: '#2e5da3', // Blue
    });
  }

  if (publicPercent > 0) {
    data.push({
      label: 'Public Float',
      value: publicPercent,
      color: '#5a6c7d', // Gray
    });
  }

  return data;
}

/**
 * Calculate bar chart data from institutional holders
 * Takes top 5 and formats for horizontal bar chart
 */
export function calculateBarChartData(
  institutionalHolders: Array<{ holder: string; shares: number }>,
  totalShares: number = 1000000000,
): BarChartData[] {
  return institutionalHolders
    .slice(0, 5) // Top 5
    .map((holder) => ({
      name: truncateName(holder.holder, 20),
      percentage: (holder.shares / totalShares) * 100,
    }))
    .sort((a, b) => b.percentage - a.percentage);
}

/**
 * Truncate long names for readability
 */
export function truncateName(name: string, maxLength: number = 20): string {
  if (name.length <= maxLength) return name;
  return name.substring(0, maxLength - 3) + '...';
}

/**
 * Format percentage for display
 */
export function formatPercentage(value: number): string {
  return `${(value * 100).toFixed(2)}%`;
}

/**
 * Format shares with thousands separator
 */
export function formatShares(shares: number): string {
  return shares.toLocaleString('en-US', { maximumFractionDigits: 0 });
}

/**
 * Cache governance data
 */
const cache = new Map<string, { data: GovernanceData | null; timestamp: number }>();
const CACHE_TTL = 86400000; // 24 hours

/**
 * Fetch governance data with caching
 */
export async function fetchGovernanceDataWithCache(
  ticker: string,
): Promise<GovernanceData | null> {
  const now = Date.now();
  const cached = cache.get(ticker);

  if (cached && now - cached.timestamp < CACHE_TTL) {
    return cached.data;
  }

  const data = await fetchGovernanceData(ticker);
  cache.set(ticker, { data, timestamp: now });

  return data;
}
