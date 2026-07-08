"""亿兆智能决策平台共用 UI 组件。"""

from __future__ import annotations

from html import escape
from typing import Any
import base64
from pathlib import Path

import pandas as pd
import streamlit as st


def _asset_data_uri(filename: str = "yizhao_logo.png") -> str:
    """Return a base64 data URI for a local asset, safe for Streamlit Cloud."""
    candidates = [
        Path(__file__).resolve().parent.parent / "assets" / filename,
        Path("assets") / filename,
    ]
    for path in candidates:
        try:
            data = path.read_bytes()
            return "data:image/png;base64," + base64.b64encode(data).decode("ascii")
        except Exception:
            continue
    return ""


CSS = """
<style>
:root {
  --yz-bg: #07111f;
  --yz-bg-2: #0f172a;
  --yz-panel: rgba(15, 23, 42, .86);
  --yz-card: rgba(255, 255, 255, .94);
  --yz-card-2: rgba(248, 250, 252, .96);
  --yz-border: rgba(148, 163, 184, .32);
  --yz-border-soft: rgba(226, 232, 240, .78);
  --yz-text: #0f172a;
  --yz-muted: #64748b;
  --yz-white: #f8fafc;
  --yz-blue: #2563eb;
  --yz-blue-2: #0ea5e9;
  --yz-green: #16a34a;
  --yz-yellow: #f59e0b;
  --yz-red: #dc2626;
  --yz-gold: #d4af37;
  --yz-shadow: 0 18px 44px rgba(2, 6, 23, .26);
  --yz-shadow-soft: 0 10px 28px rgba(2, 6, 23, .16);
}
html, body, [data-testid="stAppViewContainer"] {
  background:
    radial-gradient(circle at 18% 0%, rgba(37, 99, 235, .22), transparent 34rem),
    radial-gradient(circle at 88% 15%, rgba(14, 165, 233, .13), transparent 30rem),
    linear-gradient(180deg, #07111f 0%, #0a1220 42%, #0f172a 100%) !important;
  color: var(--yz-white);
  font-family: Inter, "Noto Sans SC", "Microsoft YaHei", "PingFang SC", "Segoe UI", sans-serif;
}
.block-container {
  max-width: 1720px !important;
  padding-top: 1.2rem !important;
  padding-left: 2.2rem !important;
  padding-right: 2.2rem !important;
  padding-bottom: 2.4rem !important;
}
[data-testid="stSidebar"] {
  background:
    radial-gradient(circle at top, rgba(37,99,235,.20), transparent 22rem),
    linear-gradient(180deg, rgba(2,6,23,.97), rgba(15,23,42,.98)) !important;
  border-right: 1px solid rgba(148,163,184,.20);
  min-width: 285px !important;
  max-width: 285px !important;
}
[data-testid="stSidebar"] > div {padding-top: 1.15rem;}
[data-testid="stSidebar"] * {color: #e5eefb;}
[data-testid="stSidebar"] div[data-testid="stRadio"] [role="radiogroup"] {
  display: flex;
  flex-direction: column;
  gap: 7px;
  padding: 0;
}
[data-testid="stSidebar"] div[data-testid="stRadio"] label {
  width: 100%;
  min-height: 44px !important;
  padding: 10px 12px !important;
  border-radius: 14px !important;
  border: 1px solid rgba(148,163,184,.16) !important;
  background: rgba(15, 23, 42, .48) !important;
  display: flex !important;
  align-items: center !important;
  transition: all .15s ease;
}
[data-testid="stSidebar"] div[data-testid="stRadio"] label:hover {
  background: rgba(37, 99, 235, .18) !important;
  border-color: rgba(96, 165, 250, .38) !important;
  transform: translateX(2px);
}
[data-testid="stSidebar"] div[data-testid="stRadio"] label p {
  font-size: 14px !important;
  font-weight: 850 !important;
  margin: 0 !important;
  white-space: nowrap !important;
}
[data-testid="stSidebar"] div[data-testid="stRadio"] label[data-baseweb="radio"] > div:first-child {margin-right: 8px;}

/* 旧顶部 radio 若仍被页面使用，也保证不切字 */
div[data-testid="stRadio"] [role="radiogroup"] {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
  min-height: 50px;
  overflow: visible;
  padding: 7px 0 8px 0;
}
div[data-testid="stRadio"] label {
  min-height: 38px !important;
  height: auto !important;
  overflow: visible !important;
  white-space: nowrap !important;
}
div[data-testid="stRadio"] label p {
  line-height: 1.35 !important;
  margin: 0 !important;
  overflow: visible !important;
  white-space: nowrap !important;
  font-weight: 800 !important;
}

/* Streamlit 常用元素 */
[data-testid="stDataFrame"] {border-radius: 18px; overflow: hidden; border: 1px solid var(--yz-border); box-shadow: var(--yz-shadow-soft);}
hr {border-color: rgba(148, 163, 184, .23);}
div[data-testid="stHorizontalBlock"] {gap: .95rem;}
.stButton > button {
  border-radius: 14px !important;
  border: 1px solid rgba(96,165,250,.36) !important;
  background: linear-gradient(135deg, #2563eb, #0ea5e9) !important;
  color: white !important;
  font-weight: 900 !important;
  box-shadow: 0 12px 28px rgba(37,99,235,.20) !important;
}

/* Sidebar brand */
.yz-sidebar-brand {
  border: 1px solid rgba(148, 163, 184, .18);
  background: linear-gradient(135deg, rgba(30,64,175,.26), rgba(2,132,199,.10));
  border-radius: 20px;
  padding: 16px 15px;
  margin-bottom: 15px;
  box-shadow: 0 14px 32px rgba(0,0,0,.22);
}
.yz-logo-img {
  height: 68px;
  max-width: 210px;
  object-fit: contain;
  display: block;
  margin-bottom: 11px;
  filter: drop-shadow(0 12px 26px rgba(37,99,235,.26));
  animation: yz-logo-in .55s ease-out both;
}
.yz-header-logo-img {
  width: 88px; height: 88px; object-fit: contain; flex: 0 0 auto;
  filter: drop-shadow(0 12px 24px rgba(37,99,235,.32));
}
.yz-header-brand {display:flex; align-items:center; gap:18px;}
@keyframes yz-logo-in {from {opacity:0; transform:scale(.94)} to {opacity:1; transform:scale(1)}}
.yz-sidebar-title {font-size: 18px; font-weight: 950; letter-spacing: .2px; line-height: 1.2; color:#fff;}
.yz-sidebar-subtitle {font-size: 11px; color:#93c5fd; font-weight: 800; margin-top: 6px;}
.yz-version-chip {display:inline-block; margin-top:10px; padding:4px 9px; border-radius:999px; background:rgba(255,255,255,.10); color:#e0f2fe; font-size:11px; font-weight:900; border:1px solid rgba(255,255,255,.12);}
.yz-side-divider {height:1px; background:rgba(148,163,184,.18); margin: 13px 0;}
.yz-side-spacer {height: 16px;}
.yz-side-status {border-radius:18px; padding:14px 13px; background:rgba(15,23,42,.58); border:1px solid rgba(148,163,184,.16); font-size:12px; line-height:1.9; font-weight:800;}
.yz-side-status-title {font-size:13px; color:#fff; font-weight:950; margin-bottom:6px;}
.yz-dot {width:8px; height:8px; display:inline-block; border-radius:999px; margin-right:7px;}
.yz-dot-ok {background:#22c55e; box-shadow:0 0 0 4px rgba(34,197,94,.14);}
.yz-dot-warn {background:#f59e0b; box-shadow:0 0 0 4px rgba(245,158,11,.14);}
.yz-dot-bad {background:#ef4444; box-shadow:0 0 0 4px rgba(239,68,68,.14);}

/* Enterprise Header */
.yz-enterprise-header {
  position: relative;
  overflow: hidden;
  border-radius: 26px;
  padding: 24px 26px;
  margin-bottom: 20px;
  border: 1px solid rgba(148, 163, 184, .26);
  background:
    radial-gradient(circle at 75% 20%, rgba(14,165,233,.28), transparent 26rem),
    radial-gradient(circle at 15% 10%, rgba(37,99,235,.38), transparent 23rem),
    linear-gradient(135deg, rgba(15,23,42,.94), rgba(30,64,175,.70) 55%, rgba(2,132,199,.42));
  box-shadow: var(--yz-shadow);
}
.yz-enterprise-header:after {
  content: "";
  position: absolute;
  right: -70px;
  top: -90px;
  width: 250px;
  height: 250px;
  border-radius: 999px;
  background: rgba(255,255,255,.06);
  border: 1px solid rgba(255,255,255,.12);
}
.yz-header-grid {display:flex; align-items:flex-start; justify-content:space-between; gap:22px; position:relative; z-index:2;}
.yz-header-title {font-size:30px; font-weight:950; color:#fff; letter-spacing:.2px; margin:0;}
.yz-header-subtitle {font-size:13px; font-weight:850; color:#bfdbfe; margin-top:6px;}
.yz-breadcrumb {margin-top:13px; display:inline-flex; gap:8px; align-items:center; padding:7px 11px; border-radius:999px; background:rgba(255,255,255,.09); border:1px solid rgba(255,255,255,.12); color:#e0f2fe; font-size:12px; font-weight:900;}
.yz-header-actions {display:flex; flex-wrap:wrap; align-items:center; justify-content:flex-end; gap:8px; max-width:720px;}
.yz-search-box {min-width:230px; padding:9px 13px; border-radius:999px; background:rgba(15,23,42,.52); border:1px solid rgba(191,219,254,.22); color:#bfdbfe; font-weight:850; font-size:12px;}
.yz-status-pill {display:inline-flex; align-items:center; gap:7px; padding:8px 10px; border-radius:999px; background:rgba(255,255,255,.10); color:#e0f2fe; border:1px solid rgba(255,255,255,.12); font-size:12px; font-weight:900;}
.yz-update-text {width:100%; text-align:right; font-size:11px; color:#bfdbfe; font-weight:850; margin-top:2px;}

/* Cards */
.gip-hero, .yz-hero {
  position: relative;
  overflow: hidden;
  border: 1px solid rgba(148, 163, 184, .32);
  border-radius: 26px;
  padding: 25px 26px;
  background:
    radial-gradient(circle at 85% 15%, rgba(14, 165, 233, .35), transparent 24rem),
    linear-gradient(135deg, #0f172a 0%, #1d4ed8 54%, #0369a1 100%);
  color: white;
  box-shadow: var(--yz-shadow);
  margin-bottom: 20px;
}
.gip-hero h1, .yz-hero h1 {margin:0 0 7px 0; font-size:31px; font-weight:950; color:#fff;}
.gip-hero p, .yz-hero p {margin:0; color:#dbeafe; font-size:14px; font-weight:750;}
.gip-version-badge {font-size:13px;background:rgba(255,255,255,.92);color:#0f172a;border-radius:999px;padding:5px 10px;vertical-align:middle;margin-left:8px;}

.gip-card {
  border: 1px solid rgba(226,232,240,.86);
  border-radius: 22px;
  padding: 19px 20px;
  background: linear-gradient(180deg, rgba(255,255,255,.98), rgba(248,250,252,.96));
  box-shadow: var(--yz-shadow-soft);
  min-height: 128px;
  transition: transform .16s ease, box-shadow .16s ease, border-color .16s ease;
}
.gip-card:hover {transform: translateY(-2px); box-shadow: var(--yz-shadow); border-color: rgba(96,165,250,.52);}
.gip-card-title {font-size: 13px; color: var(--yz-muted); margin-bottom: 10px; display:flex; align-items:center; gap:8px; font-weight:900;}
.gip-card-icon {width:30px; height:30px; border-radius:11px; display:inline-flex; align-items:center; justify-content:center; background:#eff6ff;}
.gip-card-value {font-size: 32px; font-weight: 950; color: #0f172a; line-height: 1.08; letter-spacing:-.5px;}
.gip-card-note {font-size: 12px; color: var(--yz-muted); margin-top: 11px; font-weight:750;}
.gip-delta-up {color:#16a34a; font-weight:950;}
.gip-delta-down {color:#dc2626; font-weight:950;}
.gip-delta-flat {color:#64748b; font-weight:900;}

.gip-section-title {margin-top: 24px; margin-bottom: 7px; font-size: 23px; font-weight: 950; color:#f8fafc; letter-spacing:-.2px;}
.gip-section-title:before {content:""; display:inline-block; width:8px; height:22px; border-radius:999px; background:linear-gradient(180deg,#60a5fa,#0ea5e9); margin-right:9px; vertical-align:-4px;}
.gip-section-subtitle {margin-top: -2px; margin-bottom: 14px; color:#94a3b8; font-size: 13px; font-weight:750;}

.gip-alert {border-radius:16px; padding:14px 16px; margin-bottom:10px; border:1px solid #e5e7eb; background:rgba(255,255,255,.95); color:#111827; font-weight:850; box-shadow:var(--yz-shadow-soft);}
.gip-alert span, .gip-alert div, .gip-alert p {color:#111827 !important;}
.gip-alert-critical {border-left:6px solid #dc2626; background:linear-gradient(90deg, rgba(220,38,38,.10), rgba(255,255,255,.98));}
.gip-alert-warning {border-left:6px solid #f59e0b; background:linear-gradient(90deg, rgba(245,158,11,.12), rgba(255,255,255,.98));}
.gip-alert-good {border-left:6px solid #16a34a; background:linear-gradient(90deg, rgba(22,163,74,.12), rgba(255,255,255,.98));}
.gip-brief {border-radius:22px; padding:20px 22px; background:rgba(255,255,255,.95); border:1px solid #e2e8f0; line-height:1.85; color:#0f172a; box-shadow:var(--yz-shadow-soft); font-weight:750;}
.gip-score {font-size:44px; line-height:1; font-weight:950; color:#0f172a; letter-spacing:-1px;}
.gip-pill {display:inline-block; border-radius:999px; padding:4px 10px; background:#f1f5f9; color:#334155; font-size:12px; font-weight:900; margin-right:6px; border:1px solid #e2e8f0;}
.gip-quick-card {border-radius:22px; padding:18px 20px; min-height:120px; color:#e6f0ff; border:1px solid rgba(226,232,240,.18); box-shadow:0 13px 30px rgba(2,6,23,.25); transition:transform .16s ease, box-shadow .16s ease;}
.gip-quick-card:hover {transform: translateY(-2px); box-shadow: 0 18px 42px rgba(2,6,23,.35);}
.gip-quick-card h4 {margin:0 0 10px 0; color:#fff; font-size:16px; font-weight:950;}
.gip-quick-card p {margin:0; color:#e6f0ff; line-height:1.65; font-size:14px; font-weight:750;}
.gip-quick-green {background: linear-gradient(135deg, #047857 0%, #166534 100%);}
.gip-quick-yellow {background: linear-gradient(135deg, #92400e 0%, #854d0e 100%);}
.gip-quick-blue {background: linear-gradient(135deg, #075985 0%, #1d4ed8 100%);}
.gip-quick-gray {background: linear-gradient(135deg, #1f2937 0%, #475569 100%);}
.gip-worldcup-hero {background: radial-gradient(circle at 85% 15%, rgba(212,175,55,.28), transparent 22rem), linear-gradient(135deg,#052e1a,#0f5b2a 55%,#173f2a) !important;}
.gip-worldcup-card .gip-card-value {color:#0f5b2a;}
.yz-footer {color:#94a3b8; font-size:12px; font-weight:750; margin-top:18px;}

@media (max-width: 900px) {
  [data-testid="stSidebar"] {min-width: 240px !important; max-width: 240px !important;}
  .block-container {padding-left:1rem !important; padding-right:1rem !important;}
  .yz-header-grid {flex-direction:column;}
  .yz-header-actions {justify-content:flex-start;}
  .yz-update-text {text-align:left;}
}


/* v4.3 Branding and sticky header */
.yz-enterprise-header {
  position: sticky !important;
  top: 0 !important;
  z-index: 9998 !important;
  backdrop-filter: blur(18px);
  -webkit-backdrop-filter: blur(18px);
}
section.main div[data-testid="stRadio"]:has([role="radiogroup"]) {
  position: sticky !important;
  top: 132px !important;
  z-index: 9997 !important;
  background: rgba(7, 17, 31, .88);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  border-radius: 0 0 18px 18px;
  padding: 0 4px 2px 4px;
  box-shadow: 0 16px 34px rgba(2,6,23,.22);
}
.yz-enterprise-header {
  border-radius: 22px !important;
}
.yz-header-title-wrap {min-width: 0;}

/* v4.2 Enterprise Dashboard overrides */
.block-container {
  max-width: 1840px !important;
  padding-top: .85rem !important;
}
.yz-enterprise-header {
  min-height: 124px;
  padding: 22px 26px !important;
  margin-bottom: 14px !important;
}
.yz-header-title {font-size: 36px !important;}
.yz-header-subtitle {font-size: 13px !important;}
.yz-breadcrumb {margin-top: 10px !important;}
.yz-search-box {min-width: 300px !important;}
.yz-side-caption {
  color: #93c5fd;
  font-size: 12px;
  font-weight: 850;
  padding: 8px 10px;
  border-radius: 12px;
  background: rgba(59, 130, 246, .10);
  border: 1px solid rgba(96, 165, 250, .16);
}
.yz-topnav-spacer {height: 18px;}
/* Hide legacy page hero to avoid duplicated headers */
.gip-hero, .yz-hero {display: none !important;}

/* Top secondary navigation */
section.main div[data-testid="stRadio"]:has([role="radiogroup"]) {
  margin-top: 0 !important;
}
section.main div[data-testid="stRadio"] [role="radiogroup"] {
  display: flex !important;
  gap: 8px !important;
  min-height: 46px !important;
  padding: 8px 0 12px !important;
  border-bottom: 1px solid rgba(148,163,184,.18);
  margin-bottom: 10px;
}
section.main div[data-testid="stRadio"] label {
  min-height: 38px !important;
  border: 1px solid rgba(148,163,184,.18) !important;
  background: rgba(15,23,42,.38) !important;
  border-radius: 14px !important;
  padding: 8px 14px !important;
  transition: all .16s ease;
}
section.main div[data-testid="stRadio"] label:hover {
  background: rgba(37,99,235,.22) !important;
  border-color: rgba(96,165,250,.52) !important;
  transform: translateY(-1px);
}
section.main div[data-testid="stRadio"] label p {
  color: #e5eefb !important;
  font-size: 14px !important;
  font-weight: 900 !important;
}

/* KPI section spacing and glass cards */
div[data-testid="stHorizontalBlock"] {gap: 1.25rem !important;}
.gip-card {
  min-height: 145px !important;
  margin-bottom: 16px !important;
  padding: 22px 24px !important;
  border-radius: 24px !important;
  background:
    radial-gradient(circle at 14% 16%, rgba(59,130,246,.14), transparent 12rem),
    linear-gradient(180deg, rgba(15,23,42,.92), rgba(15,23,42,.72)) !important;
  border: 1px solid rgba(148,163,184,.22) !important;
  box-shadow: 0 14px 38px rgba(2,6,23,.32) !important;
}
.gip-card:hover {
  transform: translateY(-4px) !important;
  border-color: rgba(96,165,250,.58) !important;
  box-shadow: 0 22px 54px rgba(37,99,235,.24) !important;
}
.gip-card-title {font-size: 14px !important; color: #c7d2fe !important; margin-bottom: 14px !important;}
.gip-card-icon {
  width: 38px !important;
  height: 38px !important;
  border-radius: 15px !important;
  background: linear-gradient(135deg, rgba(37,99,235,.28), rgba(14,165,233,.18)) !important;
  box-shadow: inset 0 0 0 1px rgba(255,255,255,.08);
}
.gip-card-value {
  font-size: 38px !important;
  color: #f8fafc !important;
  letter-spacing: -1px !important;
}
.gip-card-note {font-size: 13px !important; color: #94a3b8 !important; margin-top: 13px !important;}
.gip-delta-up {color:#34d399 !important;}
.gip-delta-down {color:#f87171 !important;}

/* AI brief and alerts upgraded to dark cards */
.gip-brief {
  background:
    radial-gradient(circle at 0% 0%, rgba(14,165,233,.12), transparent 16rem),
    linear-gradient(180deg, rgba(15,23,42,.92), rgba(15,23,42,.74)) !important;
  border: 1px solid rgba(148,163,184,.22) !important;
  color: #e5eefb !important;
  box-shadow: 0 14px 38px rgba(2,6,23,.30) !important;
}
.gip-brief:before {
  content: "🤖 AI经营摘要";
  display: block;
  color: #f8fafc;
  font-size: 17px;
  font-weight: 950;
  margin-bottom: 10px;
}
.gip-alert {
  background: linear-gradient(180deg, rgba(15,23,42,.90), rgba(15,23,42,.72)) !important;
  border: 1px solid rgba(148,163,184,.22) !important;
  color: #e5eefb !important;
  margin-bottom: 12px !important;
}
.gip-alert span, .gip-alert div, .gip-alert p {color:#e5eefb !important;}

/* More breathing room around section titles */
.gip-section-title {margin-top: 28px !important; margin-bottom: 9px !important;}
.gip-section-subtitle {margin-bottom: 18px !important;}

@media (max-width: 1200px) {
  .yz-search-box {min-width: 220px !important;}
  .gip-card-value {font-size: 32px !important;}
}



/* v5.2 固定顶部与 Logo 放大 */
.yz-enterprise-header {
  position: sticky !important;
  top: 0 !important;
  z-index: 2147483000 !important;
  min-height: 124px !important;
  padding: 22px 26px !important;
  margin-bottom: 0 !important;
  border-radius: 24px 24px 18px 18px !important;
  background:
    radial-gradient(circle at 78% 16%, rgba(14,165,233,.34), transparent 28rem),
    radial-gradient(circle at 12% 8%, rgba(37,99,235,.44), transparent 24rem),
    linear-gradient(135deg, rgba(15,23,42,.98), rgba(30,64,175,.78) 54%, rgba(2,132,199,.50)) !important;
  box-shadow: 0 18px 46px rgba(2,6,23,.42) !important;
  backdrop-filter: blur(20px) saturate(1.15) !important;
  -webkit-backdrop-filter: blur(20px) saturate(1.15) !important;
}
.yz-header-logo-img {
  width: 88px !important;
  height: 88px !important;
  max-width: 88px !important;
}
.yz-logo-img {
  height: 68px !important;
  max-width: 215px !important;
}
.yz-header-title {
  font-size: 36px !important;
  line-height: 1.08 !important;
}
.yz-header-subtitle {
  font-size: 13px !important;
}
.yz-breadcrumb {
  margin-top: 12px !important;
}
section.main div[data-testid="stRadio"]:has([role="radiogroup"]) {
  position: sticky !important;
  top: 132px !important;
  z-index: 2147482999 !important;
  background: linear-gradient(180deg, rgba(7,17,31,.98), rgba(7,17,31,.90)) !important;
  backdrop-filter: blur(18px) saturate(1.15) !important;
  -webkit-backdrop-filter: blur(18px) saturate(1.15) !important;
  padding: 8px 8px 0 8px !important;
  margin-bottom: 24px !important;
  border-radius: 0 0 20px 20px !important;
  box-shadow: 0 18px 38px rgba(2,6,23,.38) !important;
  border-bottom: 1px solid rgba(96,165,250,.20) !important;
}
section.main div[data-testid="stRadio"] [role="radiogroup"] {
  padding: 8px 0 12px 0 !important;
  margin-bottom: 0 !important;
}
@media (max-width: 900px) {
  .yz-enterprise-header {min-height: 156px !important;}
  section.main div[data-testid="stRadio"]:has([role="radiogroup"]) {top: 164px !important;}
  .yz-header-logo-img {width: 72px !important; height: 72px !important;}
  .yz-header-title {font-size: 28px !important;}
}
</style>
"""


