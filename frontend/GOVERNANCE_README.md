# Governance Component

A professional, responsive governance dashboard for displaying management, insiders, and institutional holders data from Yahoo Finance.

## Features

- **3-Zone Responsive Layout**
  - Top-Left: Donut chart for ownership distribution
  - Top-Right: Horizontal bar chart for top 5 institutions
  - Bottom: Full-width table of insider roster
- **Dark Mode**: Professional dark theme matching your app
- **Responsive**: Desktop 2-column grid, mobile stacked
- **Type-Safe**: Full TypeScript with governance interfaces
- **Mock Data**: Pre-configured for Apple (AAPL) and LVMH (MC.PA)
- **Cached**: 24-hour data caching

## Component Structure

```
frontend/
├── types/
│   └── governance.ts              # Type definitions
├── services/
│   └── governanceService.ts       # Data & utilities
├── components/
│   ├── GovernanceComponent.tsx    # Main component
│   └── GovernanceComponent.css    # Styles
├── pages/
│   └── governance-example.tsx     # Example usage
└── GOVERNANCE_README.md
```

## Type Definition

```typescript
interface GovernanceData {
  majorHolders: {
    insidersPercent: number;        // e.g., 0.07 (7%)
    institutionsPercent: number;    // e.g., 0.61 (61%)
  };
  institutionalHolders: Array<{
    holder: string;
    shares: number;
  }>;
  insiderRoster: Array<{
    name: string;
    position: string;
    sharesHeld: number;
  }>;
  lastUpdated?: string;
}
```

## Usage

### Basic Implementation

```tsx
import GovernanceComponent from './components/GovernanceComponent';

function App() {
  return <GovernanceComponent ticker="AAPL" />;
}
```

### With Callbacks

```tsx
function App() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  return (
    <GovernanceComponent
      ticker="AAPL"
      onLoading={setLoading}
      onError={setError}
    />
  );
}
```

## Component Zones

### Zone 1: Ownership Distribution (Donut Chart)

**Data Flow:**
1. Takes `majorHolders.insidersPercent` and `majorHolders.institutionsPercent`
2. Calculates Public Float: `100% - insiders - institutions`
3. Renders donut chart with 3 segments

**Colors:**
- Insiders: Gold (`#d4af37`)
- Institutions: Blue (`#2e5da3`)
- Public Float: Gray (`#5a6c7d`)

**Example Data:**
```
Apple (AAPL):
- Insiders: 0.07% (minimal holdings)
- Institutions: 61.04% (large institutional presence)
- Public Float: 38.89%

LVMH (MC.PA):
- Insiders: 49.3% (Arnault family)
- Institutions: 2.18% (limited institutional)
- Public Float: 48.52%
```

### Zone 2: Top Institutional Holders (Horizontal Bar Chart)

**Data Flow:**
1. Takes top 5 from `institutionalHolders` array
2. Calculates percentage of each holder
3. Truncates names to 20 characters for readability
4. Renders horizontal bars (longest first)

**Features:**
- Auto-scales based on largest holder
- Truncated labels: "Vanguard Group, Inc." → "Vanguard Group, I..."
- Color-coded bars (rotation of 5 colors)
- Percentage labels on right

**Example:**
```
Vanguard Group      [████████████] 7.43%
Blackrock Inc       [███████████ ] 6.64%
Berkshire Hathaway  [██████████  ] 5.53%
State Street        [███████     ] 3.87%
Fidelity            [█████       ] 2.91%
```

### Zone 3: Management & Insiders (Data Table)

**Data Flow:**
1. Takes `insiderRoster` array
2. Sorts by `sharesHeld` (descending) to show most invested first
3. Renders table with 3 columns

**Columns:**
- Name: Executive/board member name
- Position: Title/role
- Shares Held: Formatted with thousands separator

**Example:**
```
| Name              | Position                  | Shares Held  |
|-------------------|---------------------------|--------------|
| Tim Cook          | Chief Executive Officer   | 3,525,221    |
| Craig Federighi   | SVP Software Engineering  | 400,000      |
| Luca Maestri      | Chief Financial Officer   | 160,000      |
```

