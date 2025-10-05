import React, { useEffect, useRef, useState, useMemo } from 'react';
import solarIconUrl from './assets/icons/solar_panel.svg';
import gridIconUrl from './assets/icons/grid_pylon.svg';
import batteryOutlineUrl from './assets/icons/battery_outline.svg';
import batteryFillUrl from './assets/icons/battery_fill.svg';
import evIconUrl from './assets/icons/ev_station.svg';
import factoryIconUrl from './assets/icons/factory.svg';

const COLORS = {
  grid: '#4DA3FF',
  solar: '#FFB347',
  battery: '#7DD87D',
  ev: '#8B78FF',
  load: '#FFC4DD',
  import: '#4DA3FF',
  charge: '#7DD87D',
  direct: '#FFB347',
  discharge: '#7DD87D',
};

// Duration must align with main.jsx ALERT_FADE_DURATION
const ALERT_FADE_DURATION = 1500;

// Severity color bases (r,g,b) & base alpha multiplier
const SEVERITY_META = {
  HIGH:   { rgb: [255, 77, 79],  base: 0.75 },   // critical red
  MEDIUM: { rgb: [255, 179, 71], base: 0.65 },   // amber
  LOW:    { rgb: [77, 163, 255], base: 0.60 }    // informational blue
};

const SEVERITY_RANK = { HIGH: 3, MEDIUM: 2, LOW: 1 };

