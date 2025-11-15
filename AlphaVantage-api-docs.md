
---

# **Alpha Vantage API Reference (Non-Premium)**

---

# **Table of Contents**

### **1. Time Series Stock Data**

* [TIME_SERIES_INTRADAY](#time_series_intraday)
* [TIME_SERIES_DAILY](#time_series_daily)
* [TIME_SERIES_WEEKLY](#time_series_weekly)
* [TIME_SERIES_WEEKLY_ADJUSTED](#time_series_weekly_adjusted)
* [TIME_SERIES_MONTHLY](#time_series_monthly)
* [TIME_SERIES_MONTHLY_ADJUSTED](#time_series_monthly_adjusted)
* [GLOBAL_QUOTE](#global_quote)
* [SYMBOL_SEARCH](#symbol_search)
* [MARKET_STATUS](#market_status)

### **2. Options Data**

* [HISTORICAL_OPTIONS](#historical_options)

### **3. Alpha Intelligence**

* [NEWS_SENTIMENT](#news_sentiment)
* [EARNINGS_CALL_TRANSCRIPT](#earnings_call_transcript)
* [TOP_GAINERS_LOSERS](#top_gainers_losers)
* [INSIDER_TRANSACTIONS](#insider_transactions)

### **4. Advanced Analytics**

* [ANALYTICS_FIXED_WINDOW](#analytics_fixed_window)
* [ANALYTICS_SLIDING_WINDOW](#analytics_sliding_window)

### **5. Fundamental Data**

* [OVERVIEW](#overview)
* [ETF_PROFILE](#etf_profile)
* [DIVIDENDS](#dividends)
* [SPLITS](#splits)
* [INCOME_STATEMENT](#income_statement)
* [BALANCE_SHEET](#balance_sheet)
* [CASH_FLOW](#cash_flow)
* [SHARES_OUTSTANDING](#shares_outstanding)
* [EARNINGS](#earnings)
* [EARNINGS_ESTIMATES](#earnings_estimates)
* [LISTING_STATUS](#listing_status)
* [EARNINGS_CALENDAR](#earnings_calendar)
* [IPO_CALENDAR](#ipo_calendar)

### **6. Foreign Exchange (FX)**

* [CURRENCY_EXCHANGE_RATE](#currency_exchange_rate)
* [FX_DAILY](#fx_daily)
* [FX_WEEKLY](#fx_weekly)
* [FX_MONTHLY](#fx_monthly)

### **7. Digital & Crypto Currencies**

* [DIGITAL_CURRENCY_DAILY](#digital_currency_daily)
* [DIGITAL_CURRENCY_WEEKLY](#digital_currency_weekly)
* [DIGITAL_CURRENCY_MONTHLY](#digital_currency_monthly)

### **8. Commodities**

* [WTI](#wti)
* [BRENT](#brent)
* [NATURAL_GAS](#natural_gas)
* [COPPER](#copper)
* [ALUMINUM](#aluminum)
* [WHEAT](#wheat)
* [CORN](#corn)
* [COTTON](#cotton)
* [SUGAR](#sugar)
* [COFFEE](#coffee)
* [ALL_COMMODITIES](#all_commodities)

### **9. Economic Indicators**

* [REAL_GDP](#real_gdp)
* [REAL_GDP_PER_CAPITA](#real_gdp_per_capita)
* [TREASURY_YIELD](#treasury_yield)
* [FEDERAL_FUNDS_RATE](#federal_funds_rate)
* [CPI](#cpi)
* [INFLATION](#inflation)
* [RETAIL_SALES](#retail_sales)
* [DURABLES](#durables)
* [UNEMPLOYMENT](#unemployment)
* [NONFARM_PAYROLL](#nonfarm_payroll)

### **10. Technical Indicators**

#### 10.1 Moving Averages

* [SMA](#sma)
* [EMA](#ema)
* [WMA](#wma)
* [DEMA](#dema)
* [TEMA](#tema)
* [TRIMA](#trima)
* [KAMA](#kama)
* [MAMA](#mama)
* [T3](#t3)

#### 10.2 Oscillators & Momentum

* [MACD](#macd)
* [MACDEXT](#macdext)
* [STOCH](#stoch)
* [STOCHF](#stochf)
* [RSI](#rsi)
* [STOCHRSI](#stochrsi)
* [WILLR](#willr)
* [ADX](#adx)
* [ADXR](#adxr)
* [APO](#apo)
* [PPO](#ppo)
* [MOM](#mom)
* [BOP](#bop)
* [CCI](#cci)
* [CMO](#cmo)
* [ROC](#roc)
* [ROCR](#rocr)
* [AROON](#aroon)
* [AROONOSC](#aroonosc)
* [MFI](#mfi)
* [TRIX](#trix)
* [ULTOSC](#ultosc)
* [DX](#dx)
* [MINUS_DI](#minus_di)
* [PLUS_DI](#plus_di)
* [MINUS_DM](#minus_dm)
* [PLUS_DM](#plus_dm)
* [BBANDS](#bbands)

#### 10.3 Volatility Indicators

* [MIDPOINT](#midpoint)
* [MIDPRICE](#midprice)
* [SAR](#sar)
* [TRANGE](#trange)
* [ATR](#atr)
* [NATR](#natr)

#### 10.4 Volume Indicators

* [AD](#ad)
* [ADOSC](#adosc)
* [OBV](#obv)

#### 10.5 Hilbert Transform Indicators

* [HT_TRENDLINE](#ht_trendline)
* [HT_SINE](#ht_sine)
* [HT_TRENDMODE](#ht_trendmode)
* [HT_DCPERIOD](#ht_dcperiod)
* [HT_DCPHASE](#ht_dcphase)
* [HT_PHASOR](#ht_phasor)

---

# **1. Time Series Stock Data**

---

## <a id="time_series_intraday"></a> **TIME_SERIES_INTRADAY**

Returns intraday OHLCV time series (1m, 5m, 15m, 30m, 60m). Supports full month-level historical retrieval.

**Parameters**

* `function`: `TIME_SERIES_INTRADAY`
* `symbol` (required)
* `interval` (required): `1min` `5min` `15min` `30min` `60min`
* `adjusted` (optional): `true` (default) or `false`
* `extended_hours` (optional): `true` or `false`
* `month` (optional): YYYY-MM
* `outputsize` (optional): `compact` | `full`
* `datatype` (optional): `json` | `csv`
* `apikey` (required)

**Examples**

```
https://www.alphavantage.co/query?function=TIME_SERIES_INTRADAY&symbol=IBM&interval=5min&apikey=demo
https://www.alphavantage.co/query?function=TIME_SERIES_INTRADAY&symbol=IBM&interval=5min&outputsize=full&apikey=demo
```

---

## <a id="time_series_daily"></a> **TIME_SERIES_DAILY**

Daily raw OHLCV (20+ years).

**Parameters**

* `function`: `TIME_SERIES_DAILY`
* `symbol` (required)
* `outputsize`: `compact` | `full`
* `datatype`: `json` | `csv`
* `apikey` (required)

**Example**

```
https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol=IBM&apikey=demo
```

---

## <a id="time_series_weekly"></a> **TIME_SERIES_WEEKLY**

Weekly OHLCV time series.

**Parameters**

* `function`: `TIME_SERIES_WEEKLY`
* `symbol` (required)
* `datatype`: `json` | `csv`
* `apikey` (required)

**Example**

```
https://www.alphavantage.co/query?function=TIME_SERIES_WEEKLY&symbol=IBM&apikey=demo
```

---

## <a id="time_series_weekly_adjusted"></a> **TIME_SERIES_WEEKLY_ADJUSTED**

Weekly adjusted OHLCV + dividends.

**Parameters**

* `function`: `TIME_SERIES_WEEKLY_ADJUSTED`
* `symbol` (required)
* `datatype`
* `apikey` (required)

**Example**

```
https://www.alphavantage.co/query?function=TIME_SERIES_WEEKLY_ADJUSTED&symbol=IBM&apikey=demo
```

---

## <a id="time_series_monthly"></a> **TIME_SERIES_MONTHLY**

Monthly OHLCV.

**Parameters**

* `function`: `TIME_SERIES_MONTHLY`
* `symbol` (required)
* `datatype`
* `apikey`

**Example**

```
https://www.alphavantage.co/query?function=TIME_SERIES_MONTHLY&symbol=IBM&apikey=demo
```

---

## <a id="time_series_monthly_adjusted"></a> **TIME_SERIES_MONTHLY_ADJUSTED**

Monthly adjusted OHLCV + dividends.

**Parameters**

* `function`: `TIME_SERIES_MONTHLY_ADJUSTED`
* `symbol` (required)
* `datatype`
* `apikey`

**Example**

```
https://www.alphavantage.co/query?function=TIME_SERIES_MONTHLY_ADJUSTED&symbol=IBM&apikey=demo
```

---

## <a id="global_quote"></a> **GLOBAL_QUOTE**

Latest quote snapshot.

**Parameters**

* `function`: `GLOBAL_QUOTE`
* `symbol` (required)
* `datatype`
* `apikey`

**Example**

```
https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol=IBM&apikey=demo
```

---

## <a id="symbol_search"></a> **SYMBOL_SEARCH**

Symbol auto-complete search.

**Parameters**

* `function`: `SYMBOL_SEARCH`
* `keywords` (required)
* `datatype`
* `apikey`

**Example**

```
https://www.alphavantage.co/query?function=SYMBOL_SEARCH&keywords=tesco&apikey=demo
```

---

## <a id="market_status"></a> **MARKET_STATUS**

Global open/closed market status.

**Parameters**

* `function`: `MARKET_STATUS`
* `apikey` (required)

**Example**

```
https://www.alphavantage.co/query?function=MARKET_STATUS&apikey=demo
```

---

# **2. Options Data**

---

## <a id="historical_options"></a> **HISTORICAL_OPTIONS**

Full historical US options chain, including IV + Greeks, from 2008 onward.

**Parameters**

* `function`: `HISTORICAL_OPTIONS`
* `symbol` (required)
* `date` (optional): YYYY-MM-DD; defaults to previous trading day
* `datatype`: `json` | `csv`
* `apikey` (required)

**Examples**

```
https://www.alphavantage.co/query?function=HISTORICAL_OPTIONS&symbol=IBM&apikey=demo
https://www.alphavantage.co/query?function=HISTORICAL_OPTIONS&symbol=IBM&date=2017-11-15&apikey=demo
```

---

# **3. Alpha Intelligence**

---

## <a id="news_sentiment"></a> **NEWS_SENTIMENT**

Realtime + historical market news enriched with sentiment scores.

**Parameters**

* `function`: `NEWS_SENTIMENT`
* `tickers` (optional): comma-separated symbols
* `topics` (optional)
* `time_from` (optional): `YYYYMMDDTHHMM`
* `time_to` (optional)
* `sort` (optional): `LATEST` (default) | `EARLIEST` | `RELEVANCE`
* `limit` (optional): up to 1000
* `apikey` (required)

**Examples**

```
https://www.alphavantage.co/query?function=NEWS_SENTIMENT&tickers=AAPL&apikey=demo
https://www.alphavantage.co/query?function=NEWS_SENTIMENT&tickers=COIN,CRYPTO:BTC,FOREX:USD&time_from=20220410T0130&limit=1000&apikey=demo
```

---

## <a id="earnings_call_transcript"></a> **EARNINGS_CALL_TRANSCRIPT**

Official earnings call transcript for a specific company + quarter.

**Parameters**

* `function`: `EARNINGS_CALL_TRANSCRIPT`
* `symbol` (required)
* `quarter` (required): e.g., `2024Q1`
* `apikey` (required)

**Example**

```
https://www.alphavantage.co/query?function=EARNINGS_CALL_TRANSCRIPT&symbol=IBM&quarter=2024Q1&apikey=demo
```

---

## <a id="top_gainers_losers"></a> **TOP_GAINERS_LOSERS**

Top 20 US market gainers, losers, and most-active.

**Parameters**

* `function`: `TOP_GAINERS_LOSERS`
* `apikey` (required)

**Example**

```
https://www.alphavantage.co/query?function=TOP_GAINERS_LOSERS&apikey=demo
```

---

## <a id="insider_transactions"></a> **INSIDER_TRANSACTIONS**

Latest and historical insider trades for a public company.

**Parameters**

* `function`: `INSIDER_TRANSACTIONS`
* `symbol` (required)
* `apikey` (required)

**Example**

```
https://www.alphavantage.co/query?function=INSIDER_TRANSACTIONS&symbol=IBM&apikey=demo
```

---

# **4. Advanced Analytics**

---

## <a id="analytics_fixed_window"></a> **ANALYTICS_FIXED_WINDOW**

Fixed-window statistical analytics (mean, variance, correlation, etc.).

**Parameters**

* `function`: `ANALYTICS_FIXED_WINDOW`
* `SYMBOLS` (required): comma-separated symbols
* `RANGE` (required):

  * `full`
  * `{N}day|{N}week|{N}month|{N}year`
  * or specific date range via two `RANGE` params
* `OHLC` (optional): `open` `high` `low` `close`
* `INTERVAL` (required): `1min` `5min` `15min` `30min` `60min` `DAILY` `WEEKLY` `MONTHLY`
* `CALCULATIONS` (required): one or more metrics
* `apikey` (required)

**Example**

```
https://www.alphavantage.co/query?function=ANALYTICS_FIXED_WINDOW&SYMBOLS=AAPL,MSFT,IBM&RANGE=2023-07-01&RANGE=2023-08-31&INTERVAL=DAILY&CALCULATIONS=MEAN,STDDEV,CORRELATION&apikey=demo
```

---

## <a id="analytics_sliding_window"></a> **ANALYTICS_SLIDING_WINDOW**

Sliding-window (rolling) analytics.

**Parameters**

* `function`: `ANALYTICS_SLIDING_WINDOW`
* `SYMBOLS` (required)
* `RANGE` (required)
* `OHLC` (optional)
* `INTERVAL` (required)
* `WINDOW_SIZE` (required): ≥10
* `CALCULATIONS` (required)
* `apikey` (required)

**Example**

```
https://www.alphavantage.co/query?function=ANALYTICS_SLIDING_WINDOW&SYMBOLS=AAPL,IBM&RANGE=2month&INTERVAL=DAILY&WINDOW_SIZE=20&CALCULATIONS=MEAN&apikey=demo
```

---

# **5. Fundamental Data**

---

## <a id="overview"></a> **OVERVIEW**

Company-level financial profile & ratios.

**Parameters**

* `function`: `OVERVIEW`
* `symbol` (required)
* `apikey` (required)

**Example**

```
https://www.alphavantage.co/query?function=OVERVIEW&symbol=IBM&apikey=demo
```

---

## <a id="etf_profile"></a> **ETF_PROFILE**

ETF characteristics + holdings.

**Parameters**

* `function`: `ETF_PROFILE`
* `symbol` (required)
* `apikey` (required)

**Example**

```
https://www.alphavantage.co/query?function=ETF_PROFILE&symbol=QQQ&apikey=demo
```

---

## <a id="dividends"></a> **DIVIDENDS**

Historical + scheduled dividends.

**Parameters**

* `function`: `DIVIDENDS`
* `symbol` (required)
* `datatype` (optional)
* `apikey` (required)

**Example**

```
https://www.alphavantage.co/query?function=DIVIDENDS&symbol=IBM&apikey=demo
```

---

## <a id="splits"></a> **SPLITS**

Historical split events.

**Parameters**

* `function`: `SPLITS`
* `symbol` (required)
* `datatype` (optional)
* `apikey` (required)

**Example**

```
https://www.alphavantage.co/query?function=SPLITS&symbol=IBM&apikey=demo
```

---

## <a id="income_statement"></a> **INCOME_STATEMENT**

Annual & quarterly income statements.

**Parameters**

* `function`: `INCOME_STATEMENT`
* `symbol` (required)
* `apikey` (required)

**Example**

```
https://www.alphavantage.co/query?function=INCOME_STATEMENT&symbol=IBM&apikey=demo
```

---

## <a id="balance_sheet"></a> **BALANCE_SHEET**

Annual & quarterly balance sheets.

**Parameters**

* `function`: `BALANCE_SHEET`
* `symbol` (required)
* `apikey` (required)

**Example**

```
https://www.alphavantage.co/query?function=BALANCE_SHEET&symbol=IBM&apikey=demo
```

---

## <a id="cash_flow"></a> **CASH_FLOW**

Annual & quarterly cash flow statements.

**Parameters**

* `function`: `CASH_FLOW`
* `symbol` (required)
* `apikey` (required)

**Example**

```
https://www.alphavantage.co/query?function=CASH_FLOW&symbol=IBM&apikey=demo
```

---

## <a id="shares_outstanding"></a> **SHARES_OUTSTANDING**

Quarterly diluted + basic shares outstanding.

**Parameters**

* `function`: `SHARES_OUTSTANDING`
* `symbol` (required)
* `datatype` (optional)
* `apikey` (required)

**Example**

```
https://www.alphavantage.co/query?function=SHARES_OUTSTANDING&symbol=MSFT&apikey=demo
```

---

## <a id="earnings"></a> **EARNINGS**

Annual & quarterly EPS; quarterly surprise data.

**Parameters**

* `function`: `EARNINGS`
* `symbol` (required)
* `apikey` (required)

**Example**

```
https://www.alphavantage.co/query?function=EARNINGS&symbol=IBM&apikey=demo
```

---

## <a id="earnings_estimates"></a> **EARNINGS_ESTIMATES**

Forward annual & quarterly EPS + revenue estimates.

**Parameters**

* `function`: `EARNINGS_ESTIMATES`
* `symbol` (required)
* `apikey` (required)

**Example**

```
https://www.alphavantage.co/query?function=EARNINGS_ESTIMATES&symbol=IBM&apikey=demo
```

---

## <a id="listing_status"></a> **LISTING_STATUS**

Active or delisted US equities (CSV).

**Parameters**

* `function`: `LISTING_STATUS`
* `date` (optional)
* `state` (optional): `active` | `delisted`
* `apikey` (required)

**Examples**

```
https://www.alphavantage.co/query?function=LISTING_STATUS&apikey=demo
https://www.alphavantage.co/query?function=LISTING_STATUS&date=2014-07-10&state=delisted&apikey=demo
```

---

## <a id="earnings_calendar"></a> **EARNINGS_CALENDAR**

Upcoming earnings (3/6/12 months).

**Parameters**

* `function`: `EARNINGS_CALENDAR`
* `symbol` (optional)
* `horizon`: `3month` | `6month` | `12month`
* `apikey` (required)

**Example**

```
https://www.alphavantage.co/query?function=EARNINGS_CALENDAR&horizon=3month&apikey=demo
```

---

## <a id="ipo_calendar"></a> **IPO_CALENDAR**

Upcoming IPOs (next 3 months).

**Parameters**

* `function`: `IPO_CALENDAR`
* `apikey` (required)

**Example**

```
https://www.alphavantage.co/query?function=IPO_CALENDAR&apikey=demo
```

---

# **6. Foreign Exchange (FX)**

---

## <a id="currency_exchange_rate"></a> **CURRENCY_EXCHANGE_RATE**

Realtime FX or crypto–to–fiat exchange rate.

**Parameters**

* `function`: `CURRENCY_EXCHANGE_RATE`
* `from_currency` (required)
* `to_currency` (required)
* `apikey` (required)

**Examples**

```
https://www.alphavantage.co/query?function=CURRENCY_EXCHANGE_RATE&from_currency=USD&to_currency=JPY&apikey=demo
https://www.alphavantage.co/query?function=CURRENCY_EXCHANGE_RATE&from_currency=BTC&to_currency=EUR&apikey=demo
```

---

## <a id="fx_daily"></a> **FX_DAILY**

Daily OHLC FX data.

**Parameters**

* `function`: `FX_DAILY`
* `from_symbol` (required)
* `to_symbol` (required)
* `outputsize` (optional): `compact` | `full`
* `datatype` (optional)
* `apikey` (required)

**Example**

```
https://www.alphavantage.co/query?function=FX_DAILY&from_symbol=EUR&to_symbol=USD&apikey=demo
```

---

## <a id="fx_weekly"></a> **FX_WEEKLY**

Weekly OHLC FX data (latest week updates intraday).

**Parameters**

* `function`: `FX_WEEKLY`
* `from_symbol` (required)
* `to_symbol` (required)
* `datatype` (optional)
* `apikey` (required)

**Example**

```
https://www.alphavantage.co/query?function=FX_WEEKLY&from_symbol=EUR&to_symbol=USD&apikey=demo
```

---

## <a id="fx_monthly"></a> **FX_MONTHLY**

Monthly OHLC FX data.

**Parameters**

* `function`: `FX_MONTHLY`
* `from_symbol` (required)
* `to_symbol` (required)
* `datatype` (optional)
* `apikey` (required)

**Example**

```
https://www.alphavantage.co/query?function=FX_MONTHLY&from_symbol=EUR&to_symbol=USD&apikey=demo
```

---

# **7. Digital & Crypto Currencies**

---

## <a id="digital_currency_daily"></a> **DIGITAL_CURRENCY_DAILY**

Daily crypto OHLCV, denominated in both the target market currency and USD.

**Parameters**

* `function`: `DIGITAL_CURRENCY_DAILY`
* `symbol` (required): crypto (e.g., BTC, ETH)
* `market` (required): market currency (e.g., USD, EUR)
* `apikey` (required)

**Example**

```
https://www.alphavantage.co/query?function=DIGITAL_CURRENCY_DAILY&symbol=BTC&market=EUR&apikey=demo
```

---

## <a id="digital_currency_weekly"></a> **DIGITAL_CURRENCY_WEEKLY**

Weekly crypto OHLCV in market currency + USD.

**Parameters**

* `function`: `DIGITAL_CURRENCY_WEEKLY`
* `symbol` (required)
* `market` (required)
* `apikey` (required)

**Example**

```
https://www.alphavantage.co/query?function=DIGITAL_CURRENCY_WEEKLY&symbol=BTC&market=EUR&apikey=demo
```

---

## <a id="digital_currency_monthly"></a> **DIGITAL_CURRENCY_MONTHLY**

Monthly crypto OHLCV in market currency + USD.

**Parameters**

* `function`: `DIGITAL_CURRENCY_MONTHLY`
* `symbol` (required)
* `market` (required)
* `apikey` (required)

**Example**

```
https://www.alphavantage.co/query?function=DIGITAL_CURRENCY_MONTHLY&symbol=BTC&market=EUR&apikey=demo
```

---

# **8. Commodities**

Historical global commodity price series sourced from FRED/IMF.

---

## <a id="wti"></a> **WTI**

West Texas Intermediate (US crude oil) price.

**Parameters**

* `function`: `WTI`
* `interval` (optional): `daily` | `weekly` | `monthly` (default)
* `datatype` (optional)
* `apikey` (required)

**Example**

```
https://www.alphavantage.co/query?function=WTI&interval=monthly&apikey=demo
```

---

## <a id="brent"></a> **BRENT**

Brent (European crude oil) benchmark price.

**Parameters**

* `function`: `BRENT`
* `interval`: `daily` | `weekly` | `monthly`
* `datatype` (optional)
* `apikey` (required)

**Example**

```
https://www.alphavantage.co/query?function=BRENT&interval=monthly&apikey=demo
```

---

## <a id="natural_gas"></a> **NATURAL_GAS**

Henry Hub natural gas spot price.

**Parameters**

* `function`: `NATURAL_GAS`
* `interval`: `daily` | `weekly` | `monthly`
* `datatype` (optional)
* `apikey` (required)

**Example**

```
https://www.alphavantage.co/query?function=NATURAL_GAS&interval=monthly&apikey=demo
```

---

## <a id="copper"></a> **COPPER**

Global copper price index (IMF).

**Parameters**

* `function`: `COPPER`
* `interval`: `monthly` | `quarterly` | `annual`
* `datatype` (optional)
* `apikey` (required)

**Example**

```
https://www.alphavantage.co/query?function=COPPER&interval=monthly&apikey=demo
```

---

## <a id="aluminum"></a> **ALUMINUM**

Global aluminum price index.

**Parameters**

* `function`: `ALUMINUM`
* `interval`: `monthly` | `quarterly` | `annual`
* `datatype` (optional)
* `apikey` (required)

**Example**

```
https://www.alphavantage.co/query?function=ALUMINUM&interval=monthly&apikey=demo
```

---

## <a id="wheat"></a> **WHEAT**

Global wheat price index.

**Parameters**

* `function`: `WHEAT`
* `interval`: `monthly` | `quarterly` | `annual`
* `datatype` (optional)
* `apikey` (required)

**Example**

```
https://www.alphavantage.co/query?function=WHEAT&interval=monthly&apikey=demo
```

---

## <a id="corn"></a> **CORN**

Global corn price index.

**Parameters**

* `function`: `CORN`
* `interval`: `monthly` | `quarterly` | `annual`
* `datatype` (optional)
* `apikey` (required)

**Example**

```
https://www.alphavantage.co/query?function=CORN&interval=monthly&apikey=demo
```

---

## <a id="cotton"></a> **COTTON**

Global cotton price index.

**Parameters**

* `function`: `COTTON`
* `interval`: `monthly` | `quarterly` | `annual`
* `datatype` (optional)
* `apikey` (required)

**Example**

```
https://www.alphavantage.co/query?function=COTTON&interval=monthly&apikey=demo
```

---

## <a id="sugar"></a> **SUGAR**

Global sugar price index.

**Parameters**

* `function`: `SUGAR`
* `interval`: `monthly` | `quarterly` | `annual`
* `datatype` (optional)
* `apikey` (required)

**Example**

```
https://www.alphavantage.co/query?function=SUGAR&interval=monthly&apikey=demo
```

---

## <a id="coffee"></a> **COFFEE**

Global coffee price index.

**Parameters**

* `function`: `COFFEE`
* `interval`: `monthly` | `quarterly` | `annual`
* `datatype` (optional)
* `apikey` (required)

**Example**

```
https://www.alphavantage.co/query?function=COFFEE&interval=monthly&apikey=demo
```

---

## <a id="all_commodities"></a> **ALL_COMMODITIES**

IMF global index of overall commodity prices.

**Parameters**

* `function`: `ALL_COMMODITIES`
* `interval`: `monthly` | `quarterly` | `annual`
* `datatype` (optional)
* `apikey` (required)

**Example**

```
https://www.alphavantage.co/query?function=ALL_COMMODITIES&interval=monthly&apikey=demo
```

---

# **9. Economic Indicators**

---

## <a id="real_gdp"></a> **REAL_GDP**

US Real Gross Domestic Product (GDP), annual or quarterly.

**Parameters**

* `function`: `REAL_GDP`
* `interval` (optional): `annual` (default) | `quarterly`
* `datatype` (optional)
* `apikey` (required)

**Example**

```
https://www.alphavantage.co/query?function=REAL_GDP&interval=annual&apikey=demo
```

---

## <a id="real_gdp_per_capita"></a> **REAL_GDP_PER_CAPITA**

US Real GDP per capita.

**Parameters**

* `function`: `REAL_GDP_PER_CAPITA`
* `datatype` (optional)
* `apikey` (required)

**Example**

```
https://www.alphavantage.co/query?function=REAL_GDP_PER_CAPITA&apikey=demo
```

---

## <a id="treasury_yield"></a> **TREASURY_YIELD**

US Treasury yield curve data (3m, 2y, 5y, 7y, 10y, 30y).

**Parameters**

* `function`: `TREASURY_YIELD`
* `interval` (optional): `daily` | `weekly` | `monthly` (default)
* `maturity` (optional): `3month` | `2year` | `5year` | `7year` | `10year` | `30year`
* `datatype` (optional)
* `apikey` (required)

**Example**

```
https://www.alphavantage.co/query?function=TREASURY_YIELD&interval=monthly&maturity=10year&apikey=demo
```

---

## <a id="federal_funds_rate"></a> **FEDERAL_FUNDS_RATE**

US Federal Funds effective interest rate.

**Parameters**

* `function`: `FEDERAL_FUNDS_RATE`
* `interval` (optional): `daily` | `weekly` | `monthly` (default)
* `datatype` (optional)
* `apikey` (required)

**Example**

```
https://www.alphavantage.co/query?function=FEDERAL_FUNDS_RATE&interval=monthly&apikey=demo
```

---

## <a id="cpi"></a> **CPI**

Consumer Price Index (inflation gauge), monthly or semiannual.

**Parameters**

* `function`: `CPI`
* `interval` (optional): `monthly` (default) | `semiannual`
* `datatype` (optional)
* `apikey` (required)

**Example**

```
https://www.alphavantage.co/query?function=CPI&interval=monthly&apikey=demo
```

---

## <a id="inflation"></a> **INFLATION**

Annual US inflation rate (% change in CPI).

**Parameters**

* `function`: `INFLATION`
* `datatype` (optional)
* `apikey` (required)

**Example**

```
https://www.alphavantage.co/query?function=INFLATION&apikey=demo
```

---

## <a id="retail_sales"></a> **RETAIL_SALES**

Advance Retail Sales (Retail Trade), monthly.

**Parameters**

* `function`: `RETAIL_SALES`
* `datatype` (optional)
* `apikey` (required)

**Example**

```
https://www.alphavantage.co/query?function=RETAIL_SALES&apikey=demo
```

---

## <a id="durables"></a> **DURABLES**

Manufacturers' New Orders: Durable Goods.

**Parameters**

* `function`: `DURABLES`
* `datatype` (optional)
* `apikey` (required)

**Example**

```
https://www.alphavantage.co/query?function=DURABLES&apikey=demo
```

---

## <a id="unemployment"></a> **UNEMPLOYMENT**

US unemployment rate (% of labor force).

**Parameters**

* `function`: `UNEMPLOYMENT`
* `datatype` (optional)
* `apikey` (required)

**Example**

```
https://www.alphavantage.co/query?function=UNEMPLOYMENT&apikey=demo
```

---

## <a id="nonfarm_payroll"></a> **NONFARM_PAYROLL**

Total Nonfarm Payroll (employment level).

**Parameters**

* `function`: `NONFARM_PAYROLL`
* `datatype` (optional)
* `apikey` (required)

**Example**

```
https://www.alphavantage.co/query?function=NONFARM_PAYROLL&apikey=demo
```

---

# **10. Technical Indicators**

This is the largest section of the specification.
Indicators are grouped into:

* **10.1 Moving Averages**
* **10.2 Oscillators & Momentum**
* **10.3 Volatility Indicators**
* **10.4 Volume Indicators**
* **10.5 Hilbert Transform Indicators**

Below is **Part 5**, covering all **Moving Averages**.

---

# **10.1 Moving Averages**

---

## <a id="sma"></a> **SMA — Simple Moving Average**

**Parameters**

* `function`: `SMA`
* `symbol` (required)
* `interval` (required): `1min` `5min` `15min` `30min` `60min` `daily` `weekly` `monthly`
* `month` (optional)
* `time_period` (required)
* `series_type` (required): `open` `high` `low` `close`
* `datatype` (optional)
* `apikey` (required)

**Example**

```
https://www.alphavantage.co/query?function=SMA&symbol=IBM&interval=weekly&time_period=10&series_type=open&apikey=demo
```

---

## <a id="ema"></a> **EMA — Exponential Moving Average**

Same structure as SMA.

**Parameters**

* `function`: `EMA`
* [same as SMA]

**Example**

```
https://www.alphavantage.co/query?function=EMA&symbol=IBM&interval=weekly&time_period=10&series_type=open&apikey=demo
```

---

## <a id="wma"></a> **WMA — Weighted Moving Average**

**Parameters**

* `function`: `WMA`
* Same structure as SMA

**Example**

```
https://www.alphavantage.co/query?function=WMA&symbol=IBM&interval=weekly&time_period=10&series_type=open&apikey=demo
```

---

## <a id="dema"></a> **DEMA — Double Exponential Moving Average**

**Parameters**

* `function`: `DEMA`
* Same structure as SMA

**Example**

```
https://www.alphavantage.co/query?function=DEMA&symbol=IBM&interval=weekly&time_period=10&series_type=open&apikey=demo
```

---

## <a id="tema"></a> **TEMA — Triple Exponential Moving Average**

**Parameters**

* `function`: `TEMA`
* Same structure as SMA

**Example**

```
https://www.alphavantage.co/query?function=TEMA&symbol=IBM&interval=weekly&time_period=10&series_type=open&apikey=demo
```

---

## <a id="trima"></a> **TRIMA — Triangular Moving Average**

**Parameters**

* `function`: `TRIMA`
* Same structure as SMA

**Example**

```
https://www.alphavantage.co/query?function=TRIMA&symbol=IBM&interval=weekly&time_period=10&series_type=open&apikey=demo
```

---

## <a id="kama"></a> **KAMA — Kaufman Adaptive Moving Average**

**Parameters**

* `function`: `KAMA`
* Same structure as SMA

**Example**

```
https://www.alphavantage.co/query?function=KAMA&symbol=IBM&interval=weekly&time_period=10&series_type=open&apikey=demo
```

---

## <a id="mama"></a> **MAMA — MESA Adaptive Moving Average**

**Parameters**

* `function`: `MAMA`
* `symbol` (required)
* `interval` (required)
* `month` (optional)
* `series_type` (required)
* `fastlimit` (optional): default 0.01
* `slowlimit` (optional): default 0.01
* `datatype` (optional)
* `apikey` (required)

**Example**

```
https://www.alphavantage.co/query?function=MAMA&symbol=IBM&interval=daily&series_type=close&fastlimit=0.02&apikey=demo
```

---

## <a id="t3"></a> **T3 — Tilson Moving Average**

**Parameters**

* `function`: `T3`
* Same structure as SMA (uses time_period and series_type)

**Example**

```
https://www.alphavantage.co/query?function=T3&symbol=IBM&interval=weekly&time_period=10&series_type=open&apikey=demo
```

---

# **10.2 Oscillators & Momentum Indicators**

This section includes all classical oscillators such as MACD, RSI, Stochastic, momentum indicators, rate-of-change indicators, and composite oscillators.

---

## <a id="macd"></a> **MACD — Moving Average Convergence Divergence**

**Parameters**

* `function`: `MACD`
* `symbol` (required)
* `interval` (required)
* `month` (optional)
* `series_type` (required)
* `fastperiod` (optional): default `12`
* `slowperiod` (optional): default `26`
* `signalperiod` (optional): default `9`
* `datatype` (optional)
* `apikey` (required)

**Example**

```
https://www.alphavantage.co/query?function=MACD&symbol=IBM&interval=daily&series_type=open&apikey=demo
```

---

## <a id="macdext"></a> **MACDEXT — Extended MACD (Custom MA Types)**

Same as MACD but with configurable moving average types.

**Parameters**

* `function`: `MACDEXT`
* Same as MACD plus:
* `fastmatype`, `slowmatype`, `signalmatype` (optional): values 0–8 (SMA, EMA, WMA, DEMA, TEMA, TRIMA, T3, KAMA, MAMA)

**Example**

```
https://www.alphavantage.co/query?function=MACDEXT&symbol=IBM&interval=daily&series_type=open&apikey=demo
```

---

## <a id="stoch"></a> **STOCH — Stochastic Oscillator**

**Parameters**

* `function`: `STOCH`
* `symbol` (required)
* `interval` (required)
* `month` (optional)
* `fastkperiod` (optional): default `5`
* `slowkperiod` (optional): default `3`
* `slowdperiod` (optional): default `3`
* `slowkmatype`, `slowdmatype` (optional)
* `datatype` (optional)
* `apikey` (required)

**Example**

```
https://www.alphavantage.co/query?function=STOCH&symbol=IBM&interval=daily&apikey=demo
```

---

## <a id="stochf"></a> **STOCHF — Fast Stochastic Oscillator**

**Parameters**

* `function`: `STOCHF`
* Same base structure as STOCH
* Fast-K & Fast-D parameters:

  * `fastkperiod` (optional)
  * `fastdperiod` (optional)
  * `fastdmatype` (optional)

**Example**

```
https://www.alphavantage.co/query?function=STOCHF&symbol=IBM&interval=daily&apikey=demo
```

---

## <a id="rsi"></a> **RSI — Relative Strength Index**

**Parameters**

* `function`: `RSI`
* `symbol` (required)
* `interval` (required)
* `month` (optional)
* `time_period` (required)
* `series_type` (required)
* `datatype` (optional)
* `apikey` (required)

**Example**

```
https://www.alphavantage.co/query?function=RSI&symbol=IBM&interval=weekly&time_period=10&series_type=open&apikey=demo
```

---

## <a id="stochrsi"></a> **STOCHRSI — Stochastic RSI**

**Parameters**

* `function`: `STOCHRSI`
* `symbol` (required)
* `interval` (required)
* `month` (optional)
* `time_period` (required)
* `series_type` (required)
* `fastkperiod` (optional)
* `fastdperiod` (optional)
* `fastdmatype` (optional)
* `datatype` (optional)
* `apikey` (required)

**Example**

```
https://www.alphavantage.co/query?function=STOCHRSI&symbol=IBM&interval=daily&time_period=10&series_type=close&apikey=demo
```

---

## <a id="willr"></a> **WILLR — Williams %R**

**Parameters**

* `function`: `WILLR`
* `symbol` (required)
* `interval` (required)
* `month` (optional)
* `time_period` (required)
* `datatype` (optional)
* `apikey` (required)

**Example**

```
https://www.alphavantage.co/query?function=WILLR&symbol=IBM&interval=daily&time_period=10&apikey=demo
```

---

## <a id="adx"></a> **ADX — Average Directional Movement Index**

**Parameters**

* `function`: `ADX`
* `symbol` (required)
* `interval` (required)
* `month` (optional)
* `time_period` (required)
* `datatype` (optional)
* `apikey` (required)

**Example**

```
https://www.alphavantage.co/query?function=ADX&symbol=IBM&interval=daily&time_period=10&apikey=demo
```

---

## <a id="adxr"></a> **ADXR — Average Directional Movement Rating**

Same as ADX.

**Example**

```
https://www.alphavantage.co/query?function=ADXR&symbol=IBM&interval=daily&time_period=10&apikey=demo
```

---

## <a id="apo"></a> **APO — Absolute Price Oscillator**

**Parameters**

* `function`: `APO`
* `symbol`
* `interval`
* `month`
* `series_type` (required)
* `fastperiod` (optional)
* `slowperiod` (optional)
* `matype` (optional)
* `datatype` (optional)
* `apikey`

**Example**

```
https://www.alphavantage.co/query?function=APO&symbol=IBM&interval=daily&series_type=close&fastperiod=10&apikey=demo
```

---

## <a id="ppo"></a> **PPO — Percentage Price Oscillator**

Structure identical to APO.

**Example**

```
https://www.alphavantage.co/query?function=PPO&symbol=IBM&interval=daily&series_type=close&fastperiod=10&apikey=demo
```

---

## <a id="mom"></a> **MOM — Momentum**

**Parameters**

* `function`: `MOM`
* `symbol`
* `interval`
* `month`
* `time_period`
* `series_type`
* `datatype`
* `apikey`

**Example**

```
https://www.alphavantage.co/query?function=MOM&symbol=IBM&interval=daily&time_period=10&series_type=close&apikey=demo
```

---

## <a id="bop"></a> **BOP — Balance of Power**

**Parameters**

* `function`: `BOP`
* `symbol`
* `interval`
* `month`
* `datatype`
* `apikey`

**Example**

```
https://www.alphavantage.co/query?function=BOP&symbol=IBM&interval=daily&apikey=demo
```

---

## <a id="cci"></a> **CCI — Commodity Channel Index**

**Parameters**

* `function`: `CCI`
* `symbol`
* `interval`
* `month`
* `time_period`
* `datatype`
* `apikey`

**Example**

```
https://www.alphavantage.co/query?function=CCI&symbol=IBM&interval=daily&time_period=10&apikey=demo
```

---

## <a id="cmo"></a> **CMO — Chande Momentum Oscillator**

**Parameters**

* `function`: `CMO`
* `symbol`
* `interval`
* `month`
* `time_period`
* `series_type`
* `datatype`
* `apikey`

**Example**

```
https://www.alphavantage.co/query?function=CMO&symbol=IBM&interval=weekly&time_period=10&series_type=close&apikey=demo
```

---

## <a id="roc"></a> **ROC — Rate of Change**

**Parameters**

* `function`: `ROC`
* `symbol`
* `interval`
* `month`
* `time_period`
* `series_type`
* `datatype`
* `apikey`

**Example**

```
https://www.alphavantage.co/query?function=ROC&symbol=IBM&interval=weekly&time_period=10&series_type=close&apikey=demo
```

---

## <a id="rocr"></a> **ROCR — Rate of Change Ratio**

Identical parameter structure to ROC.

**Example**

```
https://www.alphavantage.co/query?function=ROCR&symbol=IBM&interval=daily&time_period=10&series_type=close&apikey=demo
```

---

## <a id="aroon"></a> **AROON — Aroon Up/Down Indicator**

**Parameters**

* `function`: `AROON`
* `symbol`
* `interval`
* `month`
* `time_period`
* `datatype`
* `apikey`

**Example**

```
https://www.alphavantage.co/query?function=AROON&symbol=IBM&interval=daily&time_period=14&apikey=demo
```

---

## <a id="aroonosc"></a> **AROONOSC — Aroon Oscillator**

Same parameters as AROON.

**Example**

```
https://www.alphavantage.co/query?function=AROONOSC&symbol=IBM&interval=daily&time_period=10&apikey=demo
```

---

## <a id="mfi"></a> **MFI — Money Flow Index**

**Parameters**

* `function`: `MFI`
* `symbol`
* `interval`
* `month`
* `time_period`
* `datatype`
* `apikey`

**Example**

```
https://www.alphavantage.co/query?function=MFI&symbol=IBM&interval=weekly&time_period=10&apikey=demo
```

---

## <a id="trix"></a> **TRIX — Triple Smoothed ROC**

**Parameters**

* `function`: `TRIX`
* `symbol`
* `interval`
* `month`
* `time_period`
* `series_type`
* `datatype`
* `apikey`

**Example**

```
https://www.alphavantage.co/query?function=TRIX&symbol=IBM&interval=daily&time_period=10&series_type=close&apikey=demo
```

---

## <a id="ultosc"></a> **ULTOSC — Ultimate Oscillator**

**Parameters**

* `function`: `ULTOSC`
* `symbol`
* `interval`
* `month`
* `timeperiod1` (optional): default 7
* `timeperiod2` (optional): default 14
* `timeperiod3` (optional): default 28
* `datatype`
* `apikey`

**Example**

```
https://www.alphavantage.co/query?function=ULTOSC&symbol=IBM&interval=daily&apikey=demo
```

---

## <a id="dx"></a> **DX — Directional Movement Index**

**Parameters**

* `function`: `DX`
* `symbol`
* `interval`
* `month`
* `time_period`
* `datatype`
* `apikey`

**Example**

```
https://www.alphavantage.co/query?function=DX&symbol=IBM&interval=daily&time_period=10&apikey=demo
```

---

## <a id="minus_di"></a> **MINUS_DI — Minus Directional Indicator**

Same structure as DX.

**Example**

```
https://www.alphavantage.co/query?function=MINUS_DI&symbol=IBM&interval=weekly&time_period=10&apikey=demo
```

---

## <a id="plus_di"></a> **PLUS_DI — Plus Directional Indicator**

Same structure as DX.

**Example**

```
https://www.alphavantage.co/query?function=PLUS_DI&symbol=IBM&interval=daily&time_period=10&apikey=demo
```

---

## <a id="minus_dm"></a> **MINUS_DM — Minus Directional Movement**

Same structure as DX.

**Example**

```
https://www.alphavantage.co/query?function=MINUS_DM&symbol=IBM&interval=daily&time_period=10&apikey=demo
```

---

## <a id="plus_dm"></a> **PLUS_DM — Plus Directional Movement**

Same structure as DX.

**Example**

```
https://www.alphavantage.co/query?function=PLUS_DM&symbol=IBM&interval=daily&time_period=10&apikey=demo
```

---

## <a id="bbands"></a> **BBANDS — Bollinger Bands**

**Parameters**

* `function`: `BBANDS`
* `symbol`
* `interval`
* `month`
* `time_period`
* `series_type`
* `nbdevup` (optional): default 2
* `nbdevdn` (optional): default 2
* `matype` (optional)
* `datatype`
* `apikey`

**Example**

```
https://www.alphavantage.co/query?function=BBANDS&symbol=IBM&interval=weekly&time_period=5&series_type=close&nbdevup=3&nbdevdn=3&apikey=demo
```

---

# **10.3 Volatility Indicators**

---

## <a id="midpoint"></a> **MIDPOINT — Midpoint Indicator**

MIDPOINT = (highest value + lowest value) / 2 over the given lookback.

**Parameters**

* `function`: `MIDPOINT`
* `symbol` (required)
* `interval` (required)
* `month` (optional)
* `time_period` (required)
* `series_type` (required)
* `datatype` (optional)
* `apikey` (required)

**Example**

```
https://www.alphavantage.co/query?function=MIDPOINT&symbol=IBM&interval=daily&time_period=10&series_type=close&apikey=demo
```

---

## <a id="midprice"></a> **MIDPRICE — Mid-Price Indicator**

MIDPRICE = (highest high + lowest low) / 2 over the lookback.

**Parameters**

* `function`: `MIDPRICE`
* `symbol` (required)
* `interval` (required)
* `month` (optional)
* `time_period` (required)
* `datatype` (optional)
* `apikey`

**Example**

```
https://www.alphavantage.co/query?function=MIDPRICE&symbol=IBM&interval=daily&time_period=10&apikey=demo
```

---

## <a id="sar"></a> **SAR — Parabolic Stop & Reverse**

**Parameters**

* `function`: `SAR`
* `symbol`
* `interval`
* `month` (optional)
* `acceleration` (optional): default 0.01
* `maximum` (optional): default 0.20
* `datatype` (optional)
* `apikey`

**Example**

```
https://www.alphavantage.co/query?function=SAR&symbol=IBM&interval=weekly&acceleration=0.05&maximum=0.25&apikey=demo
```

---

## <a id="trange"></a> **TRANGE — True Range**

**Parameters**

* `function`: `TRANGE`
* `symbol`
* `interval`
* `month` (optional)
* `datatype`
* `apikey`

**Example**

```
https://www.alphavantage.co/query?function=TRANGE&symbol=IBM&interval=daily&apikey=demo
```

---

## <a id="atr"></a> **ATR — Average True Range**

**Parameters**

* `function`: `ATR`
* `symbol`
* `interval`
* `month` (optional)
* `time_period` (required)
* `datatype`
* `apikey`

**Example**

```
https://www.alphavantage.co/query?function=ATR&symbol=IBM&interval=daily&time_period=14&apikey=demo
```

---

## <a id="natr"></a> **NATR — Normalized ATR**

ATR expressed as percentage of price.

**Parameters**

* `function`: `NATR`
* `symbol`
* `interval`
* `month` (optional)
* `time_period` (required)
* `datatype`
* `apikey`

**Example**

```
https://www.alphavantage.co/query?function=NATR&symbol=IBM&interval=weekly&time_period=14&apikey=demo
```

---

# **10.4 Volume Indicators**

---

## <a id="ad"></a> **AD — Chaikin Accumulation/Distribution Line**

**Parameters**

* `function`: `AD`
* `symbol`
* `interval`
* `month` (optional)
* `datatype`
* `apikey`

**Example**

```
https://www.alphavantage.co/query?function=AD&symbol=IBM&interval=daily&apikey=demo
```

---

## <a id="adosc"></a> **ADOSC — Chaikin A/D Oscillator**

**Parameters**

* `function`: `ADOSC`
* `symbol`
* `interval`
* `month` (optional)
* `fastperiod` (optional): default 3
* `slowperiod` (optional): default 10
* `datatype`
* `apikey`

**Example**

```
https://www.alphavantage.co/query?function=ADOSC&symbol=IBM&interval=daily&fastperiod=5&apikey=demo
```

---

## <a id="obv"></a> **OBV — On-Balance Volume**

**Parameters**

* `function`: `OBV`
* `symbol`
* `interval`
* `month` (optional)
* `datatype`
* `apikey`

**Example**

```
https://www.alphavantage.co/query?function=OBV&symbol=IBM&interval=weekly&apikey=demo
```

---

# **10.5 Hilbert Transform Indicators**

These indicators provide instantaneous cycles, phases, and trend-mode insights via the Hilbert Transform.

---

## <a id="ht_trendline"></a> **HT_TRENDLINE — Instantaneous Trendline**

**Parameters**

* `function`: `HT_TRENDLINE`
* `symbol`
* `interval`
* `month`
* `series_type` (required)
* `datatype`
* `apikey`

**Example**

```
https://www.alphavantage.co/query?function=HT_TRENDLINE&symbol=IBM&interval=daily&series_type=close&apikey=demo
```

---

## <a id="ht_sine"></a> **HT_SINE — Sinewave + Leads**

**Parameters**

* `function`: `HT_SINE`
* `symbol`
* `interval`
* `month`
* `series_type` (required)
* `datatype`
* `apikey`

**Example**

```
https://www.alphavantage.co/query?function=HT_SINE&symbol=IBM&interval=daily&series_type=close&apikey=demo
```

---

## <a id="ht_trendmode"></a> **HT_TRENDMODE — Trend vs Cycle Mode**

**Parameters**

* `function`: `HT_TRENDMODE`
* `symbol`
* `interval`
* `month`
* `series_type` (required)
* `datatype`
* `apikey`

**Example**

```
https://www.alphavantage.co/query?function=HT_TRENDMODE&symbol=IBM&interval=weekly&series_type=close&apikey=demo
```

---

## <a id="ht_dcperiod"></a> **HT_DCPERIOD — Dominant Cycle Period**

**Parameters**

* `function`: `HT_DCPERIOD`
* `symbol`
* `interval`
* `month`
* `series_type` (required)
* `datatype`
* `apikey`

**Example**

```
https://www.alphavantage.co/query?function=HT_DCPERIOD&symbol=IBM&interval=daily&series_type=close&apikey=demo
```

---

## <a id="ht_dcphase"></a> **HT_DCPHASE — Dominant Cycle Phase**

**Parameters**

* `function`: `HT_DCPHASE`
* `symbol`
* `interval`
* `month`
* `series_type` (required)
* `datatype`
* `apikey`

**Example**

```
https://www.alphavantage.co/query?function=HT_DCPHASE&symbol=IBM&interval=daily&series_type=close&apikey=demo
```

---

## <a id="ht_phasor"></a> **HT_PHASOR — Phasor Components**

**Parameters**

* `function`: `HT_PHASOR`
* `symbol`
* `interval`
* `month`
* `series_type` (required)
* `datatype`
* `apikey`

**Example**

```
https://www.alphavantage.co/query?function=HT_PHASOR&symbol=IBM&interval=weekly&series_type=close&apikey=demo
```

---