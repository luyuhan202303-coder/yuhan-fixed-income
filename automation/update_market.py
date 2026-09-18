#!/usr/bin/env python3
"""Generate the fixed-income dashboard from public end-of-day data.

The script is intentionally deterministic: market commentary is derived from
observed changes, and a failed primary source stops the update instead of
publishing invented or stale numbers as a new trading day.
"""

from __future__ import annotations

import csv
import io
import json
import math
import re
import sys
import time
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterable
from zoneinfo import ZoneInfo

import requests
from bs4 import BeautifulSoup


BEIJING = ZoneInfo("Asia/Shanghai")
NOW = datetime.now(BEIJING)
SITE_DIR = Path("dist") if Path("dist/index.html").exists() else Path(".")
DATA_DIR = SITE_DIR / "data"
DAILY_PATH = DATA_DIR / "daily.json"
PERIODS_PATH = DATA_DIR / "periods.json"
HISTORY_PATH = DATA_DIR / "market-history.json"

UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126 Safari/537.36"
)
SESSION = requests.Session()
SESSION.headers.update({"User-Agent": UA, "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.7"})

URLS = {
    "chinabond": "https://yield.chinabond.com.cn/",
    "chinamoney": "https://www.chinamoney.com.cn/chinese/",
    "pbc": "https://www.pbc.gov.cn/zhengcehuobisi/125207/125213/125431/125475/index.html",
    "csi_cb": "https://www.csindex.com.cn/#/indices/family/detail?indexCode=000832",
    "sse_bond": "https://bond.sse.com.cn/",
    "treasury": "https://home.treasury.gov/resource-center/data-chart-center/interest-rates/TextView?type=daily_treasury_yield_curve",
    "fed": "https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm",
    "eastmoney_futures": "https://quote.eastmoney.com/center/gridlist.html#futures_global",
    "cme_gold": "https://www.cmegroup.com/markets/metals/precious/gold.html",
    "cme_oil": "https://www.cmegroup.com/markets/energy/crude-oil/light-sweet-crude.html",
    "ice_brent": "https://www.ice.com/products/219/Brent-Crude-Futures",
}


def get(
    url: str,
    *,
    params: dict[str, Any] | None = None,
    timeout: int = 35,
    headers: dict[str, str] | None = None,
) -> requests.Response:
    last_error: Exception | None = None
    for attempt in range(3):
        try:
            response = SESSION.get(url, params=params, timeout=timeout, headers=headers)
            response.raise_for_status()
            return response
        except Exception as exc:  # network retries are deliberate in CI
            last_error = exc
            if attempt < 2:
                time.sleep(2 ** attempt)
    raise RuntimeError(f"数据源请求失败: {url}: {last_error}")


def number(value: Any) -> float | None:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value) if math.isfinite(float(value)) else None
    text = str(value).replace(",", "").replace("−", "-").strip()
    if text in {"", "-", "--", "None", "nan"}:
        return None
    match = re.search(r"[-+]?\d+(?:\.\d+)?", text)
    return float(match.group()) if match else None


def require(value: float | None, label: str) -> float:
    if value is None or not math.isfinite(value):
        raise RuntimeError(f"缺少关键数据: {label}")
    return value


def fetch_chinabond(days: int = 75) -> dict[str, dict[str, dict[str, float]]]:
    start = (NOW.date() - timedelta(days=days)).isoformat()
    end = NOW.date().isoformat()
    response = get(
        "https://yield.chinabond.com.cn/cbweb-pbc-web/pbc/historyQuery",
        params={"startDate": start, "endDate": end, "gjqx": "0", "qxId": "ycqx", "locale": "cn_ZH"},
    )
    soup = BeautifulSoup(response.text, "html.parser")
    target_table = None
    for table in soup.find_all("table"):
        text = re.sub(r"\s+", "", table.get_text(" ", strip=True))
        if "曲线名称" in text and "日期" in text and "10年" in text and "30年" in text:
            target_table = table
            break
    if target_table is None:
        raise RuntimeError("中债收益率表格结构发生变化")

    rows = target_table.find_all("tr")
    headers = [cell.get_text("", strip=True).replace(" ", "") for cell in rows[0].find_all(["td", "th"])]
    expected = ["曲线名称", "日期", "3月", "6月", "1年", "3年", "5年", "7年", "10年", "30年"]
    if headers[: len(expected)] != expected:
        raise RuntimeError(f"中债收益率列名发生变化: {headers}")

    result: dict[str, dict[str, dict[str, float]]] = {}
    wanted = {
        "中债国债收益率曲线": "gov",
        "中债中短期票据收益率曲线(AAA)": "mtn_aaa",
        "中债商业银行普通债收益率曲线(AAA)": "bank_aaa",
    }
    for row in rows[1:]:
        cells = [cell.get_text("", strip=True) for cell in row.find_all(["td", "th"])]
        if len(cells) < 10 or cells[0] not in wanted or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", cells[1]):
            continue
        curve = {headers[i]: number(cells[i]) for i in range(2, 10)}
        result.setdefault(cells[1], {})[wanted[cells[0]]] = {
            key: value for key, value in curve.items() if value is not None
        }
    if not any("gov" in curves for curves in result.values()):
        raise RuntimeError("中债收益率未返回国债曲线")
    return result


def fetch_shibor(days: int = 75) -> dict[str, dict[str, float]]:
    response = get(
        "https://www.chinamoney.com.cn/ags/ms/cm-u-bk-shibor/ShiborHis",
        params={
            "lang": "CN",
            "startDate": (NOW.date() - timedelta(days=days)).isoformat(),
            "endDate": NOW.date().isoformat(),
        },
    )
    payload = response.json()
    result = {}
    for item in payload.get("records", []):
        day = item.get("showDateCN")
        if not day:
            continue
        result[day] = {
            "on": require(number(item.get("ON")), f"{day} Shibor O/N"),
            "1w": require(number(item.get("1W")), f"{day} Shibor 1W"),
            "1m": require(number(item.get("1M")), f"{day} Shibor 1M"),
            "3m": require(number(item.get("3M")), f"{day} Shibor 3M"),
        }
    if not result:
        raise RuntimeError("中国货币网未返回 Shibor 数据")
    return result


