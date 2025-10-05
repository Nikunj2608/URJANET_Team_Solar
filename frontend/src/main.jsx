// --- EARLY BOOT INSTRUMENTATION (inserted before any React usage) ---
// This runs before React imports so we can detect if the bundle even executes.
if (typeof window !== 'undefined') {
  (function(){
    try {
      // Phase tracker
      window.__APP_BOOT_PHASES = window.__APP_BOOT_PHASES || [];
      function phase(step){
        window.__APP_BOOT_PHASES.push({ step, ts: Date.now() });
        console.log('[BOOT]', step);
      }
      phase('bundle-start');
      // Minimal visual indicator
      const root = document.getElementById('root');
      if(root && !root.firstChild){
        const pre = document.createElement('div');
        pre.id = '__boot_pre';
        pre.textContent = 'Bootstrapping UI… (pre-react)';
        pre.style.cssText = 'font:13px system-ui;padding:10px;color:#0f0;background:#111;border-bottom:1px solid #333;';
        root.appendChild(pre);
      }
      // Simple boot log element (separate from runtime error overlay later in file)
      let logEl = document.getElementById('__boot_log');
      if(!logEl){
        logEl = document.createElement('div');
        logEl.id='__boot_log';
        logEl.style.cssText='position:fixed;z-index:99998;bottom:4px;left:4px;max-width:40vw;max-height:30vh;overflow:auto;font:10px ui-monospace;background:rgba(0,0,0,0.55);color:#fff;padding:4px 6px;border:1px solid #333;border-radius:4px';
        document.body.appendChild(logEl);
      }
      function log(msg){
        try { const l=document.createElement('div'); l.textContent=msg; logEl.appendChild(l); } catch {} }
      window.__APP_BOOT_LOG = log;
      log('phase:bundle-start');
      // Fallback timer: if React hasn\'t replaced placeholder in 4s, mark stalled
      setTimeout(()=>{
        try {
          if(document.getElementById('__boot_pre')){
            log('WARNING: React render not completed after 4s – possible runtime error before createRoot.');
            document.getElementById('__boot_pre').style.color = '#f33';
          }
        } catch {}
      },4000);
    } catch(e){
      console.error('Early boot instrumentation failed', e);
    }
  })();
}

import React, { useEffect, useRef, useState } from 'react';
import './theme.css';
import './style.css'; // legacy layout + fallback styles
import { createRoot } from 'react-dom/client';
import { FlowCanvas } from './FlowCanvas.jsx';
if (typeof window !== 'undefined') { window.__APP_BOOT_LOG && window.__APP_BOOT_LOG('phase:react-imports-complete'); }

// --- Global runtime error overlay (diagnostic) ---
// Displays errors directly on the page to aid "blank screen" debugging when console isn't visible.
if(typeof window !== 'undefined' && !window.__URJA_ERROR_OVERLAY_INSTALLED){
  window.__URJA_ERROR_OVERLAY_INSTALLED = true;
  (function(){
    function ensure(){
      let el = document.getElementById('__runtime_errors');
      if(!el){
        el = document.createElement('div');
        el.id='__runtime_errors';
        Object.assign(el.style,{
          position:'fixed',zIndex:99999,top:0,left:0,right:0,maxHeight:'160px',overflow:'auto',
          fontFamily:'ui-monospace, monospace',fontSize:'11px',background:'#3b0f0f',color:'#fff',
          padding:'6px 10px',borderBottom:'1px solid #ff4e4e',boxShadow:'0 4px 18px -4px #000'
        });
        const close = document.createElement('button');
        close.textContent='×';
        Object.assign(close.style,{position:'absolute',top:2,right:6,background:'transparent',color:'#fff',border:'none',cursor:'pointer',fontSize:'14px'});
        close.onclick=()=>{ el.remove(); };
        el.appendChild(close);
        document.addEventListener('keydown',(e)=>{ if(e.key==='Escape') el.remove(); });
        document.body.appendChild(el);
      }
      return el;
    }
    function log(prefix,msg){
      try {
        const el = ensure();
        const line = document.createElement('div');
        const ts = new Date().toLocaleTimeString();
        line.textContent = `[${ts}] ${prefix}: ${msg}`;
        el.appendChild(line);
      } catch(e){ /* ignore */ }
    }
    window.addEventListener('error', e => { log('Error', e.message + (e.filename? ` @ ${e.filename}:${e.lineno}`:'')); });
    window.addEventListener('unhandledrejection', e => { log('PromiseRejection', (e.reason && (e.reason.stack||e.reason.message)) || String(e.reason)); });
    log('Info','Runtime error overlay active');
  })();
}

// Simple error boundary to surface component failures inline
class ErrorBoundary extends React.Component { constructor(p){ super(p); this.state={err:null}; }
  static getDerivedStateFromError(err){ return {err}; }
  componentDidCatch(err,info){ console.error('UI error boundary caught', err, info); }
  render(){ if(this.state.err){ return <div style={{padding:20,color:'#fff',background:'#5d1f1f',border:'2px solid #ff4e4e',borderRadius:12}}>
    <h2 style={{marginTop:0}}>UI Crash</h2>
    <pre style={{whiteSpace:'pre-wrap',fontSize:'0.55rem'}}>{String(this.state.err?.stack||this.state.err)}</pre>
    <p style={{fontSize:'0.55rem',opacity:.75}}>Check overlay at top for more details. Fix error and reload.</p>
  </div>; }
    return this.props.children; }
}

// Animated numeric/text value that flashes briefly on change
function AnimatedValue({ value, suffix="" }) {
  const ref = React.useRef();
  const prevRef = React.useRef(value);
  React.useEffect(()=>{
    if(prevRef.current !== value && ref.current){
      ref.current.classList.remove('value-flash');
      // force reflow
      void ref.current.offsetWidth;
      ref.current.classList.add('value-flash');
      prevRef.current = value;
    }
  },[value]);
  return <span ref={ref} className="value">{value}{suffix && <small className="unit">{suffix}</small>}</span>;
}

// Fade duration for alert halo acknowledgment (ms)
const ALERT_FADE_DURATION = 1500;

const BACKEND = (import.meta.env.VITE_BACKEND_URL || 'http://localhost:18000').replace(/\/$/, '');
const DEVICE_ID = '11111111-1111-1111-1111-111111111111';

function useInterval(fn, ms) {
  useEffect(() => { const id = setInterval(fn, ms); return () => clearInterval(id); }, [fn, ms]);
}

function LineChart({ points, color = '#58a6ff' }) {
  const ref = useRef();
  useEffect(() => {
    const canvas = ref.current; if (!canvas) return; const ctx = canvas.getContext('2d');
    const w = canvas.width = canvas.clientWidth; const h = canvas.height = canvas.clientHeight;
    ctx.clearRect(0,0,w,h); if (!points.length) return;
    const xs = points.map(p => p.ts);
    const ys = points.map(p => p.voltage);
    const minY = Math.min(...ys)-1, maxY = Math.max(...ys)+1;
    const minX = Math.min(...xs), maxX = Math.max(...xs);
    ctx.strokeStyle = color; ctx.lineWidth = 2; ctx.beginPath();
    points.forEach((p,i) => {
      const x = ((p.ts - minX)/(maxX-minX||1))*w;
      const y = h - ((p.voltage - minY)/(maxY-minY||1))*h;
      if(i===0) ctx.moveTo(x,y); else ctx.lineTo(x,y);
    });
    ctx.stroke();
  }, [points, color]);
  return <canvas ref={ref} style={{width:'100%',height:200}} />;
}

function Gauge({ value }) {
  const pct = Math.max(0, Math.min(100, value));
  return (
    <div className="gauge">
      <div className="gauge-circle" style={{'--pct': pct+'%'}}><span>{pct.toFixed(1)}%</span></div>
      <small>State of Charge</small>
    </div>
  );
}