def apply_theme() -> None:
    st.markdown(CSS, unsafe_allow_html=True)


def sidebar_brand(app_name: str, subtitle: str, version: str) -> None:
    logo = _asset_data_uri()
    logo_html = f'<img class="yz-logo-img" src="{logo}" alt="亿兆 Logo" />' if logo else '<div class="yz-logo-img">亿兆</div>'
    st.markdown(
        f"""
        <div class="yz-sidebar-brand">
          {logo_html}
          <div class="yz-sidebar-title">{escape(app_name)}</div>
          <div class="yz-sidebar-subtitle">{escape(subtitle)}</div>
          <span class="yz-version-chip">{escape(version)}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )


def enterprise_header(title: str, subtitle: str, version: str, date: str, active_group: str = "", active_page: str = "") -> None:
    crumb = " > ".join([x for x in [active_group, active_page] if x])
    logo = _asset_data_uri()
    logo_html = f'<img class="yz-header-logo-img" src="{logo}" alt="亿兆 Logo" />' if logo else '<div class="yz-header-logo-img">亿</div>'
    st.markdown(
        f"""
        <div class="yz-enterprise-header">
          <div class="yz-header-grid">
            <div class="yz-header-brand">
              {logo_html}
              <div class="yz-header-title-wrap">
                <div class="yz-header-title">{escape(title)}</div>
                <div class="yz-header-subtitle">{escape(subtitle)} · {escape(version)} · {escape(date)}</div>
                <div class="yz-breadcrumb">当前位置：{escape(crumb or '首页')}</div>
              </div>
            </div>
            <div class="yz-header-actions">
              <div class="yz-search-box">🔍 全局搜索：会员 / 赛事 / 游戏</div>
              <span class="yz-status-pill"><span class="yz-dot yz-dot-ok"></span>BigQuery 正常</span>
              <span class="yz-status-pill"><span class="yz-dot yz-dot-ok"></span>ETL 正常</span>
              <span class="yz-status-pill"><span class="yz-dot yz-dot-ok"></span>AI 正常</span>
              <span class="yz-status-pill"><span class="yz-dot yz-dot-ok"></span>在线</span>
              <div class="yz-update-text">最后更新时间：由 Dashboard 数据源自动更新</div>
            </div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def topbar(app_name: str = "亿兆智能决策平台", subtitle: str = "Enterprise Intelligence Platform", version: str = "v4.3.0") -> None:
    enterprise_header(app_name, subtitle, version, "", "", "")


def hero(title: str, subtitle: str, version: str = "v4.3.0") -> None:
    st.markdown(
        f"""
        <div class="gip-hero">
          <h1>{escape(title)} <span class="gip-version-badge">{escape(version)}</span></h1>
          <p>{escape(subtitle)}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def section(title: str, subtitle: str = "") -> None:
    st.markdown(f'<div class="gip-section-title">{escape(title)}</div>', unsafe_allow_html=True)
    if subtitle:
        st.markdown(f'<div class="gip-section-subtitle">{escape(subtitle)}</div>', unsafe_allow_html=True)


def metric_card(title: str, value: str, note: str = "", delta: Any = None, icon: str = "") -> None:
    delta_html = ""
    if delta is not None and not (isinstance(delta, float) and pd.isna(delta)):
        try:
            d = float(delta)
            cls = "gip-delta-up" if d >= 0 else "gip-delta-down"
            arrow = "▲" if d >= 0 else "▼"
            delta_html = f'<span class="{cls}">{arrow} {abs(d) * 100:.2f}%</span>'
        except Exception:
            delta_html = f'<span class="gip-delta-flat">{escape(str(delta))}</span>'
    st.markdown(
        f"""
        <div class="gip-card">
          <div class="gip-card-title"><span class="gip-card-icon">{escape(icon)}</span><span>{escape(title)}</span></div>
          <div class="gip-card-value">{escape(str(value))}</div>
          <div class="gip-card-note">{delta_html} {escape(note)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def alert(text: str, level: str = "warning") -> None:
    cls = {
        "critical": "gip-alert-critical",
        "warning": "gip-alert-warning",
        "good": "gip-alert-good",
    }.get(level, "gip-alert-warning")
    st.markdown(f'<div class="gip-alert {cls}">{escape(text)}</div>', unsafe_allow_html=True)


def brief(lines: list[str]) -> None:
    body = "<br>".join(escape(line) for line in lines if line)
    st.markdown(f'<div class="gip-brief">{body}</div>', unsafe_allow_html=True)


def score_card(title: str, score: int, note: str = "") -> None:
    score = max(0, min(int(score), 100))
    if score >= 85:
        label = "优秀"
        color = "#16a34a"
    elif score >= 70:
        label = "稳定"
        color = "#2563eb"
    elif score >= 55:
        label = "观察"
        color = "#f59e0b"
    else:
        label = "风险"
        color = "#dc2626"
    st.markdown(
        f"""
        <div class="gip-card">
          <div class="gip-card-title">{escape(title)}</div>
          <div class="gip-score" style="color:{color};">{score}</div>
          <div class="gip-card-note"><span class="gip-pill">{label}</span>{escape(note)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def footer(app_name: str, version: str, date: str) -> None:
    st.divider()
    st.markdown(
        f'<div class="yz-footer">{escape(app_name)} {escape(version)}（{escape(date)}） · Enterprise UI · BigQuery · ETL · AI · 数据中心</div>',
        unsafe_allow_html=True,
    )