def fetch_cb_index(days: int = 100) -> dict[str, dict[str, Any]]:
    start = (NOW.date() - timedelta(days=days)).isoformat()
    end = NOW.date().isoformat()
    response = get(
        "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get",
        params={"param": f"sh000832,day,{start},{end},120,qfq"},
        headers={"Referer": "https://gu.qq.com/sh000832/gp"},
    )
    payload = (response.json().get("data") or {}).get("sh000832") or {}
    result = {}
    previous_close: float | None = None
    for fields in payload.get("day", []):
        if len(fields) < 6:
            continue
        close = require(number(fields[2]), "中证转债收盘")
        volume = require(number(fields[5]), "中证转债成交量")
        result[fields[0]] = {
            "open": require(number(fields[1]), "中证转债开盘"),
            "close": close,
            "high": require(number(fields[3]), "中证转债最高"),
            "low": require(number(fields[4]), "中证转债最低"),
            "volume": volume,
            "volume_wan": volume / 10_000,
            "pct": (close / previous_close - 1) * 100 if previous_close else 0,
            "turnover_yi": None,
        }
        previous_close = close

    quote = (payload.get("qt") or {}).get("sh000832") or []
    if len(quote) > 35 and str(quote[30])[:8].isdigit():
        quote_date = f"{quote[30][0:4]}-{quote[30][4:6]}-{quote[30][6:8]}"
        amount_parts = str(quote[35]).split("/")
        if quote_date in result and len(amount_parts) >= 3:
            result[quote_date]["turnover_yi"] = require(number(amount_parts[2]), "中证转债成交额") / 100_000_000
    if not result:
        raise RuntimeError("中证转债指数接口未返回数据")
    return result


def fetch_cb_movers() -> dict[str, dict[str, Any]]:
    endpoint = "https://vip.stock.finance.sina.com.cn/quotes_service/api/json_v2.php/Market_Center.getHQNodeDataSimple"

    def one(ascending: bool) -> dict[str, Any]:
        response = get(
            endpoint,
            params={
                "page": "1",
                "num": "20",
                "sort": "changepercent",
                "asc": "1" if ascending else "0",
                "node": "hskzz_z",
                "_s_r_a": "page",
            },
        )
        data = response.json()
        valid = [item for item in data if number(item.get("changepercent")) is not None]
        if not valid:
            raise RuntimeError("可转债涨跌榜为空")
        item = valid[0]
        return {
            "name": item.get("name", "—"),
            "pct": require(number(item.get("changepercent")), "可转债涨跌幅"),
            "price": number(item.get("trade")),
        }

    return {"top": one(False), "bottom": one(True)}


def fetch_treasury() -> dict[str, dict[str, float]]:
    result: dict[str, dict[str, float]] = {}
    for year in sorted({NOW.year, (NOW - timedelta(days=90)).year}):
        response = get(
            f"https://home.treasury.gov/resource-center/data-chart-center/interest-rates/daily-treasury-rates.csv/{year}/all",
            params={"type": "daily_treasury_yield_curve", "field_tdr_date_value": year, "page": "", "_format": "csv"},
            timeout=50,
        )
        for row in csv.DictReader(io.StringIO(response.text)):
            try:
                day = datetime.strptime(row["Date"], "%m/%d/%Y").date().isoformat()
            except (KeyError, ValueError):
                continue
            result[day] = {
                "2y": require(number(row.get("2 Yr")), f"{day} 美债2年"),
                "10y": require(number(row.get("10 Yr")), f"{day} 美债10年"),
                "30y": require(number(row.get("30 Yr")), f"{day} 美债30年"),
            }
    if not result:
        raise RuntimeError("美国财政部未返回收益率曲线")
    return result


def fetch_global_futures() -> dict[str, dict[str, float]]:
    response = get(
        "https://futsseapi.eastmoney.com/list/COMEX,NYMEX,COBOT,SGX,NYBOT,LME,MDEX,TOCOM,IPE",
        params={
            "orderBy": "dm",
            "sort": "desc",
            "pageSize": "1000",
            "pageIndex": "0",
            "token": "58b2fa8f54638b60b87d69b31969089c",
            "field": "dm,sc,name,p,zsjd,zde,zdf,o,h,l,zjsj,vol,wp,np,ccl",
        },
    )
    wanted = {"GC00Y": "gold", "SI00Y": "silver", "CL00Y": "wti", "B00Y": "brent"}
    result = {}
    for item in response.json().get("list", []):
        key = wanted.get(item.get("dm"))
        if key:
            result[key] = {
                "price": require(number(item.get("p")), f"{key} 最新价"),
                "pct": require(number(item.get("zdf")), f"{key} 涨跌幅"),
            }
    missing = sorted(set(wanted.values()) - result.keys())
    if missing:
        raise RuntimeError(f"国际期货接口缺少品种: {', '.join(missing)}")
    return result


def latest_on_or_before(series: dict[str, Any], target: str) -> tuple[str, Any]:
    dates = sorted(day for day in series if day <= target)
    if not dates:
        raise RuntimeError(f"{target} 之前没有可用数据")
    day = dates[-1]
    return day, series[day]


def fmt_bp(value: float | None, digits: int = 2) -> str:
    if value is None:
        return "暂无可比"
    sign = "+" if value > 0 else "−" if value < 0 else ""
    return f"{sign}{abs(value):.{digits}f} BP"


def fmt_pct(value: float | None, digits: int = 2) -> str:
    if value is None:
        return "暂无可比"
    sign = "+" if value > 0 else "−" if value < 0 else ""
    return f"{sign}{abs(value):.{digits}f}%"


def direction(value: float | None, *, inverse: bool = False) -> str:
    if value is None or abs(value) < 1e-10:
        return "flat"
    up = value > 0
    if inverse:
        up = not up
    return "up" if up else "down"


def metric(label: str, value: str, change: str, move: str, note: str, source: str, url: str, numeric: float | None = None) -> dict[str, Any]:
    item: dict[str, Any] = {
        "label": label,
        "value": value,
        "change": change,
        "direction": move,
        "note": note,
        "source": source,
        "sourceUrl": url,
    }
    if numeric is not None and math.isfinite(numeric):
        item["numeric"] = round(numeric, 6)
    return item


def source(title: str, publisher: str, url: str) -> dict[str, str]:
    return {"title": title, "publisher": publisher, "url": url}


def prior_record(history: list[dict[str, Any]], target: str) -> dict[str, Any] | None:
    older = sorted((item for item in history if item.get("date", "") < target), key=lambda item: item["date"])
    return older[-1] if older else None


def spread(curve: dict[str, float], gov: dict[str, float], tenor: str) -> float:
    return (require(curve.get(tenor), f"信用曲线{tenor}") - require(gov.get(tenor), f"国债曲线{tenor}")) * 100


