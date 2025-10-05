# Quick Insights Feature - Real-Time AI Analysis

## 🎯 Overview

The **Quick Insights** feature provides 4 pre-configured AI prompts that leverage Gemini LLM to deliver instant, context-aware energy management insights. These buttons enable users to get expert analysis without typing complex questions.

---

## 🚀 Features Added

### **Frontend Enhancement** (`frontend/src/main.jsx`)

#### **4 Premade Quick Insight Buttons**

Located in the AI Insight card, users can now click:

1. **⚡ Optimize Now**
   - **Prompt**: "Analyze current battery status and provide optimization recommendations for the next 2 hours based on real-time telemetry."
   - **Use Case**: Get instant optimization advice based on current SoC, voltage, temperature
   - **Response Format**: Status assessment → 2-4 actionable steps → Risk warnings

2. **💰 Cost Analysis**
   - **Prompt**: "Calculate potential cost savings if I follow the current RL advisory decision vs baseline grid-only approach. Include carbon emissions impact."
   - **Use Case**: Understand financial and environmental benefits of AI decisions
   - **Response Format**: Cost comparison (₹) → Savings percentage → CO₂ emissions avoided

3. **⚠️ Risk Check**
   - **Prompt**: "Review active alerts and RL decision history. Identify any risks or unusual patterns in the last hour and suggest preventive actions."
   - **Use Case**: Proactive risk monitoring for battery health, thermal issues, grid anomalies
   - **Response Format**: Risk identification → Pattern analysis → Mitigation actions

4. **🔋 Backup Status**
   - **Prompt**: "Based on current SoC, load patterns, and forecast, estimate how long the battery can sustain the load without grid import. Suggest actions to extend backup time."
   - **Use Case**: Grid outage preparedness, energy independence planning
   - **Response Format**: Estimated backup hours → Load optimization tips → Recharge strategy

---

### **Backend Enhancement** (`backend/app/ai_gemini.py`)

#### **Enhanced System Prompt**

The `build_chat_prompt()` function now includes a comprehensive system prompt that instructs Gemini to:

```python
"You are an expert Energy Management System AI advisor with deep knowledge of battery optimization, 
renewable energy, grid economics, and reinforcement learning. You have real-time access to:
- Live telemetry (battery SoC, voltage, temperature, power flows)
- RL agent decisions (semantic power splits: battery/grid/EV in kW)
- Active alerts and safety flags
- Battery forecast (SoC predictions, risk scores)
- Decision history with cost/emissions data

Your responses must be:
1. DATA-DRIVEN: Reference specific numbers from telemetry (e.g., 'At 34% SoC and 149V...')
2. ACTIONABLE: Provide 2-4 concrete next-hour actions with timing and power levels
3. COST-AWARE: Estimate ₹ savings or costs when relevant
4. RISK-CONSCIOUS: Identify battery health, thermal, or grid risks with mitigation
5. INTERPRETABLE: Explain WHY RL made its decision using semantic splits
6. CONCISE: 150-200 words max, bullet points for actions/risks

Format: Brief status → Actions (numbered) → Risks (if any) → Cost/CO₂ impact (if applicable)"
```

#### **Enriched Context Injection**

The context passed to Gemini now includes:

```json
{
  "tel": {
    "soc": 34.2,
    "temp": 28.5,
    "voltage": 149.89,
    "current": -12.4,
    "power": -1.86
  },
  "rl_summary": "1:DISCHARGE_BATTERY_TO_LOAD conf=0.89 impact=2.4kW; 2:HOLD conf=0.76 impact=0kW",
  "last_decision": { /* semantic split */ },
  "alerts_top": ["LOW_SOC:WARN", "THERMAL_RISK:INFO"],
  "forecast_min_soc": 18.3,
  "forecast_horizon": 60,
  "recent_decision_count": 12,
  "timestamp": 1728107400.123
}
```

---

## 📊 Technical Implementation

### **UI Flow**

```
User clicks "⚡ Optimize Now" 
  → Button disabled (loading state)
  → Frontend calls onAsk(premade_prompt)
  → POST /ai/chat/stream with device_id + question
  → Backend builds enhanced context
  → Gemini API call with 150-200 word limit
  → Streaming response chunks displayed incrementally
  → Actions/Risks extracted client-side
  → Chat history updated + persisted to DB
  → Button re-enabled
```

### **Response Example**

**User clicks: 💰 Cost Analysis**

**Gemini Response:**
```
At 34.2% SoC (149V, 28°C), the RL agent recommends discharging battery at 2.4 kW 
to meet load, avoiding peak grid tariff.

COST COMPARISON (next 15 min):
- AI Decision: ₹8.40 (battery discharge + minimal grid top-up)
- Baseline (grid-only): ₹11.20
- SAVINGS: ₹2.80 (25%)

CARBON IMPACT:
- AI uses stored solar → 0.34 kg CO₂ avoided vs. grid
- Equivalent to 0.8 kWh renewable offset

ACTIONS:
1. Continue discharge at 2.4 kW for next 30 min (SoC drops to ~28%)
2. Grid will import 0.6 kW to meet excess load (cleaner mix expected 4-5 PM)
3. Solar surplus forecast at 5:15 PM → auto-recharge to 45%

RISK: SoC may drop below 20% if load spikes. Monitor alerts.
```

