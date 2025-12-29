/**
 * Shareholder Data Types matching Yahoo Finance structure
 */

export interface MajorHoldersBreakdown {
  /** Percentage of shares held by insiders */
  insidersPercent: number;
  /** Percentage of shares held by institutions */
  institutionsPercent: number;
  /** Estimated float percentage */
  floatPercent: number;
}

export interface TopInstitutionalHolder {
  /** Name of the institution */
  holder: string;
  /** Number of shares held */
  shares: number;
  /** Value of holdings in currency */
  value: number;
  /** Date the holding was reported */
  dateReported: string;
  /** Percentage of outstanding shares held */
  pctHeld: number;
}

export interface ShareholderData {
  /** Breakdown of ownership by type (insiders, institutions, float) */
  majorHoldersBreakdown: MajorHoldersBreakdown;
  /** Top institutional shareholders */
  topInstitutionalHolders: TopInstitutionalHolder[];
  /** Currency code (USD, EUR, etc.) */
  currency?: string;
  /** Last updated timestamp */
  lastUpdated?: string;
}

export interface ShareholderChartData {
  label: string;
  value: number;
  color: string;
}