function App({ onHeartbeat, onLatestTs, onAdvisory }) {
  const [telemetry, setTelemetry] = useState([]); // last N points (live window)
  const [latest, setLatest] = useState(null);
  const [alerts, setAlerts] = useState([]);            // raw backend alerts
  const [smartAlerts, setSmartAlerts] = useState([]);  // smart alerts (preferred if present)
  const [rlAdvisory, setRlAdvisory] = useState(null);
  const [forecast, setForecast] = useState(null);
  const [aiInsight,setAiInsight] = useState(null);
  const [aiInsightLoading,setAiInsightLoading] = useState(false);
  const [aiChatQ,setAiChatQ] = useState("");
  const [aiChatHistory,setAiChatHistory] = useState([]);
  const [aiChatLoading,setAiChatLoading] = useState(false);
  const chatListRef = React.useRef(null);
  const streamAbortRef = React.useRef(null);
  const [heartbeat, setHeartbeat] = useState(null);
  const [history, setHistory] = useState([]); // historical range
  const [rangeMinutes, setRangeMinutes] = useState(30);
  const [loadingHistory, setLoadingHistory] = useState(false);
  const [mqttStats, setMqttStats] = useState(null);
  const [reduceMotion, setReduceMotion] = useState(false);
  const [decisionHistory, setDecisionHistory] = useState([]);
  const [decisionCursor, setDecisionCursor] = useState(null); // next before_id cursor
  const [decisionsHasMore, setDecisionsHasMore] = useState(false);
  const [activePanel, setActivePanel] = useState('analytics'); // 'analytics' | 'history'
  // Live data stagnation diagnostics
  const lastServerTsRef = React.useRef(null);
  const stagnantCountRef = React.useRef(0);
  const lastWsMessageRef = React.useRef(0);

  function generateSyntheticFrom(latestPoint){
    if(!latestPoint) return null;
    const jitter = (base, pct=0.003) => base + (base * pct * (Math.random()-0.5)*2);
    return {
      ...latestPoint,
      ts: new Date().toISOString(),
      voltage: Number(jitter(latestPoint.voltage || 230)).toFixed ? Number(jitter(latestPoint.voltage || 230)).toFixed(2) : jitter(latestPoint.voltage || 230),
      temperature: Number(jitter(latestPoint.temperature || 30, 0.002)).toFixed ? Number(jitter(latestPoint.temperature || 30, 0.002)).toFixed(2) : jitter(latestPoint.temperature || 30, 0.002),
      __synthetic: true
    };
  }

  const appendTelemetry = React.useCallback((point) => {
    console.log('➡️ Calling appendTelemetry with point:', point);
    if(!point) return;
    try {
      const tsNum = new Date(point.ts).getTime();
      if(Number.isNaN(tsNum)) {
        console.warn('⚠️ appendTelemetry received point with invalid timestamp:', point.ts);
        return;
      }
      // Coerce numeric fields (API may return strings or Decimals serialized as strings)
      const coerced = { ...point };
      ['voltage','temperature','soc'].forEach(k => {
        if(coerced[k] !== undefined && coerced[k] !== null){
          const num = Number(coerced[k]);
          if(!Number.isNaN(num)) coerced[k] = num; else console.warn('⚠️ Non-numeric field after coercion', k, coerced[k]);
        }
      });
      setTelemetry(prev => {
        if(prev.length && prev[prev.length-1].ts === tsNum) {
            // Duplicate / unchanged timestamp
            return prev;
        }
        const next = [...prev, { ...coerced, ts: tsNum }];
        return next.length > 20 ? next.slice(next.length - 20) : next;
      });
    } catch(err){
      console.error('❌ appendTelemetry failed:', err, point);
    }
  }, []);

  const fetchLatest = async () => {
    try {
      const r = await fetch(`${BACKEND}/telemetry/latest?device_id=${DEVICE_ID}`);
      if (r.ok) {
        const j = await r.json();
        if(j) {
          // Stagnation detection (same server ts repeating)
          if(lastServerTsRef.current === j.ts){
            stagnantCountRef.current += 1;
          } else {
            lastServerTsRef.current = j.ts;
            stagnantCountRef.current = 0;
          }
          setLatest(j);
          onLatestTs && onLatestTs(j.ts);
          appendTelemetry(j);
          if(stagnantCountRef.current >= 3){
            console.warn('🟡 Telemetry latest endpoint returning unchanged timestamp repeatedly. Generating synthetic point to keep chart alive.');
            const synthetic = generateSyntheticFrom(j);
            if(synthetic){ appendTelemetry(synthetic); }
            stagnantCountRef.current = 0; // reset after synthetic injection
          }
        }
      }
    } catch(e) { /* ignore */ }
  };
  const fetchAlerts = async () => {
    try {
      const r = await fetch(`${BACKEND}/alerts?device_id=${DEVICE_ID}`);
      if(r.ok){
        const server = await r.json();
        // Merge server alerts with local ack_timestamp (for fade) if still within fade window
        setAlerts(prev => server.map(sa => {
          const existing = prev.find(p => p.id === sa.id);
          if(existing && existing.ack_timestamp) return {...sa, ack_timestamp: existing.ack_timestamp};
          return sa;
        }));
      }
    } catch(e) { /* ignore */ }
    try {
      const s = await fetch(`${BACKEND}/alerts/smart?device_id=${DEVICE_ID}`);
      if(s.ok){
        const serverSmart = await s.json();
        setSmartAlerts(prev => serverSmart.map(sa => {
          const existing = prev.find(p => p.id === sa.id);
            if(existing && existing.ack_timestamp) return {...sa, ack_timestamp: existing.ack_timestamp};
            return sa;
        }));
      }
    } catch(e) { /* ignore */ }
  };

  const fetchRl = async () => {
    // Prefer safe endpoint (semantic + supervision); fallback gracefully
    try {
      let r = await fetch(`${BACKEND}/advisory/rl/safe?device_id=${DEVICE_ID}`);
  if(!r.ok){ r = await fetch(`${BACKEND}/advisory/rl?device_id=${DEVICE_ID}`); }
  if(r.ok){ const adv = await r.json(); setRlAdvisory(adv); onAdvisory && onAdvisory(adv); }
    } catch(e) {}
  };
  const fetchForecast = async () => {
    try { const r = await fetch(`${BACKEND}/forecast/battery?device_id=${DEVICE_ID}`); if(r.ok){ setForecast(await r.json()); } } catch(e) {}
  };
  const fetchAiInsight = async () => {
    setAiInsightLoading(true);
    try { const r = await fetch(`${BACKEND}/ai/insight?device_id=${DEVICE_ID}`); if(r.ok){ setAiInsight(await r.json()); } } catch(e) {};
    setAiInsightLoading(false);
  };
  const fetchHeartbeat = async () => {
  try { const r = await fetch(`${BACKEND}/heartbeat/status?device_id=${DEVICE_ID}`); if(r.ok){ const hb = await r.json(); setHeartbeat(hb); onHeartbeat && onHeartbeat(hb); } } catch(e) {}
  };

  const fetchHistory = async (minutes = rangeMinutes) => {
    setLoadingHistory(true);
    try {
      const end = new Date();
      const start = new Date(end.getTime() - minutes*60*1000);
      const qs = `device_id=${DEVICE_ID}&start=${start.toISOString()}&end=${end.toISOString()}&limit=2000`;
      const r = await fetch(`${BACKEND}/telemetry/range?${qs}`);
      if(r.ok){
        const arr = await r.json();
        setHistory(arr.map(p => ({
          ...p,
          ts: new Date(p.ts).getTime(),
          voltage: p.voltage !== undefined ? Number(p.voltage) : p.voltage,
          temperature: p.temperature !== undefined ? Number(p.temperature) : p.temperature,
          soc: p.soc !== undefined ? Number(p.soc) : p.soc,
        })));
      }
    } catch(e){ /* ignore */ }
    setLoadingHistory(false);
  };

  const fetchMqttStats = async () => {
    try { const r = await fetch(`${BACKEND}/mqtt/stats`); if(r.ok){ setMqttStats(await r.json()); } } catch(e) {}
  };

  // Poll every 1 second for real-time data updates
  useInterval(fetchLatest, 1000);      // Telemetry: every 1s
  useInterval(fetchAlerts, 1000);      // Alerts: every 1s
  useInterval(fetchRl, 1000);          // RL Advisory: every 1s
  useInterval(fetchAiInsight, 1000);   // AI Insight: every 1s
  useInterval(fetchForecast, 1000);    // Forecast: every 1s
  useInterval(fetchHeartbeat, 1000);   // Heartbeat: every 1s
  useInterval(fetchMqttStats, 1000);   // MQTT Stats: every 1s
  const fetchDecisionHistory = async (reset=false) => {
    try {
      const cursorParam = reset || !decisionCursor ? '' : `&before_id=${decisionCursor}`;
      const r = await fetch(`${BACKEND}/advisory/rl/history?device_id=${DEVICE_ID}&limit=40${cursorParam}`);
      if(r.ok){
        const j = await r.json();
        if(reset){
          setDecisionHistory(j.decisions||[]);
        } else {
          setDecisionHistory(prev => [...prev, ...(j.decisions||[])]);
        }
        setDecisionCursor(j.next_before_id);
        setDecisionsHasMore(!!j.has_more);
      }
    } catch(e) {}
  };
  useInterval(fetchDecisionHistory, 25000);
  // Persistent chat history fetcher
  const fetchChatHistory = React.useCallback(async () => {
    try {
      const r = await fetch(`${BACKEND}/ai/chat/history?device_id=${DEVICE_ID}&limit=40`);
      if(r.ok){
        const js = await r.json();
        if(js && js.items){
          setAiChatHistory(js.items.map(it => ({
            role: it.role,
            content: it.content,
            actions: it.meta?.actions || null,
            risks: it.meta?.risks || null,
            advisories: it.meta?.advisories || null,
            model: it.model,
            ts: it.ts ? new Date(it.ts).getTime() : Date.now(),
            fallback: it.meta?.fallback || false
          })).slice(-60));
        }
      }
    } catch(e) { /* ignore */ }
  }, []);

  useEffect(() => { fetchLatest(); fetchAlerts(); fetchHistory(); fetchMqttStats(); fetchRl(); fetchForecast(); fetchHeartbeat(); fetchDecisionHistory(); fetchAiInsight(); fetchChatHistory(); }, [fetchChatHistory]);
  useInterval(fetchChatHistory, 30000);
  // Auto-scroll when new messages arrive
  useEffect(()=>{
    const el = chatListRef.current; if(!el) return;
    el.scrollTop = el.scrollHeight;
  }, [aiChatHistory]);

  useEffect(() => {
    const wsUrl = BACKEND.replace(/^http/, 'ws') + `/ws/telemetry?device_id=${DEVICE_ID}`;
    console.log('🔌 Opening WebSocket to', wsUrl);
    const ws = new WebSocket(wsUrl);
    ws.onopen = () => console.log('✅ WebSocket Connected');
    ws.onerror = (err) => console.error('❌ WebSocket Error:', err);
    ws.onclose = (ev) => console.warn('⚠️ WebSocket Disconnected', ev.code, ev.reason || '');
    ws.onmessage = (event) => {
      console.log('📥 Raw WebSocket message received:', event.data);
      try {
        const msg = JSON.parse(event.data);
        if(msg && msg.type === 'telemetry' && msg.data){
          setLatest(msg.data);
          appendTelemetry(msg.data);
        } else {
          console.debug('ℹ️ Non-telemetry WS message ignored', msg);
        }
      } catch(parseErr){
        console.error('❌ Failed to parse WebSocket message:', parseErr);
      }
    };
    return () => {
      console.log('🔌 Closing WebSocket');
      ws.close();
    };
  }, [appendTelemetry]);

  // Compute KPIs (simple last values / mock delta)
  const lastVoltage = latest?.voltage ?? 0;
  const lastTemp = latest?.temperature ?? 0;
  const lastSoc = latest?.soc ?? 0;
  const voltsDelta = telemetry.length > 1 ? lastVoltage - telemetry[telemetry.length-2].voltage : 0;
  const tempDelta = telemetry.length > 1 ? lastTemp - telemetry[telemetry.length-2].temperature : 0;
  const socDelta = telemetry.length > 1 ? lastSoc - telemetry[telemetry.length-2].soc : 0;

  function deltaClass(v){ if(Math.abs(v) < 0.01) return 'flat'; return v>0 ? 'up':'down'; }
  function deltaText(v){ if(Math.abs(v) < 0.01) return '0'; return (v>0?'+':'')+v.toFixed(2); }

  // Preferred list for canvas & panel
  const chosenAlerts = (smartAlerts && smartAlerts.length) ? smartAlerts : alerts;

  // Compute active alerts for canvas (include fading acknowledged ones until fade complete)
  const activeAlertsForCanvas = React.useMemo(() => {
    const now = Date.now();
      const watchdog = setInterval(() => {
        const now = Date.now();
        if(now - lastWsMessageRef.current > 12000){
          if(latest){
            console.warn('🟠 No WebSocket telemetry for >12s; injecting synthetic point.');
            const synthetic = generateSyntheticFrom(latest);
            if(synthetic) appendTelemetry(synthetic);
            lastWsMessageRef.current = now; // prevent rapid repeats
          }
        }
      }, 4000);
    return chosenAlerts.filter(a => {
      if(!a.ack_ts) return true; // still active (unacknowledged)
      if(a.ack_timestamp){
        clearInterval(watchdog);
        return (now - a.ack_timestamp) < ALERT_FADE_DURATION; // still fading
      }
      return false;
    });
  }, [chosenAlerts]);

  // Cleanup effect to drop fully faded acknowledged alerts (prevents list bloat until next poll)
  useEffect(() => {
    const id = setInterval(() => {
      const now = Date.now();
      const prune = list => list.filter(a => {
        if(!a.ack_ts) return true;
        if(a.ack_timestamp) return (now - a.ack_timestamp) < ALERT_FADE_DURATION;
        return false;
      });
      setAlerts(prev => prune(prev));
      setSmartAlerts(prev => prune(prev));
    }, 800);
    return () => clearInterval(id);
  }, []);

  // Acknowledge handler adds ack_timestamp for fade animation
  const handleAckAlert = async (id) => {
    const stamp = Date.now();
    // Optimistic local mutation (add ack_timestamp if not present)
    const tagAck = a => a.id === id && !a.ack_ts ? {...a, ack_ts: new Date().toISOString(), ack_timestamp: stamp } : a;
    setAlerts(prev => prev.map(tagAck));
    setSmartAlerts(prev => prev.map(tagAck));
    try { await fetch(`${BACKEND}/alerts/${id}/ack`, {method:'POST'}); } catch(e) { /* ignore */ }
  };

  return (
    <div className="grid-wrapper">
      <div className="kpi-row fade-in">
        <div className="kpi voltage">
          <span className="label">Voltage</span>
          <AnimatedValue value={lastVoltage.toFixed(2)} suffix=" V" />
          <span className={"delta "+deltaClass(voltsDelta)}>{deltaText(voltsDelta)}</span>
        </div>
        <div className="kpi temperature">
          <span className="label">Temperature</span>
          <AnimatedValue value={lastTemp.toFixed(1)} suffix=" °C" />
          <span className={"delta "+deltaClass(tempDelta)}>{deltaText(tempDelta)}</span>
        </div>
        <div className="kpi soc">
          <span className="label">State of Charge</span>
          <AnimatedValue value={lastSoc.toFixed(1)} suffix=" %" />
          <span className={"delta "+deltaClass(socDelta)}>{deltaText(socDelta)}</span>
        </div>
        <div className="kpi alerts">
          <span className="label">Alerts</span>
          <AnimatedValue value={(smartAlerts.length || alerts.length).toString()} />
          <span className={"delta "+(heartbeat? (heartbeat.status==='ok'?'up': heartbeat.status==='degraded'?'down':'flat'):'flat')}>{heartbeat? heartbeat.status : '...'}</span>
        </div>
      </div>

      <FlowCanvas
        backend={BACKEND}
        highlightAction={rlAdvisory?.actions?.[0]?.title?.replace(/\s+/g,'_').toUpperCase()}
        activeAlerts={activeAlertsForCanvas}
        reduceMotion={reduceMotion}
        rlSemanticSafe={rlAdvisory?.actions?.[0]?.semantic_safe}
        rlSemanticRaw={rlAdvisory?.actions?.[0]?.semantic_raw}
        rlModelVersion={rlAdvisory?.model_version}
        rlUpdatedAt={rlAdvisory?.generated_at}
      />

      <div className="grid fade-in" style={{marginTop:18}}>
        <GlassCard spanFull>
          <div style={{display:'flex',gap:8,alignItems:'center',flexWrap:'wrap'}}>
            <button className={`btn btn-tab ${activePanel==='analytics'?'is-active':''}`} onClick={()=>setActivePanel('analytics')}>Analytics</button>
            <button className={`btn btn-tab ${activePanel==='history'?'is-active':''}`} onClick={()=>{ setActivePanel('history'); fetchDecisionHistory(true); }}>Decision History</button>
            <span style={{flex:1}} />
            {activePanel==='history' && <span className="fs-xs text-dim">Showing {decisionHistory.length} decisions</span>}
          </div>
        </GlassCard>

        {activePanel==='analytics' && (
          <>
            <MultiMetricCard telemetry={telemetry} latest={latest} />
            <GlassCard title="Battery SoC">
              <Gauge value={latest? latest.soc : 0} />
              {latest && <div className="fs-sm text-secondary" style={{marginTop:8}}>Temp: {latest.temperature} °C</div>}
            </GlassCard>
            <SmartAlertsCard alerts={smartAlerts} fallback={alerts} onAck={handleAckAlert} />
            <RLAdvisoryCard advisory={rlAdvisory} latest={latest} />
            <AIInsightCard
              insight={aiInsight}
              loading={aiInsightLoading}
              onRefresh={fetchAiInsight}
              onRefreshChat={fetchChatHistory}
              loadingChat={aiChatLoading}
              onAsk={async(q)=>{
                if(!q) return; const txt = q.trim(); setAiChatQ("");
                const userTs = Date.now();
                setAiChatHistory(h=>[...h,{role:'user', content:txt, ts: userTs}]);
                setAiChatLoading(true);
                // Insert placeholder assistant entry for streaming updates
                const placeholderId = `placeholder-${userTs}`;
                setAiChatHistory(h=>[...h,{role:'assistant', content:'', ts: Date.now(), _id: placeholderId, streaming:true}]);
                let usedStreaming = false;
                try {
                  // Abort setup
                  if(streamAbortRef.current){ try { streamAbortRef.current.abort(); } catch(e){} }
                  const controller = new AbortController();
                  streamAbortRef.current = controller;
                  const streamResp = await fetch(`${BACKEND}/ai/chat/stream?device_id=${DEVICE_ID}&q=`+encodeURIComponent(txt), {signal: controller.signal});
                  if(!streamResp.ok || !streamResp.body){ throw new Error('stream not ok'); }
                  usedStreaming = true;
                  const reader = streamResp.body.getReader();
                  const decoder = new TextDecoder();
                  let buf = '';
                  let finalAnswer = '';
                  while(true){
                    const {done,value} = await reader.read();
                    if(done) break;
                    buf += decoder.decode(value, {stream:true});
                    let idx;
                    while((idx = buf.indexOf('\n')) >= 0){
                      const line = buf.slice(0, idx).trim();
                      buf = buf.slice(idx+1);
                      if(!line) continue;
                      try {
                        const evt = JSON.parse(line);
                        if(evt.type === 'chunk'){
                          const chunk = evt.data || '';
                          setAiChatHistory(h=>h.map(m => m._id===placeholderId ? {...m, content: (m.content||'') + chunk } : m));
                          finalAnswer += chunk;
                        }
                        if(evt.type === 'done'){
                          setAiChatHistory(h=>h.map(m => m._id===placeholderId ? {...m, streaming:false} : m));
                        }
                      } catch(e){ /* ignore line parse errors */ }
                    }
                  }
                  // Immediate heuristic extraction (actions/risks) from finalAnswer
                  if(finalAnswer){
                    const parsed = extractActionsRisks(finalAnswer);
                    if(parsed.actions || parsed.risks){
                      setAiChatHistory(h=>h.map(m => m._id===placeholderId ? {...m, ...parsed} : m));
                    }
                  }
                } catch(streamErr){
                  // Fallback to non-streaming call
                  try {
                    const r = await fetch(`${BACKEND}/ai/chat`, {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({device_id: DEVICE_ID, question: txt})});
                    if(r.ok){
                      const js = await r.json();
                      setAiChatHistory(h=>h.map(m => m._id===placeholderId ? {
                        ...m,
                        content: js.answer || js.error || '(no answer)',
                        actions: js.actions || null,
                        risks: js.risks || null,
                        advisories: js.advisories || null,
                        model: js.model,
                        fallback: js.fallback,
                        streaming:false
                      } : m));
                    } else {
                      setAiChatHistory(h=>h.map(m => m._id===placeholderId ? {...m, content:`(error ${r.status})`, streaming:false} : m));
                    }
                  } catch(e){
                    setAiChatHistory(h=>h.map(m => m._id===placeholderId ? {...m, content:'(network error)', streaming:false} : m));
                  }
                } finally {
                  setAiChatLoading(false);
                  // Refresh persistent history to get structured actions/risks if streaming finished
                  fetchChatHistory();
                }
              }}
              chatHistory={aiChatHistory}
              chatQ={aiChatQ}
              setChatQ={setAiChatQ}
              chatListRef={chatListRef}
            />
            <BatteryForecastCard forecast={forecast} />
            <GlassCard title={`History (${rangeMinutes}m)`}>
              <div style={{display:'flex', gap:4, flexWrap:'wrap', marginBottom:6}}>
                {[5,15,30,60,120].map(m => <button key={m} className="btn btn-ghost btn-compact" onClick={()=>{ setRangeMinutes(m); fetchHistory(m); }} disabled={rangeMinutes===m}>{m}m</button>)}
                <button className="btn btn-icon btn-ghost" onClick={()=>fetchHistory()} title="Refresh">↻</button>
                <button className="btn btn-icon btn-ghost" onClick={()=>downloadCSV(history)} title="Download CSV">CSV</button>
              </div>
              {loadingHistory ? <div>Loading…</div> : <LineChart points={history} color="#ffb347" />}
              <small className="fs-xs text-dim">{history.length} pts</small>
            </GlassCard>
            <GlassCard title="System" spanFull>
              <div style={{display:'flex',gap:12,flexWrap:'wrap',alignItems:'center'}}>
                <span className="env-badge">LOCAL</span>
                <select className="device-select" value={DEVICE_ID} disabled>
                  <option>{DEVICE_ID}</option>
                </select>
                <div className="status-bar" style={{display:'flex',alignItems:'center',gap:8}}>
                  {mqttStats && <>
                    <span className="status-pill"><strong>MQTT</strong> {mqttStats.messages_ok}</span>
                    <span className="status-pill"><strong>Fail</strong> {mqttStats.messages_failed}</span>
                    {mqttStats.last_message_ts && <span className="status-pill"><strong>Last</strong> {new Date(mqttStats.last_message_ts*1000).toLocaleTimeString()}</span>}
                  </>}
                  <a className="btn btn-ghost btn-compact" href="http://localhost:18000/docs" target="_blank" rel="noreferrer">OpenAPI</a>
                  <button className="btn btn-danger btn-compact" title="Trigger Risk Alert" onClick={()=>{ fetch(`${BACKEND}/debug/trigger-risk-alert`, {method:'POST'}).then(()=>fetchAlerts()); }}>Risk⚡</button>
                  <label className="btn btn-ghost btn-compact" style={{display:'inline-flex',alignItems:'center',gap:6}}>
                    <input type="checkbox" checked={reduceMotion} onChange={e=>setReduceMotion(e.target.checked)} /> Motion-
                  </label>
                </div>
              </div>
            </GlassCard>
          </>
        )}

        {activePanel==='history' && (
          <DecisionHistoryCard
            decisions={decisionHistory}
            onRefresh={()=>fetchDecisionHistory(true)}
            onLoadMore={()=>fetchDecisionHistory(false)}
            hasMore={decisionsHasMore}
            cursor={decisionCursor}
          />
        )}
      </div>
    </div>
  );
}