---

## 🎨 UI Design

### **Button Styling**

```css
.btn-ghost {
  background: rgba(255,255,255,0.05);
  border: 1px solid var(--color-border);
  font-size: 0.55rem;
  padding: 4px 8px;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-ghost:hover {
  background: rgba(255,255,255,0.1);
  border-color: var(--color-accent-cyan);
}

.btn-ghost:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
```

### **Button Layout**

- Horizontal flex row with 4px gap
- Wraps on small screens (flexWrap: 'wrap')
- 4px margin-bottom spacing from input field
- Icons (⚡💰⚠️🔋) for quick visual recognition

---

## 📈 Benefits

### **1. User Experience**
- **Zero Learning Curve**: Click instead of typing complex queries
- **Instant Insights**: No need to formulate perfect questions
- **Consistent Quality**: Prompts engineered for optimal responses
- **Mobile-Friendly**: Large touch targets, no keyboard required

### **2. System Intelligence**
- **Context-Aware**: Gemini receives full telemetry + RL state
- **Real-Time**: Responses based on live data, not cached summaries
- **Interpretable**: Explains RL decisions in plain language
- **Actionable**: Numbered steps with timing and power levels

### **3. Cost Efficiency**
- **Token Optimization**: 150-200 word responses reduce API costs
- **Caching**: Insight generation cached for 30s per device
- **Fallback Mode**: Stub responses when API unavailable (no errors)

### **4. Scalability**
- **Rate Limiting**: Disabled button during loading prevents spam
- **Streaming**: Chunks displayed incrementally (better UX for slow networks)
- **Abort Support**: ✕ button cancels streaming (saves tokens mid-request)

---

## 🔧 Configuration

### **Environment Variables**

```bash
# Backend (.env or docker-compose.yml)
GEMINI_API_KEY=your_api_key_here
GEMINI_MODEL=gemini-1.5-flash  # or gemini-2.0-flash-exp
GEMINI_MINIMAL_MODE=false      # Set true for ultra-concise responses
GEMINI_FALLBACK=stub           # Returns local context when API down
```

### **Model Selection**

- **Recommended**: `gemini-1.5-flash` (balanced speed/quality, ₹0.02/1K tokens)
- **High Quality**: `gemini-1.5-pro` (deeper analysis, ₹0.50/1K tokens)
- **Experimental**: `gemini-2.0-flash-exp` (latest features, free quota)

---

## 🧪 Testing

### **Manual Test**

1. Open browser: `http://localhost:15173`
2. Navigate to **AI Insight (Gemini)** card
3. Click **⚡ Optimize Now**
4. Observe:
   - Button disabled during loading
   - Streaming response chunks appearing incrementally
   - Actions/Risks highlighted in colored boxes
   - Chat history persisted after completion

### **API Test (PowerShell)**

```powershell
# Test Cost Analysis prompt
$prompt = "Calculate potential cost savings if I follow the current RL advisory decision vs baseline grid-only approach. Include carbon emissions impact."
$encoded = [System.Web.HttpUtility]::UrlEncode($prompt)
irm -Method Post "http://localhost:18000/ai/chat?device_id=11111111-1111-1111-1111-111111111111&q=$encoded"
```

### **Expected Response Structure**

```json
{
  "answer": "At 34.2% SoC...",
  "actions": [
    {"text": "Discharge battery at 2.4 kW for 30 min"},
    {"text": "Grid import 0.6 kW during 4-5 PM"}
  ],
  "risks": [
    {"text": "SoC may drop below 20% if load spikes"}
  ],
  "model": "gemini-1.5-flash",
  "fallback": false
}
```

---

## 🚀 Future Enhancements

### **Phase 1 (Immediate)**
- [ ] Add 5th button: **🌤️ Weather Forecast** (solar irradiance + cloud cover impact)
- [ ] Voice input support for custom questions (Web Speech API)
- [ ] Export chat history as PDF report

### **Phase 2 (1-2 months)**
- [ ] Custom prompt builder (user saves favorite questions)
- [ ] Multi-language support (Hindi, Spanish, German)
- [ ] Sentiment analysis on responses (flag overly risky advice)

### **Phase 3 (3-6 months)**
- [ ] Predictive insights: "At 3 PM tomorrow, you'll need to..."
- [ ] Collaborative filtering: "Users like you often ask..."
- [ ] A/B testing framework for prompt optimization

---

## 📚 Related Documentation

- **AI Integration Guide**: `backend/app/ai_gemini.py` (line 305+)
- **Chat UI Component**: `frontend/src/main.jsx` (line 1103+)
- **System Architecture**: `README.md` (AI/LLM section)
- **API Reference**: `http://localhost:18000/docs` (FastAPI Swagger UI)

---

## 🎓 Prompt Engineering Best Practices

### **What Makes a Good Quick Insight Prompt?**