def make_record(
    target: str,
    curves: dict[str, dict[str, float]],
    shibor: dict[str, float],
    cb: dict[str, float],
    movers: dict[str, dict[str, Any]],
    treasury_date: str,
    treasury: dict[str, float],
    commodities: dict[str, dict[str, float]],
) -> dict[str, Any]:
    gov = curves["gov"]
    mtn = curves.get("mtn_aaa") or {}
    bank = curves.get("bank_aaa") or {}
    return {
        "date": target,
        "rates": {
            "cn1": require(gov.get("1年"), "中债国债1年"),
            "cn3": require(gov.get("3年"), "中债国债3年"),
            "cn5": require(gov.get("5年"), "中债国债5年"),
            "cn10": require(gov.get("10年"), "中债国债10年"),
            "cn30": require(gov.get("30年"), "中债国债30年"),
        },
        "credit": {
            "mtn1_spread": spread(mtn, gov, "1年"),
            "mtn3_spread": spread(mtn, gov, "3年"),
            "mtn5_spread": spread(mtn, gov, "5年"),
            "bank5_spread": spread(bank, gov, "5年"),
        },
        "shibor": shibor,
        "convertible": {**cb, **movers},
        "ust": {**treasury, "source_date": treasury_date},
        "commodities": {**commodities, "quote_time": NOW.isoformat(timespec="minutes")},
    }


def value_at(record: dict[str, Any] | None, *path: str) -> float | None:
    node: Any = record
    for key in path:
        if not isinstance(node, dict):
            return None
        node = node.get(key)
    return number(node)


def deep_merge(base: dict[str, Any], update: dict[str, Any]) -> dict[str, Any]:
    merged = dict(base)
    for key, value in update.items():
        if value is None:
            continue
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def historical_record(
    target: str,
    curves: dict[str, dict[str, float]],
    shibor: dict[str, float],
    cb: dict[str, Any],
    treasury_date: str,
    treasury: dict[str, float],
) -> dict[str, Any]:
    gov = curves["gov"]
    mtn = curves.get("mtn_aaa") or {}
    bank = curves.get("bank_aaa") or {}
    return {
        "date": target,
        "rates": {
            "cn1": require(gov.get("1年"), f"{target} 中债国债1年"),
            "cn3": require(gov.get("3年"), f"{target} 中债国债3年"),
            "cn5": require(gov.get("5年"), f"{target} 中债国债5年"),
            "cn10": require(gov.get("10年"), f"{target} 中债国债10年"),
            "cn30": require(gov.get("30年"), f"{target} 中债国债30年"),
        },
        "credit": {
            "mtn1_spread": spread(mtn, gov, "1年"),
            "mtn3_spread": spread(mtn, gov, "3年"),
            "mtn5_spread": spread(mtn, gov, "5年"),
            "bank5_spread": spread(bank, gov, "5年"),
        },
        "shibor": shibor,
        "convertible": cb,
        "ust": {**treasury, "source_date": treasury_date},
    }


def day_label(day: str) -> str:
    parsed = date.fromisoformat(day)
    weekdays = "一二三四五六日"
    return f"{parsed:%m月%d日} · 周{weekdays[parsed.weekday()]}"


def make_interview(category: str, period_word: str, latest: dict[str, Any], first: dict[str, Any]) -> dict[str, Any]:
    cn_delta = delta(latest, first, ("rates", "cn10"), "bp")
    cb_delta = delta(latest, first, ("convertible", "close"), "pct")
    us_delta = delta(latest, first, ("ust", "10y"), "bp")
    gold_delta = delta(latest, first, ("commodities", "gold", "price"), "pct")
    templates = {
        "overview": {
            "short": f"{period_word}市场的核心是中外利率与风险资产表现并不完全同步。中国10年国债收益率变化{fmt_bp(cn_delta)}，美国10年期变化{fmt_bp(us_delta)}，中证转债指数变化{fmt_pct(cb_delta)}。因此回答面试问题时，我会先区分国内资金与基本面，再讨论海外通胀和政策，最后落到转债及商品的风险偏好。",
            "logic": [("国内债市", "观察基本面、资金面和政府债供给，收益率下行代表债券价格走强。"), ("海外债市", "美债更多受通胀、政策路径和期限溢价影响。"), ("风险资产", "转债与商品需要结合权益风险偏好、美元和实际利率判断。")],
            "qa": [("为什么中美债市可能不同步？", "两国增长、通胀、货币政策和资金结构不同，收益率不会机械联动。"), ("如何把行情转成面试观点？", "先说方向和幅度，再解释基本面、资金面、政策面，最后补充反向风险。")],
        },
        "rates": {
            "short": f"{period_word}中国10年国债收益率变化{fmt_bp(cn_delta)}。我的判断重点不只看涨跌，还要看资金价格和曲线形态：资金宽松会支撑短端，增长与供给预期影响长端。当前更适合结合绝对点位判断配置价值，而不是只根据单日方向追涨杀跌。",
            "logic": [("基本面", "弱增长和低通胀通常压低名义利率中枢。"), ("资金面", "Shibor与公开市场操作影响杠杆和短端定价。"), ("曲线", "长短端变化差异反映政策预期、供给和期限溢价。")],
            "qa": [("收益率下降为什么债券上涨？", "固定票息债券的现金流不变，市场要求收益率下降时，其现值和价格会上升。"), ("低利率下还能追多吗？", "需要比较票息、资金成本与潜在资本利得；绝对收益率越低，追涨的安全垫越薄。")],
        },
        "credit": {
            "short": f"{period_word}信用债要同时看无风险利率和信用利差。网站用中债AAA中票相对同期限国债的利差作为公开代理指标。利差压缩代表信用表现更强，但利差越低，继续下沉的容错率越小，因此我更重视票息、主体现金流和再融资能力。",
            "logic": [("利率底", "国债收益率决定信用债估值的无风险基准。"), ("信用利差", "补偿违约、流动性和估值波动风险。"), ("策略", "低利差阶段应提高主体筛选标准并控制杠杆。")],
            "qa": [("利差低为什么要谨慎下沉？", "额外收益不足以覆盖尾部风险时，信用下沉的收益风险比会恶化。"), ("信用利差怎么计算？", "用同期限信用债收益率减去国债或政策性金融债收益率，并统一估值口径。")],
        },
        "convertible": {
            "short": f"{period_word}中证转债指数变化{fmt_pct(cb_delta)}。转债同时具有股性和债性，指数上涨可能来自正股、估值或两者共同推动。分析时还要看成交额、领涨品种和转股溢价率；若成交放大且领涨扩散，行情持续性通常更好。",
            "logic": [("正股", "决定平价和向上弹性。"), ("估值", "转股溢价率反映市场为期权价值支付的价格。"), ("条款", "强赎、下修与回售会改变收益分布。")],
            "qa": [("转债上涨一定是正股上涨吗？", "不一定，也可能是转股溢价率抬升或条款预期变化。"), ("如何判断转债贵不贵？", "比较平价、转股溢价率、纯债价值、历史分位和同类券估值。")],
        },
        "ust": {
            "short": f"{period_word}美国10年期国债收益率变化{fmt_bp(us_delta)}。短端主要反映联储政策路径，长端还包含增长、通胀、财政供给和期限溢价。若短端上行快于长端，通常表现为熊平；反之则可能熊陡。配置上需要确认通胀和期限溢价是否见顶。",
            "logic": [("政策路径", "2年期对联储预期最敏感。"), ("期限溢价", "财政供给与不确定性会推高长端补偿。"), ("曲线形态", "比较2年和10年变化，判断熊平、熊陡、牛平或牛陡。")],
            "qa": [("为什么降息预期升温长端仍可能上行？", "财政供给、通胀风险和期限溢价可能抵消政策利率下降。"), ("高收益率是否等于高配置价值？", "还要看通胀路径、久期波动和收益率是否已经见顶。")],
        },
        "commodities": {
            "short": f"{period_word}黄金价格变化{fmt_pct(gold_delta)}。商品与债市最重要的联系是通胀预期：能源上涨可能推高名义收益率并延后宽松，黄金则同时受实际利率、美元和避险需求影响，所以油价与金价并不一定同向。",
            "logic": [("能源", "供给冲击先影响通胀，再影响政策预期和债券收益率。"), ("黄金", "实际利率和美元上升通常构成压力，避险需求提供支撑。"), ("风险", "期货报价波动快，需区分盘中价、结算价和现货定盘价。")],
            "qa": [("油价上涨为什么利空债券？", "油价推高通胀预期，市场可能要求更高名义收益率。"), ("黄金和美债为什么有时同涨？", "避险冲击下资金可能同时买入黄金和国债，压过实际利率渠道。")],
        },
    }
    raw = templates[category]
    return {
        "short": raw["short"],
        "logic": [{"label": label, "text": text} for label, text in raw["logic"]],
        "qa": [{"q": q, "a": answer} for q, answer in raw["qa"]],
    }