function MultiMetricCard({ telemetry, latest }) {
  const [normalized, setNormalized] = React.useState(false);
  return (
    <GlassCard title="Voltage & Temperature (Live)">
      <div style={{display:'flex',gap:12,alignItems:'center',marginBottom:4}}>
        <label className="fs-sm text-secondary" style={{display:'flex',gap:4,alignItems:'center'}}>
          <input type="checkbox" checked={normalized} onChange={e=>setNormalized(e.target.checked)} /> Normalize (0-1)
        </label>
      </div>
      <MultiLineChart points={telemetry} normalized={normalized} seriesConfig={[
        { key: 'voltage', color: '#58a6ff', label: 'Voltage (V)' },
        { key: 'temperature', color: '#ff9933', label: 'Temp (°C)' }
      ]} />
      {latest && (
        <div className="fs-sm text-secondary" style={{display:'flex',gap:12,flexWrap:'wrap',marginTop:4}}>
          <span>V: {latest.voltage}</span>
          <span>T: {latest.temperature}°C</span>
          <span>@ {new Date(latest.ts).toLocaleTimeString()}</span>
        </div>
      )}
      <Legend series={[{c:'#58a6ff',l:'Voltage'},{c:'#ff9933',l:'Temperature'}]} />
    </GlassCard>
  );
}

