#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Radar de fondos - motor de actualizacion diaria.
Lee funds.json, resuelve cada fondo a su simbolo Yahoo (por ISIN o nombre),
descarga el historico y calcula desempenos 1M/3M/YTD/1A/3A, volatilidad 1A,
Sharpe 1A, y beta + alfa (3A) frente a un indice por clase de activo.
Escribe data.json (lo que lee index.html). Sin claves de API.
Pensado para GitHub Actions, una vez al dia. Uso personal.
"""
import json, time, math, datetime, sys
import urllib.request, urllib.parse

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36"
SEARCH = "https://query2.finance.yahoo.com/v1/finance/search?quotesCount=6&newsCount=0&q="
CHART  = "https://query1.finance.yahoo.com/v8/finance/chart/{sym}?range=4y&interval=1d"
RF = 0.025          # tipo sin riesgo aprox (2,5%) para Sharpe/alfa
DAY = 86400

def _get(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=25) as r:
        return json.loads(r.read().decode("utf-8"))

def resolve_symbol(fund):
    qs = []
    if fund.get("isin"): qs.append(fund["isin"])
    qs.append(fund["name"])
    for q in qs:
        try:
            d = _get(SEARCH + urllib.parse.quote(q))
            quotes = d.get("quotes", [])
            for qt in quotes:
                if qt.get("quoteType") in ("MUTUALFUND", "ETF", "FUND"):
                    return qt.get("symbol")
            if quotes: return quotes[0].get("symbol")
        except Exception as e:
            sys.stderr.write("search fail %s: %s\n" % (q, e))
        time.sleep(0.35)
    return None

def history(sym):
    d = _get(CHART.format(sym=urllib.parse.quote(sym)))
    res = d["chart"]["result"][0]
    ts = res["timestamp"]
    q = res["indicators"]["quote"][0]
    adj = res["indicators"].get("adjclose", [{}])[0].get("adjclose")
    closes = adj if adj else q.get("close")
    T, C = [], []
    for t, c in zip(ts, closes):
        if c is not None: T.append(t); C.append(c)
    return T, C

def p_at(ts, cl, target):
    best = None
    for t, c in zip(ts, cl):
        if t <= target: best = c
        else: break
    return best
def pct(a, b): return None if (a is None or b is None or b == 0) else round((a/b-1)*100, 2)
def annu(p, y): return None if p is None else round(((1+p/100)**(1/y)-1)*100, 2)

def daily_returns(ts, cl, since):
    out = {}
    prev_t = prev_c = None
    for t, c in zip(ts, cl):
        if t >= since and prev_c and prev_c > 0:
            out[t] = c/prev_c - 1
        prev_t, prev_c = t, c
    return out

def returns_block(ts, cl):
    if len(cl) < 20: return None
    now_t, now_p = ts[-1], cl[-1]
    def back(d): return p_at(ts, cl, now_t - d*DAY)
    yr = datetime.datetime.utcfromtimestamp(now_t).year
    jan1 = datetime.datetime(yr, 1, 1).timestamp()
    r1y = pct(now_p, back(365))
    r3y_tot = pct(now_p, back(365*3))
    return dict(r_1w=pct(now_p, back(7)), r_1m=pct(now_p, back(30)), r_3m=pct(now_p, back(91)),
                r_ytd=pct(now_p, p_at(ts, cl, jan1)), r_1y=r1y,
                r_3y=annu(r3y_tot, 3) if r3y_tot is not None else None)

def weekly_series(ts, cl, weeks=53):
    """Serie semanal normalizada (base 100) del ultimo ~ano, para graficar."""
    if len(cl) < 10: return []
    now_t = ts[-1]; since = now_t - (weeks+1)*7*DAY
    pts, last_bucket = [], None
    for t, c in zip(ts, cl):
        if t < since: continue
        b = int((t - since)//(7*DAY))
        if b != last_bucket:
            pts.append(c); last_bucket = b
    if len(pts) < 4: return []
    base = pts[0]
    if not base: return []
    return [round(p/base*100, 1) for p in pts]

def vol_sharpe(ts, cl):
    now_t = ts[-1]
    dr = list(daily_returns(ts, cl, now_t-365*DAY).values())
    if len(dr) < 30: return None, None
    m = sum(dr)/len(dr); var = sum((x-m)**2 for x in dr)/(len(dr)-1)
    sd = math.sqrt(var); vol = round(sd*math.sqrt(252)*100, 2)
    return vol, None

def beta_alpha(fts, fcl, bts, bcl, f_r3y, b_r3y):
    if not bts: return None, None
    now_t = fts[-1]; since = now_t-365*3*DAY
    fd = daily_returns(fts, fcl, since); bd = daily_returns(bts, bcl, since)
    common = sorted(set(fd) & set(bd))
    if len(common) < 60: return None, None
    fx = [fd[t] for t in common]; bx = [bd[t] for t in common]
    mf = sum(fx)/len(fx); mb = sum(bx)/len(bx)
    cov = sum((fx[i]-mf)*(bx[i]-mb) for i in range(len(fx)))/(len(fx)-1)
    varb = sum((x-mb)**2 for x in bx)/(len(bx)-1)
    if varb == 0: return None, None
    beta = round(cov/varb, 2)
    alpha = None
    if f_r3y is not None and b_r3y is not None:
        alpha = round(f_r3y - (RF*100 + beta*(b_r3y - RF*100)), 2)
    return beta, alpha

def main():
    funds = json.load(open("funds.json", encoding="utf-8"))["funds"]
    try: symcache = json.load(open("symbols.json", encoding="utf-8"))
    except Exception: symcache = {}

    # benchmarks (descarga unica)
    bsyms = sorted(set(f.get("benchmark") for f in funds if f.get("benchmark")))
    bench = {}
    for bs in bsyms:
        try:
            bt, bc = history(bs)
            blk = returns_block(bt, bc)
            bench[bs] = (bt, bc, blk["r_3y"] if blk else None)
        except Exception as e:
            sys.stderr.write("bench fail %s: %s\n" % (bs, e)); bench[bs] = (None, None, None)
        time.sleep(0.4)

    out = []; ok = 0
    for fund in funds:
        rec = {k: fund.get(k) for k in ("id","name","gestora","tipo","categoria","sectores","propio","isin","benchmark")}
        rec.update(dict(symbol=None, r_1w=None, r_1m=None, r_3m=None, r_ytd=None, r_1y=None, r_3y=None,
                        vol_1y=None, sharpe_1y=None, beta=None, alpha=None, series=[], verified=False))
        sym = symcache.get(fund["id"]) or resolve_symbol(fund)
        if sym: symcache[fund["id"]] = sym
        rec["symbol"] = sym
        if sym:
            try:
                ts, cl = history(sym)
                blk = returns_block(ts, cl)
                if blk:
                    rec.update(blk)
                    vol, _ = vol_sharpe(ts, cl)
                    rec["vol_1y"] = vol
                    if vol and rec["r_1y"] is not None:
                        rec["sharpe_1y"] = round((rec["r_1y"] - RF*100)/vol, 2)
                    bt, bc, b3y = bench.get(fund.get("benchmark"), (None, None, None))
                    rec["beta"], rec["alpha"] = beta_alpha(ts, cl, bt, bc, rec["r_3y"], b3y)
                    rec["series"] = weekly_series(ts, cl)
                    ok += 1
            except Exception as e:
                sys.stderr.write("hist fail %s (%s): %s\n" % (fund["name"], sym, e))
        out.append(rec); time.sleep(0.45)

    json.dump(symcache, open("symbols.json","w",encoding="utf-8"), ensure_ascii=False, indent=1)
    data = {"updated": datetime.datetime.utcnow().strftime("%Y-%m-%d"), "status": "ok",
            "resolved": ok, "total": len(funds), "source": "Yahoo Finance (uso personal)",
            "benchmarks": {"Renta Variable / Multiactivo": "ACWI (MSCI ACWI)", "Renta Fija": "AGGG.L (Global Aggregate Bond)"},
            "note": "Desempenos orientativos. Rent. 3A anualizada. Beta y alfa (3A) frente al indice de su clase de activo. Verifica en la ficha oficial / Morningstar antes de usar con cliente.",
            "funds": out}
    json.dump(data, open("data.json","w",encoding="utf-8"), ensure_ascii=False, indent=1)
    print("Resueltos %d/%d fondos." % (ok, len(funds)))

if __name__ == "__main__":
    main()
