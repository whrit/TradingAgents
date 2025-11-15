# Alpaca Data Vendor - Quick Start Guide

## Setup

### 1. Set Environment Variables

Add to your `.env` file or export in your shell:

```bash
export ALPACA_API_KEY="your_alpaca_api_key_here"
export ALPACA_SECRET_KEY="your_alpaca_secret_key_here"
```

**Getting Alpaca API Keys:**
1. Sign up at [alpaca.markets](https://alpaca.markets)
2. Navigate to Dashboard → API Keys
3. Generate new API keys (paper or live trading)

### 2. Configure Data Vendor

#### Option A: Use Alpaca as Primary Vendor

Edit your config file or environment:

```python
# config.py or similar
{
    "data_vendors": {
        "core_stock_apis": "alpaca"
    }
}
```

#### Option B: Use Alpaca with Fallback

```python
{
    "data_vendors": {
        "core_stock_apis": "alpaca,yfinance"
    }
}
```

If Alpaca rate limit is exceeded, it will automatically fall back to yfinance.

## Usage Examples

### Example 1: Get Historical Stock Data

```python
from tradingagents.dataflows.interface import route_to_vendor

# Get AAPL data for a date range
data = route_to_vendor(
    'get_stock_data',
    'AAPL',
    '2025-01-01',
    '2025-01-14'
)

print(data)
# Output:
# # Stock data for AAPL from 2025-01-01 to 2025-01-14
# # Total records: 10
# # Data retrieved on: 2025-11-14 19:04:16
# # Data source: Alpaca Markets
#
# Date,Open,High,Low,Close,Volume
# 2025-01-02,150.0,152.0,149.5,151.5,1000000
# 2025-01-03,151.5,153.0,150.0,152.0,1200000
# ...
```

### Example 2: Direct Alpaca Function Call

```python
from tradingagents.dataflows.alpaca.data import get_stock_data

# Direct call (bypasses vendor routing)
data = get_stock_data('TSLA', '2025-01-10', '2025-01-14')
```

### Example 3: Get Latest Quote

```python
from tradingagents.dataflows.alpaca.data import get_latest_quote

quote = get_latest_quote('NVDA')
print(quote)
# Output:
# {
#     'symbol': 'NVDA',
#     'bid': 500.25,
#     'ask': 500.35,
#     'bid_size': 100,
#     'ask_size': 200,
#     'timestamp': '2025-01-14T15:30:00Z'
# }
```

### Example 4: Get Intraday Bar Data

```python
from tradingagents.dataflows.alpaca.data import get_bars

# Get hourly bars
bars = get_bars(
    symbol='GOOGL',
    timeframe='1Hour',
    start='2025-01-14',
    end='2025-01-14'
)

print(bars)
# Output:
# # Bar data for GOOGL (1Hour)
# # Period: 2025-01-14 to 2025-01-14
# # Total bars: 7
#
# Timestamp,Open,High,Low,Close,Volume,VWAP
# 2025-01-14 09:30:00,150.0,151.0,149.5,150.5,100000,150.25
# 2025-01-14 10:30:00,150.5,151.5,150.0,151.0,120000,150.75
# ...
```

### Example 5: Use in Trading Agent

```python
from agents.utils.stock_data import get_stock_data

# This will use the configured vendor (Alpaca if configured)
data = get_stock_data('AAPL', '2025-01-01', '2025-01-14')

# Parse the CSV data
import pandas as pd
from io import StringIO

# Skip header comments (lines starting with #)
lines = [line for line in data.split('\n') if not line.startswith('#')]
csv_data = '\n'.join(lines)

df = pd.read_csv(StringIO(csv_data), index_col='Date', parse_dates=True)
print(df.head())
```

## Available Timeframes for Bars

- **Minute bars:** `1Min`, `5Min`, `15Min`, `30Min`
- **Hour bars:** `1Hour`, `2Hour`, `4Hour`
- **Day/Week/Month:** `1Day`, `1Week`, `1Month`

## Rate Limits

Alpaca has different rate limits based on account tier:

- **Free tier:** 200 requests per minute per API key group
- **Unlimited tier:** Higher limits

The implementation automatically handles rate limits by:
1. Detecting 429 status codes
2. Raising `AlpacaRateLimitError`
3. Triggering fallback to alternative vendors (if configured)

## Error Handling

### Rate Limit Errors

```python
from tradingagents.dataflows.alpaca.common import AlpacaRateLimitError

try:
    data = get_stock_data('AAPL', '2025-01-01', '2025-01-14')
except AlpacaRateLimitError as e:
    print(f"Rate limit exceeded: {e}")
    # Will automatically fall back to yfinance if configured
```

### Authentication Errors

```python
from tradingagents.dataflows.alpaca.common import AlpacaAuthenticationError

try:
    data = get_stock_data('AAPL', '2025-01-01', '2025-01-14')
except AlpacaAuthenticationError as e:
    print(f"Authentication failed: {e}")
    print("Check your ALPACA_API_KEY and ALPACA_SECRET_KEY")
```

### General API Errors

```python
from tradingagents.dataflows.alpaca.common import AlpacaAPIError

try:
    data = get_stock_data('AAPL', '2025-01-01', '2025-01-14')
except AlpacaAPIError as e:
    print(f"API error: {e}")
    print(f"Status code: {e.status_code}")
```

## Testing Your Integration

### Quick Test Script

Save as `test_alpaca.py`:

```python
#!/usr/bin/env python3
"""Quick test of Alpaca integration."""

import os
from tradingagents.dataflows.alpaca.data import get_stock_data, get_latest_quote

# Check credentials
api_key = os.getenv("ALPACA_API_KEY")
secret_key = os.getenv("ALPACA_SECRET_KEY")

if not api_key or not secret_key:
    print("❌ Missing credentials!")
    print("Set ALPACA_API_KEY and ALPACA_SECRET_KEY environment variables")
    exit(1)

print("✅ Credentials found")
print(f"API Key: {api_key[:8]}...")

# Test 1: Get stock data
print("\n📊 Test 1: Getting AAPL historical data...")
try:
    data = get_stock_data('AAPL', '2025-01-10', '2025-01-14')
    if "Stock data for AAPL" in data and "Alpaca Markets" in data:
        print("✅ Successfully retrieved historical data")
        print(data[:200] + "...")
    else:
        print("⚠️  Unexpected data format")
        print(data[:200])
except Exception as e:
    print(f"❌ Error: {e}")

# Test 2: Get latest quote
print("\n💹 Test 2: Getting AAPL latest quote...")
try:
    quote = get_latest_quote('AAPL')
    if 'symbol' in quote and 'bid' in quote:
        print("✅ Successfully retrieved quote")
        print(f"   Symbol: {quote['symbol']}")
        print(f"   Bid: ${quote['bid']:.2f}")
        print(f"   Ask: ${quote['ask']:.2f}")
    else:
        print("⚠️  Unexpected quote format")
        print(quote)
except Exception as e:
    print(f"❌ Error: {e}")

print("\n🎉 Alpaca integration test complete!")
```

Run with:
```bash
python3 test_alpaca.py
```

## Comparison with Other Vendors

| Feature | Alpaca | yfinance | Alpha Vantage |
|---------|--------|----------|---------------|
| Real-time data | ✅ Yes | ❌ No | ❌ Limited |
| Intraday bars | ✅ Yes | ✅ Yes | ✅ Yes |
| Rate limits | Moderate | None | Strict (5/min) |
| Free tier | ✅ Yes | ✅ Yes | ✅ Yes |
| API key required | ✅ Yes | ❌ No | ✅ Yes |
| Data latency | Low | 15min delay | 15min delay |
| Historical depth | ~5 years | ~20 years | ~20 years |

## Best Practices

### 1. Use Fallback Configuration

Always configure a fallback vendor:

```python
{
    "data_vendors": {
        "core_stock_apis": "alpaca,yfinance"
    }
}
```

### 2. Handle Rate Limits

If you're making many requests, implement delays:

```python
import time

symbols = ['AAPL', 'GOOGL', 'MSFT', 'TSLA', 'NVDA']

for symbol in symbols:
    data = get_stock_data(symbol, '2025-01-01', '2025-01-14')
    # Process data...
    time.sleep(0.5)  # 500ms delay to avoid rate limits
```

### 3. Cache Responses

For repeated requests, cache the data:

```python
import functools

@functools.lru_cache(maxsize=100)
def cached_get_stock_data(symbol, start, end):
    return get_stock_data(symbol, start, end)
```

### 4. Use Appropriate Timeframes

Choose the right timeframe for your use case:
- Day trading: `1Min`, `5Min`
- Swing trading: `1Hour`, `1Day`
- Long-term analysis: `1Day`, `1Week`

## Troubleshooting

### Issue: "No data found"

**Cause:** Symbol invalid or no data for date range

**Solution:**
- Verify symbol is correct (use uppercase)
- Check date range is valid (not weekends/holidays)
- Try a different date range

### Issue: "Authentication failed"

**Cause:** Invalid or missing API credentials

**Solution:**
1. Verify credentials in Alpaca dashboard
2. Check environment variables are set correctly
3. Ensure no extra spaces in credentials
4. Try regenerating API keys

### Issue: "Rate limit exceeded"

**Cause:** Too many requests in short time

**Solution:**
1. Configure fallback vendor: `"alpaca,yfinance"`
2. Add delays between requests
3. Upgrade Alpaca account tier
4. Implement request batching

### Issue: "Connection timeout"

**Cause:** Network issues or API downtime

**Solution:**
1. Check internet connection
2. Verify Alpaca API status
3. Client has automatic retry (3 attempts)
4. Configure fallback vendor

## Additional Resources

- **Alpaca Documentation:** https://alpaca.markets/docs/
- **Alpaca Data API:** https://alpaca.markets/docs/api-references/market-data-api/
- **Project Tests:** `/tests/dataflows/test_alpaca*.py`
- **Implementation:** `/tradingagents/dataflows/alpaca/`

## Support

For issues specific to this integration:
1. Check test files for examples
2. Review error messages carefully
3. Ensure credentials are valid
4. Try fallback vendor configuration

For Alpaca API issues:
- Contact Alpaca support: https://alpaca.markets/support
- Check API status: https://status.alpaca.markets/