function Legend({ series }) {
  return (
    <div className="fs-sm text-dim" style={{display:'flex',gap:12,flexWrap:'wrap',marginTop:6}}>
      {series.map(s => <span key={s.l} style={{display:'flex',alignItems:'center',gap:4}}><span style={{width:10,height:10,background:s.c,borderRadius:2,display:'inline-block'}} />{s.l}</span>)}
    </div>
  );
}

function MultiLineChart({ points, seriesConfig, normalized }) {
  const ref = React.useRef();
  const overlayRef = React.useRef();
  const [hover, setHover] = React.useState(null);
  React.useEffect(() => {
    const canvas = ref.current; if(!canvas) return; const ctx = canvas.getContext('2d');
    const w = canvas.width = canvas.clientWidth; const h = canvas.height = canvas.clientHeight;
    ctx.clearRect(0,0,w,h);
    if(!points.length) { ctx.fillStyle='#888'; ctx.font='12px sans-serif'; ctx.fillText('No data', 8,16); return; }
    const xs = points.map(p=>p.ts);
    const minX = Math.min(...xs), maxX = Math.max(...xs);
    seriesConfig.forEach(sc => {
      const ys = points.map(p => p[sc.key]).filter(v => typeof v === 'number'); if(!ys.length) return;
      let minY = Math.min(...ys), maxY = Math.max(...ys);
      if(normalized){ minY = 0; maxY = 1; }
      ctx.strokeStyle = sc.color; ctx.lineWidth = 2; ctx.beginPath();
      points.forEach((p,i) => {
        const raw = p[sc.key]; if(typeof raw !== 'number') return;
        const val = normalized ? normalize(raw, ys) : raw;
        const x = ((p.ts - minX)/(maxX-minX||1))*w;
        const y = h - ((val - minY)/(maxY-minY||1))*h;
        if(i===0) ctx.moveTo(x,y); else ctx.lineTo(x,y);
      }); ctx.stroke();
    });
  }, [points, seriesConfig, normalized]);

  React.useEffect(() => {
    const overlay = overlayRef.current; if(!overlay) return; const canvas = ref.current; if(!canvas) return;
    const handler = (e) => {
      if(!points.length) return;
      const rect = overlay.getBoundingClientRect();
      const x = e.clientX - rect.left;
      const xs = points.map(p=>p.ts);
      const minX = Math.min(...xs), maxX = Math.max(...xs);
      const rel = x / rect.width;
      const targetTs = minX + rel*(maxX-minX);
      // nearest point
      let nearest = points[0];
      let best = Math.abs(nearest.ts - targetTs);
      for(const p of points){ const d = Math.abs(p.ts - targetTs); if(d < best){ best = d; nearest = p; } }
      setHover(nearest);
    };
    const leave = () => setHover(null);
    overlay.addEventListener('mousemove', handler);
    overlay.addEventListener('mouseleave', leave);
    return () => { overlay.removeEventListener('mousemove', handler); overlay.removeEventListener('mouseleave', leave); };
  }, [points]);

  // Axis labels (simple)
  const xs = points.map(p=>p.ts);
  const minX = xs.length ? Math.min(...xs) : 0;
  const maxX = xs.length ? Math.max(...xs) : 0;
  const timeLabels = [];
  if(xs.length > 1){
    const steps = 3;
    for(let i=0;i<=steps;i++){
      const t = new Date(minX + (i/steps)*(maxX-minX));
      timeLabels.push(t.toLocaleTimeString());
    }
  }
  // y ranges from first series (approx for label)
  let yMin = 0, yMax = 0;
  if(points.length){
    const ys = points.map(p => p[seriesConfig[0].key]).filter(v=>typeof v==='number');
    if(ys.length){ yMin = Math.min(...ys); yMax = Math.max(...ys); }
  }
  return (
    <div style={{position:'relative'}}>
      <canvas ref={ref} style={{width:'100%',height:200}} />
      <div ref={overlayRef} style={{position:'absolute',inset:0}} />
      <div className="chart-axes">
        <div className="x-labels">
          {timeLabels.map(l => <span key={l}>{l}</span>)}
        </div>
        {points.length>0 && <div className="y-label" style={{top:2}}>{yMax.toFixed(1)}</div>}
        {points.length>0 && <div className="y-label" style={{bottom:2}}>{yMin.toFixed(1)}</div>}
      </div>
      {hover && (
        <div style={{position:'absolute',top:4,right:4,background:'rgba(0,0,0,0.55)',backdropFilter:'blur(4px)',color:'#fff',padding:'5px 8px',fontSize:'0.6rem',borderRadius:6, boxShadow:'0 2px 6px rgba(0,0,0,0.4)'}}>
          <div style={{fontWeight:600, marginBottom:2}}>{new Date(hover.ts).toLocaleTimeString()}</div>
          {seriesConfig.map(sc => <div key={sc.key} style={{color:sc.color}}>{sc.key}: {hover[sc.key]?.toFixed?.(2)}</div>)}
        </div>
      )}
    </div>
  );
}