## Service Functions

### `fetchGovernanceDataWithCache(ticker)`
Fetches governance data with caching:
```typescript
const data = await fetchGovernanceDataWithCache('AAPL');
```

### `calculateDonutChartData(majorHolders)`
Transforms major holders to chart format:
```typescript
const chartData = calculateDonutChartData({
  insidersPercent: 0.07,
  institutionsPercent: 61.04
});
// Returns: [
//   { label: 'Insiders', value: 0.07, color: '#d4af37' },
//   { label: 'Institutions', value: 61.04, color: '#2e5da3' },
//   { label: 'Public Float', value: 38.89, color: '#5a6c7d' }
// ]
```

### `calculateBarChartData(holders, totalShares)`
Transforms institutional holders to bar chart format:
```typescript
const chartData = calculateBarChartData(
  [
    { holder: 'Vanguard Group, Inc.', shares: 1235000000 },
    { holder: 'Blackrock Inc.', shares: 1102000000 }
  ],
  1660000000 // Total shares outstanding
);
// Returns: [
//   { name: 'Vanguard Group, I...', percentage: 7.43 },
//   { name: 'Blackrock Inc.', percentage: 6.64 }
// ]
```

### `formatShares(shares)`
Formats number with thousands separator:
```typescript
formatShares(3525221); // "3,525,221"
```

## Styling

### Color Palette
- **Primary BG**: `#0a0e27`
- **Card BG**: `#1a202c`
- **Border**: `#2a3055`
- **Text Primary**: `#ffffff`
- **Text Secondary**: `#a8afc7`

### Ownership Colors
- **Insiders**: `#d4af37` (Gold)
- **Institutions**: `#2e5da3` (Blue)
- **Float**: `#5a6c7d` (Gray)

## Data Integration

### Python Backend (FastAPI)

```python
# src/api/governance.py
from fastapi import APIRouter
import yfinance as yf

@router.get("/governance/{ticker}")
async def get_governance(ticker: str):
    stock = yf.Ticker(ticker)
    return {
        "majorHolders": {
            "insidersPercent": stock.info.get("heldPercentInsiders", 0),
            "institutionsPercent": stock.info.get("heldPercentInstitutions", 0),
        },
        "institutionalHolders": [
            {"holder": name, "shares": count}
            for name, count in zip(
                stock.info.get("holdersNames", []),
                stock.info.get("holdersShares", [])
            )
        ],
        "insiderRoster": [
            {
                "name": insider["name"],
                "position": insider["relation"],
                "sharesHeld": insider["shares"]
            }
            for insider in stock.insider_roster
        ]
    }
```

### Update Service

```typescript
// services/governanceService.ts
export async function fetchGovernanceData(ticker: string) {
  const response = await fetch(`/api/governance/${ticker}`);
  return response.json();
}
```

## Mock Data

Mock data is available for testing:

```typescript
import { mockGovernanceData } from '../services/governanceService';

const appleData = mockGovernanceData['AAPL'];
const lvmhData = mockGovernanceData['MC.PA'];
```

## Responsive Behavior

### Desktop (> 1024px)
- 2-column grid for top zones
- Full-width table below

### Tablet/Mobile (≤ 1024px)
- 1-column layout
- All sections stacked vertically
- Reduced padding

## Browser Support

- Chrome/Edge: Latest 2 versions
- Firefox: Latest 2 versions
- Safari: Latest 2 versions
- Mobile: iOS Safari, Chrome Mobile

## Performance

- **Caching**: 24-hour TTL for data
- **Canvas Rendering**: Lightweight donut chart
- **Lazy Loading**: Data fetches only when ticker changes
- **Memoization**: Components use React.memo where appropriate

## Next Steps

1. **Connect to Real Data**: Update `fetchGovernanceData()` to call your backend
2. **Integration**: Import into main app's Management & Capital tab
3. **Testing**: Test with different tickers
4. **Optimization**: Consider caching layer in backend

## License

MIT