export function FlowCanvas({
  backend,
  highlightAction,
  activeAlerts = [],
  reduceMotion = false,
  rlSemanticSafe = null,
  rlSemanticRaw = null,
  rlModelVersion = null,
  rlUpdatedAt = null
}) {
  const canvasRef = useRef(null);
  const overlayRef = useRef(null);
  const [data,setData] = useState(null);
  const [capacities,setCapacities] = useState(null);
  const prevEdgesRef = useRef(null);
  const [hover,setHover] = useState(null);
  const [t,setT] = useState(0);
  const [showRaw,setShowRaw] = useState(false);
  const [semanticAge,setSemanticAge] = useState(0);
  const [colorThresholds,setColorThresholds] = useState({ pos: 0.5, neg: -0.5 });
  const [showThreshCfg,setShowThreshCfg] = useState(false);
  const [rlTooltip,setRlTooltip] = useState(null); // {metric, raw, safe, delta, x, y}
  const diffWidthsRef = useRef({}); // animated widths per metric
  const iconsRef = useRef({});
  // Preload icons once
  useEffect(()=>{
    const sources = {
      solar: solarIconUrl,
      grid: gridIconUrl,
      batteryOutline: batteryOutlineUrl,
      batteryFill: batteryFillUrl,
      ev: evIconUrl,
      load: factoryIconUrl
    };
    const entries = Object.entries(sources);
    let loaded = 0;
    entries.forEach(([k,src])=>{
      const img = new Image();
      img.onload = () => { loaded++; iconsRef.current[k] = img; };
      img.src = src;
    });
  },[]);

  // Initial fetch
  useEffect(()=>{ fetch(`${backend}/flow/topology`).then(r=>r.json()).then(setData).catch(()=>{}); },[backend]);
  // Capacities for scaling
  useEffect(()=>{ fetch(`${backend}/flow/rl/capacities`).then(r=>r.json()).then(setCapacities).catch(()=>{}); },[backend]);
  // Animation tick
  useEffect(()=>{ const id=setInterval(()=>setT(t=>t+1), 750); return ()=>clearInterval(id); },[]);
  // Delta polling every 5s
  useEffect(()=>{
    let failures = 0;
    const tick = () => {
      fetch(`${backend}/flow/topology/delta`).then(r=>{
        if(!r.ok) throw new Error('bad status');
        return r.json();
      }).then(delta => {
        failures = 0;
        setData(prev => {
          if(!prev) return delta;
          delta.edges.forEach(ed => {
            const old = prev.edges.find(o=>o.from===ed.from && o.to===ed.to && o.type===ed.type);
            if(old){ ed._delta = ed.power_kw - old.power_kw; }
          });
          return delta;
        });
      }).catch(()=>{
        failures += 1;
        if(failures >= 2){
          // fallback to static endpoint once
          fetch(`${backend}/flow/topology`).then(r=>r.json()).then(staticTopo => {
            setData(staticTopo);
          }).catch(()=>{});
        }
      });
    };
    const id = setInterval(tick, 5000);
    tick();
    return ()=>clearInterval(id);
  },[backend]);

  useEffect(()=>{
    const canvas = canvasRef.current; if(!canvas || !data) return;
    const ctx = canvas.getContext('2d');
    canvas.width = canvas.clientWidth; canvas.height = canvas.clientHeight;
    ctx.clearRect(0,0,canvas.width,canvas.height);

    // If RL semantic provided, derive virtual power adjustments for key edges:
    // battery_kw (>0 charging, <0 discharging), grid_kw (>0 import, <0 export), ev_kw (always >=0 charging load)
    // We'll clone edges locally to avoid mutating state.
    const chosenSemantic = showRaw ? (rlSemanticRaw || rlSemanticSafe) : (rlSemanticSafe || rlSemanticRaw);
    let edges = data.edges.map(e => ({...e}));
    if(chosenSemantic){
      const b = Number(chosenSemantic.battery_kw);
      const g = Number(chosenSemantic.grid_kw);
      const ev = Number(chosenSemantic.ev_kw);
      const capBatCharge = capacities ? (capacities.BAT1_MAX_CHARGE + capacities.BAT2_MAX_CHARGE) : 800;
      const capBatDis = capacities ? (capacities.BAT1_MAX_DISCHARGE + capacities.BAT2_MAX_DISCHARGE) : 800;
      const capGridImp = capacities ? capacities.GRID_MAX_IMPORT : 5000;
      const capGridExp = capacities ? capacities.GRID_MAX_EXPORT : 3000;
      const capEv = capacities ? capacities.EV_MAX_AGG_CHARGE : 450;
      // Adjust battery -> load and solar -> battery or grid -> battery flows conceptually
      edges = edges.map(e => {
        const copy = {...e};
        if(copy.from === 'battery' && (copy.to === 'load' || copy.to === 'ev')){
          // Discharge scenario: negative battery_kw means discharge (power leaving battery)
          if(b < -1){
            const dischargeNorm = Math.min(1, Math.abs(b)/capBatDis);
            const dischargeKw = dischargeNorm * 40;
            copy.power_kw = dischargeKw;
            copy.direction = 'forward'; // from battery to load/ev
          } else if(b > 5){
            // Charging -> suppress discharge visual
            const chargeNorm = Math.min(1, b/capBatCharge);
            copy.power_kw = Math.max(0.2, chargeNorm * 6);
            copy.direction = 'reverse';
          }
        }
        if(copy.from === 'solar' && copy.to === 'battery'){
          if(b > 5){
            const chargeNorm = Math.min(1, b/capBatCharge);
            const chargeKw = chargeNorm * 30;
            copy.power_kw = chargeKw;
            copy.direction = 'forward';
          } else if(b < -5){
            // Battery not charging from solar; maybe exporting/ discharging -> reduce
            copy.power_kw = Math.max(0.1, copy.power_kw * 0.3);
          }
        }
        if(copy.from === 'grid' && copy.to === 'load'){
          if(g > 50){ // import
            const importNorm = Math.min(1, g/capGridImp);
            copy.power_kw = importNorm * 50;
            copy.direction = 'forward';
          } else if(g < -50){ // export
            const exportNorm = Math.min(1, Math.abs(g)/capGridExp);
            copy.power_kw = exportNorm * 50;
            copy.direction = 'reverse';
          }
        }
        if(copy.from === 'grid' && copy.to === 'ev'){
          if(ev > 10){
            const evNorm = Math.min(1, ev/capEv);
            copy.power_kw = evNorm * 30;
            copy.direction = 'forward';
          }
        }
        return copy;
      });
    }

    // Interpolate with previous edges for smoothness
    const prev = prevEdgesRef.current;
    if(prev){
      edges = edges.map(e => {
        const p = prev.find(pe => pe.from===e.from && pe.to===e.to && pe.type===e.type);
        if(!p) return e;
        const alpha = 0.25; // smoothing factor
        return { ...e, power_kw: p.power_kw + (e.power_kw - p.power_kw)*alpha };
      });
    }
    prevEdgesRef.current = edges.map(e=>({...e}));

    // Preselect best (highest severity) alert per node type
    const alertNodeMap = {};
    activeAlerts.forEach(a => {
      const type = (a.type||'').toUpperCase();
      // Derive node type heuristic
      let nodeType = null;
      if(type.includes('BATTERY') || type.includes('SOC') || type.includes('TEMP')) nodeType = 'battery';
      else if(type.includes('GRID') || type.includes('VOLT')) nodeType = 'grid';
      else if(type.includes('LOAD')) nodeType = 'load';
      else if(type.includes('SOLAR') || type.includes('PV')) nodeType = 'solar';
      if(!nodeType) return;
      const sev = (a.severity||'').toUpperCase();
      if(!alertNodeMap[nodeType] || (SEVERITY_RANK[sev]||0) > (SEVERITY_RANK[alertNodeMap[nodeType].severity||'']||0)){
        alertNodeMap[nodeType] = a;
      }
    });

    // Gradient cache keyed by severity+radius
    const gradientCache = new Map();
    function getHaloGradient(sevKey, radius, ctx, alpha){
      const key = sevKey+':'+radius;
      let gObj = gradientCache.get(key);
      if(!gObj){
        const { rgb } = SEVERITY_META[sevKey] || SEVERITY_META.LOW;
        const g = ctx.createRadialGradient(0,0, radius*0.15, 0,0, radius);
        // store raw stops (we'll apply alpha dynamically by fillStyle modification)
        gObj = { g, rgb };
        gradientCache.set(key, gObj);
      }
      // We cannot mutate existing gradient stops with new alpha; recreate each frame with alpha
      // So caching only rgb & radius shape saves computation for geometry; construct real gradient now:
      const { rgb } = gObj;
      const gLive = ctx.createRadialGradient(0,0, radius*0.15, 0,0, radius);
      gLive.addColorStop(0,    `rgba(${rgb[0]},${rgb[1]},${rgb[2]},${alpha})`);
      gLive.addColorStop(0.55, `rgba(${rgb[0]},${rgb[1]},${rgb[2]},${alpha*0.35})`);
      gLive.addColorStop(1,    `rgba(${rgb[0]},${rgb[1]},${rgb[2]},0)`);
      return gLive;
    }

    // Draw edges first
    edges.forEach(e => {
      const from = data.nodes.find(n=>n.id===e.from);
      const to = data.nodes.find(n=>n.id===e.to);
      if(!from || !to) return;
      // Base color chooses source node color based on direction
      const sourceNode = e.direction === 'reverse' ? to : from;
      const col = COLORS[sourceNode.type] || COLORS[e.type] || '#eee';
      const power = e.power_kw;
      const thickness = Math.min(18, 2 + Math.log(Math.abs(power)+1)*3);
      // path
      const isDischarge = highlightAction === 'DISCHARGE_BATTERY_TO_LOAD' && from.type==='battery' && to.type==='load';
      const isCharge = highlightAction === 'CHARGE_BATTERY' && from.type==='grid' && to.type==='battery';
      if(isDischarge || isCharge){
        const pulse = 0.5 + 0.5*Math.sin(Date.now()/250);
        ctx.strokeStyle = isDischarge? `rgba(255,80,80,${0.4 + 0.5*pulse})` : `rgba(80,180,255,${0.4 + 0.5*pulse})`;
      } else if(e._delta && Math.abs(e._delta) > 0.4){
        const pulse = 0.5 + 0.5*Math.sin(Date.now()/300);
        ctx.strokeStyle = `rgba(255,255,255,${0.35 + 0.4*pulse})`;
      } else ctx.strokeStyle = col;
      ctx.lineWidth = thickness;
      ctx.lineCap = 'round';
      ctx.beginPath();
      const mx = (from.x + to.x)/2;
      const my = (from.y + to.y)/2 - 40; // subtle arc
      // Quadratic curve
      ctx.moveTo(from.x, from.y);
      ctx.quadraticCurveTo(mx, my, to.x, to.y);
      ctx.stroke();
      // Directional arrowhead (animated unless reduceMotion)
      let xPos, yPos, angle;
      if(reduceMotion){
        const tNorm = 0.5; // static midpoint
        xPos = (1-tNorm)*(1-tNorm)*from.x + 2*(1-tNorm)*tNorm*mx + tNorm*tNorm*to.x;
        yPos = (1-tNorm)*(1-tNorm)*from.y + 2*(1-tNorm)*tNorm*my + tNorm*tNorm*to.y;
        const dx = 2*(1-tNorm)*(mx-from.x) + 2*tNorm*(to.x-mx);
        const dy = 2*(1-tNorm)*(my-from.y) + 2*tNorm*(to.y-my);
        angle = Math.atan2(dy, dx) + (e.direction==='forward'?0:Math.PI);
      } else {
        const baseSpeed = 1400 + (300 * (1/Math.max(0.2, Math.abs(power))));
        const tRaw = (Date.now()/baseSpeed) % 1;
        const tHead = e.direction==='forward' ? tRaw : (1 - tRaw);
        const tNorm = 0.08 + 0.84 * tHead;
        xPos = (1-tNorm)*(1-tNorm)*from.x + 2*(1-tNorm)*tNorm*mx + tNorm*tNorm*to.x;
        yPos = (1-tNorm)*(1-tNorm)*from.y + 2*(1-tNorm)*tNorm*my + tNorm*tNorm*to.y;
        const dx = 2*(1-tNorm)*(mx-from.x) + 2*tNorm*(to.x-mx);
        const dy = 2*(1-tNorm)*(my-from.y) + 2*tNorm*(to.y-my);
        angle = Math.atan2(dy, dx) + (e.direction==='forward'?0:Math.PI);
      }
      ctx.save();
      ctx.translate(xPos, yPos);
      ctx.rotate(angle);
      const ah = Math.max(16, thickness*1.4); // enlarged arrowhead
      const aw = ah * 0.6;
      ctx.beginPath();
      ctx.moveTo(0,0);
      ctx.lineTo(-ah, aw);
      ctx.lineTo(-ah, -aw);
      ctx.closePath();
      // High contrast fill + outline
      ctx.fillStyle = col;
      ctx.strokeStyle = '#000';
      ctx.lineWidth = 2;
      ctx.fill();
      ctx.stroke();
      ctx.restore();
    });

    // Draw nodes
    const iconScale = 0.5; // scale down big svg bounding boxes
  data.nodes.forEach(n => {
      const outlineCol = COLORS[n.type] || '#666';
      const metrics = n.metrics || {};
      const power = metrics.power_kw ?? 0;
      const soc = metrics.soc ?? null;
      // Determine icon image
      let img; let extraDraw = null;
      if(n.type==='solar') img = iconsRef.current.solar;
      else if(n.type==='grid') img = iconsRef.current.grid;
      else if(n.type==='battery') img = iconsRef.current.batteryOutline;
      else if(n.type==='ev') img = iconsRef.current.ev;
      else if(n.type==='load') img = iconsRef.current.load;
      const w = (img?.width||120)*iconScale;
      const h = (img?.height||120)*iconScale;
      const x = n.x - w/2; const y = n.y - h/2;

      // Severity-aware Alert Halo (with fade & flicker) if mapped
      const alert = alertNodeMap[n.type];
      if(alert){
        const sevKey = (alert.severity||'').toUpperCase();
        const meta = SEVERITY_META[sevKey] || SEVERITY_META.LOW;
        const now = Date.now();
        // Pulse / flicker
        let modulation;
        if(sevKey === 'HIGH'){
          if(reduceMotion){
            modulation = 0.75; // static strong presence
          } else {
            const fastT = (now / 1000) * 7; // 7 Hz
            const saw = fastT - Math.floor(fastT);
            const jitter = Math.random()*0.25;
            modulation = Math.min(1, (saw*0.9) + jitter*0.6);
          }
        } else {
          modulation = reduceMotion ? 0.55 : 0.35 + 0.65 * ((Math.sin(now/370) + 1)/2);
        }
        // Fade-out easing if acknowledged (ack_timestamp added by parent)
        let fade = 1;
        if(alert.ack_timestamp){
          const elapsed = now - alert.ack_timestamp;
          if(elapsed >= ALERT_FADE_DURATION){
            fade = 0; // skip drawing
          } else {
            const tNorm = elapsed / ALERT_FADE_DURATION; // 0..1
            // Ease-out (quadratic) for smoother finish
            fade = 1 - (tNorm * tNorm);
          }
        }
        if(fade > 0){
          const finalAlpha = modulation * meta.base * fade;
          const haloR = Math.max(w,h)/2 + 34;
          ctx.save();
          ctx.translate(n.x, n.y);
          ctx.fillStyle = getHaloGradient(sevKey || 'LOW', haloR, ctx, finalAlpha);
          ctx.globalCompositeOperation = 'lighter';
          ctx.beginPath(); ctx.arc(0,0,haloR,0,Math.PI*2); ctx.fill();
          // Extra subtle outer ring for HIGH severity
          if(sevKey === 'HIGH'){
            ctx.strokeStyle = `rgba(255,77,79,${0.25*fade})`;
            ctx.lineWidth = 3;
            ctx.beginPath(); ctx.arc(0,0,haloR+6,0,Math.PI*2); ctx.stroke();
          }
          ctx.restore();
        }
      }

      // Dynamic effects
      if(n.type==='solar'){
        const glowIntensity = Math.min(1, Math.abs(power)/20); // assume ~20kW max
        const grd = ctx.createRadialGradient(n.x, n.y, 5, n.x, n.y, 60);
        grd.addColorStop(0, `rgba(255,179,71,${0.15*glowIntensity})`);
        grd.addColorStop(1, 'rgba(255,179,71,0)');
        ctx.fillStyle = grd;
        ctx.beginPath(); ctx.arc(n.x, n.y, 60, 0, Math.PI*2); ctx.fill();
      }
      if(n.type==='grid' || n.type==='load'){
        if(reduceMotion){
          if(img) ctx.drawImage(img, x, y, w, h);
        } else {
          const speedFactor = Math.min(1.5, Math.abs(power)/30 + 0.2);
          const pulseGlow = 0.5 + 0.5*Math.sin(Date.now()/ (900 / speedFactor));
          ctx.save();
          ctx.globalAlpha = 0.85 + 0.15*pulseGlow;
          if(img) ctx.drawImage(img, x, y, w, h);
          ctx.restore();
        }
      } else if(n.type==='battery'){
        // Draw outline first
        if(img) ctx.drawImage(img, x, y, w, h);
        // Battery fill overlay
        if(soc !== null){
          const fillImg = iconsRef.current.batteryFill;
          if(fillImg){
            const fillHeight = h * Math.max(0, Math.min(1, soc / 100));
            ctx.save();
            // Clip inside fill rectangle region
            ctx.beginPath();
            ctx.rect(x, y + (h - fillHeight), w, fillHeight);
            ctx.clip();
            ctx.globalAlpha = 0.85;
            ctx.drawImage(fillImg, x, y, w, h);
            ctx.restore();
          }
        }
      } else {
        if(img) ctx.drawImage(img, x, y, w, h);
      }

      // Metric text overlay below icon
      ctx.font = '600 11px Inter, sans-serif';
      ctx.textAlign = 'center';
      ctx.fillStyle = outlineCol;
      if(metrics.power_kw !== undefined){
        ctx.fillText((power>0?'+':'')+power.toFixed(1)+' kW', n.x, n.y + h/2 + 18);
      } else if(soc !== null){
        ctx.fillText(soc.toFixed(1)+'% SoC', n.x, n.y + h/2 + 18);
      } else {
        ctx.fillText(n.label, n.x, n.y + h/2 + 18);
      }

      // Heartbeat ring repurposed: subtle ring for all nodes
  const pulse = reduceMotion ? 0.5 : (0.5 + 0.5*Math.sin(Date.now()/600));
      ctx.beginPath();
      ctx.strokeStyle = 'rgba(90,178,255,'+ (0.15 + pulse*0.15)+')';
      ctx.lineWidth = 4;
      ctx.arc(n.x, n.y, Math.max(w,h)/2 + 10, 0, Math.PI*2);
      ctx.stroke();
    });

  },[data,t,rlSemanticSafe,rlSemanticRaw,showRaw,highlightAction,activeAlerts,reduceMotion,capacities]);

  // Track semantic staleness age (seconds)
  useEffect(()=>{
    if(!rlUpdatedAt){ setSemanticAge(0); return; }
    const ts = new Date(rlUpdatedAt).getTime();
    const tick = () => {
      setSemanticAge(Math.max(0, (Date.now()-ts)/1000));
    };
    tick();
    const id = setInterval(tick, 1000);
    return ()=>clearInterval(id);
  },[rlUpdatedAt]);

  useEffect(()=>{
    const ov = overlayRef.current; if(!ov) return;
    const handler = (e) => {
      if(!data) return;
      const rect = ov.getBoundingClientRect();
      const x = e.clientX - rect.left; const y = e.clientY - rect.top;
      const hit = data.nodes.find(n => Math.hypot(n.x - x, n.y - y) < 42);
      setHover(hit||null);
    };
    ov.addEventListener('mousemove', handler);
    ov.addEventListener('mouseleave', ()=>setHover(null));
    return ()=>{ ov.removeEventListener('mousemove', handler); };
  },[data]);

  return (
    <div className="card energy" style={{gridColumn:'1/-1', position:'relative', minHeight:420}}>
      <h2>Energy Flow</h2>
      <div style={{position:'absolute', inset:12, top:42}}>
        <canvas ref={canvasRef} style={{width:'100%',height:360, display:'block'}} />
        <div ref={overlayRef} style={{position:'absolute', inset:0}} />
        <div style={{position:'absolute', right:8, bottom:8, background:'rgba(0,0,0,0.55)', backdropFilter:'blur(4px)', padding:'8px 10px', borderRadius:8, fontSize:10, lineHeight:1.3, minWidth:170}}>
          <div style={{fontWeight:600, marginBottom:4}}>Legend</div>
          <div style={{display:'flex',alignItems:'center',gap:6}}><span style={{width:10,height:10,background:'#FFB347',borderRadius:3,display:'inline-block'}} /> Solar</div>
          <div style={{display:'flex',alignItems:'center',gap:6}}><span style={{width:10,height:10,background:'#4DA3FF',borderRadius:3,display:'inline-block'}} /> Grid</div>
            <div style={{display:'flex',alignItems:'center',gap:6}}><span style={{width:10,height:10,background:'#7DD87D',borderRadius:3,display:'inline-block'}} /> Battery</div>
            <div style={{display:'flex',alignItems:'center',gap:6}}><span style={{width:10,height:10,background:'#8B78FF',borderRadius:3,display:'inline-block'}} /> EV</div>
            <div style={{display:'flex',alignItems:'center',gap:6}}><span style={{width:10,height:10,background:'#FFC4DD',borderRadius:3,display:'inline-block'}} /> Load</div>
            <div style={{marginTop:4,opacity:0.7}}>Arrow shows flow direction & speed ~ kW</div>
            {(rlSemanticSafe || rlSemanticRaw) && (
              <div style={{marginTop:6, paddingTop:6, borderTop:'1px solid rgba(255,255,255,0.15)'}}>
                <div style={{display:'flex',alignItems:'center',gap:6}}>
                  <div style={{fontWeight:600}}>RL Influence</div>
                  <button onClick={()=>setShowRaw(s=>!s)} style={{cursor:'pointer',background:'rgba(255,255,255,0.08)',border:'1px solid rgba(255,255,255,0.15)',color:'#fff',fontSize:9,padding:'2px 6px',borderRadius:4}}>
                    {showRaw? 'Raw' : 'Safe'}
                  </button>
                  <button onClick={()=>setShowThreshCfg(v=>!v)} title="Configure thresholds" style={{cursor:'pointer',background:'rgba(255,255,255,0.08)',border:'1px solid rgba(255,255,255,0.15)',color:'#fff',fontSize:9,padding:'2px 6px',borderRadius:4}}>⚙</button>
                </div>
                <div style={{fontSize:9, opacity:0.75, marginBottom:2}}>v{rlModelVersion||'?'} • {semanticAge.toFixed(0)}s old{semanticAge>15?' (stale)':''}</div>
                {showThreshCfg && (
                  <div style={{background:'rgba(255,255,255,0.07)',padding:'6px 6px 8px',border:'1px solid rgba(255,255,255,0.15)',borderRadius:6,marginBottom:6}}>
                    <div style={{fontSize:9, marginBottom:4}}>Color thresholds (kW):</div>
                    <div style={{display:'flex',gap:6,alignItems:'center',flexWrap:'wrap'}}>
                      <label style={{fontSize:9}}>Pos≥<input type="number" step="0.1" value={colorThresholds.pos} onChange={e=>setColorThresholds(th=>({...th,pos:parseFloat(e.target.value)||0}))} style={{width:60,marginLeft:4}} /></label>
                      <label style={{fontSize:9}}>Neg≤<input type="number" step="0.1" value={colorThresholds.neg} onChange={e=>setColorThresholds(th=>({...th,neg:parseFloat(e.target.value)||0}))} style={{width:60,marginLeft:4}} /></label>
                      <button onClick={()=>setShowThreshCfg(false)} style={{fontSize:9,background:'rgba(255,255,255,0.12)',border:'1px solid rgba(255,255,255,0.2)',color:'#fff',borderRadius:4,padding:'2px 6px'}}>Close</button>
                    </div>
                  </div>
                )}
                {(() => {
                  const sem = showRaw ? (rlSemanticRaw||rlSemanticSafe) : (rlSemanticSafe||rlSemanticRaw);
                  if(!sem) return null;
                  const staleFade = semanticAge > 15 ? 0.35 : 1;
                  const raw = rlSemanticRaw || {};
                  const safe = rlSemanticSafe || {};
                  const metrics = [
                    { key:'battery_kw', label:'Battery' },
                    { key:'grid_kw', label:'Grid' },
                    { key:'ev_kw', label:'EV' }
                  ];
                  const valStyle = (v) => {
                    let col = '#ddd';
                    if(typeof v === 'number'){
                      if(v >= colorThresholds.pos) col = '#4caf50';
                      else if(v <= colorThresholds.neg) col = '#ff5252';
                    }
                    return {color: col, opacity: staleFade, cursor:'pointer'};
                  };
                  const capTotals = {
                    battery_kw: capacities ? (capacities.BAT1_MAX_CHARGE + capacities.BAT2_MAX_CHARGE) : 800,
                    grid_kw: capacities ? Math.max(capacities.GRID_MAX_IMPORT, capacities.GRID_MAX_EXPORT) : 5000,
                    ev_kw: capacities ? capacities.EV_MAX_AGG_CHARGE : 450
                  };
                  return metrics.map(m => {
                    const v = sem[m.key];
                    const rawV = raw[m.key];
                    const safeV = safe[m.key];
                    const hasBoth = typeof rawV === 'number' && typeof safeV === 'number';
                    let delta = null;
                    if(hasBoth) delta = rawV - safeV;
                    // Diff bar magnitude
                    const cap = capTotals[m.key] || 1;
                    const absFrac = hasBoth ? Math.min(1, Math.abs(delta)/cap) : 0;
                    const targetWidth = Math.round( absFrac * 100 ); // px
                    const prevW = diffWidthsRef.current[m.key] ?? 0;
                    const animatedW = prevW + (targetWidth - prevW) * 0.3;
                    diffWidthsRef.current[m.key] = animatedW;
                    return (
                      <div key={m.key} style={{marginBottom:4}}>
                        <div>{m.label}: <span
                          style={valStyle(v)}
                          onMouseEnter={e=> setRlTooltip({ metric: m.label, raw: rawV, safe: safeV, delta, x: e.clientX, y: e.clientY })}
                          onMouseLeave={()=> setRlTooltip(null)}
                        >{Number(v||0).toFixed(1)} kW</span></div>
                        {hasBoth && (
                          <div style={{position:'relative', height:6, marginTop:2, background:'rgba(255,255,255,0.08)', borderRadius:3, overflow:'hidden'}}>
                            <div style={{position:'absolute', left:'50%', top:0, bottom:0, width:1, background:'rgba(255,255,255,0.25)'}} />
                            <div style={{
                              position:'absolute',
                              top:0,
                              bottom:0,
                              width:animatedW,
                              transform: delta < 0 ? `translateX(calc(50% - ${animatedW}px))` : 'translateX(50%)',
                              background: delta < 0 ? 'linear-gradient(90deg,#ff5252,#ff867f)' : 'linear-gradient(90deg,#4caf50,#81c784)',
                              transition: 'transform 0.4s ease, width 0.4s ease',
                              opacity: staleFade
                            }} />
                          </div>
                        )}
                      </div>
                    );
                  });
                })()}
                {rlTooltip && (
                  <div style={{position:'fixed', left: rlTooltip.x + 12, top: rlTooltip.y + 12, background:'rgba(0,0,0,0.72)', padding:'6px 8px', borderRadius:6, fontSize:10, pointerEvents:'none', zIndex:999}}>
                    <div style={{fontWeight:600, marginBottom:2}}>{rlTooltip.metric} Delta</div>
                    {typeof rlTooltip.raw === 'number' && typeof rlTooltip.safe === 'number' ? (
                      <>
                        <div>Raw: {rlTooltip.raw.toFixed(2)} kW</div>
                        <div>Safe: {rlTooltip.safe.toFixed(2)} kW</div>
                        <div>Δ Raw-Safe: {(rlTooltip.delta).toFixed(2)} kW</div>
                      </>
                    ) : <div>No diff</div>}
                  </div>
                )}
              </div>
            )}
        </div>
        {hover && (
          <div style={{position:'absolute', left:hover.x+10, top:hover.y-10, background:'rgba(8,12,20,0.85)', backdropFilter:'blur(8px)', padding:'8px 10px', borderRadius:10, fontSize:10, pointerEvents:'none', boxShadow:'0 4px 18px -4px rgba(0,0,0,0.6)', maxWidth:180}}>
            <div style={{fontWeight:600,marginBottom:4}}>{hover.label}</div>
            {hover.metrics && Object.entries(hover.metrics).map(([k,v]) => <div key={k} style={{display:'flex',justifyContent:'space-between',gap:8}}><span style={{opacity:0.65}}>{k}</span><span style={{fontWeight:500}}>{typeof v==='number'? v.toFixed(2): String(v)}</span></div>)}
            {hover.type==='battery' && <div style={{marginTop:4,display:'flex',justifyContent:'space-between'}}><span style={{opacity:0.65}}>Health</span><span style={{color:'#7dd87d'}}>98%</span></div>}
            {hover.type==='grid' && <div style={{marginTop:4,display:'flex',justifyContent:'space-between'}}><span style={{opacity:0.65}}>Tariff</span><span style={{color:'#58a6ff'}}>₹8.2/kWh</span></div>}
          </div>
        )}
      </div>
    </div>
  );
}
