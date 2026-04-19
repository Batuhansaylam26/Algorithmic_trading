# API Comparison

| API | Transport | Latency / Freshness | Data Types | Time Ranges | Markets & Assets* | Best For | Request Example |
|:----|:----------|:--------------------|:-----------|:------------|:------------------|:---------|:----------------|
| EODHD API/Real-Time| Websocket | ~live (<50 ms transport) | US trades & quotes; FX ticks; crypto ticks | n/a (streaming) | US stocks (pre/post supported), Forex & Digital Currencies | Dashboards, signals, market-making tools | GET /users/5 |
| EODHD API/Live (Delayed) | HTTPS REST (pull) | Stocks: 15–20 min delay; Currencies: ~1 min | Latest OHLCV snapshot (1-min updates) | n/a (snapshot feed) | US & Global Stocks, Forex & Digital Currencies | Quote tickers, watchlists, lightweight UIs | ws.send("subscribe") |
| EODHD API/Intraday Historical | HTTPS REST (pull) | Finalized ~2–3 h after US after-hours close| OHLCV bars at 1m / 5m / 1h| 1m: 120 d · 5m: 600 d · 1h: 7200 d | US & Global Stocks, Forex & Digital Currencies | Backtests, analytics, charting | ws.send("subscribe") |