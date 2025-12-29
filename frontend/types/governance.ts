/**
 * Governance Data Types
 * Interface matching Yahoo Finance governance structure
 */

export interface MajorHolders {
  /** Percentage of shares held by insiders (0-100) */
  insidersPercent: number;
  /** Percentage of shares held by institutions (0-100) */
  institutionsPercent: number;
}

export interface InstitutionalHolder {
  /** Name of the institution */
  holder: string;
  /** Number of shares held */
  shares: number;
}

export interface InsiderRoster {
  /** Name of the insider */
  name: string;
  /** Position/Title */
  position: string;
  /** Number of shares held */
  sharesHeld: number;
}

export interface GovernanceData {
  /** Major holders breakdown (insiders vs institutions) */
  majorHolders: MajorHolders;
  /** Top institutional holders */
  institutionalHolders: InstitutionalHolder[];
  /** Insider roster (executives, board members) */
  insiderRoster: InsiderRoster[];
  /** Last updated timestamp */
  lastUpdated?: string;
}

/** Chart data point for donut chart */
export interface DonutChartData {
  label: string;
  value: number;
  color: string;
}

/** Chart data point for horizontal bar chart */
export interface BarChartData {
  name: string;
  percentage: number;
}