def difference(current: float, previous: float | None, multiplier: float = 1) -> float | None:
    return (current - previous) * multiplier if previous is not None else None


def make_daily(record: dict[str, Any], previous: dict[str, Any] | None) -> dict[str, Any]:
    day = record["date"]
    r = record["rates"]
    c = record["credit"]
    s = record["shibor"]
    cb = record["convertible"]
    us = record["ust"]
    co = record["commodities"]

    cn10_bp = difference(r["cn10"], value_at(previous, "rates", "cn10"), 100)
    cn30_bp = difference(r["cn30"], value_at(previous, "rates", "cn30"), 100)
    on_bp = difference(s["on"], value_at(previous, "shibor", "on"), 100)
    curve = (r["cn30"] - r["cn10"]) * 100
    mtn3_delta = c["mtn3_spread"] - value_at(previous, "credit", "mtn3_spread") if previous and value_at(previous, "credit", "mtn3_spread") is not None else None
    turnover = number(cb.get("turnover_yi"))
    volume_wan = require(number(cb.get("volume_wan")), "中证转债成交量")
    turnover_delta = difference(turnover, value_at(previous, "convertible", "turnover_yi")) if turnover is not None else None
    volume_delta = difference(volume_wan, value_at(previous, "convertible", "volume_wan"))
    us2_bp = difference(us["2y"], value_at(previous, "ust", "2y"), 100)
    us10_bp = difference(us["10y"], value_at(previous, "ust", "10y"), 100)
    us30_bp = difference(us["30y"], value_at(previous, "ust", "30y"), 100)
    us_curve = (us["10y"] - us["2y"]) * 100

    rate_tone = "走强" if cn10_bp is not None and cn10_bp < -0.5 else "走弱" if cn10_bp is not None and cn10_bp > 0.5 else "窄幅震荡"
    funding = "偏松" if on_bp is not None and on_bp < -2 else "偏紧" if on_bp is not None and on_bp > 2 else "平稳"
    cb_tone = "回升" if cb["pct"] > 0.2 else "回落" if cb["pct"] < -0.2 else "震荡"
    us_tone = "承压" if us10_bp is not None and us10_bp > 1 else "走强" if us10_bp is not None and us10_bp < -1 else "震荡"

    rate_sources = [
        source("中债国债收益率曲线", "中国债券信息网 · 官方", URLS["chinabond"]),
        source("Shibor 历史数据", "中国货币网 · 官方", URLS["chinamoney"]),
    ]
    credit_sources = [
        source("中债中短期票据与银行债收益率曲线", "中国债券信息网 · 官方", URLS["chinabond"]),
        source("银行间市场数据与披露", "中国货币网 · 官方", URLS["chinamoney"]),
    ]
    cb_sources = [
        source("中证转债指数（000832）", "中证指数 · 官方", URLS["csi_cb"]),
        source("债券行情与信息披露", "上海证券交易所 · 官方", URLS["sse_bond"]),
    ]
    us_sources = [
        source("Daily Treasury Par Yield Curve Rates", "U.S. Treasury · 官方", URLS["treasury"]),
        source("FOMC statements and calendars", "Federal Reserve · 官方", URLS["fed"]),
    ]
    commodity_sources = [
        source("Gold Futures", "CME Group · 交易所", URLS["cme_gold"]),
        source("WTI Crude Oil Futures", "CME Group · 交易所", URLS["cme_oil"]),
        source("Brent Crude Futures", "ICE · 交易所", URLS["ice_brent"]),
        source("国际期货行情聚合", "东方财富 · 市场数据", URLS["eastmoney_futures"]),
    ]

    rates = {
        "title": "中国利率债",
        "commentary": f"利率债当日{rate_tone}，10年国债收益率为{r['cn10']:.4f}%，较前值{fmt_bp(cn10_bp)}；资金面{funding}。当前应同时观察绝对收益率、资金价格和超长端供给，避免只根据单日涨跌判断趋势。",
        "watch": "央行公开市场操作、政府债供给、Shibor和30年—10年曲线变化。",
        "metrics": [
            metric("10年国债收益率", f"{r['cn10']:.4f}%", fmt_bp(cn10_bp), direction(cn10_bp, inverse=True), "中债国债收益率曲线；收益率下行代表债券价格走强", "中国债券信息网", URLS["chinabond"], r["cn10"]),
            metric("30年国债收益率", f"{r['cn30']:.4f}%", fmt_bp(cn30_bp), direction(cn30_bp, inverse=True), "观察超长端供给与期限溢价", "中国债券信息网", URLS["chinabond"], r["cn30"]),
            metric("30年—10年利差", f"{curve:.2f} BP", "曲线斜率", "flat", "利差扩大代表超长端相对走弱", "中国债券信息网", URLS["chinabond"], curve),
            metric("隔夜 Shibor", f"{s['on']:.4f}%", fmt_bp(on_bp), direction(on_bp), f"资金面判断：{funding}", "中国货币网", URLS["chinamoney"], s["on"]),
        ],
        "sources": rate_sources,
    }
    credit = {
        "title": "中国信用债",
        "commentary": f"公开曲线显示，AAA中票3年信用利差约{c['mtn3_spread']:.1f}BP，较前值{fmt_bp(mtn3_delta)}。低利差环境下，票息策略仍可用，但继续下沉需要更高的基本面和流动性补偿。",
        "watch": "中债估值曲线、季末理财行为、信用债净融资和弱资质主体负面事件。",
        "metrics": [
            metric("AAA中票1年利差", f"{c['mtn1_spread']:.1f} BP", "较同期限国债", "flat", "中债AAA中票收益率减同期限国债收益率", "中国债券信息网", URLS["chinabond"], c["mtn1_spread"]),
            metric("AAA中票3年利差", f"{c['mtn3_spread']:.1f} BP", fmt_bp(mtn3_delta), direction(mtn3_delta, inverse=True), "衡量高等级信用债相对价值的公开代理指标", "中国债券信息网", URLS["chinabond"], c["mtn3_spread"]),
            metric("AAA中票5年利差", f"{c['mtn5_spread']:.1f} BP", "较同期限国债", "flat", "久期更长，对利率和信用估值均更敏感", "中国债券信息网", URLS["chinabond"], c["mtn5_spread"]),
            metric("AAA银行债5年利差", f"{c['bank5_spread']:.1f} BP", "较5年国债", "flat", "商业银行普通债AAA曲线相对国债", "中国债券信息网", URLS["chinabond"], c["bank5_spread"]),
        ],
        "sources": credit_sources,
    }
    if turnover is not None:
        activity_text = f"成交额约{turnover:.1f}亿元"
        activity_metric = metric(
            "全市场成交额",
            f"{turnover:.1f}亿元",
            f"较前日 {turnover_delta:+.1f}亿元" if turnover_delta is not None else "暂无可比",
            direction(turnover_delta),
            "中证转债指数口径成交额",
            "腾讯行情 / 中证指数",
            URLS["csi_cb"],
            turnover,
        )
    else:
        activity_text = f"指数成交量约{volume_wan:.1f}万手"
        activity_metric = metric(
            "指数成交量",
            f"{volume_wan:.1f}万手",
            f"较前日 {volume_delta:+.1f}万手" if volume_delta is not None else "暂无可比",
            direction(volume_delta),
            "腾讯行情历史K线成交量；成交额尚未发布时采用该口径",
            "腾讯行情 / 中证指数",
            URLS["csi_cb"],
            volume_wan,
        )

    convertible = {
        "title": "可转债",
        "commentary": f"中证转债指数当日{cb_tone}{abs(cb['pct']):.2f}%，{activity_text}。领涨与领跌个券分化反映行情仍需结合正股主线、估值和条款，不能只看指数方向。",
        "watch": "正股风格、成交额、转股溢价率、强赎密度以及领涨品种扩散度。",
        "metrics": [
            metric("中证转债指数", f"{cb['close']:.2f}", fmt_pct(cb["pct"]), direction(cb["pct"]), "000832收盘指数", "中证指数 / 东方财富", URLS["csi_cb"], cb["close"]),
            activity_metric,
            metric("最新领涨个券", cb["top"]["name"], fmt_pct(cb["top"]["pct"]), "up", "自动抓取时点涨幅居前，需结合正股和交易拥挤度", "新浪财经 / 上交所", URLS["sse_bond"], cb["top"]["pct"]),
            metric("最新领跌个券", cb["bottom"]["name"], fmt_pct(cb["bottom"]["pct"]), "down", "自动抓取时点跌幅居前，关注条款和正股负反馈", "新浪财经 / 上交所", URLS["sse_bond"], cb["bottom"]["pct"]),
        ],
        "sources": cb_sources,
    }
    ust = {
        "title": "美国国债",
        "commentary": f"截至美国{us['source_date']}，10年期美债收益率较前值{fmt_bp(us10_bp)}，债券价格整体{us_tone}。2年期更敏感于政策路径，10年及30年还受到通胀、财政供给和期限溢价影响。",
        "watch": "美国通胀与就业数据、FOMC表态、财政供给以及2年—10年曲线变化。",
        "metrics": [
            metric("2年期美债", f"{us['2y']:.2f}%", fmt_bp(us2_bp), direction(us2_bp, inverse=True), f"美国财政部{us['source_date']}官方曲线", "U.S. Treasury", URLS["treasury"], us["2y"]),
            metric("10年期美债", f"{us['10y']:.2f}%", fmt_bp(us10_bp), direction(us10_bp, inverse=True), f"美国财政部{us['source_date']}官方曲线", "U.S. Treasury", URLS["treasury"], us["10y"]),
            metric("30年期美债", f"{us['30y']:.2f}%", fmt_bp(us30_bp), direction(us30_bp, inverse=True), f"美国财政部{us['source_date']}官方曲线", "U.S. Treasury", URLS["treasury"], us["30y"]),
            metric("2s10s曲线", f"{us_curve:.0f} BP", "10年减2年", "flat", "正值代表曲线为正斜率", "U.S. Treasury", URLS["treasury"], us_curve),
        ],
        "sources": us_sources,
    }
    commodities = {
        "title": "商品市场",
        "commentary": f"自动抓取时点显示，COMEX黄金{fmt_pct(co['gold']['pct'])}、Brent原油{fmt_pct(co['brent']['pct'])}。能源主要通过通胀预期影响债市，黄金则同时受实际利率、美元和避险需求驱动。",
        "watch": "原油供给与地缘风险、实际利率、美元和交易所结算价。",
        "metrics": [
            metric("COMEX黄金", f"${co['gold']['price']:,.2f}", fmt_pct(co["gold"]["pct"]), direction(co["gold"]["pct"]), "自动抓取时点报价，非官方结算价", "东方财富 / CME", URLS["cme_gold"], co["gold"]["price"]),
            metric("COMEX白银", f"${co.get('silver', {}).get('price', 0):,.3f}", fmt_pct(co.get("silver", {}).get("pct")), direction(co.get("silver", {}).get("pct")), "自动抓取时点报价，非官方结算价", "东方财富 / CME", URLS["cme_gold"], co.get("silver", {}).get("price")),
            metric("Brent原油", f"${co['brent']['price']:,.2f}", fmt_pct(co["brent"]["pct"]), direction(co["brent"]["pct"]), "当月连续合约自动报价", "东方财富 / ICE", URLS["ice_brent"], co["brent"]["price"]),
            metric("WTI原油", f"${co.get('wti', {}).get('price', 0):,.2f}", fmt_pct(co.get("wti", {}).get("pct")), direction(co.get("wti", {}).get("pct")), "NYMEX当月连续合约自动报价", "东方财富 / CME", URLS["cme_oil"], co.get("wti", {}).get("price")),
        ],
        "sources": commodity_sources,
    }
    markets = {"rates": rates, "credit": credit, "convertible": convertible, "ust": ust, "commodities": commodities}
    comparison = previous or record
    for category, block in markets.items():
        block["interview"] = make_interview(category, "当日", record, comparison)

    overview = {
        "title": "固收市场总览",
        "commentary": f"当日国内利率债{rate_tone}，中证转债指数{cb_tone}，美债整体{us_tone}。中外债市需要分别从国内资金与供给、海外通胀与政策路径解释；商品则通过通胀预期和风险偏好影响固收定价。",
        "watch": "国内资金和政府债供给、美国通胀与政策路径、转债成交和能源价格。",
        "metrics": [rates["metrics"][0], convertible["metrics"][0], ust["metrics"][1], commodities["metrics"][0]],
        "sources": [rate_sources[0], cb_sources[0], us_sources[0], commodity_sources[0]],
        "interview": make_interview("overview", "当日", record, comparison),
    }
    return {"date": day, "label": day_label(day), "verified": True, "markets": {"overview": overview, **markets}}