function normalize(val, arr){
  const min = Math.min(...arr); const max = Math.max(...arr); if(max-min===0) return 0.5; return (val-min)/(max-min);
}

function ThemeToggle(){
  const [theme,setTheme] = useState(()=> localStorage.getItem('urjanet_theme') || 'dark');
  useEffect(()=>{ const shell=document.getElementById('app-shell'); if(shell) shell.setAttribute('data-theme',theme); localStorage.setItem('urjanet_theme', theme); },[theme]);
  return <div className="theme-toggle" onClick={()=>setTheme(t=>t==='dark'?'light':'dark')}><span /></div>;
}

function DensityToggle(){
  const [dense,setDense] = useState(false);
  useEffect(()=>{ const shell=document.getElementById('app-shell'); if(shell) shell.setAttribute('data-density',dense?'dense':''); },[dense]);
  return <button onClick={()=>setDense(d=>!d)} title="Toggle density">{dense?'Comfort':'Dense'}</button>;
}

function Sidebar({ collapsed, onToggle }) {
  return (
    <aside className={`sidebar ${collapsed ? 'collapsed' : ''}`}>
      <div className="brand urjanet-logo">
        <svg className="logo-icon" width="28" height="28" viewBox="0 0 32 32" fill="none" xmlns="http://www.w3.org/2000/svg">
          <circle cx="16" cy="16" r="14" stroke="currentColor" strokeWidth="2" fill="none" opacity="0.3"/>
          <path d="M16 6 L16 16 L22 22" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"/>
          <circle cx="16" cy="16" r="2" fill="currentColor"/>
        </svg>
        {!collapsed && <span className="brand-text">Urja<span className="accent">Net</span></span>}
      </div>
      <nav className="nav-group">
        <button className="nav-item active">Dashboard</button>
        <button className="nav-item" disabled>History</button>
        <button className="nav-item" disabled>Forecast</button>
        <button className="nav-item" disabled>Settings</button>
      </nav>
      <div className="grow" />
      <button className="collapse-btn" onClick={onToggle}>{collapsed ? '›' : '‹'}</button>
    </aside>
  );
}

function TopBar({ latestTs, heartbeat, advisory }) {
  const [tooltip,setTooltip] = useState(null);
  const status = heartbeat?.status || 'missing';
  // Age calculation for last telemetry
  let ageSec = null; let recency='missing';
  if(latestTs){ ageSec = (Date.now() - new Date(latestTs).getTime())/1000; if(ageSec < 10) recency='ok'; else if(ageSec < 30) recency='degraded'; else if(ageSec < 120) recency='warn'; else recency='missing'; }
  const dotClass = recency==='ok'?'ok': recency==='degraded'?'degraded': (recency==='warn'?'degraded':'missing');
  function showTip(e){
    setTooltip({ x:e.clientX+14, y:e.clientY+14, content: {
      latest: latestTs ? new Date(latestTs).toLocaleTimeString() : '—',
      age: ageSec!==null? ageSec.toFixed(0)+'s':'—',
      heartbeat: heartbeat?.status || '—',
      rl: advisory?.actions?.[0]?.title || '—',
      model: advisory?.model_version || '—'
    }});
  }
  return (
    <header className="topbar-modern" onMouseLeave={()=>setTooltip(null)}>
      <div className="left cluster" style={{display:'flex',alignItems:'center',gap:10}}>
        <h1 className="app-title">Energy Control Center</h1>
        <div className={`live-status-dot ${dotClass}`} onMouseMove={showTip} />
      </div>
      <div className="spacer" />
      <div className="right cluster" style={{gap:8}}>
        <div id="theme-toggle-mount" />
        <div id="density-toggle-mount" />
      </div>
      {tooltip && (
        <div className="tooltip" style={{left:tooltip.x, top:tooltip.y}}>
          <h4>Live Status</h4>
          <div><strong>Last:</strong> {tooltip.content.latest}</div>
          <div><strong>Age:</strong> {tooltip.content.age}</div>
            <div><strong>Heartbeat:</strong> {tooltip.content.heartbeat}</div>
          <div><strong>RL Action:</strong> {tooltip.content.rl}</div>
          <div><strong>Model:</strong> {tooltip.content.model}</div>
        </div>
      )}
    </header>
  );
}

function Root(){
  const [collapsed,setCollapsed] = useState(false);
  const [latestTs,setLatestTs] = useState(null);
  const [heartbeat,setHeartbeat] = useState(null);
  const [advisory,setAdvisory] = useState(null);
  useEffect(()=>{
    // Mount toggles after first paint
    const themeMount=document.getElementById('theme-toggle-mount');
    if(themeMount && !themeMount.hasChildNodes()){ const el=document.createElement('div'); themeMount.appendChild(el); createRoot(el).render(<ThemeToggle />); }
    const densityMount=document.getElementById('density-toggle-mount');
    if(densityMount && !densityMount.hasChildNodes()){ const el=document.createElement('div'); densityMount.appendChild(el); createRoot(el).render(<DensityToggle />); }
  },[]);
  return (
    <div id="app-shell" className="app-shell">
      <Sidebar collapsed={collapsed} onToggle={()=>setCollapsed(c=>!c)} />
      <div className="app-main">
        <TopBar latestTs={latestTs} heartbeat={heartbeat} advisory={advisory} />
        <div className="app-content">
          <App onLatestTs={setLatestTs} onHeartbeat={setHeartbeat} onAdvisory={setAdvisory} />
        </div>
      </div>
    </div>
  );
}

// Guarded React mount with diagnostic logging
try {
  if (typeof window !== 'undefined') { window.__APP_BOOT_LOG && window.__APP_BOOT_LOG('phase:pre-createRoot'); }
  const rootEl = document.getElementById('root');
  if(!rootEl){
    console.error('Root element #root not found');
    window.__APP_BOOT_LOG && window.__APP_BOOT_LOG('ERROR: #root missing');
  } else {
    createRoot(rootEl).render(<ErrorBoundary><Root /></ErrorBoundary>);
    if (typeof window !== 'undefined') {
      window.__APP_BOOT_LOG && window.__APP_BOOT_LOG('phase:render-called');
      // Remove placeholder if it still exists
      const pre = document.getElementById('__boot_pre');
      if(pre) pre.remove();
    }
  }
} catch(e){
  console.error('React render failed', e);
  if (typeof window !== 'undefined') {
    window.__APP_BOOT_LOG && window.__APP_BOOT_LOG('ERROR: '+ (e?.message||e));
    // Visibly mark failure
    const r = document.getElementById('root');
    if(r){
      const div = document.createElement('div');
      div.style.cssText='font:12px ui-monospace;padding:12px;color:#fff;background:#5d1f1f;border:2px solid #ff4e4e;border-radius:8px;';
      div.textContent='React failed to mount: '+ (e?.message||e);
      r.appendChild(div);
    }
  }
}

function downloadCSV(rows){
  if(!rows || !rows.length) return;
  const headers = ['ts','voltage','soc','temperature'];
  const lines = [headers.join(',')].concat(rows.map(r => [new Date(r.ts).toISOString(), r.voltage, r.soc, r.temperature].join(',')));
  const blob = new Blob([lines.join('\n')], {type:'text/csv'});
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url; a.download = 'telemetry_history.csv';
  document.body.appendChild(a); a.click(); a.remove();
  URL.revokeObjectURL(url);
}

