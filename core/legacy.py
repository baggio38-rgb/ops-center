"""
运营数据分析面板（Claude 交接版）
- 保留原始中文字段命名
- BigQuery 联动
- 会员价值页补齐筛选与默认排除提示
- 实时波动页修复「时间=2026-01-31 23~24」解析
- 若会员表未补 _snapshot_month / _snapshot_date，则留存明确标记为暂未启用
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from html import escape
from typing import Dict, List, Optional, Tuple

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st
from config import PROJECT_ID, DATASET_ID, BQ_PREFIX
from version import APP_NAME, APP_VERSION, APP_VERSION_DATE
from services.bigquery_client import get_bq_client
from utils.formatter import (
    fmt_num,
    fmt_pct,
    safe_sum,
    safe_mean,
    safe_nunique,
    member_count,
    tone_by_sign,
)

from constants import (
    BLUE,
    CYAN,
    GREEN,
    RED,
    PURPLE,
    AMBER,
    TEXT_COLUMNS,
)

st.set_page_config(page_title=APP_NAME, layout="wide")

# ── 样式 ──────────────────────────────────────────────────
st.markdown(
    """
<style>
:root {
  --bg-1: #040a16;
  --bg-2: #081226;
  --card: rgba(9, 22, 42, 0.85);
  --card-2: rgba(12, 28, 52, 0.90);
  --line: rgba(34, 211, 238, 0.18);
  --line-strong: rgba(34, 211, 238, 0.45);
  --glow: rgba(34, 211, 238, 0.30);
  --text-1: #e8f7ff;
  --text-2: #9fc1d9;
  --text-3: #6d8aa6;
  --accent: #22d3ee;
  --accent-page: #22d3ee;
  --good: #2dd4a7;
  --good-soft: rgba(45, 212, 167, 0.12);
  --good-text: #7df0c8;
  --bad: #fb7185;
  --bad-soft: rgba(251, 113, 133, 0.12);
  --bad-text: #fda4af;
  --warn: #fbbf24;
  --warn-soft: rgba(251, 191, 36, 0.12);
  --warn-text: #fde08a;
  --green: #2dd4a7;
  --red: #fb7185;
  --amber: #fbbf24;
}
html, body, [data-testid="stAppViewContainer"] {
  background:
    radial-gradient(900px 420px at 12% -8%, rgba(14, 90, 130, 0.22) 0%, rgba(14, 90, 130, 0) 60%),
    radial-gradient(1100px 500px at 88% -10%, rgba(20, 60, 130, 0.28) 0%, rgba(20, 60, 130, 0) 60%),
    linear-gradient(180deg, #030810 0%, #050d1c 100%);
}
[data-testid="stHeader"] { background: rgba(0,0,0,0); }
[data-testid="stSidebar"] { display: none; }
.block-container { padding-top: 0.9rem; padding-bottom: 2rem; max-width: 1480px; }

/* ── 导航：科技感分段控件 ── */
div[role="radiogroup"] { gap: 0.35rem 0.4rem; }
div[role="radiogroup"] label {
  background: rgba(7, 18, 36, 0.85);
  border: 1px solid var(--line);
  border-radius: 4px;
  padding: 0.34rem 0.95rem;
  transition: border-color 0.15s, background 0.15s, box-shadow 0.15s;
  clip-path: polygon(8px 0, 100% 0, 100% calc(100% - 8px), calc(100% - 8px) 100%, 0 100%, 0 8px);
}
div[role="radiogroup"] label:hover { border-color: var(--line-strong); }
div[role="radiogroup"] label:has(input:checked) {
  background: linear-gradient(135deg, rgba(34,211,238,0.22) 0%, rgba(34,211,238,0.06) 100%);
  border-color: var(--accent-page);
  box-shadow: 0 0 14px var(--glow), inset 0 0 10px rgba(34,211,238,0.08);
}
div[role="radiogroup"] label p { color: #c9e6f5; font-weight: 600; font-size: 0.88rem; }
div[role="radiogroup"] label:has(input:checked) p { color: #ffffff; text-shadow: 0 0 8px var(--glow); }

/* ── 页头：大屏式标题横幅 ── */
.hero-card {
  position: relative;
  overflow: hidden;
  background: linear-gradient(180deg, rgba(10,26,48,0.92) 0%, rgba(6,15,30,0.88) 100%);
  border: 1px solid var(--line);
  border-radius: 6px;
  padding: 0.95rem 1.3rem;
  margin-bottom: 0.9rem;
  box-shadow: inset 0 0 30px rgba(34,211,238,0.04);
}
.hero-card::before {
  content: '';
  position: absolute;
  top: 0; left: 0; right: 0;
  height: 2px;
  background: linear-gradient(90deg, rgba(0,0,0,0) 0%, var(--accent-page) 18%, var(--accent-page) 82%, rgba(0,0,0,0) 100%);
  filter: drop-shadow(0 0 6px var(--accent-page));
}
.hero-card::after {
  content: '';
  position: absolute;
  bottom: 0; left: 8%; right: 8%;
  height: 1px;
  background: linear-gradient(90deg, rgba(0,0,0,0) 0%, var(--line-strong) 50%, rgba(0,0,0,0) 100%);
}
.hero-title {
  color: var(--text-1);
  font-size: 1.22rem;
  font-weight: 800;
  letter-spacing: 0.12em;
  margin-bottom: 0.25rem;
  text-shadow: 0 0 16px var(--glow);
}
.hero-subtitle {
  color: var(--text-2);
  font-size: 0.9rem;
  line-height: 1.45;
}
.badge-row { display: flex; flex-wrap: wrap; gap: 0.5rem; margin-bottom: 0.7rem; }
.badge {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  background: rgba(11, 32, 58, 0.65);
  border: 1px solid var(--line);
  color: #cfeefb;
  border-radius: 3px;
  padding: 0.22rem 0.62rem;
  font-size: 0.78rem;
  font-weight: 600;
}
.badge::before { content: ''; width: 6px; height: 6px; border-radius: 50%; background: var(--accent-page); }
.badge-good { background: var(--good-soft); border-color: rgba(45,212,167,0.40); color: var(--good-text); }
.badge-good::before { background: var(--good); }
.badge-bad { background: var(--bad-soft); border-color: rgba(251,113,133,0.40); color: var(--bad-text); }
.badge-bad::before { background: var(--bad); }
.badge-warn { background: var(--warn-soft); border-color: rgba(251,191,36,0.40); color: var(--warn-text); }
.badge-warn::before { background: var(--warn); }

/* ── 顶部核心结论横幅 ── */
.kpi-banner {
  display: flex;
  flex-wrap: wrap;
  align-items: baseline;
  gap: 0.4rem 1.5rem;
  background: linear-gradient(90deg, rgba(34,211,238,0.10) 0%, rgba(6,15,30,0.85) 60%);
  border: 1px solid var(--line-strong);
  border-radius: 5px;
  padding: 0.7rem 1.2rem;
  margin-bottom: 0.9rem;
  box-shadow: 0 0 18px rgba(34,211,238,0.08), inset 0 0 24px rgba(34,211,238,0.05);
}
.kpi-banner .kb-main { font-size: 1.25rem; font-weight: 800; color: #eafcff; text-shadow: 0 0 14px var(--glow); }
.kpi-banner .kb-item { color: var(--text-2); font-size: 0.95rem; font-weight: 600; }
.kpi-banner .kb-up { color: var(--good-text); font-weight: 700; }
.kpi-banner .kb-down { color: var(--bad-text); font-weight: 700; }

/* ── 指标卡：大屏式发光数字 + 角标，tone-* 上状态色 ── */
.metric-card {
  position: relative;
  background: linear-gradient(180deg, rgba(11,28,52,0.85) 0%, rgba(6,15,30,0.92) 100%);
  border: 1px solid var(--line);
  border-radius: 5px;
  padding: 0.8rem 0.95rem 0.8rem 1.05rem;
  min-height: 118px;
  box-shadow: inset 0 0 22px rgba(34,211,238,0.04);
}
.metric-card::before {
  content: '';
  position: absolute;
  left: 0; top: 14%; bottom: 14%;
  width: 3px;
  border-radius: 0 3px 3px 0;
  background: transparent;
}
.metric-card::after {
  content: '';
  position: absolute;
  top: -1px; right: -1px;
  width: 12px; height: 12px;
  border-top: 2px solid var(--line-strong);
  border-right: 2px solid var(--line-strong);
}
.metric-card.tone-good { border-color: rgba(45,212,167,0.40); box-shadow: inset 0 0 22px rgba(45,212,167,0.06); }
.metric-card.tone-good::before { background: var(--good); box-shadow: 0 0 8px var(--good); }
.metric-card.tone-good::after { border-color: rgba(45,212,167,0.65); }
.metric-card.tone-good .metric-value { color: var(--good-text); text-shadow: 0 0 14px rgba(45,212,167,0.45); }
.metric-card.tone-bad { border-color: rgba(251,113,133,0.40); box-shadow: inset 0 0 22px rgba(251,113,133,0.06); }
.metric-card.tone-bad::before { background: var(--bad); box-shadow: 0 0 8px var(--bad); }
.metric-card.tone-bad::after { border-color: rgba(251,113,133,0.65); }
.metric-card.tone-bad .metric-value { color: var(--bad-text); text-shadow: 0 0 14px rgba(251,113,133,0.45); }
.metric-card.tone-warn { border-color: rgba(251,191,36,0.40); box-shadow: inset 0 0 22px rgba(251,191,36,0.05); }
.metric-card.tone-warn::before { background: var(--warn); box-shadow: 0 0 8px var(--warn); }
.metric-card.tone-warn::after { border-color: rgba(251,191,36,0.65); }
.metric-card.tone-warn .metric-value { color: var(--warn-text); text-shadow: 0 0 14px rgba(251,191,36,0.40); }
.metric-card.tone-accent { border-color: var(--line-strong); }
.metric-card.tone-accent::before { background: var(--accent-page); box-shadow: 0 0 8px var(--accent-page); }
.metric-label { color: #8fb6cf; font-size: 0.84rem; margin-bottom: 0.3rem; letter-spacing: 0.03em; }
.metric-value {
  color: #eafcff;
  font-size: 1.78rem;
  font-weight: 800;
  line-height: 1.12;
  font-variant-numeric: tabular-nums;
  text-shadow: 0 0 14px var(--glow);
}
.metric-delta {
  display: inline-block;
  margin-top: 0.5rem;
  padding: 0.18rem 0.55rem;
  border-radius: 999px;
  font-size: 0.8rem;
  font-weight: 700;
  color: #d8e6ff;
  background: rgba(255,255,255,0.07);
  border: 1px solid rgba(255,255,255,0.10);
}
.metric-delta.d-up { color: var(--good-text); background: var(--good-soft); border-color: rgba(45,212,167,0.35); }
.metric-delta.d-down { color: var(--bad-text); background: var(--bad-soft); border-color: rgba(251,113,133,0.35); }
.metric-help {
  color: var(--text-3);
  font-size: 0.78rem;
  line-height: 1.35;
  margin-top: 0.5rem;
  white-space: normal;
  word-break: break-word;
}

/* ── 区块标题：大屏式面板头（左标记 + 右延伸线）── */
.section-title {
  display: flex;
  align-items: center;
  gap: 0.55rem;
  color: var(--text-1);
  font-size: 1.05rem;
  font-weight: 700;
  letter-spacing: 0.05em;
  margin-top: 0.5rem;
  margin-bottom: 0.25rem;
}
.section-title::before {
  content: '';
  width: 4px;
  height: 1.0em;
  background: var(--accent-page);
  box-shadow: 0 0 8px var(--accent-page);
  flex: 0 0 auto;
}
.section-title::after {
  content: '';
  flex: 1 1 auto;
  height: 1px;
  margin-left: 0.6rem;
  background: linear-gradient(90deg, var(--line-strong) 0%, rgba(0,0,0,0) 85%);
}
.section-subtitle {
  color: var(--text-3);
  font-size: 0.84rem;
  margin-bottom: 0.55rem;
}
.info-chip {
  background: rgba(42, 55, 20, 0.65);
  border: 1px solid rgba(220, 214, 82, 0.24);
  color: #f3edbb;
  border-radius: 12px;
  padding: 0.8rem 0.95rem;
  margin: 0.45rem 0 0.9rem 0;
}
.filter-note {
  background: rgba(22, 33, 58, 0.72);
  border: 1px dashed rgba(115, 156, 255, 0.35);
  color: #d8e6ff;
  border-radius: 12px;
  padding: 0.7rem 0.85rem;
  margin: 0.35rem 0 0.8rem 0;
}
.tooltip-note {
  color: #f4e6a5;
  font-weight: 700;
}
div[data-testid="stTabs"] button {
  border-radius: 4px !important;
  border: 1px solid var(--line) !important;
  background: rgba(7, 18, 36, 0.75) !important;
  color: #c9e6f5 !important;
  padding: 0.4rem 1rem !important;
  margin-right: 0.4rem !important;
}
div[data-testid="stTabs"] button[aria-selected="true"] {
  border-color: var(--accent-page) !important;
  box-shadow: 0 0 12px var(--glow);
}
button[kind="secondaryFormSubmit"] { border-radius: 6px !important; }
[data-testid="stDataFrame"] {
  border: 1px solid var(--line);
  border-radius: 5px;
  overflow: hidden;
}

/* ── 面板卡：st.container(border=True) 重绘成大屏 panel（角标 + 内光）── */
[data-testid="stVerticalBlockBorderWrapper"] {
  position: relative;
  background: linear-gradient(180deg, rgba(9,23,44,0.60) 0%, rgba(5,13,26,0.72) 100%);
  border: 1px solid var(--line) !important;
  border-radius: 5px !important;
  padding: 0.85rem 0.95rem 0.5rem !important;
  box-shadow: inset 0 0 28px rgba(34,211,238,0.04);
}
[data-testid="stVerticalBlockBorderWrapper"]::before {
  content: '';
  position: absolute;
  top: -1px; left: -1px;
  width: 14px; height: 14px;
  border-top: 2px solid var(--line-strong);
  border-left: 2px solid var(--line-strong);
  pointer-events: none;
}
[data-testid="stVerticalBlockBorderWrapper"]::after {
  content: '';
  position: absolute;
  bottom: -1px; right: -1px;
  width: 14px; height: 14px;
  border-bottom: 2px solid var(--line-strong);
  border-right: 2px solid var(--line-strong);
  pointer-events: none;
}
[data-testid="stVerticalBlockBorderWrapper"] [data-testid="stVerticalBlockBorderWrapper"] {
  background: rgba(6, 14, 28, 0.45);
}
[data-testid="stVerticalBlockBorderWrapper"] .metric-card {
  background: rgba(6, 14, 28, 0.55);
}

/* ── 输入控件统一暗色科技风 ── */
[data-testid="stNumberInput"] input,
[data-testid="stDateInput"] input,
[data-testid="stTextInput"] input {
  background: rgba(7, 18, 36, 0.9) !important;
  border-radius: 4px !important;
  color: var(--text-1) !important;
}
[data-baseweb="select"] > div {
  background: rgba(7, 18, 36, 0.9) !important;
  border-radius: 4px !important;
}
[data-testid="stNumberInput"] button { background: rgba(12, 28, 52, 0.85) !important; }
[data-testid="stFileUploader"] section {
  background: rgba(7, 18, 36, 0.6) !important;
  border: 1px dashed var(--line-strong) !important;
  border-radius: 5px !important;
}
[data-testid="stWidgetLabel"] p { color: var(--text-2) !important; font-size: 0.84rem !important; }
[data-testid="stCaptionContainer"] { color: var(--text-3) !important; }
hr { border-color: var(--line) !important; margin: 0.8rem 0 !important; }
</style>
""",
    unsafe_allow_html=True,
)

# ── 自定义图表主题（全站统一）：透明底融入面板卡、细网格、统一字体与悬浮样式 ──
import plotly.io as pio

_ops_template = go.layout.Template(pio.templates["plotly_dark"])
_ops_template.layout.update(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(
        family='-apple-system, "Segoe UI", "PingFang SC", "Microsoft YaHei", sans-serif',
        size=12,
        color="#9fc1d9",
    ),
    title=dict(font=dict(color="#e8f7ff", size=14)),
    margin=dict(l=14, r=14, t=36, b=14),
    hoverlabel=dict(
        bgcolor="#0a1d36",
        bordercolor="rgba(34,211,238,0.45)",
        font=dict(color="#e8f7ff", size=12),
    ),
    xaxis=dict(
        gridcolor="rgba(56,189,248,0.07)",
        zeroline=False,
        linecolor="rgba(56,189,248,0.22)",
        tickfont=dict(size=11),
    ),
    yaxis=dict(
        gridcolor="rgba(56,189,248,0.07)",
        zeroline=False,
        linecolor="rgba(0,0,0,0)",
        tickfont=dict(size=11),
    ),
    legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(size=11)),
    colorway=[CYAN, "#3B82F6", GREEN, PURPLE, AMBER, RED, "#38BDF8", "#34D399"],
    bargap=0.35,
)
try:
    _ops_template.layout.barcornerradius = 4  # plotly>=5.19 圆角柱状图，旧版自动跳过
except Exception:
    pass
pio.templates["ops_dark"] = _ops_template
pio.templates.default = "ops_dark"
TEMPLATE = "ops_dark"

# 各页强调色（页头色条 / 区块标记 / 导航选中态）：统一大屏冷色科技系，页间微差
PAGE_ACCENTS = {
    "经营总览": "#22D3EE",
    "红利分析": "#38BDF8",
    "红利 ROI & 代理质量": "#3B82F6",
    "代理佣金 & 退成": "#6366F1",
    "会员结构 & ARPU": "#A78BFA",
    "投注分析": "#8B5CF6",
    "客服分析": "#C084FC",
    "电访召回": "#7DD3FC",
    "实时波动 & DAU": "#2DD4A7",
    "代理团队 & 渠道": "#34D399",
    "代理 × 会员 明细": "#4ADE80",
    "游戏 & 场馆": "#10B981",
    # hero 标题别名（与导航名不同的页头标题）
    "渠道与代理": "#34D399",
    "游戏与场馆": "#10B981",
    "会员价值": "#A78BFA",
    "实时波动": "#2DD4A7",
    "代理佣金深度分析": "#6366F1",
    "投注分析（2026 年 4 月）": "#8B5CF6",
}

METRIC_META = {
    "公司输赢": {"source": "raw_platform_report", "fields": ["公司输赢"], "formula": "直接汇总原始字段【公司输赢】"},
    "有效投注额": {"source": "raw_platform_report", "fields": ["有效投注额"], "formula": "直接汇总原始字段【有效投注额】"},
    "存提差": {"source": "raw_platform_report / raw_finance_report", "fields": ["存提差"], "formula": "直接汇总原始字段【存提差】"},
    "实际总存款": {"source": "raw_finance_report", "fields": ["实际总存款"], "formula": "直接汇总原始字段【实际总存款】"},
    "首存转化率": {"source": "raw_platform_report", "fields": ["首存人数", "注册数"], "formula": "当前筛选范围内：首存人数 ÷ 注册数"},
    "公司收入": {"source": "raw_member_report", "fields": ["公司收入"], "formula": "当前直接汇总原始字段【公司收入】，不在前端做二次推导"},
    "TOP20投注占比": {"source": "raw_top_report", "fields": ["有效投注额", "_snapshot_month"], "formula": "当前快照月份：TOP20 有效投注额 ÷ 全部快照有效投注额"},
    "次月活跃留存率": {
        "source": "raw_member_report（需含 _snapshot_month）",
        "fields": ["会员账号", "存款额", "有效投注额", "_snapshot_month"],
        "formula": (
            "活跃定义：该月存款额 > 0 或有效投注额 > 0。"
            "计算：本月活跃会员中，次月仍为活跃的比例。"
            "公式 = COUNT(本月活跃 ∩ 次月活跃) ÷ COUNT(本月活跃)。"
            "卡片显示最近一期（如 2月→3月）的值，非平均值。"
            "注意：计算前会先套用当前筛选条件（默认：会员状态=启用、是否为代理=非代理）。"
        ),
    },
    "次月存款留存率": {
        "source": "raw_member_report（需含 _snapshot_month）",
        "fields": ["会员账号", "存款额", "_snapshot_month"],
        "formula": (
            "存款定义：该月存款额 > 0。"
            "计算：本月有存款的会员中，次月仍有存款的比例。"
            "公式 = COUNT(本月有存款 ∩ 次月有存款) ÷ COUNT(本月有存款)。"
            "卡片显示最近一期的值。"
            "注意：计算前会先套用当前筛选条件（默认：会员状态=启用、是否为代理=非代理）。"
        ),
    },
    "首存用户次月留存率": {
        "source": "raw_member_report（需含 _snapshot_month、首存时间）",
        "fields": ["会员账号", "首存时间", "存款额", "有效投注额", "_snapshot_month"],
        "formula": (
            "首存用户定义：首存时间落在该快照月份内的会员。"
            "次月活跃定义：次月存款额 > 0 或有效投注额 > 0。"
            "计算：本月首存用户中，次月仍为活跃的比例。"
            "公式 = COUNT(本月首存用户 ∩ 次月活跃) ÷ COUNT(本月首存用户)。"
            "卡片显示最近一期的值。"
            "注意：计算前会先套用当前筛选条件（默认：会员状态=启用、是否为代理=非代理）。"
        ),
    },
    "ARPU（用户均收）": {
        "source": "raw_member_report",
        "fields": ["公司收入", "会员账号"],
        "formula": (
            "ARPU（Average Revenue Per User，用户均收）= SUM(公司收入) ÷ DISTINCT(会员账号)。"
            "口径与当前筛选完全一致（含 VIP 等级、用户来源、会员状态、是否为代理等）。"
            "面板默认排除代理账号、仅看启用会员，避免被代理流水稀释。"
        ),
    },
    "日投注人次（DAU 近似）": {
        "source": "raw_realtime_bet",
        "fields": ["日期", "时段", "时段投注人数"],
        "formula": (
            "日投注人次 = 当日所有时段「时段投注人数」加总。"
            "是 DAU（Daily Active Users，日活跃用户数）的近似值——实时表是按【日期 × 时段 × 游戏类型】聚合的，"
            "同一会员若跨时段或跨游戏类型出现会被重复计入，所以严格意义不是去重后的 DAU。"
            "要拿到精准 DAU 需新增「每会员每日活跃」明细表。"
        ),
    },
    "退成（介绍人佣金分成）": {
        "source": "客服主管月报（手动汇整 / 4 月代理帐 xlsx）",
        "fields": ["业绩总额", "退成比例", "实际佣金"],
        "formula": (
            "退成（亦称「介绍人引荐分成」）：介绍人从其推荐下线代理之「业绩总额」中，"
            "按固定比例额外获取之佣金。该笔佣金由平台独立派发，"
            "与下线代理之主佣金互不影响、互不抵销。\n\n"
            "核心定义：\n"
            "• 业绩总额 = 下线代理当月所有有效业务产生之累计金额（与主佣金共用同一基础数据）\n"
            "• 主佣金 = 下线代理依其合约比例领取之常态月佣金（一般为业绩 × 55%）\n"
            "• 退成 = 平台在主佣金之外，额外支付给介绍人之分成，不从下线之主佣金中扣除\n"
            "• 叠付 = 主佣金 + 退成 皆由平台承担，平台之单笔业绩成本系两者「相加」（叠付），非「嵌套」\n\n"
            "退成比例分档（依 2026 年 4 月代理帐实际派发记录）：\n"
            "• 引荐分成（基础档）业绩 × 1% — 较远端引荐链\n"
            "• 标准退成 业绩 × 3% – 5% — 常态档位（占多数）\n"
            "• 新代理特殊安排 业绩 × 30% — 仅限特定新代理与平台之个案约定\n\n"
            "平台单笔业绩之总成本：\n"
            "• 常态：主佣金 55% + 退成 1–5% = 56% – 60%\n"
            "• 特殊：主佣金 55% + 退成 30% = 85%\n\n"
            "对照举例（2026-04 代理帐）：\n"
            "• YU → 豪Hao：业绩 246,971 → 主佣金 135,834（55%）+ 退成 12,349（5%）= 平台总支出 148,183（60%）\n"
            "• 咪娜 → 咬咬咬：业绩 285,386 → 主佣金 156,963（55%）+ 退成 8,562（3%）= 平台总支出 165,525（58%）\n"
            "• 豪Hao → 八万：业绩 374,806 → 主佣金 206,143（55%）+ 退成 3,748（1%）= 平台总支出 209,891（56%）"
        ),
    },
}


@dataclass
class FilterNotice:
    title: str
    detail: str


@st.cache_data(ttl=300)
def query_bq(sql: str) -> pd.DataFrame:
    client = get_bq_client()
    df = client.query(sql).to_dataframe()
    return normalize_dataframe(df)


@st.cache_data(ttl=300)
def load_table(table_name: str) -> pd.DataFrame:
    """读取 BigQuery 表。表还没建立时返回空表，避免新项目第一次打开页面直接 404。"""
    sql = f"SELECT * FROM `{BQ_PREFIX}.{table_name}`"
    try:
        return query_bq(sql)
    except Exception:
        return pd.DataFrame()


def normalize_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    for col in out.columns:
        if col in TEXT_COLUMNS:
            continue
        if pd.api.types.is_numeric_dtype(out[col]):
            continue
        out[col] = pd.to_numeric(out[col], errors="coerce")
    return out


def clean_text_series(s: pd.Series) -> pd.Series:
    return s.astype(str).str.strip().replace({"nan": None, "None": None, "": None})


def to_datetime_safe(series: pd.Series) -> pd.Series:
    s = series.copy()
    if s.dtype == object:
        s = s.astype(str).str.replace('="', '', regex=False).str.replace('"', '', regex=False)
    return pd.to_datetime(s, errors="coerce")

def show_metric(card_col, label: str, value: str, delta: Optional[str] = None, help_text: Optional[str] = None,
                tone: Optional[str] = None, delta_tone: str = 'auto'):
    """指标卡。tone: good/bad/warn/accent 上状态色；delta_tone: auto(按±符号着色)/up/down/flat。"""
    tone_cls = f' tone-{tone}' if tone in ('good', 'bad', 'warn', 'accent') else ''
    delta_html = ''
    if delta:
        d = delta_tone
        if d == 'auto':
            ds = str(delta).strip()
            if ds.startswith(('+', '▲', '↑')):
                d = 'up'
            elif ds.startswith(('-', '▼', '↓')):
                d = 'down'
            else:
                d = 'flat'
        elif d in ('good',):
            d = 'up'
        elif d in ('bad',):
            d = 'down'
        elif d not in ('up', 'down'):
            d = 'flat'
        delta_html = f'<div class="metric-delta d-{d}">{escape(str(delta))}</div>'
    help_html = f'<div class="metric-help">{escape(help_text)}</div>' if help_text else ''
    html = (
        f'<div class="metric-card{tone_cls}">'
        f'<div class="metric-label">{escape(label)}</div>'
        f'<div class="metric-value">{escape(str(value))}</div>'
        f'{delta_html}'
        f'{help_html}'
        f'</div>'
    )
    with card_col:
        st.markdown(html, unsafe_allow_html=True)


def status_badge(text: str, tone: Optional[str] = None) -> str:
    """返回状态徽章 HTML（嵌进 badge-row / hero 用）。tone: good/bad/warn/None。"""
    cls = f'badge badge-{tone}' if tone in ('good', 'bad', 'warn') else 'badge'
    return f'<span class="{cls}">{escape(str(text))}</span>'


def section_header(title: str, subtitle: str = ""):
    st.markdown(f'<div class="section-title">{title}</div>', unsafe_allow_html=True)
    if subtitle:
        st.markdown(f'<div class="section-subtitle">{subtitle}</div>', unsafe_allow_html=True)



def hero(title: str, subtitle: str, updated_at: Optional[str] = None, extra_badges: Optional[List[str]] = None,
         basis: Optional[str] = None, detail: Optional[str] = None, source_badge: Optional[str] = None):
    """basis：标题下一行中文「数据基础」灰字（一眼看的）。
    detail：折叠「数据详情」markdown（想深入的点开，可放来源表/口径/更新方式）。
    source_badge：首个徽章文字，默认「数据库：BigQuery」；读谷歌表的页可传中文来源。"""
    accent = PAGE_ACCENTS.get(title)
    if accent:
        st.markdown(f'<style>:root {{ --accent-page: {accent}; }}</style>', unsafe_allow_html=True)
    badges = [f'<span class="badge">{escape(source_badge or "数据库：BigQuery")}</span>']
    if updated_at:
        badges.append(f'<span class="badge">最近更新：{updated_at}</span>')
    if extra_badges:
        badges.extend(extra_badges)
    basis_html = ''
    if basis:
        basis_html = (f'<div style="margin-top:.55rem;font-size:.82rem;color:#9fb3c8;'
                      f'line-height:1.55;">📊 数据基础：{escape(basis)}</div>')
    html = (
        '<div class="hero-card">'
        f'<div class="badge-row">{"".join(badges)}</div>'
        f'<div class="hero-title">{escape(title)}</div>'
        f'<div class="hero-subtitle">{escape(subtitle)}</div>'
        f'{basis_html}'
        '</div>'
    )
    st.markdown(html, unsafe_allow_html=True)
    if detail:
        with st.expander('ℹ️ 数据详情（来源 / 口径 / 更新方式）'):
            st.markdown(detail)


def latest_imported_at(*dfs: pd.DataFrame) -> str:
    vals = []
    for df in dfs:
        if '_imported_at' in df.columns:
            ts = to_datetime_safe(df['_imported_at'])
            if ts.notna().any():
                vals.append(ts.max())
    if not vals:
        return ""  # 没有 _imported_at（如早期 import 灌的红利表）→ 不显示「最近更新」徽章，比显示「未提供」干净
    return max(vals).strftime("%Y-%m-%d %H:%M")


def date_range_picker(df: pd.DataFrame, date_col: str, key_prefix: str, default_last_days: Optional[int] = None) -> Tuple[pd.DataFrame, Optional[pd.Timestamp], Optional[pd.Timestamp], Optional[str]]:
    """全站统一日期筛选：快捷预设(全部/本月/上月/近7天/近30天)或自订日期，单选不互相盖。
    跟「新注册分析」同款口径。返回 (筛后df, start_ts, end_ts, sel_month)，
    sel_month 只在选「本月/上月」这种单一自然月时给 'YYYY-MM'，其余为 None（呼叫端据此决定要不要按月切第二张表）。"""
    import datetime as _dt
    if date_col not in df.columns:
        return df, None, None, None
    out = df.copy()
    out[date_col] = to_datetime_safe(out[date_col])
    out = out[out[date_col].notna()].copy()
    if out.empty:
        return out, None, None, None
    min_d = out[date_col].min().date()
    max_d = out[date_col].max().date()
    first_this = max_d.replace(day=1)
    prev_last = first_this - _dt.timedelta(days=1)
    prev_first = prev_last.replace(day=1)
    presets = {
        '全部': (min_d, max_d, None),
        '本月': (max(min_d, first_this), max_d, first_this.strftime('%Y-%m')),
        '上月': (max(min_d, prev_first), min(max_d, prev_last), prev_first.strftime('%Y-%m')),
        '近7天': (max(min_d, max_d - _dt.timedelta(days=6)), max_d, None),
        '近30天': (max(min_d, max_d - _dt.timedelta(days=29)), max_d, None),
    }
    keys = list(presets.keys()) + ['自订日期']
    default_pick = '近30天' if default_last_days == 30 else ('近7天' if default_last_days == 7 else '全部')
    pick = st.radio('快速选择', keys, index=keys.index(default_pick),
                    horizontal=True, key=f'{key_prefix}_pick')
    if pick == '自订日期':
        c1, c2 = st.columns(2)
        with c1:
            start = st.date_input('开始日期', value=min_d, min_value=min_d, max_value=max_d, key=f'{key_prefix}_start')
        with c2:
            end = st.date_input('结束日期', value=max_d, min_value=min_d, max_value=max_d, key=f'{key_prefix}_end')
        sel_month = None
    else:
        start, end, sel_month = presets[pick]
    if start > end:
        start, end = end, start
    start_ts = pd.Timestamp(start)
    mask_end = pd.Timestamp(end) + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)
    out = out[(out[date_col] >= start_ts) & (out[date_col] <= mask_end)].copy()
    st.caption(f'📅 当前显示 {start} ~ {end}，共 {len(out)} 条。改上面就立刻跟着变。')
    return out, start_ts, pd.Timestamp(end), sel_month


def apply_multiselect(df: pd.DataFrame, col: str, label: str, key: str, default_all: bool = True,
                      options_df: pd.DataFrame = None, auto_include_new: bool = True) -> pd.DataFrame:
    if col not in df.columns:
        return df
    # 选项来源用 options_df（通常是「未经其他筛选的全量」），让选项清单跨筛选/日期保持稳定，
    # 避免 Streamlit 多选框因选项集变动而保留旧选择、把新出现的值默默漏掉（会造成总数对不上）。
    src = options_df if options_df is not None else df
    if col not in src.columns:
        src = df
    options = [x for x in sorted(src[col].dropna().astype(str).unique().tolist()) if x not in ("", "nan", "None")]
    if not options:
        return df
    # auto_include_new：当数据新增了以前没有的值（如上传了带新域名的报表），
    # 自动把这些新值补进当前勾选，确保「没主动取消的东西永远默认显示」，根治 stale-default 漏算。
    if auto_include_new and default_all and key in st.session_state:
        seen_key = f'_{key}_seen'
        prev = st.session_state.get(seen_key, options)
        new_opts = [o for o in options if o not in prev]
        if new_opts:
            cur = [o for o in st.session_state.get(key, []) if o in options]
            st.session_state[key] = cur + new_opts
    st.session_state[f'_{key}_seen'] = options
    default = options if default_all else options[: min(8, len(options))]
    selected = st.multiselect(label, options, default=default, key=key)
    if selected:
        return df[df[col].astype(str).isin(selected)].copy()
    return df.iloc[0:0].copy()


def add_info_box(notices: List[FilterNotice]):
    if not notices:
        return
    lines = [f"<span class='tooltip-note'>!</span> <strong>{n.title}</strong>：{n.detail}" for n in notices]
    st.markdown(f"<div class='filter-note'>{'<br>'.join(lines)}</div>", unsafe_allow_html=True)


def tooltip_text(metric_name: str) -> str:
    meta = METRIC_META.get(metric_name)
    if not meta:
        return ""
    return f"来源：{meta['source']}"


def normalize_month_key(series: pd.Series) -> pd.Series:
    s = series.copy()
    s = s.astype(str).str.strip()
    s = s.replace({"nan": None, "None": None, "": None})
    mask = s.notna() & s.str.fullmatch(r"\d{6}")
    s.loc[mask] = s.loc[mask].str.slice(0, 4) + "-" + s.loc[mask].str.slice(4, 6)
    return s




def month_start_end(month_key: str) -> Tuple[pd.Timestamp, pd.Timestamp]:
    start = pd.Timestamp(f"{month_key}-01")
    end = (start + pd.offsets.MonthEnd(1)).normalize()
    return start, end

def get_snapshot_month(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    if '_snapshot_month' in out.columns:
        out['__snapshot_month__'] = normalize_month_key(out['_snapshot_month'])
        return out
    if '_snapshot_date' in out.columns:
        dt = to_datetime_safe(out['_snapshot_date'])
        out['__snapshot_month__'] = dt.dt.strftime('%Y-%m')
        return out
    out['__snapshot_month__'] = None
    return out


def has_member_snapshot(df: pd.DataFrame) -> bool:
    if '_snapshot_month' in df.columns:
        s = normalize_month_key(df['_snapshot_month'])
        if s.notna().any():
            return True
    if '_snapshot_date' in df.columns:
        s = to_datetime_safe(df['_snapshot_date'])
        if s.notna().any():
            return True
    return False


def member_default_filters(df: pd.DataFrame) -> Tuple[pd.DataFrame, List[FilterNotice], Dict[str, List[str]]]:
    notices: List[FilterNotice] = []
    current = {}
    out = df.copy()
    # defaults only if fields exist
    if '会员状态' in out.columns:
        opts = sorted(out['会员状态'].dropna().astype(str).unique())
        default = ['启用'] if '启用' in opts else opts
        sel = st.multiselect('会员状态', opts, default=default, key='mv_status')
        if set(sel) != set(opts):
            notices.append(FilterNotice('当前已应用会员状态筛选', f"仅保留：{' / '.join(sel)}"))
        out = out[out['会员状态'].astype(str).isin(sel)] if sel else out.iloc[0:0].copy()
        current['会员状态'] = sel
    if '是否为代理' in out.columns:
        opts = sorted(out['是否为代理'].dropna().astype(str).unique())
        default = ['非代理'] if '非代理' in opts else opts
        sel = st.multiselect('是否为代理', opts, default=default, key='mv_is_agent')
        if set(sel) != set(opts):
            notices.append(FilterNotice('当前已应用是否为代理筛选', f"仅保留：{' / '.join(sel)}"))
        out = out[out['是否为代理'].astype(str).isin(sel)] if sel else out.iloc[0:0].copy()
        current['是否为代理'] = sel
    if '用户来源' in out.columns:
        opts = sorted(out['用户来源'].dropna().astype(str).unique())
        sel = st.multiselect('用户来源', opts, default=opts, key='mv_user_source')
        out = out[out['用户来源'].astype(str).isin(sel)] if sel else out.iloc[0:0].copy()
        current['用户来源'] = sel

    with st.expander('高级筛选', expanded=False):
        cols = st.columns(3)
        with cols[0]:
            if 'VIP等级' in out.columns:
                out = apply_multiselect(out, 'VIP等级', 'VIP等级', 'mv_vip')
        with cols[1]:
            if '注册来源' in out.columns:
                out = apply_multiselect(out, '注册来源', '注册来源', 'mv_reg_source')
        with cols[2]:
            if '代理' in out.columns:
                agent_options = [x for x in sorted(out['代理'].dropna().astype(str).unique().tolist()) if x not in ('', 'nan', 'None')]
                if agent_options:
                    selected = st.multiselect('代理', agent_options, default=[], key='mv_agent')
                    if selected:
                        out = out[out['代理'].astype(str).isin(selected)].copy()
        if '用户标签' in out.columns:
            keyword = st.text_input('用户标签包含关键字', key='mv_tag_kw')
            if keyword:
                out = out[out['用户标签'].astype(str).str.contains(keyword, na=False)].copy()
    return out, notices, current


def render_metric_explainer(page_metrics: List[str]):
    with st.expander('本页指标口径说明', expanded=False):
        for name in page_metrics:
            meta = METRIC_META.get(name)
            if not meta:
                continue
            st.markdown(f"**{name}**")
            st.write(f"来源表：{meta['source']}")
            st.write(f"来源字段：{'、'.join(meta['fields'])}")
            st.write(f"口径：{meta['formula']}")
            st.markdown('---')


def compute_monthly_retention(member_df: pd.DataFrame) -> Optional[pd.DataFrame]:
    required = {'会员账号'}
    if not required.issubset(member_df.columns):
        return None
    df = member_df.copy()
    if '_snapshot_month' in df.columns:
        df['__snapshot_month__'] = normalize_month_key(df['_snapshot_month'])
    elif '_snapshot_date' in df.columns:
        df['__snapshot_month__'] = to_datetime_safe(df['_snapshot_date']).dt.strftime('%Y-%m')
    else:
        return None
    if df['__snapshot_month__'].isna().all():
        return None
    # 会员身份键含代理（同名挂不同代理=不同人），与 member_count / 矩阵口径一致
    if '代理' in df.columns:
        df['__account__'] = df['会员账号'].astype(str) + '\x01' + df['代理'].astype(str)
    else:
        df['__account__'] = df['会员账号'].astype(str)
    if '存款额' in df.columns:
        df['__has_deposit__'] = pd.to_numeric(df['存款额'], errors='coerce').fillna(0) > 0
    else:
        df['__has_deposit__'] = False
    if '有效投注额' in df.columns:
        df['__has_valid_bet__'] = pd.to_numeric(df['有效投注额'], errors='coerce').fillna(0) > 0
    else:
        df['__has_valid_bet__'] = False
    df['__is_active__'] = df['__has_deposit__'] | df['__has_valid_bet__']

    if '首存时间' in df.columns:
        first_deposit_month = to_datetime_safe(df['首存时间']).dt.strftime('%Y-%m')
        df['__is_first_deposit_month__'] = first_deposit_month == df['__snapshot_month__']
    else:
        df['__is_first_deposit_month__'] = False

    per_month = []
    months = sorted([m for m in df['__snapshot_month__'].dropna().unique().tolist()])
    for i in range(len(months) - 1):
        m = months[i]
        next_m = months[i + 1]
        cur = df[df['__snapshot_month__'] == m].copy()
        nxt = df[df['__snapshot_month__'] == next_m].copy()
        nxt_accounts = set(nxt['__account__'])
        nxt_active = set(nxt.loc[nxt['__is_active__'], '__account__'])
        nxt_deposit = set(nxt.loc[nxt['__has_deposit__'], '__account__'])

        cur_active = set(cur.loc[cur['__is_active__'], '__account__'])
        cur_deposit = set(cur.loc[cur['__has_deposit__'], '__account__'])
        cur_first = set(cur.loc[cur['__is_first_deposit_month__'], '__account__'])

        active_ret = len(cur_active & nxt_active) / len(cur_active) if cur_active else None
        deposit_ret = len(cur_deposit & nxt_deposit) / len(cur_deposit) if cur_deposit else None
        first_ret = len(cur_first & nxt_active) / len(cur_first) if cur_first else None

        per_month.append({
            '月份': m,
            '次月': next_m,
            '次月活跃留存率': active_ret,
            '次月存款留存率': deposit_ret,
            '首存用户次月留存率': first_ret,
            '本月活跃会员数': len(cur_active),
            '本月存款会员数': len(cur_deposit),
            '本月首存用户数': len(cur_first),
        })
    return pd.DataFrame(per_month)


def parse_realtime_time(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    if '时间' not in out.columns:
        return out
    raw = out['时间'].astype(str).str.replace('="', '', regex=False).str.replace('"', '', regex=False).str.strip()
    # try patterns like 2026-01-31 23~24
    date_part = raw.str.extract(r'^(\d{4}-\d{2}-\d{2})')[0]
    slot_part = raw.str.extract(r'(\d{1,2}~\d{1,2})')[0]
    parsed_date = pd.to_datetime(date_part, errors='coerce')
    # fallback if already normal datetime
    fallback = pd.to_datetime(raw, errors='coerce')
    parsed_date = parsed_date.fillna(fallback.dt.normalize())
    out['日期'] = parsed_date
    out['时段'] = slot_part.fillna(fallback.dt.strftime('%H:00').where(fallback.notna()))
    return out


def _venue_category(name) -> str:
    s = str(name)
    if '真人' in s: return '真人'
    if '体育' in s or '體育' in s: return '体育'
    if '电竞' in s or '電競' in s: return '电竞'
    if '电子' in s or '電子' in s or '老虎' in s or 'PG' in s.upper() or 'PP' in s.upper(): return '电子'
    if '棋牌' in s: return '棋牌'
    if '捕鱼' in s or '捕魚' in s: return '捕鱼'
    if '哈希' in s or 'hash' in s.lower(): return '哈希'
    if '彩' in s: return '彩票'
    return '其他'


def _gsheet_client():
    import gspread
    from google.oauth2 import service_account
    creds = service_account.Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=["https://www.googleapis.com/auth/spreadsheets.readonly",
                "https://www.googleapis.com/auth/drive.readonly"])
    return gspread.authorize(creds)


def _recent_month_labels(n=3):
    import datetime as _dt
    today = _dt.date.today()
    y, m, labs = today.year, today.month, []
    for _ in range(n):
        labs.append(f"{y}年{m}月 运营日报")
        m -= 1
        if m == 0:
            m, y = 12, y - 1
    return tuple(labs)


@st.cache_data(ttl=600)
def load_daily_ops(month_labels: tuple) -> pd.DataFrame:
    """读「运营日报」谷歌表 各月份 sheet 的「平台报表」分页，合并成每日 df。"""
    gc = _gsheet_client()
    frames = []
    for lab in month_labels:
        try:
            ws = gc.open(lab).worksheet("平台报表")
            recs = ws.get_all_records()
            if recs:
                frames.append(pd.DataFrame(recs))
        except Exception:
            continue
    if not frames:
        return pd.DataFrame()
    df = pd.concat(frames, ignore_index=True)
    if "日期" not in df.columns:
        return pd.DataFrame()
    df = df[df["日期"].astype(str).str.match(r"\d{4}-\d{2}-\d{2}")].copy()
    for c in df.columns:
        if c == "日期":
            continue
        df[c] = pd.to_numeric(
            df[c].astype(str).str.replace("%", "", regex=False).str.replace(",", "", regex=False),
            errors="coerce")
    return df.drop_duplicates(subset="日期", keep="last").sort_values("日期").reset_index(drop=True)


# 1 finance page implementation moved to features/finance_results.py

# 1 finance page implementation moved to features/finance_results.py


# V6.4: render_channel_agent moved to features/agent_channel.py



# V6.4: render_game_venue moved to features/agent_channel.py


def source_note(origin_html: str):
    """页面顶部「数据来源」说明 — 给接手的人看：后台从哪导、怎么导、多久一次。
    （延续 Miru『我走了也要有人能运作』原则：每页都该标清楚来源，不靠记忆/不靠问人。）"""
    st.markdown(
        '<div style="background:rgba(56,189,248,0.08);border-left:3px solid #38bdf8;'
        'border-radius:6px;padding:0.55rem 0.85rem;margin:0.1rem 0 0.9rem;'
        'font-size:0.86rem;line-height:1.65;color:#b6c5e1;">'
        '📂 <b style="color:#e2e8f0;">数据来源（怎么更新）</b>：' + origin_html +
        '</div>', unsafe_allow_html=True)


# 1 finance page implementation moved to features/finance_results.py

# ── 投注分析(月度注单明细,每月一张 raw_bet_detail_YYYY_MM 表) ──────────────────────────


# V6.4: render_agent_member_matrix moved to features/agent_channel.py


# 对话内容按「发言人>时间戳 :」切分成轮次
_CS_TURN_RE = re.compile(r'\n\s*([^\n>]{1,40})>\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}\s*:')


def cs_member_text(content, agent) -> str:
    """只抽取「会员(访客)」说的话，剔除 系统 自动消息 + 接待客服 的话术/模板开场。
    每段对话都以一长串系统提醒 + 客服欢迎模板开头(含 提款/返水/VIP/体育/下载/注册 等词),
    若直接扫全文,这些词会在每笔对话里命中,把热点图顶到天花板。去掉非会员发言后才是真实问题。"""
    s = str(content)
    parts = _CS_TURN_RE.split(s)
    # parts[0] = 开场白("对话开始>>..."), 之后是 [发言人, 内容, 发言人, 内容, ...]
    if len(parts) < 3:
        return ''  # 解析不出轮次,宁可空也不要把模板算进去
    agent = str(agent).strip()
    keep = []
    for i in range(1, len(parts) - 1, 2):
        speaker = parts[i].strip()
        if speaker == '系统' or (agent and speaker == agent):
            continue
        keep.append(parts[i + 1])
    return ' '.join(keep)


def _wb_num(x) -> float:
    if x is None:
        return 0.0
    t = str(x).strip().replace(',', '').replace('，', '')
    if t in ('', 'nan', 'None', '-', '—'):
        return 0.0
    try:
        return float(t)
    except ValueError:
        return 0.0


def _wb_yes(x) -> bool:
    return str(x).strip() in ('是', 'Y', 'y', 'TRUE', 'True', '1')


def parse_winback_file(uploaded) -> Tuple[pd.DataFrame, Dict[str, str]]:
    """解析撥打紀錄總表。回传 (per-agent DataFrame, 元信息)。
    统计结果页是块状布局(每位专员占 2 列:标签/数值)；各专员明细页补 召回充值 + 七天回登。"""
    xls = pd.read_excel(uploaded, sheet_name=None, header=None, dtype=str)
    meta = {'sheets': ', '.join(xls.keys())}

    # 1. 官方「统计结果」块状解析
    official: Dict[str, dict] = {}
    stats_raw = xls.get('统计结果')
    if stats_raw is not None and not stats_raw.empty:
        m = stats_raw.values.tolist()
        row0 = m[0]
        for c in range(0, len(row0), 2):
            name = str(row0[c]).strip() if (c < len(row0) and row0[c] is not None) else ''
            if not name or name.lower() in ('none', 'nan'):
                continue
            d = {}
            for r in range(1, len(m)):
                if c + 1 < len(m[r]):
                    lbl = m[r][c]
                    if lbl is not None and str(lbl).strip():
                        d[str(lbl).strip()] = m[r][c + 1]
            official[name] = d

    # 2. 每位专员明细页 → 召回充值 + 七天回登；顺便从拨打日期判月份
    rows = []
    month_votes: Dict[str, int] = {}
    for name, d in official.items():
        detail = None
        for sn, df in xls.items():
            if sn.strip().lower() == name.strip().lower():
                detail = df
                break
        recharge, relogin, n_detail = 0.0, 0, 0
        if detail is not None and not detail.empty:
            mm = detail.values.tolist()
            hdr_idx = None
            for i, row in enumerate(mm[:4]):
                if any(str(c).strip() == '账号' for c in row if c is not None):
                    hdr_idx = i
                    break
            if hdr_idx is not None:
                hdr = [str(c).strip() if c is not None else '' for c in mm[hdr_idx]]

                def _col(key, _hdr=hdr):
                    for j, h in enumerate(_hdr):
                        if key in h:
                            return j
                    return None

                c_acct = _col('账号')
                c_rech = _col('充值金额')
                c_login = _col('七天')
                if c_login is None:
                    c_login = _col('登入')
                c_date = _col('拨打日期')
                if c_date is None:
                    c_date = _col('日期')
                for row in mm[hdr_idx + 1:]:
                    if c_acct is None or c_acct >= len(row) or row[c_acct] is None or str(row[c_acct]).strip() == '':
                        continue
                    n_detail += 1
                    if c_rech is not None and c_rech < len(row):
                        recharge += _wb_num(row[c_rech])
                    if c_login is not None and c_login < len(row) and _wb_yes(row[c_login]):
                        relogin += 1
                    if c_date is not None and c_date < len(row) and row[c_date] is not None:
                        mt = re.match(r'\s*(\d{4})[-/年](\d{1,2})', str(row[c_date]))
                        if mt:
                            ym = f'{int(mt.group(1))}-{int(mt.group(2)):02d}'
                            month_votes[ym] = month_votes.get(ym, 0) + 1
        rows.append({
            '专员': name,
            '名单数': int(_wb_num(d.get('名单数'))),
            '已播数': int(_wb_num(d.get('已播数'))),
            '接通数': int(_wb_num(d.get('接通数'))),
            '有效通话': int(_wb_num(d.get('有效通话'))),
            '申请彩金': int(_wb_num(d.get('是否申请彩金'))),
            '七天回登': relogin,
            '召回充值': recharge,
        })
    if month_votes:
        meta['month'] = max(month_votes.items(), key=lambda kv: kv[1])[0]
    return pd.DataFrame(rows), meta


_CN_MONTH = {'一': 1, '二': 2, '三': 3, '四': 4, '五': 5, '六': 6,
             '七': 7, '八': 8, '九': 9, '十': 10, '十一': 11, '十二': 12}


def _winback_label(meta: dict, fname: str) -> str:
    """优先用数据里拨打日期判出的月份；否则从档名解析（X月 / 五月）。"""
    if meta.get('month'):
        y, m = meta['month'].split('-')
        return f'{y}年{int(m)}月'
    mt = re.search(r'(\d{1,2})\s*月', fname or '')
    if mt:
        return f'{int(mt.group(1))}月'
    for cn, num in _CN_MONTH.items():
        if f'{cn}月' in (fname or ''):
            return f'{num}月'
    return (fname or '本期').replace('.xlsx', '')


def _winback_agg(df: pd.DataFrame) -> dict:
    n_dial = int(df['已播数'].sum())
    n_conn = int(df['接通数'].sum())
    return {
        '名单数': int(df['名单数'].sum()),
        '已播数': n_dial,
        '接通数': n_conn,
        '有效通话': int(df['有效通话'].sum()),
        '七天回登': int(df['七天回登'].sum()),
        '召回充值': float(df['召回充值'].sum()),
        '接通率': (n_conn / n_dial) if n_dial else 0.0,
        '有效通话率': (int(df['有效通话'].sum()) / n_conn) if n_conn else 0.0,
        '七天回登率': (int(df['七天回登'].sum()) / int(df['名单数'].sum())) if int(df['名单数'].sum()) else 0.0,
    }


def _winback_ym_from_name(fname: str) -> str:
    """从档名兜底判月份(YYYY-MM)；优先用数据里拨打日期判出的 meta['month']，这里只兜底。"""
    s = fname or ''
    mt = re.search(r'(20\d{2})\D{0,3}(\d{1,2})\s*月', s)
    if mt:
        return f'{int(mt.group(1))}-{int(mt.group(2)):02d}'
    mt2 = re.search(r'(20\d{2})[-/](\d{1,2})', s)
    if mt2:
        return f'{int(mt2.group(1))}-{int(mt2.group(2)):02d}'
    for cn, num in _CN_MONTH.items():
        if f'{cn}月' in s:
            return f'2026-{num:02d}'  # 无年份兜底；正常会被 meta['month'] 覆盖
    return ''


def _bq_winback_month_exists(client, ym: str) -> int:
    try:
        sql = f"SELECT COUNT(*) AS n FROM `{BQ_PREFIX}.raw_winback` WHERE CAST(`月份` AS STRING)=@m"
        cfg = bigquery.QueryJobConfig(query_parameters=[bigquery.ScalarQueryParameter('m', 'STRING', ym)])
        return int(list(client.query(sql, job_config=cfg).result())[0].n)
    except Exception:
        return 0


def _write_winback(client, new_df, months, source_file):
    """电访按「月份」刷新：去掉这些月的旧行→写新行，其他月一行不动。沙盒禁 DML→整表读改写。"""
    table = f"{BQ_PREFIX}.raw_winback"
    try:
        existing = client.query(f"SELECT * FROM `{table}`").result().to_dataframe()
    except Exception:
        existing = pd.DataFrame()
    nd = new_df.copy()
    nd['_imported_at'] = pd.Timestamp.now()
    nd['_source_file'] = source_file
    months = [str(m) for m in months]
    if not existing.empty and '月份' in existing.columns:
        keep = existing[~existing['月份'].astype(str).isin(months)].copy()
        # 防掉数据：其他月行数必须原样保留
        for m, cnt in existing['月份'].astype(str).value_counts().to_dict().items():
            if m not in months and int((keep['月份'].astype(str) == m).sum()) != cnt:
                raise RuntimeError(f'安全中止：其他月份 {m} 行数会变，拒绝写入')
        combined = pd.concat([keep, nd], ignore_index=True)
    else:
        combined = nd
    cfg = bigquery.LoadJobConfig(
        write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE, autodetect=True)
    client.load_table_from_dataframe(combined, table, job_config=cfg).result()
    return len(combined)


def _winback_month_view(df: pd.DataFrame, label: str):
    df = df.sort_values('召回充值', ascending=False).reset_index(drop=True)
    a = _winback_agg(df)
    n_list, n_dial, n_conn, n_valid = a['名单数'], a['已播数'], a['接通数'], a['有效通话']
    n_relogin, sum_rech = a['七天回登'], a['召回充值']
    conn_rate, valid_rate, relogin_rate = a['接通率'], a['有效通话率'], a['七天回登率']

    cols = st.columns(5)
    show_metric(cols[0], '名单总数', fmt_num(n_list), help_text='本月分配给电访专员的待召回会员数')
    show_metric(cols[1], '接通率', fmt_pct(conn_rate), help_text='接通数 ÷ 已播数', tone='accent')
    show_metric(cols[2], '有效通话率', fmt_pct(valid_rate), help_text='有效通话 ÷ 接通数（接通后真正聊起来的比例）', tone='accent')
    show_metric(cols[3], '七天回登率', fmt_pct(relogin_rate), help_text='名单里七天内有登入的人数 ÷ 名单总数', tone='accent')
    show_metric(cols[4], '召回充值总额', fmt_num(sum_rech), help_text='名单会员在拨打后（复查口径）的充值金额合计',
                tone=tone_by_sign(sum_rech))

    with st.container(border=True):
        section_header('召回漏斗', '从名单一路漏到接通、有效通话；七天回登与召回充值另算（含未接通但自行回来的会员）。')
        fig = go.Figure(go.Funnel(
            y=['名单/已播', '接通', '有效通话'],
            x=[n_dial, n_conn, n_valid],
            textinfo='value+percent initial',
            marker={'color': [BLUE, PURPLE, GREEN]},
            connector={'line': {'color': 'rgba(150,170,210,0.4)'}},
        ))
        fig.update_layout(height=320, template=TEMPLATE, margin=dict(l=10, r=10, t=10, b=10))
        st.plotly_chart(fig, width='stretch')

    section_header(f'{label}召回小结', '可直接用于月度汇报。')
    top = df.iloc[0]

    def _hl(text, color=None):
        style = f'color:{color};font-weight:600;' if color else 'font-weight:600;'
        return f'<span style="{style}">{escape(str(text))}</span>'

    line1 = (f'本月对 {_hl(fmt_num(n_list))} 名会员进行电访，接通 {_hl(fmt_num(n_conn))} 通'
             f'（接通率 {_hl(fmt_pct(conn_rate))}），其中有效通话 {_hl(fmt_num(n_valid))} 通。')
    line2 = (f'名单中七天内回登 {_hl(fmt_num(n_relogin))} 人（回登率 {_hl(fmt_pct(relogin_rate))}），'
             f'带回充值 {_hl(fmt_num(sum_rech), GREEN)}。')
    line3 = f'召回充值表现最佳：{_hl(top["专员"])}，{_hl(fmt_num(top["召回充值"]), GREEN)}。'
    st.markdown(
        '<div class="hero-card" style="padding:1.1rem 1.4rem;line-height:2.05;">'
        f'<div>{line1}</div>'
        f'<div>{line2}</div>'
        f'<div style="margin-top:0.35rem;color:#9fb0d0;">{line3}</div>'
        '</div>',
        unsafe_allow_html=True,
    )

    section_header('各专员表现', '按召回充值排序。接通率反映触达能力，召回充值反映实际召回成效。')
    cc = st.columns(2)
    with cc[0]:
        with st.container(border=True):
            figc = go.Figure(go.Bar(
                x=df['专员'], y=df['召回充值'], marker_color=GREEN,
                text=[fmt_num(v) for v in df['召回充值']], textposition='outside',
            ))
            figc.update_layout(height=340, template=TEMPLATE, showlegend=False,
                               title='召回充值', yaxis_title='', margin=dict(t=40))
            st.plotly_chart(figc, width='stretch')
    with cc[1]:
        with st.container(border=True):
            rate = (df['接通数'] / df['已播数'].replace(0, pd.NA)).fillna(0)
            figr = go.Figure(go.Bar(
                x=df['专员'], y=rate, marker_color=BLUE,
                text=[fmt_pct(v) for v in rate], textposition='outside',
            ))
            figr.update_layout(height=340, template=TEMPLATE, showlegend=False,
                               title='接通率', yaxis_tickformat='.0%', margin=dict(t=40))
            st.plotly_chart(figr, width='stretch')

    with st.container(border=True):
        disp = df.copy()
        disp['接通率'] = (disp['接通数'] / disp['已播数'].replace(0, pd.NA)).fillna(0).map(lambda v: f'{v*100:.1f}%')
        disp['召回充值'] = disp['召回充值'].map(lambda v: f'{v:,.0f}')
        disp = disp[['专员', '名单数', '已播数', '接通数', '有效通话', '接通率', '七天回登', '申请彩金', '召回充值']]
        st.dataframe(disp, width='stretch', hide_index=True)
    st.caption('数据来源：上传的「撥打紀錄總表」。召回充值/七天回登为「复查」口径，反映名单会员拨打后一段时间内的实际行为。')


def _winback_compare_view(months: List[Tuple[str, pd.DataFrame]]):
    """多月对比：months = [(label, df), ...]，按月份排好序。"""
    comp = pd.DataFrame([{'月份': lab, **_winback_agg(d)} for lab, d in months])

    section_header('月度对比', '各月关键指标趋势。要看某个月的明细，用下面的选单切换。')
    c1, c2 = st.columns(2)
    with c1:
        with st.container(border=True):
            f1 = go.Figure(go.Bar(
                x=comp['月份'], y=comp['召回充值'], marker_color=GREEN,
                text=[fmt_num(v) for v in comp['召回充值']], textposition='outside',
            ))
            f1.update_layout(height=340, template=TEMPLATE, showlegend=False,
                             title='召回充值', margin=dict(t=40))
            st.plotly_chart(f1, width='stretch')
    with c2:
        with st.container(border=True):
            f2 = go.Figure()
            f2.add_trace(go.Scatter(x=comp['月份'], y=comp['接通率'], mode='lines+markers',
                                    name='接通率', line={'color': BLUE, 'width': 2.5}))
            f2.add_trace(go.Scatter(x=comp['月份'], y=comp['七天回登率'], mode='lines+markers',
                                    name='七天回登率', line={'color': PURPLE, 'width': 2.5}))
            f2.update_layout(height=340, template=TEMPLATE, title='接通率 / 七天回登率',
                             yaxis_tickformat='.0%', margin=dict(t=40),
                             legend=dict(orientation='h', y=1.12))
            st.plotly_chart(f2, width='stretch')

    show = comp.copy()
    for c in ['接通率', '有效通话率', '七天回登率']:
        show[c] = show[c].map(lambda v: f'{v*100:.1f}%')
    show['召回充值'] = show['召回充值'].map(lambda v: f'{v:,.0f}')
    show = show[['月份', '名单数', '接通数', '接通率', '有效通话率', '七天回登', '七天回登率', '召回充值']]
    st.dataframe(show, width='stretch', hide_index=True)

    if len(months) >= 2:
        cur, prv = comp.iloc[-1], comp.iloc[-2]
        def _delta(cur_v, prv_v, money=False):
            d = cur_v - prv_v
            arrow = '▲' if d >= 0 else '▼'
            val = fmt_num(abs(d)) if money else f'{abs(d)*100:.1f} 个百分点'
            return f'{arrow} {val}'
        st.markdown(
            '<div class="hero-card" style="padding:1.1rem 1.4rem;line-height:2.05;">'
            f'<div>对比上月（{escape(prv["月份"])} → {escape(cur["月份"])}）：'
            f'召回充值 <span style="color:{GREEN};font-weight:600;">{_delta(cur["召回充值"], prv["召回充值"], money=True)}</span>'
            f'（{fmt_num(prv["召回充值"])} → {fmt_num(cur["召回充值"])}）；'
            f'接通率 {_delta(cur["接通率"], prv["接通率"])}；'
            f'七天回登率 {_delta(cur["七天回登率"], prv["七天回登率"])}。</div>'
            '</div>',
            unsafe_allow_html=True,
        )


# ══════════════════════════════════════════════════════════════
# 新注册分析 — 从数据库(raw_member_report)读，看新注册从哪来 / 谁带的 / 质量
# 统一入口：上传一律走「数据上传」页；这页只「读数据库 + 出分析」(跟其他分析页一致)。
# 跨月快照按会员账号去重(取最新)，再按注册时间筛 + 派生 域名/邀请码/首存。
# ══════════════════════════════════════════════════════════════

def _nm_domain(u):
    if pd.isna(u):
        return '(未记录)'
    u = str(u)
    m = re.search(r'https?://([^/:]+)', u)
    if m:
        return m.group(1)
    if u.startswith('null'):
        return '(仅邀请码)'
    return u[:40] if u.strip() else '(未记录)'


def _nm_icode(u):
    if pd.isna(u):
        return None
    # 容错真实数据里的手误变体：i_code= / i_code- / i code- / i%20code- / r_code= 等
    s = str(u).replace('%20', ' ')
    m = re.search(r'[ir][_ ]?code[=\-](\d+)', s)
    return m.group(1) if m else None


def _nm_rank(fdf, col, label):
    if col not in fdf.columns:
        return
    full = (fdf.groupby(col)
            .agg(注册数=('会员账号', 'size'), 有首存=('有首存', 'sum'), 首存额=('首存额', 'sum'))
            .sort_values('注册数', ascending=False))
    total_n = int(full['注册数'].sum())
    n_groups = len(full)
    g = full.head(20).reset_index().rename(columns={'代理n': '代理'})
    g['未充值率'] = ((g['注册数'] - g['有首存']) / g['注册数'] * 100).round(0).astype(int).astype(str) + '%'
    g['首存额'] = g['首存额'].round(0).astype(int)
    st.markdown(f'**{label}**')
    st.dataframe(g, use_container_width=True, hide_index=True)
    if n_groups > 20:
        shown = int(g['注册数'].sum())
        st.caption(f'共 {n_groups} 个、{total_n} 个注册；上表为前 20 名（{shown} 个），'
                   f'其余 {n_groups - 20} 个合计 {total_n - shown} 个（长尾，未列出）。')
    else:
        st.caption(f'共 {n_groups} 个、{total_n} 个注册（已全部列出）。')


def _nm_fill_agent(s):
    """代理列空值统一成「(直客/无代理)」——给分组 / merge 当稳定 key 用。"""
    return s.astype(object).where(s.notna(), '(直客/无代理)').replace('', '(直客/无代理)')


# 这些字段是「逐月可加总」的：每月快照各记当月值，算 cohort 终身净值要跨快照求和，不能取单月。
# (首存金额是一次性属性，不在此列——取去重后单行即可。)
_NM_ADDITIVE = {'公司收入': '净收入', '有效投注额': '有效投注', '红利': '红利n', '返水': '返水n'}


def _nm_prepare(raw: pd.DataFrame) -> pd.DataFrame:
    """从 raw_member_report 准备新注册分析用 df：跨月快照按「会员账号+代理」去重(取最新) + 派生字段。
    去重含代理：同一个账号名挂在不同代理底下=不同的人，不能只按账号合并(跟「代理×会员明细」口径一致)。
    另外把逐月可加总字段(公司收入/有效投注/红利/返水)跨快照求和，挂成 cohort 终身净值列。"""
    df = raw.copy()
    if '会员账号' not in df.columns:
        return df.iloc[0:0]
    dedup_keys = ['会员账号', '代理'] if '代理' in df.columns else ['会员账号']
    if '_snapshot_month' in df.columns:
        df['__sm'] = df['_snapshot_month'].astype(str)
        df = (df.sort_values('__sm')
              .drop_duplicates(subset=dedup_keys, keep='last')
              .drop(columns='__sm'))
    else:
        df = df.drop_duplicates(subset=dedup_keys, keep='first')
    df['注册时间'] = to_datetime_safe(df['注册时间'])
    df = df[df['注册时间'].notna()].copy()
    df['注册日'] = df['注册时间'].dt.strftime('%Y-%m-%d')
    df['首存额'] = pd.to_numeric(df.get('首存金额'), errors='coerce').fillna(0)
    df['有首存'] = df['首存额'] > 0
    df['首投额'] = pd.to_numeric(df.get('首投金额'), errors='coerce').fillna(0)
    df['有首投'] = df['首投额'] > 0
    if '首存时间' in df.columns:
        fdt = to_datetime_safe(df['首存时间'])
        ttf = (fdt - df['注册时间']).dt.total_seconds() / 3600.0
        df['TTF小时'] = ttf.where(df['有首存'] & ttf.ge(0))  # 注册→首存隔多少小时(只算有首存且非负)
    else:
        df['TTF小时'] = pd.NA
    agent_col = df['代理'] if '代理' in df.columns else pd.Series([None] * len(df), index=df.index)
    df['代理n'] = _nm_fill_agent(agent_col)
    url_col = df['注册网址'] if '注册网址' in df.columns else pd.Series([None] * len(df), index=df.index)
    df['域名'] = url_col.map(_nm_domain)
    df['邀请码'] = url_col.map(_nm_icode)

    # ── cohort 终身净值：从原始全量(未去重)按「会员账号+代理」跨快照求和 ──
    # 先按「会员账号+代理+快照月」去重(防同月重复导入被重复计)，再跨月相加，才是这批人到今天为止的真实净值。
    present = {k: v for k, v in _NM_ADDITIVE.items() if k in raw.columns}
    if present:
        base = raw.copy()
        base['代理n'] = _nm_fill_agent(base['代理']) if '代理' in base.columns else '(直客/无代理)'
        if '_snapshot_month' in base.columns:
            sort_col = '_imported_at' if '_imported_at' in base.columns else '_snapshot_month'
            base = (base.sort_values(sort_col)
                    .drop_duplicates(subset=['会员账号', '代理n', '_snapshot_month'], keep='last'))
        for src in present:
            base[src] = pd.to_numeric(base[src], errors='coerce').fillna(0)
        agg = (base.groupby(['会员账号', '代理n'], as_index=False)[list(present)]
               .sum().rename(columns=present))
        df = df.merge(agg, on=['会员账号', '代理n'], how='left')
        for v in present.values():
            df[v] = pd.to_numeric(df[v], errors='coerce').fillna(0)
    return df


def _nm_date_filter(df):
    """这页专用日期筛选：快捷预设(全部/本月/上月/近7天/近30天)或自订日期 + 实时显示。
    用单选(预设 或 自订)，不会出现「月份盖过日期」那种撞。预设相对资料里最新日期算，保证落在数据范围内。"""
    import datetime as _dt
    d = df[df['注册时间'].notna()].copy()
    if d.empty:
        st.warning('没有可用的注册时间。')
        return d
    min_d = d['注册时间'].min().date()
    max_d = d['注册时间'].max().date()
    first_this = max_d.replace(day=1)
    prev_last = first_this - _dt.timedelta(days=1)
    prev_first = prev_last.replace(day=1)
    presets = {
        '全部': (min_d, max_d),
        '本月': (max(min_d, first_this), max_d),
        '上月': (max(min_d, prev_first), min(max_d, prev_last)),
        '近7天': (max(min_d, max_d - _dt.timedelta(days=6)), max_d),
        '近30天': (max(min_d, max_d - _dt.timedelta(days=29)), max_d),
    }
    pick = st.radio('快速选择', list(presets.keys()) + ['自订日期'],
                    horizontal=True, key='nm_dpick')
    if pick == '自订日期':
        c1, c2 = st.columns(2)
        with c1:
            start = st.date_input('开始日期', value=min_d, min_value=min_d, max_value=max_d, key='nm_start')
        with c2:
            end = st.date_input('结束日期', value=max_d, min_value=min_d, max_value=max_d, key='nm_end')
    else:
        start, end = presets[pick]
    if start > end:
        start, end = end, start
    s_ts = pd.Timestamp(start)
    e_ts = pd.Timestamp(end) + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)
    out = d[(d['注册时间'] >= s_ts) & (d['注册时间'] <= e_ts)].copy()
    st.caption(f'📅 当前显示 {start} ~ {end}，共 {len(out)} 个新注册（已按 会员账号+代理 去重）。改上面就立刻跟着变。')
    return out


_NM_QUALITY_COLS = ['有首存', '首存额', '净收入', '有效投注', '红利n', '返水n']


def _nm_q_cols(df):
    """质量指标需要、且当前 df 里确实存在的列。"""
    return [c for c in _NM_QUALITY_COLS if c in df.columns]


def _nm_int_display(tbl):
    """把整数性质的列转成 Int64，避免 st.dataframe 显示成 10.0 这种带小数点的。"""
    for c in ['注册数', '未充值率%', '人均首存', '人均净收入', '净收入合计']:
        if c in tbl.columns:
            tbl[c] = tbl[c].round().astype('Int64')
    return tbl


def _nm_group_quality(g):
    """对一组新注册算质量指标：转化率 / 未充值率 / 人均首存 / 人均净收入 / 红利套利比值。
    净收入等是去重后挂上的 cohort 终身净值列(跨月累计·公司角度)，直接对当前这批人求和。"""
    n = len(g)
    has = int(g['有首存'].sum())
    fd = float(g['首存额'].sum())
    row = {
        '注册数': n,
        '转化率%': round(has / n * 100, 1) if n else 0.0,
        '未充值率%': round((n - has) / n * 100) if n else 0,
        '人均首存': round(fd / n) if n else 0,
    }
    if '净收入' in g.columns:
        net = float(g['净收入'].sum())
        row['人均净收入'] = round(net / n) if n else 0
        row['净收入合计'] = round(net)
    if {'红利n', '返水n', '有效投注'}.issubset(g.columns):
        to = float(g['有效投注'].sum())
        give = float(g['红利n'].sum()) + float(g['返水n'].sum())
        if to > 0:
            row['套利比值%'] = round(give / to * 100, 1)
        else:
            row['套利比值%'] = (999.0 if give > 0 else None)
    return pd.Series(row)


def _nm_value_by_source(fdf):
    """① 直客 vs 代理来源 价值对比——不只比人数，比转化 / 人均首存 / 人均净收入。"""
    if '用户来源' not in fdf.columns:
        return
    section_header('① 直客 vs 代理来源 — 价值对比',
                   '不只比人数：比转化率、人均首存、人均净收入。直接回答「直客掉到底多痛」。')
    src = fdf.copy()
    src['用户来源'] = src['用户来源'].fillna('(未记录)').astype(str)
    tbl = (src.groupby('用户来源')[_nm_q_cols(src)].apply(_nm_group_quality)
           .reset_index())
    order = {'直客': 0, '普代下线': 1, '官代下线': 2}
    tbl['_o'] = tbl['用户来源'].map(order).fillna(9)
    tbl = tbl.sort_values('_o').drop(columns='_o')
    tbl = _nm_int_display(tbl)
    st.dataframe(tbl, use_container_width=True, hide_index=True)
    direct = src[src['用户来源'] == '直客']
    agent = src[src['用户来源'] != '直客']
    if len(direct) and len(agent) and '净收入' in src.columns:
        d_arpu = direct['净收入'].sum() / len(direct)
        a_arpu = agent['净收入'].sum() / len(agent)
        d_conv = direct['有首存'].mean() * 100
        a_conv = agent['有首存'].mean() * 100
        verdict = ('直客更值钱 → 直客下滑的影响大于人数本身。'
                   if d_arpu > a_arpu else
                   '代理来源人均更高 → 直客量下滑相对可控，但仍要看结构。')
        st.caption(f'📌 直客 {len(direct)} 人、转化 {d_conv:.0f}%、人均净收入 {d_arpu:,.0f}；'
                   f'代理来源 {len(agent)} 人、转化 {a_conv:.0f}%、人均净收入 {a_arpu:,.0f}。{verdict}')
    st.caption('💡 净收入＝公司角度(已扣红利)，负数代表这批人到今天为止公司是亏的；跨月累计。'
               '「直客」指用户来源=直客，代理来源含普代下线＋官代下线。')


def _nm_quality_board(fdf):
    """② 代理质量分层榜——量×质一起看，自动标「疑似刷量 / 红利套利」。"""
    if '代理n' not in fdf.columns:
        return
    section_header('② 代理质量分层榜',
                   '不只看量：转化率＋人均首存＋人均净收入＋未充值率一起看，'
                   '一眼分辨「高量低质 / 疑似刷量」和「量小但真值钱」。')
    vol = st.slider('最少注册数（滤掉长尾，只看够量的代理）', 1, 50, 5, key='nm_q_vol')
    tbl = (fdf.groupby('代理n')[_nm_q_cols(fdf)].apply(_nm_group_quality)
           .reset_index().rename(columns={'代理n': '代理'}))
    tbl = tbl[tbl['注册数'] >= vol].sort_values('注册数', ascending=False)
    if tbl.empty:
        st.caption(f'没有注册数 ≥ {vol} 的代理，把门槛调低一点。')
        return

    def _flag(r):
        marks = []
        if r['注册数'] >= max(vol, 10) and r['未充值率%'] >= 80:
            marks.append('🚩刷量嫌疑')
        if '套利比值%' in r and pd.notna(r['套利比值%']) and r['套利比值%'] >= 100:
            marks.append('⚠️红利套利')
        return ' '.join(marks) if marks else '✅'

    tbl['风险'] = tbl.apply(_flag, axis=1)
    n_flag = int((tbl['风险'] != '✅').sum())
    tbl = _nm_int_display(tbl.head(40))
    st.dataframe(tbl, use_container_width=True, hide_index=True)
    st.caption(
        f'共标出 {n_flag} 个风险代理。🚩刷量嫌疑＝注册量够大(≥10)但未充值率≥80%'
        '(像 qwe8825252 注册46、未充值93%)；⚠️红利套利＝(红利+返水)≥有效投注额(领了优惠几乎不打)。'
        '人均净收入＝这批人到今天为止给公司带来的净收入÷人数(跨月累计·公司角度·负数代表公司亏)。')


def _nm_funnel_ttf(fdf):
    """③ 转化漏斗(注册→首存→首投) + 首存速度 TTF。"""
    section_header('③ 转化漏斗 + 首存速度（TTF）',
                   '注册→首存→首投 三段漏斗，看哪一段漏最多；首存速度比注册量更早预警转化变差。')
    n = len(fdf)
    if n == 0:
        return
    has_fd = int(fdf['有首存'].sum())
    has_fb = int(fdf['有首投'].sum()) if '有首投' in fdf.columns else 0
    # 只画 注册→首存：首存→首投 几乎恒等于 100%(充了钱的人基本都会下注)，当指标没信息量，不单列。
    fig = go.Figure(go.Funnel(
        y=['注册', '首存（充值）'], x=[n, has_fd],
        textposition='inside', textinfo='value+percent initial',
        marker={'color': ['#60a5fa', '#2dd4a7']}))
    fig.update_layout(template='plotly_dark', height=220,
                      paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                      margin=dict(l=10, r=10, t=10, b=10))
    st.plotly_chart(fig, use_container_width=True)

    ttf = fdf['TTF小时'].dropna() if 'TTF小时' in fdf.columns else pd.Series([], dtype=float)
    reg2fd = has_fd / n
    fd_med = float(fdf.loc[fdf['有首存'], '首存额'].median()) if has_fd else 0
    mc = st.columns(4)
    show_metric(mc[0], '注册→首存 转化', fmt_pct(reg2fd), tone='warn' if reg2fd < 0.5 else 'good',
                help_text=f'有首存人数 ÷ 注册数 ＝ {has_fd} ÷ {n}（这批注册里有多少人真的充了第一笔）')
    show_metric(mc[1], '首存中位额', fmt_num(round(fd_med)) if has_fd else 'N/A',
                help_text='有首存的人，首存金额取中位数（看这批人首存大不大；中位比平均更抗大户拉高）')
    show_metric(mc[2], '首存速度 TTF 中位', f'{ttf.median():.1f} 小时' if len(ttf) else 'N/A',
                help_text='有首存的人，(首存时间 － 注册时间) 取中位数；越短越好')
    fast = (ttf < 1).mean() * 100 if len(ttf) else 0
    show_metric(mc[3], '1 小时内首存占比', f'{fast:.0f}%' if len(ttf) else 'N/A',
                help_text='有首存的人里，注册后 1 小时内就完成首存的占比')

    drop_reg = n - has_fd
    fb_note = ('；充了钱的人几乎都会下注（首存→首投 '
               f'{has_fb / has_fd * 100:.0f}%），所以这步不另列' if has_fd else '')
    st.caption(f'📌 流失全卡在「注册→首存」：{n} 人注册、只有 {has_fd} 人充值，漏掉 {drop_reg} 人'
               f'（{drop_reg / n * 100:.0f}%）{fb_note}。瓶颈是拉新质量 / 首存引导，不是下注意愿。')

    if len(ttf):
        labels = ['<1小时', '1-24小时', '1-7天', '>7天']
        dist = (pd.cut(ttf, bins=[0, 1, 24, 168, float('inf')], labels=labels, right=False)
                .value_counts().reindex(labels).fillna(0).astype(int))
        fig2 = go.Figure(go.Bar(x=labels, y=dist.values, marker_color='#2dd4a7',
                                text=dist.values, textposition='outside'))
        fig2.update_layout(template='plotly_dark', height=240,
                           paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                           margin=dict(l=10, r=10, t=40, b=10),
                           title='首存速度分布（注册到首存隔多久）')
        st.plotly_chart(fig2, use_container_width=True)

    if len(ttf) and '用户来源' in fdf.columns:
        seg = fdf[fdf['TTF小时'].notna()].copy()
        seg['用户来源'] = seg['用户来源'].fillna('(未记录)').astype(str)
        g = seg.groupby('用户来源')['TTF小时'].agg(['median', 'count']).reset_index()
        g.columns = ['用户来源', 'TTF中位(小时)', '首存人数']
        g['TTF中位(小时)'] = g['TTF中位(小时)'].round(1)
        g['首存人数'] = g['首存人数'].astype(int)
        st.caption('各来源首存速度对比（中位 TTF 越短代表转化越顺）：')
        st.dataframe(g.sort_values('首存人数', ascending=False), use_container_width=True, hide_index=True)


def _nm_cohort_pl(fdf):
    """④ Cohort 损益走势：按注册月分组，看每批人到今天为止累计净收入（公司角度）。"""
    section_header('④ Cohort 损益走势（按注册月）',
                   '把新注册按「注册月份」分组，看每一批人到今天为止累计给公司带来多少净收入——'
                   '比注册量更接近「这批客到底值不值」。')
    if '净收入' not in fdf.columns or fdf.empty:
        st.caption('当前数据缺少净收入字段（公司收入），无法算 cohort 损益。')
        return
    df = fdf.copy()
    df['注册月'] = df['注册时间'].dt.strftime('%Y-%m')
    tbl = (df.groupby('注册月')[_nm_q_cols(df)].apply(_nm_group_quality)
           .reset_index().sort_values('注册月'))
    keep = ['注册月', '注册数', '转化率%', '人均首存', '净收入合计', '人均净收入']
    tbl = tbl[[c for c in keep if c in tbl.columns]]
    if tbl.empty:
        st.caption('当前筛选下没有可分组的注册月。')
        return

    colors = ['#2dd4a7' if v >= 0 else '#fb7185' for v in tbl['净收入合计']]
    fig = go.Figure(go.Bar(x=tbl['注册月'], y=tbl['净收入合计'], marker_color=colors))
    fig.update_layout(template='plotly_dark', height=300,
                      paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                      margin=dict(l=10, r=10, t=40, b=10),
                      title='各注册月 cohort 到今天的累计净收入（公司角度·绿赚红亏）')
    st.plotly_chart(fig, use_container_width=True)

    fig2 = go.Figure(go.Scatter(x=tbl['注册月'], y=tbl['人均净收入'],
                                mode='lines+markers', line=dict(color='#60a5fa')))
    fig2.update_layout(template='plotly_dark', height=260,
                       paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                       margin=dict(l=10, r=10, t=40, b=10),
                       title='各注册月 cohort 人均净收入')
    st.plotly_chart(fig2, use_container_width=True)

    st.dataframe(_nm_int_display(tbl), use_container_width=True, hide_index=True)
    st.caption('⚠️ 看这页要扣掉「账龄」因素：老月份人均净收入偏高，是因为他们入金时间长、留下来的多是大户；'
               '当月/上月注册的人账龄短，累计自然低，别直接拿绝对值跟老月份比。'
               '真正有意义的是——①近几个月之间的对比 ②哪个月的 cohort 到今天还是「负的」（这批人累计还在亏，要查当月拉来的是什么客）。')



# V6.4: render_new_member_analysis moved to features/agent_channel.py


def _fin_minutes(df, t_start, t_end):
    s = to_datetime_safe(df[t_start]); e = to_datetime_safe(df[t_end])
    return (e - s).dt.total_seconds() / 60


def _fin_deposit_view(dep):
    if dep is None or dep.empty or '订单状态' not in dep.columns:
        st.info('暂无充值数据。')
        return
    dep, _s, _e, _m = date_range_picker(dep, '完成时间', 'fd_dep')
    if dep.empty:
        st.warning('该日期范围内无充值数据。')
        return
    n = len(dep)
    succ = int((dep['订单状态'] == '存款成功').sum())
    cancel = int((dep['订单状态'] == '已取消').sum())
    wait = None
    if '完成时间' in dep.columns:
        wait = _fin_minutes(dep[dep['订单状态'] == '存款成功'], '订单时间', '完成时间')
        wait = wait[(wait >= 0) & (wait.notna())]
    section_header('充值总览', f'共 {n} 笔（成功率 = 成功÷总；掉单率 = 已取消÷总）')
    c = st.columns(4)
    show_metric(c[0], '充值笔数', fmt_num(n))
    show_metric(c[1], '成功率', fmt_pct(succ / n) if n else 'N/A', tone='good')
    show_metric(c[2], '掉单率（已取消）', fmt_pct(cancel / n) if n else 'N/A',
                tone='warn' if n and cancel / n > 0.15 else None)
    show_metric(c[3], '平均到账（成功单）', f'{wait.mean():.1f} 分' if wait is not None and len(wait) else 'N/A',
                tone='accent', help_text='完成时间 − 订单时间')
    if '支付方式' in dep.columns:
        rows = []
        for pm, g in dep.groupby('支付方式'):
            gn = len(g); gs = int((g['订单状态'] == '存款成功').sum()); gc = int((g['订单状态'] == '已取消').sum())
            gw = _fin_minutes(g[g['订单状态'] == '存款成功'], '订单时间', '完成时间') if '完成时间' in g.columns else None
            gw = gw[(gw >= 0) & (gw.notna())] if gw is not None else None
            rows.append({'支付方式': pm, '笔数': gn, '_succ': gs / gn if gn else 0, '_drop': gc / gn if gn else 0,
                         '平均到账(分)': round(gw.mean(), 1) if gw is not None and len(gw) else 0})
        ch = pd.DataFrame(rows).sort_values('笔数', ascending=False)
        disp = ch.copy()
        disp['成功率'] = disp['_succ'].map(lambda v: f'{v*100:.0f}%')
        disp['掉单率'] = disp['_drop'].map(lambda v: f'{v*100:.0f}%')
        disp = disp[['支付方式', '笔数', '成功率', '掉单率', '平均到账(分)']]
        section_header('分渠道（支付方式）', '成功率低的渠道＝客户在这关掉单。建议主推高成功率渠道 + 优化低成功率渠道的引导。')
        st.dataframe(disp, use_container_width=True, hide_index=True)
        low = ch[(ch['笔数'] >= 20) & (ch['_succ'] < 0.6)].sort_values('笔数', ascending=False)
        if not low.empty:
            st.warning('⚠️ 成功率偏低（<60%、≥20 笔）的渠道：'
                       + '、'.join(f"{r['支付方式']}({r['_succ']*100:.0f}%)" for _, r in low.iterrows())
                       + ' —— 客户多在这几关掉单，建议主推高成功率渠道 + 优化引导话术。')
    if '取消原因' in dep.columns:
        rc = dep[dep['订单状态'] == '已取消']['取消原因'].astype(str).str.strip()
        rc = rc[~rc.str.lower().isin(['nan', 'none', ''])]
        if len(rc):
            section_header('掉单原因 Top')
            vc = rc.value_counts().head(8).reset_index()
            vc.columns = ['取消原因', '笔数']
            st.dataframe(vc, use_container_width=True, hide_index=True)


def _fin_withdraw_view(wd):
    if wd is None or wd.empty or '订单状态' not in wd.columns:
        st.info('暂无提款数据。')
        return
    wd, _s, _e, _m = date_range_picker(wd, '完成时间', 'fd_wd')
    if wd.empty:
        st.warning('该日期范围内无提款数据。')
        return
    n = len(wd)
    succ = int((wd['订单状态'] == '提款成功').sum())
    reject = int((wd['订单状态'] == '审核拒绝').sum())
    fail = int((wd['订单状态'] == '提款失败').sum())
    wait = None
    if '完成时间' in wd.columns:
        wait = _fin_minutes(wd[wd['订单状态'] == '提款成功'], '申请时间', '完成时间')
        wait = wait[(wait >= 0) & (wait.notna())]
    section_header('提款总览', f'共 {n} 笔')
    c = st.columns(4)
    show_metric(c[0], '提款笔数', fmt_num(n))
    show_metric(c[1], '成功率', fmt_pct(succ / n) if n else 'N/A', tone='good')
    show_metric(c[2], '拒绝率（审核拒绝）', fmt_pct(reject / n) if n else 'N/A',
                tone='warn' if n and reject / n > 0.1 else None)
    show_metric(c[3], '平均出款（成功单）', f'{wait.mean():.1f} 分' if wait is not None and len(wait) else 'N/A',
                tone='accent', help_text='完成时间 − 申请时间')
    if wait is not None and len(wait):
        c2 = st.columns(4)
        show_metric(c2[0], '出款中位', f'{wait.median():.1f} 分')
        show_metric(c2[1], '90% 在', f'{wait.quantile(.9):.1f} 分内')
        show_metric(c2[2], '超 1 小时', fmt_num(int((wait > 60).sum())),
                    tone='warn' if int((wait > 60).sum()) else None)
        show_metric(c2[3], '提款失败笔数', fmt_num(fail))
        w2 = wd[wd['订单状态'] == '提款成功'].copy()
        w2['处理分钟'] = _fin_minutes(w2, '申请时间', '完成时间')
        slow = w2[w2['处理分钟'] > 60].sort_values('处理分钟', ascending=False)
        if not slow.empty:
            section_header('出款慢单（>1 小时）', '大额 / 风控长尾，值得逐笔查。')
            cols = [c for c in ['订单号', '会员账号', '会员等级', '订单金额', '申请时间', '完成时间', '处理分钟']
                    if c in slow.columns]
            sd = slow[cols].head(50).copy()
            sd['处理分钟'] = sd['处理分钟'].round(0).astype(int)
            st.dataframe(sd, use_container_width=True, hide_index=True)


# 1 finance page implementation moved to features/finance_results.py

# V6.5: data admin/upload implementation moved to features.upload_admin.
# Keep compatibility imports for older modules that still import these names from core.
from features.upload_admin import (  # noqa: E402,F401
    render_data_health,
    render_data_source_guide,
    _render_data_upload_impl,
    render_data_manage,
)

def main():
    # 两层导航：大类 → 细项
    GROUPS = {
        '🅰️ 财务结果': [
            ('经营总览', render_overview),
            ('近期走势(日报)', render_recent_trend),
            ('存取款分析', render_finance_channel),
            ('红利分析', render_bonus_analysis),
            ('红利 ROI & 代理质量', render_bonus_roi_agent_quality),
            ('代理佣金 & 退成', render_agent_commission),
        ],
        '🅱️ 会员价值': [
            ('会员结构 & ARPU', render_member_value),
            ('投注分析', render_bet_analysis),
            ('客服分析', render_cs_analysis),
            ('电访召回', render_winback),
            ('实时波动 & DAU', render_realtime),
        ],
        '🅲 代理 / 渠道': [
            ('代理团队 & 渠道', render_channel_agent),
            ('新注册分析', render_new_member_analysis),
            ('代理 × 会员 明细', render_agent_member_matrix),
            ('市代月度结算', render_agent_market_monthly),
            ('游戏 & 场馆', render_game_venue),
        ],
        '🗂 数据上传': [
            ('🩺 数据健康', render_data_health),
            ('📖 数据说明', render_data_source_guide),
            ('月度报表上传', _render_data_upload_impl),
            ('删除数据', render_data_manage),
        ],
    }
    group = st.radio(
        '大类', list(GROUPS.keys()),
        horizontal=True, label_visibility='collapsed', key='nav_group',
    )
    sub_options = [name for name, _ in GROUPS[group]]
    sub_renderers = {name: fn for name, fn in GROUPS[group]}
    st.markdown(
        '<div style="height:0.4rem;"></div>',
        unsafe_allow_html=True,
    )
    sub = st.radio(
        '细项', sub_options,
        horizontal=True, label_visibility='collapsed', key=f'nav_sub_{group}',
    )
    sub_renderers[sub]()
    st.divider()
    st.caption(f'运营数据面板 {APP_VERSION}（{APP_VERSION_DATE}）· 更新内容见仓库 CHANGELOG.md')


if __name__ == '__main__':
    main()