def delta(latest: dict[str, Any], first: dict[str, Any], path: tuple[str, ...], kind: str) -> float | None:
    last_value = value_at(latest, *path)
    first_value = value_at(first, *path)
    if last_value is None or first_value is None:
        return None
    if kind == "bp":
        return (last_value - first_value) * 100
    if kind == "pct":
        return (last_value / first_value - 1) * 100 if first_value else None
    return last_value - first_value


def make_period(name: str, records: list[dict[str, Any]]) -> dict[str, Any]:
    ordered = sorted(records, key=lambda item: item["date"])
    first, latest = ordered[0], ordered[-1]
    period_word = "本周" if name == "week" else "本月"
    start_date, end_date = date.fromisoformat(first["date"]), date.fromisoformat(latest["date"])
    range_text = f"{start_date:%m月%d日}—{end_date:%m月%d日}"
    daily_latest = make_daily(latest, ordered[-2] if len(ordered) > 1 else None)["markets"]

    cn10 = delta(latest, first, ("rates", "cn10"), "bp")
    cn30 = delta(latest, first, ("rates", "cn30"), "bp")
    on_change = delta(latest, first, ("shibor", "on"), "bp")
    cb_change = delta(latest, first, ("convertible", "close"), "pct")
    us2 = delta(latest, first, ("ust", "2y"), "bp")
    us10 = delta(latest, first, ("ust", "10y"), "bp")
    us30 = delta(latest, first, ("ust", "30y"), "bp")
    gold = delta(latest, first, ("commodities", "gold", "price"), "pct")
    brent = delta(latest, first, ("commodities", "brent", "price"), "pct")
    wti = delta(latest, first, ("commodities", "wti", "price"), "pct")
    silver = delta(latest, first, ("commodities", "silver", "price"), "pct")
    latest_turnover = value_at(latest, "convertible", "turnover_yi")
    latest_volume_wan = require(value_at(latest, "convertible", "volume_wan"), "中证转债成交量")
    if latest_turnover is not None:
        cb_activity_text = f"最新成交额{latest_turnover:.1f}亿元"
        cb_activity_metric = metric("最新成交额", f"{latest_turnover:.1f}亿元", "指数口径", "flat", "观察市场活跃度", "腾讯行情 / 中证指数", URLS["csi_cb"], latest_turnover)
    else:
        cb_activity_text = f"最新指数成交量{latest_volume_wan:.1f}万手"
        cb_activity_metric = metric("最新指数成交量", f"{latest_volume_wan:.1f}万手", "历史K线口径", "flat", "成交额尚未发布时用于观察市场活跃度", "腾讯行情 / 中证指数", URLS["csi_cb"], latest_volume_wan)

    def block(category: str, title: str, commentary: str, watch: str, metrics: list[dict[str, Any]]) -> dict[str, Any]:
        return {
            "title": title,
            "commentary": commentary,
            "watch": watch,
            "metrics": metrics,
            "interview": make_interview(category, period_word, latest, first),
            "sources": daily_latest[category if category != "overview" else "rates"]["sources"] if category != "overview" else [
                source("中债国债收益率曲线", "中国债券信息网 · 官方", URLS["chinabond"]),
                source("Daily Treasury Par Yield Curve Rates", "U.S. Treasury · 官方", URLS["treasury"]),
                source("中证转债指数（000832）", "中证指数 · 官方", URLS["csi_cb"]),
            ],
        }

    markets = {
        "overview": block(
            "overview", f"{period_word}固收总览",
            f"{period_word}中国10年国债收益率变化{fmt_bp(cn10)}，美国10年期变化{fmt_bp(us10)}，中证转债指数变化{fmt_pct(cb_change)}。核心是区分国内资金与基本面、海外通胀与政策，以及风险偏好对转债和商品的影响。",
            "国内资金和政府债供给、美国通胀与政策路径、转债成交和商品风险溢价。",
            [
                metric("中国10年国债", f"{latest['rates']['cn10']:.4f}%", fmt_bp(cn10), direction(cn10, inverse=True), f"{period_word}首尾交易日比较", "中国债券信息网", URLS["chinabond"], latest["rates"]["cn10"]),
                metric("中证转债指数", f"{latest['convertible']['close']:.2f}", fmt_pct(cb_change), direction(cb_change), f"{period_word}首尾交易日比较", "中证指数 / 东方财富", URLS["csi_cb"], latest["convertible"]["close"]),
                metric("美国10年国债", f"{latest['ust']['10y']:.2f}%", fmt_bp(us10), direction(us10, inverse=True), f"官方曲线截至{latest['ust']['source_date']}", "U.S. Treasury", URLS["treasury"], latest["ust"]["10y"]),
                metric("COMEX黄金", f"${latest['commodities']['gold']['price']:,.2f}", fmt_pct(gold), direction(gold), "自动报价首尾比较", "东方财富 / CME", URLS["cme_gold"], latest["commodities"]["gold"]["price"]),
            ],
        ),
        "rates": block(
            "rates", f"{period_word}中国利率债",
            f"{period_word}10年国债收益率变化{fmt_bp(cn10)}、30年变化{fmt_bp(cn30)}，隔夜Shibor变化{fmt_bp(on_change)}。债市方向与资金面需要结合判断。",
            "公开市场操作、政府债发行、资金价格和超长端期限溢价。",
            [
                metric("10年国债收益率", f"{latest['rates']['cn10']:.4f}%", fmt_bp(cn10), direction(cn10, inverse=True), "首尾交易日比较", "中国债券信息网", URLS["chinabond"], latest["rates"]["cn10"]),
                metric("30年国债收益率", f"{latest['rates']['cn30']:.4f}%", fmt_bp(cn30), direction(cn30, inverse=True), "首尾交易日比较", "中国债券信息网", URLS["chinabond"], latest["rates"]["cn30"]),
                metric("隔夜 Shibor", f"{latest['shibor']['on']:.4f}%", fmt_bp(on_change), direction(on_change), "资金价格首尾比较", "中国货币网", URLS["chinamoney"], latest["shibor"]["on"]),
                metric("30年—10年利差", f"{(latest['rates']['cn30']-latest['rates']['cn10'])*100:.2f} BP", "最新曲线", "flat", "衡量超长端相对10年期的期限补偿", "中国债券信息网", URLS["chinabond"], (latest['rates']['cn30']-latest['rates']['cn10'])*100),
            ],
        ),
        "credit": block(
            "credit", f"{period_word}中国信用债",
            f"{period_word}AAA中票3年信用利差最新约{latest['credit']['mtn3_spread']:.1f}BP。低利差下应重视票息保护、主体筛选和流动性。",
            "信用利差、季末理财行为、净融资和弱主体负面事件。",
            [
                metric("AAA中票1年利差", f"{latest['credit']['mtn1_spread']:.1f} BP", "较同期限国债", "flat", "公开曲线代理", "中国债券信息网", URLS["chinabond"], latest["credit"]["mtn1_spread"]),
                metric("AAA中票3年利差", f"{latest['credit']['mtn3_spread']:.1f} BP", "较同期限国债", "flat", "公开曲线代理", "中国债券信息网", URLS["chinabond"], latest["credit"]["mtn3_spread"]),
                metric("AAA中票5年利差", f"{latest['credit']['mtn5_spread']:.1f} BP", "较同期限国债", "flat", "公开曲线代理", "中国债券信息网", URLS["chinabond"], latest["credit"]["mtn5_spread"]),
                metric("AAA银行债5年利差", f"{latest['credit']['bank5_spread']:.1f} BP", "较5年国债", "flat", "公开曲线代理", "中国债券信息网", URLS["chinabond"], latest["credit"]["bank5_spread"]),
            ],
        ),
        "convertible": block(
            "convertible", f"{period_word}可转债",
            f"{period_word}中证转债指数变化{fmt_pct(cb_change)}，{cb_activity_text}。指数之外仍需观察领涨扩散、估值和条款。",
            "正股风格、成交额、转股溢价率和强赎密度。",
            [
                metric("中证转债指数", f"{latest['convertible']['close']:.2f}", fmt_pct(cb_change), direction(cb_change), "首尾交易日比较", "中证指数 / 东方财富", URLS["csi_cb"], latest["convertible"]["close"]),
                cb_activity_metric,
                metric("最新领涨", latest["convertible"]["top"]["name"], fmt_pct(latest["convertible"]["top"]["pct"]), "up", "最新收盘涨幅居前", "新浪财经 / 上交所", URLS["sse_bond"], latest["convertible"]["top"]["pct"]),
                metric("最新领跌", latest["convertible"]["bottom"]["name"], fmt_pct(latest["convertible"]["bottom"]["pct"]), "down", "最新收盘跌幅居前", "新浪财经 / 上交所", URLS["sse_bond"], latest["convertible"]["bottom"]["pct"]),
            ],
        ),
        "ust": block(
            "ust", f"{period_word}美国国债",
            f"{period_word}2年期收益率变化{fmt_bp(us2)}、10年期变化{fmt_bp(us10)}、30年期变化{fmt_bp(us30)}。比较长短端变化可判断曲线由政策路径还是期限溢价主导。",
            "通胀、就业、FOMC、财政供给和期限溢价。",
            [
                metric("2年期美债", f"{latest['ust']['2y']:.2f}%", fmt_bp(us2), direction(us2, inverse=True), f"截至{latest['ust']['source_date']}", "U.S. Treasury", URLS["treasury"], latest["ust"]["2y"]),
                metric("10年期美债", f"{latest['ust']['10y']:.2f}%", fmt_bp(us10), direction(us10, inverse=True), f"截至{latest['ust']['source_date']}", "U.S. Treasury", URLS["treasury"], latest["ust"]["10y"]),
                metric("30年期美债", f"{latest['ust']['30y']:.2f}%", fmt_bp(us30), direction(us30, inverse=True), f"截至{latest['ust']['source_date']}", "U.S. Treasury", URLS["treasury"], latest["ust"]["30y"]),
                metric("2s10s曲线", f"{(latest['ust']['10y']-latest['ust']['2y'])*100:.0f} BP", "最新斜率", "flat", "10年期减2年期", "U.S. Treasury", URLS["treasury"], (latest['ust']['10y']-latest['ust']['2y'])*100),
            ],
        ),
        "commodities": block(
            "commodities", f"{period_word}商品市场",
            f"{period_word}黄金变化{fmt_pct(gold)}、Brent原油变化{fmt_pct(brent)}。能源看供给与通胀，黄金看实际利率、美元和避险需求。",
            "能源供给、地缘风险、实际利率、美元和交易所结算价。",
            [
                metric("COMEX黄金", f"${latest['commodities']['gold']['price']:,.2f}", fmt_pct(gold), direction(gold), "自动报价首尾比较", "东方财富 / CME", URLS["cme_gold"], latest["commodities"]["gold"]["price"]),
                metric("COMEX白银", f"${latest['commodities']['silver']['price']:,.3f}", fmt_pct(silver), direction(silver), "自动报价首尾比较", "东方财富 / CME", URLS["cme_gold"], latest["commodities"]["silver"]["price"]),
                metric("Brent原油", f"${latest['commodities']['brent']['price']:,.2f}", fmt_pct(brent), direction(brent), "自动报价首尾比较", "东方财富 / ICE", URLS["ice_brent"], latest["commodities"]["brent"]["price"]),
                metric("WTI原油", f"${latest['commodities']['wti']['price']:,.2f}", fmt_pct(wti), direction(wti), "自动报价首尾比较", "东方财富 / CME", URLS["cme_oil"], latest["commodities"]["wti"]["price"]),
            ],
        ),
    }
    return {"label": period_word, "range": range_text, "asOf": latest["date"], "verified": True, "markets": markets}