function SmartAlertsCard({ alerts, fallback, onAck }) {
  const list = alerts && alerts.length ? alerts : fallback || [];
  const [ackPending, setAckPending] = React.useState(null);
  const [showUnacked, setShowUnacked] = React.useState(()=> localStorage.getItem('urjanet_alert_filter') === 'unacked');
  const display = showUnacked ? list.filter(a => !a.ack_ts) : list;
  const newIdsRef = React.useRef(new Set());
  const prevIdsRef = React.useRef(new Set());
  React.useEffect(()=>{
    const current = new Set(display.map(a=>a.id));
    display.forEach(a=>{ if(!prevIdsRef.current.has(a.id)) newIdsRef.current.add(a.id); });
    prevIdsRef.current = current;
    const t = setTimeout(()=>{ newIdsRef.current.clear(); }, 1200);
    return ()=>clearTimeout(t);
  }, [display]);
  async function ack(id){
    setAckPending(id);
    try { await onAck(id); } finally { setAckPending(null); }
  }
  return (
    <GlassCard title="Smart Alerts">
      <div className="card-head" style={{justifyContent:'space-between',alignItems:'center',marginBottom:8}}>
        <h2 className="heading-sm">Smart Alerts</h2>
        <span className="btn-group">
          <button className={`btn btn-compact btn-tab ${!showUnacked?'is-active':''}`} onClick={()=>{ setShowUnacked(false); localStorage.setItem('urjanet_alert_filter','all'); }}>All</button>
          <button className={`btn btn-compact btn-tab ${showUnacked?'is-active':''}`} onClick={()=>{ setShowUnacked(true); localStorage.setItem('urjanet_alert_filter','unacked'); }}>Unacked</button>
        </span>
      </div>
      <ul className="alert-list">
        {display.map(a => (
          <li key={a.id} className={newIdsRef.current.has(a.id)?'alert-item-enter':''} style={a.ack_ts ? {opacity:0.75, transition:'0.4s opacity'} : {}}>
            <div style={{display:'flex', justifyContent:'space-between', alignItems:'center'}}>
              <strong>{a.type}</strong>
              <span className={'severity '+ (a.type==='BATTERY_SOC_RISK' ? 'sev-RISK' : 'sev-'+(a.severity||'').toUpperCase())}>{a.type==='BATTERY_SOC_RISK' ? 'RISK' : a.severity}</span>
            </div>
            <div style={{marginTop:2}}>{a.message}</div>
            {a.recommended_action && <div style={{marginTop:6, fontSize:'0.6rem', color:'#9ea7b3'}}><em>{a.recommended_action}</em></div>}
            {!a.ack_ts && <button className="btn btn-primary btn-compact" style={{marginTop:6}} disabled={ackPending===a.id} onClick={()=>ack(a.id)}>Acknowledge</button>}
            <small style={{opacity:0.6, display:'block', marginTop:4}}>{new Date(a.ts).toLocaleTimeString()}</small>
            {a.ack_ts && <small style={{opacity:0.4, display:'block'}}>Ack {new Date(a.ack_ts).toLocaleTimeString()}</small>}
          </li>
        ))}
        {!display.length && (
          <li style={{textAlign:'center',padding:'20px 8px',opacity:0.8}}>
            <div style={{fontSize:'34px', lineHeight:1, color:'#2ecc71', filter:'drop-shadow(0 0 6px rgba(46,204,113,0.4))'}}>✓</div>
            <div style={{marginTop:6,fontSize:'0.7rem',color:'#2ecc71',fontWeight:600}}>System Normal</div>
            <div style={{marginTop:2,fontSize:'0.55rem',color:'#9ba6be'}}>{showUnacked ? 'No unacknowledged alerts' : 'No active alerts'}</div>
          </li>
        )}
      </ul>
    </GlassCard>
  );
}

function RLAdvisoryCard({ advisory, latest }) {
  const [costs,setCosts] = React.useState(null);
  const [loadingCost,setLoadingCost] = React.useState(false);
  const aiAction = advisory?.actions?.[0];
  const aiLabel = aiAction?.id?.toUpperCase();
  const modelVersion = advisory?.model_version;

  React.useEffect(()=>{
    let abort=false;
    async function evaluate(){
      if(!aiAction || !latest) return;
      setLoadingCost(true);
      try {
        // Horizon from advisory action
        const horizon = aiAction.horizon_min || 15;
        // Approximations for missing context
        const loadKw = (latest.voltage || 230) * 0.02; // existing proxy in backend
        const solarKw = 8.0; // placeholder until live PV integrated
        const gridPrice = 0.12; // static for now

        // Translate AI action to approximate grid import assumption:
        // DISCHARGE -> reduce grid import, CHARGE -> increase, HOLD -> neutral
        let aiGridImportKw = Math.max(0, loadKw - solarKw); // baseline hold
        if(aiLabel === 'DISCHARGE_BATTERY_TO_LOAD') {
          aiGridImportKw = Math.max(0, aiGridImportKw - 3.0); // assume 3 kW battery contribution
        } else if(aiLabel === 'CHARGE_BATTERY') {
          aiGridImportKw = Math.max(0, aiGridImportKw + 2.0); // extra import to charge
        }
        const baselineGridImportKw = Math.max(0, loadKw - solarKw); // HOLD / grid-only baseline

  const co2Factor = 0.82; // kg CO2 per kWh (mock average grid intensity)
  const aiPayload = { grid_power_kw: aiGridImportKw, grid_price_per_kwh: gridPrice, horizon_min: horizon, co2_factor: co2Factor };
  const basePayload = { grid_power_kw: baselineGridImportKw, grid_price_per_kwh: gridPrice, horizon_min: horizon, co2_factor: co2Factor };
        const [aiResp, baseResp] = await Promise.all([
          fetch(`${BACKEND}/api/evaluate-cost`, {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(aiPayload)}),
          fetch(`${BACKEND}/api/evaluate-cost`, {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(basePayload)})
        ]);
        if(!abort){
          const aiJson = aiResp.ok ? await aiResp.json() : null;
          const baseJson = baseResp.ok ? await baseResp.json() : null;
          if(aiJson && baseJson){
            const savings = baseJson.estimated_cost_inr - aiJson.estimated_cost_inr;
            const pct = baseJson.estimated_cost_inr > 0 ? (savings / baseJson.estimated_cost_inr) * 100 : 0;
            // Emissions avoided (using quarter-hour normalized emissions field as provided)
            const aiCo2 = aiJson.estimated_co2_saved_kg ?? aiJson.components?.co2_quarter_norm_kg ?? 0;
            const baseCo2 = baseJson.estimated_co2_saved_kg ?? baseJson.components?.co2_quarter_norm_kg ?? 0;
            const co2Avoided = Math.max(0, baseCo2 - aiCo2);
            setCosts({ ai: aiJson, base: baseJson, savings, pct, co2Avoided, aiCo2, baseCo2 });
          }
        }
      } catch(e) { /* ignore */ }
      if(!abort) setLoadingCost(false);
    }
    evaluate();
    return ()=>{ abort=true; };
  }, [aiLabel, aiAction?.horizon_min, latest?.voltage, latest?.soc]);

  return (
    <GlassCard title="AI Advisory">
      <div className="card-head" style={{justifyContent:'space-between',alignItems:'center'}}>
        <h2 className="heading-sm" style={{margin:0}}>AI Advisory</h2>
        {modelVersion && <span className="fs-2xs text-dim">model {modelVersion}</span>}
      </div>
      {!advisory && <div style={{fontSize:'0.65rem', opacity:0.6}}>Loading advisory…</div>}
      {advisory && aiAction && (
        <div style={{display:'flex', flexDirection:'column', gap:10}}>
          <div style={{fontSize:'0.55rem',letterSpacing:0.5,opacity:0.7}}>RECOMMENDED ACTION</div>
          <div style={{display:'flex',alignItems:'center',gap:8}}>
            <strong style={{fontSize:'0.8rem'}}>{aiAction.title}</strong>
            <ConfidenceBadge value={aiAction.confidence} />
          </div>
          <div style={{fontSize:'0.6rem',opacity:0.8}}>{aiAction.description}</div>
          <div style={{display:'flex',gap:6,flexWrap:'wrap'}}>
            <span className="badge-outline">Impact {aiAction.impact_kw} kW</span>
            <span className="badge-outline">Horizon {aiAction.horizon_min}m</span>
            {aiAction.value_estimate!==undefined && aiAction.value_estimate!==null && <span className="badge-outline">V {aiAction.value_estimate.toFixed(2)}</span>}
          </div>
          {aiAction.raw_vector && aiAction.raw_vector.length>0 && (
            <div style={{fontSize:'0.55rem',opacity:0.65,display:'flex',flexWrap:'wrap',gap:4}}>
              {aiAction.raw_vector.slice(0,5).map((v,i)=><span key={i} style={{background:'var(--bg-accent)',padding:'2px 4px',borderRadius:4}}>{v.toFixed(2)}</span>)}
            </div>
          )}
          {(aiAction.semantic_raw || aiAction.semantic_safe) && (
            <div style={{marginTop:4, fontSize:'0.55rem', display:'flex', flexDirection:'column', gap:4}}>
              {aiAction.semantic_raw && <div style={{display:'flex',flexWrap:'wrap',gap:6}}>
                {Object.entries(aiAction.semantic_raw).map(([k,v]) => <span key={k} className="badge-outline" style={{background:'var(--bg-accent)',color:'var(--fg)',border:'none'}}>{k}:{typeof v==='number'? v.toFixed(1):v}</span>)}
              </div>}
              {aiAction.semantic_safe && JSON.stringify(aiAction.semantic_safe)!==JSON.stringify(aiAction.semantic_raw) && <div style={{display:'flex',flexWrap:'wrap',gap:6}}>
                {Object.entries(aiAction.semantic_safe).map(([k,v]) => <span key={k} className="badge-outline" style={{background:'#213040',color:'#7dd87d',border:'1px solid #284d3d'}}>{k}:{typeof v==='number'? v.toFixed(1):v}</span>)}
              </div>}
              {aiAction.safety_flags && aiAction.safety_flags.length>0 && <div style={{color:'#d4a72c'}}>Safety: {aiAction.safety_flags.join(', ')}</div>}
              <SemanticSplitBar semantic={aiAction.semantic_safe || aiAction.semantic_raw} />
            </div>
          )}
          <div style={{marginTop:6,borderTop:'1px solid var(--border)',paddingTop:6}}>
            <div className="label-up" style={{marginBottom:4}}>COST ANALYSIS ({aiAction.horizon_min}m)</div>
            {loadingCost && <div style={{fontSize:'0.6rem',opacity:0.6}}>Evaluating cost…</div>}
            {!loadingCost && costs && (
              <div className="fs-sm text-secondary" style={{display:'flex',flexDirection:'column',gap:4}}>
                <div>AI Decision Cost: ₹{costs.ai.estimated_cost_inr?.toFixed?.(2)}</div>
                <div>Baseline Cost: ₹{costs.base.estimated_cost_inr?.toFixed?.(2)} {costs.savings!==undefined && <span style={{color: costs.savings>0?'#2e8b57':'#da3633'}}>({costs.savings>0? 'Savings':'Penalty'}: ₹{Math.abs(costs.savings).toFixed(2)}{costs.pct!==undefined? ` / ${Math.abs(costs.pct).toFixed(0)}%`:''})</span>}</div>
                {costs.co2Avoided !== undefined && <div style={{color:'#58a6ff'}}>Emissions Avoided: {costs.co2Avoided.toFixed(2)} kg CO₂</div>}
              </div>
            )}
          </div>
          <small style={{opacity:0.55}}>Generated {new Date(advisory.generated_at).toLocaleTimeString()}</small>
        </div>
      )}
    </GlassCard>
  );
}

