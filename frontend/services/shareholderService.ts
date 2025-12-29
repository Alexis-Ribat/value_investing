/**
 * Shareholder Data Service
 * Handles fetching and caching shareholder data from Yahoo Finance
 */

import { ShareholderData } from '../types/shareholder';

/**
 * Mock Yahoo Finance data for testing
 * Replace with actual API calls later
 */
export const mockYahooData: Record<string, ShareholderData> = {
  AAPL: {
    majorHoldersBreakdown: {
      insidersPercent: 0.07,
      institutionsPercent: 61.04,
      floatPercent: 38.89,
    },
    topInstitutionalHolders: [
      {
        holder: 'Vanguard Group, Inc.',
        shares: 1235000000,
        value: 195000000000,
        dateReported: '2024-01-15',
        pctHeld: 7.43,
      },
      {
        holder: 'Blackrock Inc.',
        shares: 1102000000,
        value: 174000000000,
        dateReported: '2024-01-15',
        pctHeld: 6.64,
      },
      {
        holder: 'Berkshire Hathaway Inc.',
        shares: 916000000,
        value: 145000000000,
        dateReported: '2024-01-15',
        pctHeld: 5.53,
      },
      {
        holder: 'State Street Corporation',
        shares: 641000000,
        value: 101000000000,
        dateReported: '2024-01-15',
        pctHeld: 3.87,
      },
      {
        holder: 'FMR LLC',
        shares: 482000000,
        value: 76000000000,
        dateReported: '2024-01-15',
        pctHeld: 2.91,
      },
    ],
    currency: 'USD',
    lastUpdated: '2024-01-15',
  },
  'MC.PA': {
    // LVMH mock data
    majorHoldersBreakdown: {
      insidersPercent: 49.3, // Christian Dior SE + Arnault Family
      institutionsPercent: 2.18,
      floatPercent: 48.52,
    },
    topInstitutionalHolders: [
      {
        holder: 'Christian Dior SE',
        shares: 209504613,
        value: 155000000000,
        dateReported: '2024-01-15',
        pctHeld: 42.1,
      },
      {
        holder: 'Arnault Family',
        shares: 35669321,
        value: 26307000000,
        dateReported: '2024-01-15',
        pctHeld: 7.17,
      },
      {
        holder: 'OFI Invest Asset Management SA',
        shares: 697528,
        value: 514000000,
        dateReported: '2024-01-15',
        pctHeld: 0.14,
      },
      {
        holder: 'Rothschild & Co Asset Management',
        shares: 426829,
        value: 315000000,
        dateReported: '2024-01-15',
        pctHeld: 0.086,
      },
      {
        holder: 'State Street Global Advisors',
        shares: 369770,
        value: 273000000,
        dateReported: '2024-01-15',
        pctHeld: 0.074,
      },
    ],
    currency: 'EUR',
    lastUpdated: '2024-01-15',
  },
};

/**
 * Fetch shareholder data for a given ticker
 * @param ticker - Stock ticker symbol
 * @returns ShareholderData or null if not found
 */
export async function fetchShareholders(ticker: string): Promise<ShareholderData | null> {
  try {
    // TODO: Replace with actual API call
    // Option 1: Call Python backend (Streamlit/FastAPI)
    // const response = await fetch(`/api/shareholders/${ticker}`);
    // const data = await response.json();
    // return data;

    // Option 2: Call Node.js yahoo-finance2 service
    // const response = await fetch(`http://localhost:3001/shareholders/${ticker}`);
    // const data = await response.json();
    // return data;

    // For now, return mock data if available
    return mockYahooData[ticker] || null;
  } catch (error) {
    console.error(`Failed to fetch shareholder data for ${ticker}:`, error);
    return null;
  }
}

/**
 * Calculate chart data from major holders breakdown
 * @param breakdown - Major holders breakdown data
 * @returns Array of chart data points
 */
export function calculateChartData(breakdown: { insidersPercent: number; institutionsPercent: number; floatPercent: number }) {
  return [
    {
      label: 'Insiders',
      value: breakdown.insidersPercent,
      color: '#1f3a7d', // Dark blue
    },
    {
      label: 'Institutions',
      value: breakdown.institutionsPercent,
      color: '#2e5da3', // Medium blue
    },
    {
      label: 'Public Float',
      value: breakdown.floatPercent,
      color: '#8fb3f5', // Light blue
    },
  ].filter((item) => item.value > 0); // Only show non-zero values
}

/**
 * Format currency value based on magnitude
 * @param value - Numeric value to format
 * @param currency - Currency code (USD, EUR, etc.)
 * @returns Formatted string
 */
export function formatCurrencyValue(
  value: number,
  currency: string = 'USD',
): string {
  const symbols: Record<string, string> = {
    USD: '$',
    EUR: '€',
    GBP: '£',
    JPY: '¥',
  };

  const symbol = symbols[currency] || '$';

  if (value >= 1e9) {
    return `${symbol}${(value / 1e9).toFixed(1)}B`;
  } else if (value >= 1e6) {
    return `${symbol}${(value / 1e6).toFixed(1)}M`;
  } else if (value >= 1e3) {
    return `${symbol}${(value / 1e3).toFixed(1)}K`;
  }
  return `${symbol}${value.toFixed(2)}`;
}

/**
 * Format share count with thousands separators
 * @param shares - Number of shares
 * @returns Formatted string
 */
export function formatShares(shares: number): string {
  return shares.toLocaleString('en-US', { maximumFractionDigits: 0 });
}

/**
 * Cache for shareholder data (simple in-memory cache)
 */
const cache = new Map<string, { data: ShareholderData | null; timestamp: number }>();
const CACHE_TTL = 86400000; // 24 hours in milliseconds

/**
 * Fetch shareholder data with caching
 * @param ticker - Stock ticker symbol
 * @returns ShareholderData or null if not found
 */
export async function fetchShareholdersWithCache(ticker: string): Promise<ShareholderData | null> {
  const now = Date.now();
  const cached = cache.get(ticker);

  if (cached && now - cached.timestamp < CACHE_TTL) {
    return cached.data;
  }

  const data = await fetchShareholders(ticker);
  cache.set(ticker, { data, timestamp: now });

  return data;
}