def json_load(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def seed_history_from_daily() -> list[dict[str, Any]]:
    archive = json_load(DAILY_PATH, {"days": []})
    seeded = []
    for item in archive.get("days", []):
        markets = item.get("markets", {})

        def find(category: str, label_fragment: str) -> float | None:
            for candidate in markets.get(category, {}).get("metrics", []):
                if label_fragment in candidate.get("label", ""):
                    return number(candidate.get("numeric", candidate.get("value")))
            return None

        record = {
            "date": item.get("date"),
            "rates": {"cn10": find("rates", "10年国债"), "cn30": find("rates", "30年国债")},
            "shibor": {"on": find("rates", "隔夜 Shibor")},
            "convertible": {
                "close": find("convertible", "中证转债指数"),
                "turnover_yi": find("convertible", "成交额"),
                "volume_wan": find("convertible", "成交量"),
            },
            "ust": {"2y": find("ust", "2年期"), "10y": find("ust", "10年期"), "30y": find("ust", "30年期")},
            "commodities": {"gold": {"price": find("commodities", "黄金")}, "brent": {"price": find("commodities", "Brent")}},
        }
        if record["date"] and record["rates"]["cn10"] and record["convertible"]["close"]:
            seeded.append(record)
    return seeded


def validate_output(daily: dict[str, Any], periods: dict[str, Any]) -> None:
    categories = ["rates", "credit", "convertible", "ust", "commodities"]
    if not daily.get("days"):
        raise RuntimeError("日报归档为空")
    for item in daily["days"]:
        for category in categories:
            block = item.get("markets", {}).get(category)
            if not block or len(block.get("metrics", [])) < 4:
                raise RuntimeError(f"{item.get('date')}/{category} 内容不完整")
            for row in block["metrics"]:
                if not str(row.get("sourceUrl", "")).startswith("https://"):
                    raise RuntimeError(f"{item.get('date')}/{category} 来源链接无效")
    for period_name in ("week", "month"):
        period = periods.get(period_name, {})
        for category in ["overview", *categories]:
            block = period.get("markets", {}).get(category)
            if not block or len(block.get("metrics", [])) < 4 or not block.get("interview", {}).get("short"):
                raise RuntimeError(f"{period_name}/{category} 内容不完整")


def saved_convertible_snapshot(archive: dict[str, Any], target: str) -> tuple[float | None, dict[str, dict[str, Any]] | None]:
    saved = next((item for item in archive.get("days", []) if item.get("date") == target), None)
    metrics = saved.get("markets", {}).get("convertible", {}).get("metrics", []) if saved else []

    def find(fragment: str) -> dict[str, Any] | None:
        return next((item for item in metrics if fragment in item.get("label", "")), None)

    turnover_row = find("成交额")
    top_row = find("领涨")
    bottom_row = find("领跌")
    turnover = number(turnover_row.get("numeric", turnover_row.get("value"))) if turnover_row else None
    if not top_row or not bottom_row:
        return turnover, None
    movers = {
        "top": {"name": top_row.get("value", "—"), "pct": require(number(top_row.get("change")), "历史领涨涨幅")},
        "bottom": {"name": bottom_row.get("value", "—"), "pct": require(number(bottom_row.get("change")), "历史领跌跌幅")},
    }
    return turnover, movers


def main() -> int:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    existing_daily = json_load(DAILY_PATH, {"days": []})
    print("[1/6] 获取中债收益率曲线")
    chinabond = fetch_chinabond()
    target_dates = sorted(day for day, curves in chinabond.items() if "gov" in curves and "mtn_aaa" in curves and "bank_aaa" in curves)
    if not target_dates:
        raise RuntimeError("没有同时包含国债、AAA中票和AAA银行债的交易日")
    target = target_dates[-1]

    print("[2/6] 获取 Shibor 与中证转债")
    shibor_all = fetch_shibor()
    cb_all = fetch_cb_index()
    shibor_date, shibor = latest_on_or_before(shibor_all, target)
    cb_date, cb = latest_on_or_before(cb_all, target)
    if shibor_date != target or cb_date != target:
        raise RuntimeError(f"国内数据日期未对齐: 中债={target}, Shibor={shibor_date}, 转债={cb_date}")
    saved_turnover, saved_movers = saved_convertible_snapshot(existing_daily, target)
    if cb.get("turnover_yi") is None and saved_turnover is not None:
        cb["turnover_yi"] = saved_turnover
    if target == max(cb_all):
        movers = fetch_cb_movers()
    elif saved_movers:
        movers = saved_movers
    else:
        # The public ranking endpoint exposes the current snapshot rather than
        # a historical ranking. The UI labels these rows as the latest movers.
        movers = fetch_cb_movers()

    print("[3/6] 获取美国财政部曲线与商品报价")
    treasury_all = fetch_treasury()
    treasury_date, treasury = latest_on_or_before(treasury_all, target)
    commodities = fetch_global_futures()

    print("[4/6] 生成结构化市场记录")
    record = make_record(target, chinabond[target], shibor, cb, movers, treasury_date, treasury, commodities)
    history_data = json_load(HISTORY_PATH, {"days": seed_history_from_daily()})
    history_by_date = {item["date"]: item for item in history_data.get("days", []) if item.get("date")}
    for historical_day in target_dates:
        if historical_day > target or historical_day not in shibor_all or historical_day not in cb_all:
            continue
        historical_treasury_date, historical_treasury = latest_on_or_before(treasury_all, historical_day)
        generated_history = historical_record(
            historical_day,
            chinabond[historical_day],
            shibor_all[historical_day],
            cb_all[historical_day],
            historical_treasury_date,
            historical_treasury,
        )
        history_by_date[historical_day] = deep_merge(history_by_date.get(historical_day, {}), generated_history)
    history_by_date[target] = deep_merge(history_by_date.get(target, {}), record)
    history = sorted(history_by_date.values(), key=lambda item: item["date"], reverse=True)[:120]
    previous = prior_record(history, target)

    generated_day = make_daily(record, previous)
    daily_days = [item for item in existing_daily.get("days", []) if item.get("date") != target]
    daily_days.append(generated_day)
    daily_days = sorted(daily_days, key=lambda item: item["date"], reverse=True)[:90]
    daily = {"generatedAt": NOW.astimezone(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"), "days": daily_days}

    print("[5/6] 生成本周与本月分析")
    target_date = date.fromisoformat(target)
    week_start = target_date - timedelta(days=target_date.weekday())
    month_start = target_date.replace(day=1)
    chronological = sorted(history, key=lambda item: item["date"])
    week_records = [item for item in chronological if week_start.isoformat() <= item["date"] <= target]
    month_records = [item for item in chronological if month_start.isoformat() <= item["date"] <= target]
    if not week_records:
        week_records = [record]
    if not month_records:
        month_records = [record]
    periods = {"week": make_period("week", week_records), "month": make_period("month", month_records)}

    print("[6/6] 校验并写入")
    validate_output(daily, periods)
    HISTORY_PATH.write_text(json.dumps({"generatedAt": daily["generatedAt"], "days": history}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    DAILY_PATH.write_text(json.dumps(daily, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    PERIODS_PATH.write_text(json.dumps(periods, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"完成：{target}；美债口径截至 {treasury_date}；站点目录 {SITE_DIR}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"自动更新失败：{exc}", file=sys.stderr)
        raise