function AIInsightCard({ insight, loading, onRefresh, onAsk, chatHistory, chatQ, setChatQ, loadingChat, onRefreshChat, chatListRef: chatListRefProp }) {
  // Fallback in case prop not provided (prevents ReferenceError / crash)
  const chatListRef = chatListRefProp || React.useRef(null);
  return (
    <GlassCard title="AI Insight (Gemini)">
      <div className="card-head" style={{justifyContent:'space-between',alignItems:'center'}}>
        <h2 className="heading-sm" style={{margin:0}}>AI Insight</h2>
        <span className="btn-group">
          <button className="btn btn-ghost btn-compact" onClick={onRefresh} title="Refresh insight">↻</button>
          <button className="btn btn-ghost btn-compact" onClick={onRefreshChat} title="Refresh chat history">💬</button>
        </span>
      </div>
      {loading && <div className="fs-xs text-dim">Generating insight…</div>}
      {!loading && insight && !insight.error && (
        <div style={{display:'flex',flexDirection:'column',gap:8,fontSize:'0.6rem'}}>
          <div style={{fontSize:'0.55rem',letterSpacing:.75,opacity:.7}}>SUMMARY</div>
          <div style={{lineHeight:1.3}}>{insight.summary}</div>
          {insight.opportunities && insight.opportunities.length>0 && (
            <div>
              <div className="label-up" style={{marginBottom:4}}>OPPORTUNITIES</div>
              <ul style={{paddingLeft:14,margin:0}}>
                {insight.opportunities.map((o,i)=><li key={i} style={{marginBottom:2}}>{o}</li>)}
              </ul>
            </div>
          )}
          {insight.risks && insight.risks.length>0 && (
            <div>
              <div className="label-up" style={{marginBottom:4}}>RISKS</div>
              <ul style={{paddingLeft:14,margin:0}}>
                {insight.risks.map((r,i)=><li key={i} style={{marginBottom:2}}>{r}</li>)}
              </ul>
            </div>
          )}
          {insight.semantic_interpretation && <div style={{fontSize:'0.55rem',opacity:.75}}>Semantics: {insight.semantic_interpretation}</div>}
          {insight.cached && <div className="fs-2xs text-dim">(cached)</div>}
        </div>
      )}
      {insight && insight.error && <div style={{color:'#da3633',fontSize:'0.6rem'}}>Error: {insight.error}</div>}
      <div className="divider" />
      <div style={{display:'flex',flexDirection:'column',gap:6}}>
        <div className="label-up" style={{marginBottom:0}}>Quick Insights</div>
        <div style={{display:'flex',gap:4,flexWrap:'wrap',marginBottom:4}}>
          <button 
            className="btn btn-ghost btn-compact" 
            style={{fontSize:'0.55rem',padding:'4px 8px'}}
            onClick={()=>onAsk("Analyze current battery status and provide optimization recommendations for the next 2 hours based on real-time telemetry.")}
            disabled={loadingChat}
          >
            ⚡ Optimize Now
          </button>
          <button 
            className="btn btn-ghost btn-compact" 
            style={{fontSize:'0.55rem',padding:'4px 8px'}}
            onClick={()=>onAsk("Calculate potential cost savings if I follow the current RL advisory decision vs baseline grid-only approach. Include carbon emissions impact.")}
            disabled={loadingChat}
          >
            💰 Cost Analysis
          </button>
          <button 
            className="btn btn-ghost btn-compact" 
            style={{fontSize:'0.55rem',padding:'4px 8px'}}
            onClick={()=>onAsk("Review active alerts and RL decision history. Identify any risks or unusual patterns in the last hour and suggest preventive actions.")}
            disabled={loadingChat}
          >
            ⚠️ Risk Check
          </button>
          <button 
            className="btn btn-ghost btn-compact" 
            style={{fontSize:'0.55rem',padding:'4px 8px'}}
            onClick={()=>onAsk("Based on current SoC, load patterns, and forecast, estimate how long the battery can sustain the load without grid import. Suggest actions to extend backup time.")}
            disabled={loadingChat}
          >
            🔋 Backup Status
          </button>
        </div>
        <div className="label-up" style={{marginBottom:0}}>Ask a Question</div>
        <form onSubmit={e=>{e.preventDefault(); onAsk(chatQ);}} style={{display:'flex',gap:6}}>
          <input value={chatQ} onChange={e=>setChatQ(e.target.value)} placeholder="e.g. How to reduce grid import next hour?" style={{flex:1,background:'rgba(255,255,255,0.05)',border:'1px solid var(--color-border)',color:'var(--color-text-primary)',borderRadius:6,padding:'6px 8px',fontSize:'0.6rem'}} />
          <button className="btn btn-primary btn-compact" disabled={!chatQ.trim() || loadingChat}>{loadingChat? '...':'Ask'}</button>
          {loadingChat && <button type="button" className="btn btn-ghost btn-compact" onClick={()=>{ try { streamAbortRef.current?.abort(); } catch(e){} }} title="Cancel streaming">✕</button>}
        </form>
        <div ref={chatListRef} style={{maxHeight:180,overflow:'auto',fontSize:'0.55rem',display:'flex',flexDirection:'column',gap:6,paddingRight:2}}>
          {chatHistory.map((m,i)=>(
            <div key={i} style={{background: m.role==='user'
                ? 'rgba(255,255,255,0.06)'
                : m.fallback ? 'rgba(128,128,128,0.18)' : 'rgba(38,209,255,0.08)',
              padding:'6px 8px',borderRadius:6,whiteSpace:'pre-wrap',display:'flex',flexDirection:'column',gap:4,position:'relative',fontStyle: m.fallback? 'italic':'normal'}}>
              <div><strong style={{opacity:0.7}}>{m.role==='user' ? 'You' : 'AI'}:</strong> {m.content}</div>
              {m.streaming && <div className="typing-dots" style={{position:'absolute', bottom:4, right:6, fontSize:'0.5rem', opacity:0.5}}>…</div>}
              {m.actions && m.actions.length>0 && (
                <div style={{fontSize:'0.5rem',opacity:0.75}}>
                  <strong>Actions:</strong> {m.actions.map(a => a.text || a.label || a).join('; ')}
                </div>
              )}
              {m.risks && m.risks.length>0 && (
                <div style={{fontSize:'0.5rem',opacity:0.65,color:'#d4a72c'}}>
                  <strong>Risks:</strong> {m.risks.map(r => r.text || r).join('; ')}
                </div>
              )}
              {m.fallback && <div style={{fontSize:'0.45rem',opacity:0.5}}>(fallback)</div>}
              {!m.streaming && (!m.content || m.content.trim()==='' || m.content==='(No content returned)') && (
                <div style={{fontSize:'0.5rem',opacity:0.6}}>
                  No model content. <button
                    type="button"
                    className="btn btn-ghost btn-compact"
                    style={{fontSize:'0.5rem'}}
                    onClick={()=>onAsk('Re-answer the previous question with more detail and actionable steps')}
                  >Retry</button>
                </div>
              )}
            </div>
          ))}
          {!chatHistory.length && <div style={{opacity:0.5}}>No questions yet.</div>}
        </div>
      </div>
    </GlassCard>
  );
}