1. **Specific Task**: "Calculate cost savings" not "Tell me about costs"
2. **Context Reference**: "Based on current SoC" ensures real-time data usage
3. **Output Format**: "Include carbon emissions impact" requests structured info
4. **Time Horizon**: "Next 2 hours" sets clear scope
5. **Action-Oriented**: "Suggest actions to extend backup time" demands practical advice

### **Anti-Patterns to Avoid**

❌ **Vague**: "How's the battery?"  
✅ **Specific**: "Analyze current battery status and provide optimization recommendations"

❌ **Too Broad**: "Explain everything about energy management"  
✅ **Focused**: "Review active alerts and identify risks in the last hour"

❌ **No Context**: "What should I do?"  
✅ **Contextual**: "Based on current SoC and load patterns, estimate backup time"

---

## 🔐 Security Considerations

### **API Key Protection**
- ✅ `GEMINI_API_KEY` stored in `.env` (not committed to Git)
- ✅ Backend validates key before API calls
- ✅ Frontend never sees API key (proxied through backend)

### **Rate Limiting**
- ⏱️ UI disables buttons during active requests
- ⏱️ Backend caches insights for 30s per device
- ⏱️ Streaming abort prevents runaway token usage

### **Input Sanitization**
- 🔒 User questions truncated to 3000 chars
- 🔒 Context JSON capped at 3000 chars total
- 🔒 No SQL injection risk (parameterized queries)

---

## 💡 Usage Tips

### **For Residential Users**
- Click **⚡ Optimize Now** every morning to set daily strategy
- Use **💰 Cost Analysis** before peak hours (4-9 PM)
- Check **🔋 Backup Status** before weather events (storms, outages)

### **For Commercial Users**
- Schedule **⚠️ Risk Check** every 2 hours (cron job)
- Integrate **Cost Analysis** into monthly reports (API export)
- Use **Optimize Now** for demand response events

### **For Developers**
- Add custom buttons by copying the `onClick={()=>onAsk("...")}` pattern
- Monitor API costs: `docker logs backend | grep "gemini_api_call"`
- Test fallback mode: `docker compose stop backend; refresh UI`

---

## 📊 Metrics & Analytics

### **Track Performance**

```bash
# View Gemini API latency
docker exec backend cat /tmp/gemini_metrics.log

# Count Quick Insight button clicks (future: Prometheus)
grep "quick_insight_click" /var/log/frontend.log | wc -l

# Measure token usage per prompt type
SELECT AVG(token_count) FROM chat_messages 
WHERE question LIKE 'Calculate potential cost savings%';
```

---

## 🎉 Success Criteria

### **KPIs**

- ✅ **User Engagement**: 60%+ of users click Quick Insights within first 5 minutes
- ✅ **Response Quality**: 85%+ of responses include numbered actions + risks
- ✅ **Latency**: <3s for full response (streaming starts <1s)
- ✅ **Accuracy**: Cost estimates within ±10% of actual savings
- ✅ **Reliability**: <1% fallback mode usage (API uptime >99%)

### **User Satisfaction**

- "I understand my battery decisions better" → 90% agree
- "Quick Insights saves me time" → 85% agree
- "I trust the AI recommendations" → 80% agree

---

## 🐛 Troubleshooting

### **Issue: Buttons Don't Respond**

**Symptoms**: Click button, no loading state, no chat message  
**Cause**: Backend not running or GEMINI_API_KEY missing  
**Fix**:
```bash
docker logs backend | grep "GEMINI_API_KEY"
docker compose restart backend
```

### **Issue: Response is Generic (Not Real-Time)**

**Symptoms**: Gemini says "I don't have access to live data"  
**Cause**: Context not properly injected  
**Fix**: Check backend logs for context payload:
```bash
docker logs backend | grep "build_chat_prompt" -A 10
```

### **Issue: "(Stub Fallback) Gemini unreachable"**

**Symptoms**: Responses contain stub text, no AI inference  
**Cause**: API key invalid, quota exceeded, or network error  
**Fix**:
```bash
# Test API key manually
curl -H "Content-Type: application/json" \
  -d '{"contents":[{"parts":[{"text":"Hello"}]}]}' \
  "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key=$GEMINI_API_KEY"
```

### **Issue: Streaming Stops Mid-Response**

**Symptoms**: Response cuts off after 2-3 chunks  
**Cause**: WebSocket timeout or browser tab backgrounded  
**Fix**: 
- Keep browser tab active during streaming
- Increase backend timeout: `GEMINI_TIMEOUT=30` in `.env`

---

## 📝 Changelog

### **v1.0.0 (Oct 5, 2025)**
- ✨ Initial release of Quick Insights feature
- 🎨 Added 4 premade buttons (Optimize, Cost, Risk, Backup)
- 🧠 Enhanced backend system prompt for data-driven responses
- 📊 Enriched context injection (forecast, power flows, recent decisions)
- 🎯 150-200 word response limit for consistency
- 🚀 Streaming support with abort capability

---

*Built with ❤️ using Gemini 1.5 Flash, React 18, and FastAPI*
