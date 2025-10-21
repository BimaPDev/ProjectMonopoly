#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test2.py
- Sim trading on Solana pairs discovered via DexScreener (search + boosts top + boosts latest).
- Orders routed via GMGN route API (preview only when DRY_RUN/SIM).
- Position mgmt with TP/SL/time-based exit. Optional scalp mode.
- Local AI (Ollama) advisor for size/TP/SL. Auto-start Ollama if not running.
- Threaded route previews. Full preflight health checks before scanning.
All runtime config comes from .env
"""

import os, sys, time, json, threading, queue, subprocess, shutil, platform
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple
import requests
from dotenv import load_dotenv

load_dotenv()

# --- core run mode ---
SIM_MODE          = os.getenv("SIM_MODE","true").lower()=="true"
SIM_START_USD     = float(os.getenv("SIM_START_USD","100"))
USD_BUDGET        = float(os.getenv("USD_BUDGET","10"))
DRY_RUN           = os.getenv("DRY_RUN","true").lower()=="true"

# --- prices ---
SOL_PRICE_SRC     = os.getenv("SOL_PRICE_SRC","coingecko").lower()
FIXED_SOL_PRICE   = float(os.getenv("FIXED_SOL_PRICE","150"))

# --- router ---
GMGN_SWAP_ROUTE_URL = os.getenv("GMGN_SWAP_ROUTE_URL","https://gmgn.ai/defi/router/v1/sol/tx/get_swap_route")
SLIPPAGE_PCT      = float(os.getenv("SLIPPAGE_PCT","2.0"))
IS_ANTI_MEV       = os.getenv("IS_ANTI_MEV","true").lower()=="true"
FEE_SOL           = float(os.getenv("FEE_SOL","0.002"))
SWAP_MODE         = os.getenv("SWAP_MODE","ExactIn")
VERBOSE_ROUTE     = os.getenv("VERBOSE_ROUTE","false").lower()=="true"

# --- signal filters ---
MIN_5M_PCT        = float(os.getenv("MIN_5M_PCT","1.0"))
MIN_15M_PCT       = float(os.getenv("MIN_15M_PCT","2.0"))
MIN_LIQ_USD       = float(os.getenv("MIN_LIQ_USD","5000"))
MAX_MC_USD        = float(os.getenv("MAX_MC_USD","20000000"))
REQUIRE_RAYDIUM   = os.getenv("REQUIRE_RAYDIUM","false").lower()=="true"
ALLOW_NO_VOL_5M   = os.getenv("ALLOW_NO_VOL_5M","true").lower()=="true"
OUTLIER_PC5M_THRESHOLD = float(os.getenv("OUTLIER_PC5M_THRESHOLD","300"))
OUTLIER_LIQ_MAX   = float(os.getenv("OUTLIER_LIQ_MAX","1000000"))

# --- discovery sources ---
DISCOVERY_SOURCES = [s.strip() for s in os.getenv("DISCOVERY_SOURCES","search,boosts_top,boosts_latest").split(",") if s.strip()]
SEARCH_QUERY      = os.getenv("SEARCH_QUERY","solana raydium")
NEW_PAIR_MAX_AGE_MIN = int(os.getenv("NEW_PAIR_MAX_AGE_MIN","60"))
GAINERS_WINDOW    = os.getenv("GAINERS_WINDOW","m5")  # m5 or m15

# --- loop ---
POLL_SECS         = int(os.getenv("POLL_SECS","20"))
TP_PCT            = float(os.getenv("TP_PCT","15"))
SL_PCT            = float(os.getenv("SL_PCT","-10"))
MAX_HOLD_SEC      = int(os.getenv("MAX_HOLD_SEC","900"))
COOLDOWN_SEC      = int(os.getenv("COOLDOWN_SEC","300"))

# --- wallet ---
WALLET_ADDRESS    = os.getenv("WALLET_ADDRESS","<YOUR_BASE58_PUBKEY>")
DUMMY_WALLET      = os.getenv("DUMMY_WALLET","6uY2kGi99ZTSdKCbFf8gUpZZQzQpimeJVFRCGDpa2BkL")

# --- LLM advisor ---
LLM_KIND          = os.getenv("LLM_KIND","ollama").lower()   # ollama | off
LLM_ENDPOINT      = os.getenv("LLM_ENDPOINT","http://127.0.0.1:11434")
LLM_MODEL         = os.getenv("LLM_MODEL","gemma3:latest")
LLM_TEMP          = float(os.getenv("LLM_TEMP","0.1"))
LLM_TIMEOUT       = float(os.getenv("LLM_TIMEOUT","5.0"))
ADVISOR_MAX_FRACTION = float(os.getenv("ADVISOR_MAX_FRACTION","0.30"))
LLM_DEBUG         = os.getenv("LLM_DEBUG","false").lower()=="true"

# --- scalp mode ---
SCALP_ENABLE      = os.getenv("SCALP_ENABLE","false").lower()=="true"
SCALP_TP_PCT      = float(os.getenv("SCALP_TP_PCT","2.0"))
SCALP_SL_PCT      = float(os.getenv("SCALP_SL_PCT","-1.0"))
SCALP_MAX_HOLD_SEC= int(os.getenv("SCALP_MAX_HOLD_SEC","120"))
SCALP_MIN_PC5M    = float(os.getenv("SCALP_MIN_PC5M","3.0"))
SCALP_MIN_TXNS_5M = int(os.getenv("SCALP_MIN_TXNS_5M","20"))
SCALP_COOLDOWN_SEC= int(os.getenv("SCALP_COOLDOWN_SEC","120"))

# --- concurrency ---
ROUTE_THREADS     = int(os.getenv("ROUTE_THREADS","4"))

# --- constants ---
DS_BASE = "https://api.dexscreener.com"

# ---------------- helpers ----------------
def now_ts(): return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
def log(s): print(f"{now_ts()} {s}", flush=True)
def short(x, n=6): return x[:n]+"…" if x else "NA"
def usd(x): return f"${x:,.2f}"

def get_sol_price() -> float:
    if SOL_PRICE_SRC == "fixed": return FIXED_SOL_PRICE
    if SOL_PRICE_SRC == "coingecko":
        try:
            r = requests.get("https://api.coingecko.com/api/v3/simple/price",
                             params={"ids":"solana","vs_currencies":"usd"}, timeout=5)
            return float(r.json()["solana"]["usd"])
        except Exception:
            return FIXED_SOL_PRICE
    return FIXED_SOL_PRICE

# -------- Ollama helpers (auto-start) --------
def _ollama_url(path:str)->str:
    base = LLM_ENDPOINT.rstrip("/")
    return f"{base}{path}"

def ollama_is_up(timeout_s:float=2.5)->bool:
    try:
        r = requests.get(_ollama_url("/api/tags"), timeout=timeout_s)
        return r.status_code == 200
    except Exception:
        return False

def start_ollama(max_wait_s:int=25)->bool:
    is_windows = platform.system().lower().startswith("win")
    started = False

    if is_windows:
        try:
            subprocess.run(["sc", "start", "Ollama"], check=False,
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            started = True
        except Exception:
            pass

    if not started:
        exe = shutil.which("ollama")
        if exe:
            try:
                flags = 0
                if is_windows:
                    CREATE_NO_WINDOW = 0x08000000
                    DETACHED_PROCESS = 0x00000008
                    CREATE_NEW_PROCESS_GROUP = 0x00000200
                    flags = CREATE_NO_WINDOW | DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP

                subprocess.Popen([exe, "serve"],
                                 stdout=subprocess.DEVNULL,
                                 stderr=subprocess.STDOUT,
                                 creationflags=flags if is_windows else 0,
                                 close_fds=not is_windows)
                started = True
            except Exception:
                started = False

    if started:
        deadline = time.time() + max_wait_s
        while time.time() < deadline:
            if ollama_is_up():
                return True
            time.sleep(0.5)
    return ollama_is_up()

# --------------- preflight ---------------
def preflight() -> bool:
    ok = True
    log("PRECHECK start")

    # config echo
    log(f"CFG discovery={','.join(DISCOVERY_SOURCES)} scalp={SCALP_ENABLE} raydium_only={REQUIRE_RAYDIUM}")
    log(f"CFG tp={TP_PCT}% sl={SL_PCT}% hold={MAX_HOLD_SEC}s scalp_tp={SCALP_TP_PCT}% scalp_sl={SCALP_SL_PCT}%")
    log(f"CFG router={GMGN_SWAP_ROUTE_URL} slippage={SLIPPAGE_PCT}% antiMEV={IS_ANTI_MEV} feeSOL={FEE_SOL}")

    # price source
    try:
        t0=time.time(); px=get_sol_price(); dt=(time.time()-t0)*1000
        if px>0:
            log(f"CHECK price[{SOL_PRICE_SRC}] PASS sol={usd(px)} ({dt:.0f}ms)")
        else:
            log("CHECK price FAIL invalid"); ok=False
    except Exception as e:
        log(f"CHECK price FAIL {e}"); ok=False

    # DexScreener endpoints
    try:
        r = requests.get(f"{DS_BASE}/latest/dex/search", params={"q":"solana"}, timeout=6)
        j = r.json(); n = len(j.get("pairs",[]) or [])
        log(f"CHECK dexscreener/search PASS pairs={n}")
    except Exception as e:
        log(f"CHECK dexscreener/search FAIL {e}"); ok=False
    try:
        r = requests.get(f"{DS_BASE}/token-boosts/top/v1", timeout=6)
        _ = r.json()
        log("CHECK dexscreener/boosts_top PASS")
    except Exception as e:
        log(f"CHECK dexscreener/boosts_top FAIL {e}"); ok=False
    try:
        r = requests.get(f"{DS_BASE}/token-boosts/latest/v1", timeout=6)
        _ = r.json()
        log("CHECK dexscreener/boosts_latest PASS")
    except Exception as e:
        log(f"CHECK dexscreener/boosts_latest FAIL {e}"); ok=False

    # GMGN route host reachability
    try:
        host = "https://gmgn.ai"
        t0=time.time()
        _ = requests.get(host, timeout=5)
        log(f"CHECK gmgn host PASS ({int((time.time()-t0)*1000)}ms)")
    except Exception as e:
        log(f"CHECK gmgn host WARN {e}")

    # Ollama advisor
    if LLM_KIND == "ollama":
        if not ollama_is_up():
            log("CHECK ollama not responding → attempting auto-start…")
            ok_started = start_ollama(max_wait_s=int(LLM_TIMEOUT)+20)
            if not ok_started:
                log("CHECK ollama FAIL could not start or reach endpoint")
            else:
                log("CHECK ollama started")
        try:
            t0=time.time()
            tags = requests.get(_ollama_url("/api/tags"), timeout=3).json().get("models",[])
            names = {m.get("name") for m in tags}
            if LLM_MODEL in names or any(LLM_MODEL in (m.get("model") or "") for m in tags):
                log(f"CHECK ollama/tags PASS models={len(tags)} ({int((time.time()-t0)*1000)}ms)")
            else:
                log(f"CHECK ollama/tags WARN model_missing={LLM_MODEL}")
            payload={"model":LLM_MODEL,"prompt":"{\"ping\":true}","stream":False,"options":{"temperature":LLM_TEMP}}
            t0=time.time()
            r = requests.post(_ollama_url("/api/generate"), json=payload, timeout=LLM_TIMEOUT)
            j = r.json(); txt = (j.get("response") or "").strip()
            log(f"CHECK ollama/generate PASS ({int((time.time()-t0)*1000)}ms) resp={txt[:60].replace(chr(10),' ')}")
        except Exception as e:
            log(f"CHECK ollama FAIL {e}")
    else:
        log("CHECK advisor skipped (LLM_KIND!=ollama)")

    log("PRECHECK done")
    return ok

# --------------- Dexscreener fetchers ---------------
def ds_search_pairs(q:str)->List[Dict[str,Any]]:
    r=requests.get(f"{DS_BASE}/latest/dex/search", params={"q":q}, timeout=10); j=r.json()
    return j.get("pairs",[]) or []

def ds_pairs_by_token(chain:str, token_addr:str)->List[Dict[str,Any]]:
    r=requests.get(f"{DS_BASE}/token-pairs/v1/{chain}/{token_addr}", timeout=10); return r.json() or []

def ds_boosts_latest()->List[Dict[str,Any]]:
    r=requests.get(f"{DS_BASE}/token-boosts/latest/v1", timeout=10); return r.json() or []

def ds_boosts_top()->List[Dict[str,Any]]:
    r=requests.get(f"{DS_BASE}/token-boosts/top/v1", timeout=10); return r.json() or []

# --------------- discovery ---------------
def pair_is_new(p)->bool:
    ts=p.get("pairCreatedAt")
    if not ts: return False
    try:
        age_ms=int(datetime.now(tz=timezone.utc).timestamp()*1000)-int(ts)
        return age_ms<=NEW_PAIR_MAX_AGE_MIN*60*1000
    except Exception:
        return False

def build_universe()->List[Dict[str,Any]]:
    pairs=[]
    if "search" in DISCOVERY_SOURCES:
        try: pairs+=ds_search_pairs(SEARCH_QUERY)
        except Exception as e: log(f"WARN discovery search: {e}")
    def expand(bs):
        out=[]
        for it in bs:
            if it.get("chainId")!="solana": continue
            t=it.get("tokenAddress")
            if not t: continue
            try: out+=ds_pairs_by_token("solana", t)
            except Exception: pass
        return out
    if "boosts_top" in DISCOVERY_SOURCES:
        try: pairs+=expand(ds_boosts_top())
        except Exception as e: log(f"WARN boosts_top: {e}")
    if "boosts_latest" in DISCOVERY_SOURCES:
        try: pairs+=expand(ds_boosts_latest())
        except Exception as e: log(f"WARN boosts_latest: {e}")
    # dedup
    seen=set(); uniq=[]
    for p in pairs:
        k=f"{p.get('chainId')}|{p.get('pairAddress')}"
        if k in seen: continue
        seen.add(k); uniq.append(p)
    return uniq

def extract_metrics(p)->Dict[str,Any]:
    pc=p.get("priceChange",{}) or {}
    vol=p.get("volume",{}) or {}
    liq=(p.get("liquidity",{}) or {}).get("usd")
    fdv=p.get("fdv") or p.get("marketCap")
    base=(p.get("baseToken") or {})
    return {
        "name": base.get("name") or base.get("symbol") or "NA",
        "symbol": base.get("symbol") or "NA",
        "pc5": float(pc.get("m5") or 0),
        "pc15": float(pc.get("m15") or 0),
        "tx5_buys": int((p.get("txns",{}) or {}).get("m5",{}).get("buys",0)),
        "tx5_sells": int((p.get("txns",{}) or {}).get("m5",{}).get("sells",0)),
        "vol5": float(vol.get("m5") or 0),
        "liq": float(liq or 0),
        "fdv": float(fdv or 0),
        "dex": p.get("dexId",""),
        "price": float(p.get("priceUsd") or 0),
        "pair": p.get("pairAddress",""),
        "url": p.get("url",""),
        "is_new": pair_is_new(p),
        "base_addr": (p.get("baseToken") or {}).get("address",""),
    }

def reject_reason(m)->Optional[str]:
    if REQUIRE_RAYDIUM and m["dex"]!="raydium": return "not_raydium"
    if m["liq"] < MIN_LIQ_USD: return "liq_low"
    if m["fdv"] and m["fdv"]>MAX_MC_USD: return "cap_too_large"
    if m["pc5"] < MIN_5M_PCT: return "pc5m_low"
    if m["pc15"] < MIN_15M_PCT: return "pc15m_low"
    if abs(m["pc5"])>OUTLIER_PC5M_THRESHOLD and m["liq"]<OUTLIER_LIQ_MAX: return "pc5m_outlier"
    return None

def score_signal(m)->float:
    s=0.0; s+=max(0,m["pc5"])/50.0; s+=max(0,m["pc15"])/100.0; s+=min(m["liq"]/250000.0,0.5)
    if m["is_new"]: s+=0.2
    return round(min(s,1.0),2)

# --------------- routing (async preview) ---------------
class RouteJob:
    def __init__(self, token_out:str, amount_in_sol:float, label:str):
        self.token_out=token_out; self.amount_in_sol=amount_in_sol; self.label=label
        self.result=None; self.err=None

def gmgn_route(job:RouteJob, from_address:str):
    params={
        "token_in_address":"So11111111111111111111111111111111111111112",
        "token_out_address":job.token_out,
        "in_amount":str(int(job.amount_in_sol*1e9)),
        "from_address":from_address,
        "swap_mode":SWAP_MODE,
        "slippage":f"{SLIPPAGE_PCT}",
        "fee":f"{FEE_SOL:.3f}",
    }
    if IS_ANTI_MEV: params["is_anti_mev"]="true"
    try:
        r=requests.post(GMGN_SWAP_ROUTE_URL, data=params, timeout=10)
        try: job.result=r.json()
        except Exception: job.result={"raw": r.text}
        if VERBOSE_ROUTE:
            log(f"ROUTE {job.label} params={params} resp={json.dumps(job.result)[:200]}")
    except Exception as e:
        job.err=str(e)

class RoutePool:
    def __init__(self, n=4):
        self.q=queue.Queue(); self.threads=[]
        for _ in range(n):
            t=threading.Thread(target=self._worker, daemon=True); t.start(); self.threads.append(t)
    def _worker(self):
        while True:
            job:RouteJob=self.q.get()
            if job is None:
                self.q.task_done(); break
            gmgn_route(job, WALLET_ADDRESS if not SIM_MODE else DUMMY_WALLET)
            self.q.task_done()
    def submit(self, job:RouteJob): self.q.put(job)
    def drain(self): self.q.join()

# --------------- sim ---------------
class Position:
    def __init__(self, sym, pair, name, size_tokens, entry_price, tp_pct, sl_pct, opened_at, dex, url):
        self.sym=sym; self.pair=pair; self.name=name; self.size=size_tokens
        self.entry=entry_price; self.tp=tp_pct; self.sl=sl_pct
        self.opened_at=opened_at; self.dex=dex; self.url=url

class Sim:
    def __init__(self, sol_px, start_usd):
        self.sol_px=sol_px
        self.cash_sol=start_usd/sol_px
        self.positions:Dict[str,Position]={}
        self.realized_usd=0.0
    def equity_usd(self, marks:Dict[str,float])->float:
        hold=0.0
        for k,p in self.positions.items():
            px=marks.get(k,p.entry); hold+=px*p.size
        return self.cash_sol*self.sol_px + hold

# --------------- advisor ---------------
def advisor_size_frac(pc5, pc15, liq_usd, vol5_usd, price_usd, cash_sol) -> Tuple[float,float,float,int,bool]:
    size_frac=min(0.10, ADVISOR_MAX_FRACTION); tp=TP_PCT; sl=SL_PCT; cooldown=COOLDOWN_SEC; used=False
    if LLM_KIND=="ollama":
        payload={
            "model": LLM_MODEL,
            "prompt": (
                "You are a trading sizing assistant. Output STRICT JSON only.\n"
                'Schema: {"type":"object","properties":{"size_frac":{"type":"number","minimum":0,"maximum":0.5},"tp_pct":{"type":"number"},"sl_pct":{"type":"number"},"cooldown_sec":{"type":"integer","minimum":0}},"required":["size_frac","tp_pct","sl_pct","cooldown_sec"]}\n'
                f"Context: pc5m={pc5:.2f}, pc15m={pc15:.2f}, liq_usd={liq_usd:.0f}, vol5_usd={vol5_usd:.0f}, price={price_usd:.8f}, cash_sol={cash_sol:.6f}.\n"
                "Constraints: prefer smaller size when liquidity<100k; tp in [5,25], sl in [-15,-3].\n"
                "Answer:"
            ),
            "options": {"temperature": LLM_TEMP},
            "stream": False
        }
        try:
            if LLM_DEBUG: log("ADVISE_REQ model=%s %s" % (LLM_MODEL, json.dumps({"pc5m":pc5,"pc15m":pc15,"liq_usd":liq_usd,"vol5_usd":vol5_usd,"price_usd":price_usd,"cash_sol":cash_sol,"max_fraction":ADVISOR_MAX_FRACTION})))
            r=requests.post(_ollama_url("/api/generate"), json=payload, timeout=LLM_TIMEOUT)
            txt=r.json().get("response","").strip()
            if LLM_DEBUG: log("ADVISE_RAW "+txt[:200].replace("\n"," "))
            data=json.loads(txt)
            size_frac=float(data.get("size_frac", size_frac))
            tp=float(data.get("tp_pct", tp))
            sl=float(data.get("sl_pct", sl))
            cooldown=int(data.get("cooldown_sec", cooldown))
            size_frac=min(max(size_frac,0.0), ADVISOR_MAX_FRACTION)
            tp=max(1.0, min(tp, 30.0))
            sl=max(-30.0, min(sl, -1.0))
            used=True
        except Exception as e:
            if LLM_DEBUG: log(f"ADVISE_ERR {e}")
    return size_frac, tp, sl, cooldown, used

# --------------- trading ---------------
def consider_buy(sim, m, route_pool, cooldowns):
    pair=m["pair"]; sym=m["symbol"]
    cool = SCALP_COOLDOWN_SEC if SCALP_ENABLE else COOLDOWN_SEC
    if pair in cooldowns and time.time()-cooldowns[pair] < cool:
        log(f"SKIP [DRY] {sym}@{m['dex']} {short(pair)} | reason=cooldown"); return
    cash_usd=sim.cash_sol*sim.sol_px
    if cash_usd < USD_BUDGET:
        log(f"SKIP [DRY] {sym}@{m['dex']} {short(pair)} | reason=insufficient_cash"); return
    size_frac,tp_pct,sl_pct,cd_s,used_ai = advisor_size_frac(m["pc5"],m["pc15"],m["liq"],m["vol5"],m["price"],sim.cash_sol)
    buy_usd=max(USD_BUDGET, cash_usd*size_frac); buy_sol=buy_usd/sim.sol_px
    if m["base_addr"]:
        route_pool.submit(RouteJob(token_out=m["base_addr"], amount_in_sol=buy_sol, label=f"{sym}@{m['dex']} {short(pair)}"))
    size_tokens = buy_usd/max(m["price"],1e-12)
    p=Position(sym, pair, m["name"], size_tokens, m["price"], tp_pct, sl_pct, time.time(), m["dex"], m["url"])
    sim.positions[pair]=p; sim.cash_sol-=buy_sol
    note="ai" if used_ai else "signal_ok"
    log(f"BUY [{'DRY' if DRY_RUN else 'LIVE'}] {sym}@{m['dex']} {short(pair)} | in={buy_sol:.4f} SOL → out≈{size_tokens:.6f} {sym} | price={usd(m['price'])} impact=0.00% slipBps={int(SLIPPAGE_PCT*100)} fee={FEE_SOL:.6f} antiMEV={IS_ANTI_MEV} | {note} size_frac={size_frac:.3f} tp={tp_pct:.1f}% sl={sl_pct:.1f}% cooldown={cd_s}s")

def maybe_sell(sim, marks, pair, reason):
    if pair not in sim.positions: return
    p=sim.positions[pair]; px=marks.get(pair,p.entry)
    out_usd=px*p.size; in_usd=p.entry*p.size; pnl_usd=out_usd-in_usd
    sim.realized_usd+=pnl_usd; sim.cash_sol += out_usd/sim.sol_px; del sim.positions[pair]
    pnl_sol=pnl_usd/sim.sol_px; tag="GAIN" if pnl_usd>=0 else "LOSS"
    log(f"SELL [{'DRY' if DRY_RUN else 'LIVE'}] {p.sym}@{p.dex} {short(pair)} | out≈{out_usd/sim.sol_px:.6f} SOL | price={usd(px)} | {reason} {tag} pnlSOL={pnl_sol:+.6f} pnlUSD={usd(pnl_usd)}")

def manage_positions(sim, marks):
    now=time.time()
    for pair,p in list(sim.positions.items()):
        px=marks.get(pair,p.entry); chg=(px/p.entry-1.0)*100.0
        max_hold = SCALP_MAX_HOLD_SEC if SCALP_ENABLE else MAX_HOLD_SEC
        tp = SCALP_TP_PCT if SCALP_ENABLE else p.tp
        sl = SCALP_SL_PCT if SCALP_ENABLE else p.sl
        if chg>=tp: maybe_sell(sim, marks, pair, "TP")
        elif chg<=sl: maybe_sell(sim, marks, pair, "SL")
        elif (now-p.opened_at)>=max_hold: maybe_sell(sim, marks, pair, "TIME")

def print_total(sim, marks):
    eq=sim.equity_usd(marks); hold_usd=eq - sim.cash_sol*sim.sol_px
    log(f"TOTAL | cash={sim.cash_sol:.6f} SOL ({usd(sim.cash_sol*sim.sol_px)}) | holdings={usd(hold_usd)} | equity={usd(eq)} | realized={usd(sim.realized_usd)} | PNL_unreal={usd(hold_usd)} | PNL_total={usd(sim.realized_usd+hold_usd)}")

# --------------- scan loop ---------------
def build_candidates()->Tuple[List[Dict[str,Any]],Dict[str,int]]:
    pairs=build_universe()
    log(f"Discovered pairs: {len(pairs)}")
    rejects={}; cands=[]
    for p in pairs:
        if p.get("chainId")!="solana": continue
        m=extract_metrics(p)
        if SCALP_ENABLE:
            if m["pc5"]<SCALP_MIN_PC5M:
                rejects["scalp_pc5m_low"]=rejects.get("scalp_pc5m_low",0)+1; continue
            if (m["tx5_buys"]+m["tx5_sells"])<SCALP_MIN_TXNS_5M:
                rejects["scalp_flow_low"]=rejects.get("scalp_flow_low",0)+1; continue
        rr=reject_reason(m)
        if rr: rejects[rr]=rejects.get(rr,0)+1; continue
        m["score"]=score_signal(m); cands.append(m)
    key = (lambda x:(not x["is_new"], -(x["pc15"]), -(x["pc5"]), -x["score"])) if GAINERS_WINDOW=="m15" \
          else (lambda x:(not x["is_new"], -(x["pc5"]), -(x["pc15"]), -x["score"]))
    cands.sort(key=key)
    return cands, rejects

def main():
    sol_px=get_sol_price()
    head = f"SIM=ON | cash≈{SIM_START_USD/sol_px:.6f} SOL ({usd(SIM_START_USD)}) | DRY_RUN={DRY_RUN}" if SIM_MODE \
        else f"SIM=OFF | wallet={short(WALLET_ADDRESS,8)} | DRY_RUN={DRY_RUN}"
    log(head)

    # ---- PRECHECK ----
    preflight()

    # sim + routing
    sim=Sim(sol_px, SIM_START_USD if SIM_MODE else 0.0)
    cooldowns={}
    route_pool=RoutePool(n=ROUTE_THREADS)

    while True:
        try:
            cands, rejects = build_candidates()
            log("Reject reasons: " + str(rejects or {}))
            marks={m["pair"]:m["price"] for m in cands}
            # take top 3 each cycle
            limit = 3
            for m in cands[:limit]:
                tag="SCALP" if SCALP_ENABLE else "SCAN"
                log(f"{tag} {m['symbol']}@{m['dex']} {short(m['pair'])} | score=#{m['score']:.2f} pc5m={m['pc5']:.1f} pc15m={m['pc15']:.1f} liq={usd(m['liq'])} vol5m={m['vol5']:.2f} new={m['is_new']} url={m['url']}")
                consider_buy(sim, m, route_pool, cooldowns)
            manage_positions(sim, marks)
            print_total(sim, marks)
        except KeyboardInterrupt:
            break
        except Exception as e:
            log(f"LOOP_ERR {e}")
        time.sleep(POLL_SECS)

if __name__=="__main__":
    main()