// Heuristic extraction replicated client-side for immediate streaming display
function extractActionsRisks(answer){
  const actions=[]; const risks=[]; if(!answer) return {actions:null, risks:null};
  const lower=answer.toLowerCase();
  function sliceAfter(keyword){ const idx=lower.indexOf(keyword); if(idx<0) return ''; return answer.slice(idx, idx+600); }
  const actBlock = sliceAfter('action');
  if(actBlock){ actBlock.split(/\n|;|•/).slice(0,8).forEach(line=>{ const t=line.replace(/^[-*0-9).\s]+/,'').trim(); if(t && t.length<160 && /[a-z]/i.test(t)) actions.push({text:t}); }); }
  const riskBlock = sliceAfter('risk');
  if(riskBlock){ riskBlock.split(/\n|;|•/).slice(0,8).forEach(line=>{ const t=line.replace(/^[-*0-9).\s]+/,'').trim(); if(t && t.length<160 && /[a-z]/i.test(t)) risks.push({text:t}); }); }
  return {actions: actions.length? actions: null, risks: risks.length? risks: null};
}

function ConfidenceBadge({ value }){
  const pct = Math.round((value||0)*100);
  const confColor = pct>80?'#2e8b57': pct>60? '#d4a72c':'#da3633';
  return <span className="badge-outline" style={{background:confColor,color:'#fff'}}>{pct}%</span>;
}

function SemanticSplitBar({ semantic }){
  if(!semantic) return null;
  const parts = ['battery_kw','grid_kw','ev_kw'];
  const total = parts.reduce((s,k)=> s + Math.abs(semantic[k]||0), 0) || 1;
  return (
    <div style={{display:'flex',height:6,borderRadius:4,overflow:'hidden',background:'var(--bg-accent)'}}>
      {parts.map(k => {
        const val = Math.abs(semantic[k]||0); const pct = (val/total)*100;
        const colors = {battery_kw:'#7dd87d', grid_kw:'#58a6ff', ev_kw:'#ffb347'};
        return <div key={k} style={{width:`${pct}%`,background:colors[k]||'#999'}} title={`${k} ${semantic[k]?.toFixed?.(1)} kW`} />;
      })}
    </div>
  );
}

function BatteryForecastCard({ forecast }) {
  const ref = React.useRef();
  React.useEffect(()=>{
    if(!ref.current || !forecast) return; const canvas = ref.current; const ctx = canvas.getContext('2d');
    canvas.width = canvas.clientWidth; canvas.height = canvas.clientHeight; ctx.clearRect(0,0,canvas.width,canvas.height);
    if(!forecast.points.length) return;
    const xs = forecast.points.map((p,i)=>i); const ys = forecast.points.map(p=>p.soc);
    const minY = Math.min(...ys, 0); const maxY = Math.max(...ys, 100);
    ctx.strokeStyle = '#7dd87d'; ctx.lineWidth = 2; ctx.beginPath();
    forecast.points.forEach((p,i)=>{ const x = (i/(xs.length-1))*canvas.width; const y = canvas.height - ((p.soc - minY)/(maxY-minY||1))*canvas.height; if(i===0) ctx.moveTo(x,y); else ctx.lineTo(x,y); });
    ctx.stroke();
    // threshold at 15%
    const th = canvas.height - ((15 - minY)/(maxY-minY||1))*canvas.height; ctx.strokeStyle='#da3633'; ctx.setLineDash([4,4]); ctx.beginPath(); ctx.moveTo(0,th); ctx.lineTo(canvas.width, th); ctx.stroke(); ctx.setLineDash([]);
  },[forecast]);
  return (
    <GlassCard title="Battery Forecast">
      {!forecast && <div className="fs-sm text-dim">Loading forecast…</div>}
      {forecast && (
        <>
          <div style={{position:'relative'}}>
            <canvas ref={ref} style={{width:'100%',height:120}} />
            {forecast.risk_score>0 && <div style={{position:'absolute', top:4, right:4, background:'rgba(218,54,51,0.15)', color:'#da3633', padding:'4px 6px', fontSize:'0.55rem', borderRadius:4}}>Risk: Low SoC</div>}
          </div>
          <small className="fs-xs text-dim">Generated {new Date(forecast.generated_at).toLocaleTimeString()} | Method {forecast.method}</small>
        </>
      )}
    </GlassCard>
  );
}

function DecisionHistoryCard({ decisions, onRefresh, onLoadMore, hasMore, cursor }) {
  async function exportCsv(){
    try {
      const url = `${BACKEND}/advisory/rl/history/export?device_id=${DEVICE_ID}&limit=1000`;
      const r = await fetch(url);
      if(!r.ok) return; const blob = await r.blob();
      const dl = document.createElement('a');
      dl.href = URL.createObjectURL(blob); dl.download = 'rl_decision_history.csv';
      document.body.appendChild(dl); dl.click(); dl.remove();
      setTimeout(()=>URL.revokeObjectURL(dl.href), 5000);
    } catch(e) {}
  }
  return (
    <GlassCard title="Decision History" spanFull>
      <div className="card-head" style={{justifyContent:'space-between',alignItems:'center'}}>
        <h2 className="heading-sm" style={{margin:0}}>Decision History</h2>
        <span className="btn-group"><button className="btn btn-ghost btn-compact" onClick={onRefresh}>↻</button><button className="btn btn-ghost btn-compact" onClick={exportCsv}>CSV</button></span>
      </div>
      <div style={{overflowX:'auto'}}>
        <table style={{width:'100%',borderCollapse:'collapse',fontSize:'0.6rem'}}>
          <thead>
            <tr style={{textAlign:'left'}}>
              <th>ID</th>
              <th>Time</th>
              <th>Battery kW</th>
              <th>Grid kW</th>
              <th>EV kW</th>
              <th>Curtail</th>
              <th>ΔBat</th>
              <th>ΔGrid</th>
              <th>ΔEV</th>
              <th>Value</th>
              <th>Safety Flags</th>
            </tr>
          </thead>
          <tbody>
            {decisions.map(d => {
              const safe = d.semantic_safe || d.semantic_raw || {};
              const flags = d.safety_flags || [];
              const highlight = flags.length > 0;
              const delta = d.semantic_delta || {};
              function fmt(n, digits=1){ return typeof n==='number' && !isNaN(n) ? n.toFixed(digits): ''; }
              return (
                <tr key={d.id} style={highlight? {background:'rgba(212,167,44,0.15)'}: {}}>
                  <td>{d.id}</td>
                  <td>{new Date(d.ts).toLocaleTimeString()}</td>
                  <td>{fmt(safe.battery_kw)}</td>
                  <td>{fmt(safe.grid_kw)}</td>
                  <td>{fmt(safe.ev_kw)}</td>
                  <td>{fmt(safe.curtailment,2)}</td>
                  <td style={{color: delta.battery_kw? '#ffb347':''}}>{fmt(delta.battery_kw)}</td>
                  <td style={{color: delta.grid_kw? '#ffb347':''}}>{fmt(delta.grid_kw)}</td>
                  <td style={{color: delta.ev_kw? '#ffb347':''}}>{fmt(delta.ev_kw)}</td>
                  <td>{d.value_estimate?.toFixed?.(2) ?? ''}</td>
                  <td style={{color: flags.length? '#d4a72c':'',maxWidth:160,whiteSpace:'nowrap',overflow:'hidden',textOverflow:'ellipsis'}} title={flags.join(', ')}>{flags.join(', ')}</td>
                </tr>
              );
            })}
            {!decisions.length && <tr><td colSpan={11} style={{opacity:0.6}}>No decisions logged yet.</td></tr>}
          </tbody>
        </table>
      </div>
      {hasMore && <div style={{marginTop:6}}><button onClick={onLoadMore} style={{fontSize:'0.6rem'}}>Load Older ▾</button></div>}
      {!hasMore && decisions.length > 0 && <div style={{marginTop:6,opacity:0.5,fontSize:'0.5rem'}}>End of history</div>}
    </GlassCard>
  );
}

// Reusable GlassCard wrapper
function GlassCard({ title, children, spanFull, paddingTight }) {
  const className = 'glass-card' + (spanFull ? ' span-full' : '');
  const style = spanFull ? {gridColumn:'1/-1'} : undefined;
  return (
    <div className={className} style={style}>
      {title && <h2 style={{marginTop:0,marginBottom:12}}>{title}</h2>}
      {children}
    </div>
  );
}
