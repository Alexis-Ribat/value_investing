# Shareholder Component - TypeScript Frontend

A responsive, dark-mode shareholder data component built with TypeScript and React. Displays institutional shareholders in a table format with an ownership distribution pie chart.

## Features

- **Type-Safe**: Full TypeScript support with interfaces matching Yahoo Finance data structure
- **Responsive**: 2-column layout on desktop, stacked on mobile
- **Dark Mode**: Professional dark theme with proper contrast
- **Cached Data**: 24-hour caching to minimize API calls
- **Mock Data**: Built-in mock data for testing (Apple, LVMH)
- **Accessibility**: Semantic HTML, keyboard navigation support

## Project Structure

```
frontend/
├── types/
│   └── shareholder.ts           # Type definitions
├── services/
│   └── shareholderService.ts    # Data fetching & utilities
├── components/
│   ├── ShareholderComponent.tsx # Main React component
│   └── ShareholderComponent.css # Styles
├── pages/
│   └── example.tsx              # Example usage
└── README.md
```

## Type Definitions

### `ShareholderData`
Main interface matching Yahoo Finance structure:

```typescript
interface ShareholderData {
  majorHoldersBreakdown: {
    insidersPercent: number;
    institutionsPercent: number;
    floatPercent: number;
  };
  topInstitutionalHolders: {
    holder: string;
    shares: number;
    value: number;
    dateReported: string;
    pctHeld: number;
  }[];
  currency?: string;
  lastUpdated?: string;
}
```

## Usage

### Basic Implementation

```tsx
import ShareholderComponent from './components/ShareholderComponent';

function App() {
  return <ShareholderComponent ticker="AAPL" />;
}
```

### With Callbacks

```tsx
function App() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  return (
    <ShareholderComponent
      ticker="AAPL"
      onLoading={setLoading}
      onError={setError}
    />
  );
}
```

## Available Utilities

### `fetchShareholdersWithCache(ticker)`
Fetches shareholder data with 24-hour caching:

```typescript
const data = await fetchShareholdersWithCache('AAPL');
```

### `calculateChartData(breakdown)`
Converts breakdown data to chart format:

```typescript
const chartData = calculateChartData(data.majorHoldersBreakdown);
// Returns: [{ label: 'Insiders', value: 0.07, color: '#1f3a7d' }, ...]
```

### `formatCurrencyValue(value, currency)`
Formats numbers as currency:

```typescript
formatCurrencyValue(195000000000, 'USD'); // Returns: "$195.0B"
formatCurrencyValue(155000000000, 'EUR'); // Returns: "€155.0B"
```

### `formatShares(shares)`
Formats share counts with separators:

```typescript
formatShares(1235000000); // Returns: "1,235,000,000"
```

## Data Integration

### Option 1: Python Backend (Streamlit/FastAPI)

Modify `shareholderService.ts`:

```typescript
export async function fetchShareholders(ticker: string): Promise<ShareholderData | null> {
  const response = await fetch(`http://localhost:8501/api/shareholders/${ticker}`);
  return response.json();
}
```

### Option 2: Node.js Yahoo Finance Service

```typescript
export async function fetchShareholders(ticker: string): Promise<ShareholderData | null> {
  const response = await fetch(`http://localhost:3001/shareholders/${ticker}`);
  return response.json();
}
```

### Option 3: Direct API Integration

```typescript
import { queryTechnicals } from 'yahoo-finance2/dist/esm/src';

export async function fetchShareholders(ticker: string): Promise<ShareholderData | null> {
  const quote = await queryTechnicals(ticker);
  // Transform quote into ShareholderData format
}
```

## Styling

### Color Palette

- **Primary BG**: `#0a0e27`
- **Secondary BG**: `#141829`
- **Tertiary BG**: `#1a1f3a`
- **Text**: `#ffffff` (primary), `#a8afc7` (secondary)
- **Border**: `#2a3055`

### Chart Colors

- **Insiders**: `#1f3a7d` (dark blue)
- **Institutions**: `#2e5da3` (medium blue)
- **Float**: `#8fb3f5` (light blue)

## Mock Data

Pre-configured mock data is available for testing:

```typescript
import { mockYahooData } from '../services/shareholderService';

const appleData = mockYahooData['AAPL'];
const lvmhData = mockYahooData['MC.PA'];
```

## Next Steps

1. **Connect to Real Data Source**:
   - Update `fetchShareholders()` in `shareholderService.ts`
   - Choose: Python backend, Node.js service, or direct API

2. **Integrate with Main Application**:
   - Add to your management & capital page
   - Pass dynamic ticker from parent component

3. **Testing**:
   - Unit tests for data transformation functions
   - Component tests for React component
   - Integration tests for API calls

4. **Performance Optimization**:
   - Consider using React Query or SWR for caching
   - Implement request deduplication
   - Add loading states and error boundaries

## Browser Support

- Chrome/Edge: Latest 2 versions
- Firefox: Latest 2 versions
- Safari: Latest 2 versions
- Mobile browsers: iOS Safari, Chrome Mobile

## License

MIT
