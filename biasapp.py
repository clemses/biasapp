"""
📊 Multi-Timeframe Bias Rule Sheet

✅ General Principle:
Each timeframe (Daily, 4H, 30min) contributes to the session bias through predefined rules. Each rule outputs a partial bias classification (e.g., bullish, bearish, neutral), which is combined into a final session-level classification.

---

🗓 Daily Chart Rules

Volume & Price Structure (Lookback: configurable N days):
- ✅ Count of days where POC increased → Signals directional confidence
- ✅ Days where VWAP is above POC → Suggests bullish conviction
- ✅ Days with closes above VAH → Signals initiative buying
- ✅ Days with closes below VAL → Signals initiative selling

Thresholds:
- Configurable minimums for each of the above (e.g., at least 2 bullish closes to trigger bias).

Daily Bias Outcomes:
- Strong Bullish / Bullish / Neutral / Bearish / Strong Bearish
- Determined by how many bullish vs bearish signals trigger above thresholds

---

⏱ 4H Chart Rules

Recent N 4H candles (configurable):
- ✅ Number of candles with:
  - VWAP > POC → Signals consistent upward pressure
  - Closes above VAH → Suggests breakout behavior
  - Closes below VAL → Suggests breakdown behavior

4H Bias Outcomes:
- 4H Bullish Bias / Neutral / 4H Bearish Bias

---

🕒 30-Min Chart Rules

Short-Term Price Action Structure:
- ✅ Mean change of closing prices (momentum proxy)
- ✅ Mean Δ VWAP (intraday volume-weighted trend)

Thresholds:
- Average change in price above +X → Bullish
- Below −X → Bearish
- Between −X and +X → Flat / Choppy

30min Trend Classification:
- Bullish Trend / Bearish Trend / Flat-Choppy

---

🧠 Final Session Bias (Aggregate Rule Logic)

Combination Logic:
- 🟢 High Confidence Long: Strong Bullish + 4H Bullish + Bullish Trend
- 🔴 High Confidence Short: Strong Bearish + 4H Bearish + Bearish Trend
- 🟡 Mixed or Rotation: Conflicting signals across timeframes
- ⚪️ No Bias: All timeframes are neutral or inconclusive
"""
