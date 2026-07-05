"""世界杯专区。

v1.4.1 World Cup Center MVP
- 从 raw_bet_detail 自动识别世界杯注单
- 排除 Panda 注单
- 支持赛事总览、比赛监控、玩家排行、识别规则
"""

from __future__ import annotations

from typing import Any

import pandas as pd
import plotly.express as px
import streamlit as st

try:
    from components.ui import apply_theme, hero, metric_card, section, alert, brief
except Exception:  # 兼容旧版项目
    def apply_theme() -> None:
        return None

    def hero(title: str, subtitle: str, version: str = "") -> None:
        st.title(title)
        st.caption(subtitle)

    def metric_card(title: str, value: str, note: str = "", delta: str = "", icon: str = "") -> None:
        st.metric(f"{icon} {title}", value, delta or None)
        if note:
            st.caption(note)

    def section(title: str, subtitle: str = "") -> None:
        st.subheader(title)
        if subtitle:
            st.caption(subtitle)

    def alert(text: str, level: str = "warning") -> None:
        if level == "critical":
            st.error(text)
        elif level == "good":
            st.success(text)
        else:
            st.warning(text)

    def brief(items: list[str]) -> None:
        for item in items:
            st.write(f"• {item}")

from services.bigquery_client import query_bq

PROJECT = "mydata-494606"
DATASET = "mydata"
VERSION = "v1.4.1"


WORLD_CUP_WHERE = """
`投注详情` IS NOT NULL
AND REGEXP_CONTAINS(LOWER(CAST(`投注详情` AS STRING)), r'世界杯2026|fifa世界杯2026|world cup 2026')
AND NOT REGEXP_CONTAINS(LOWER(CAST(`投注详情` AS STRING)), r'panda')
"""

WORLD_CUP_BASE = f"""
WITH wc AS (
  SELECT
    TRIM(`会员账号`) AS member_id,
    UPPER(REGEXP_REPLACE(TRIM(`会员账号`), r'[^A-Za-z0-9]', '')) AS member_key,
    IFNULL(TRIM(`上级代理名称`), '') AS agent_name,
    TRIM(`场馆名称`) AS provider,
    TRIM(`游戏名称`) AS game_name,
    TRIM(`玩法`) AS play_type,
    TRIM(`盘口`) AS handicap,
    TRIM(`状态`) AS bet_status,
    TRIM(`投注详情`) AS bet_detail,
    SAFE_CAST(`下注金额` AS FLOAT64) AS turnover,
    SAFE_CAST(`有效投注` AS FLOAT64) AS valid_turnover,
    SAFE_CAST(`盈亏` AS FLOAT64) AS profit_loss,
    SAFE_CAST(`手续费` AS FLOAT64) AS fee,
    SAFE.PARSE_DATETIME('%Y-%m-%d %H:%M:%S', CAST(`下注时间` AS STRING)) AS bet_time,
    COALESCE(
      SAFE.PARSE_DATETIME('%Y-%m-%d %H:%M:%S', CAST(`开赛时间` AS STRING)),
      SAFE.PARSE_DATETIME('%Y-%m-%d %H:%M:%S', REGEXP_EXTRACT(CAST(`投注详情` AS STRING), r'足球\\((\\d{{4}}-\\d{{2}}-\\d{{2}} \\d{{2}}:\\d{{2}}:\\d{{2}})\\)'))
    ) AS match_time,
    CASE
      WHEN REGEXP_CONTAINS(LOWER(CONCAT(IFNULL(`游戏名称`, ''), ' ', IFNULL(`投注详情`, ''))), r'串关|parlay') THEN '串关/多场'
      ELSE COALESCE(
        REGEXP_REPLACE(
          REGEXP_EXTRACT(CAST(`投注详情` AS STRING), r'世界杯2026[^\\r\\n]*[\\r\\n]+([^\\r\\n]+)'),
          r'\\s+vs\\s+', ' v '
        ),
        REGEXP_REPLACE(
          REGEXP_EXTRACT(CAST(`投注详情` AS STRING), r'FIFA世界杯2026[^\\r\\n]*[\\r\\n]+([^\\r\\n]+)'),
          r'\\s+vs\\s+', ' v '
        ),
        '未识别赛事'
      )
    END AS match_name,
    `注单流水号` AS bet_id
  FROM `{PROJECT}.{DATASET}.raw_bet_detail`
  WHERE {WORLD_CUP_WHERE}
)
"""


def _fmt_num(value: Any, digits: int = 0) -> str:
    if value is None or pd.isna(value):
        return "-"
    try:
        n = float(value)
    except Exception:
        return str(value)
    if abs(n) >= 100000000:
        return f"{n / 100000000:.2f}亿"
    if abs(n) >= 10000:
        return f"{n / 10000:.2f}万"
    if digits == 0:
        return f"{n:,.0f}"
    return f"{n:,.{digits}f}"


def _fmt_pct(value: Any) -> str:
    if value is None or pd.isna(value):
        return "-"
    try:
        return f"{float(value) * 100:.2f}%"
    except Exception:
        return "-"


def _safe_query(sql: str) -> pd.DataFrame:
    try:
        return query_bq(sql)
    except Exception as exc:
        st.error(f"BigQuery 查询失败：{exc}")
        return pd.DataFrame()


def _load_summary() -> pd.DataFrame:
    return _safe_query(
        WORLD_CUP_BASE
        + """
SELECT
  COUNT(*) AS bet_count,
  COUNT(DISTINCT member_key) AS members,
  COUNT(DISTINCT match_name) AS matches,
  SUM(turnover) AS turnover,
  SUM(valid_turnover) AS valid_turnover,
  SUM(profit_loss) AS profit_loss,
  SAFE_DIVIDE(SUM(profit_loss), NULLIF(SUM(valid_turnover), 0)) AS rtp,
  MIN(bet_time) AS first_bet_time,
  MAX(bet_time) AS last_bet_time
FROM wc;
"""
    )


def _load_daily() -> pd.DataFrame:
    return _safe_query(
        WORLD_CUP_BASE
        + """
SELECT
  DATE(bet_time) AS report_date,
  COUNT(*) AS bet_count,
  COUNT(DISTINCT member_key) AS members,
  SUM(turnover) AS turnover,
  SUM(valid_turnover) AS valid_turnover,
  SUM(profit_loss) AS profit_loss
FROM wc
WHERE bet_time IS NOT NULL
GROUP BY report_date
ORDER BY report_date;
"""
    )


def _load_matches(limit: int = 100) -> pd.DataFrame:
    return _safe_query(
        WORLD_CUP_BASE
        + f"""
SELECT
  match_name,
  MIN(match_time) AS match_time,
  COUNT(*) AS bet_count,
  COUNT(DISTINCT member_key) AS members,
  SUM(turnover) AS turnover,
  SUM(valid_turnover) AS valid_turnover,
  SUM(profit_loss) AS profit_loss,
  AVG(turnover) AS avg_bet,
  SAFE_DIVIDE(SUM(profit_loss), NULLIF(SUM(valid_turnover), 0)) AS rtp
FROM wc
GROUP BY match_name
ORDER BY valid_turnover DESC
LIMIT {int(limit)};
"""
    )


def _load_play_types(match_name: str | None = None) -> pd.DataFrame:
    where = ""
    if match_name and match_name != "全部赛事":
        safe = match_name.replace("'", "\\'")
        where = f"WHERE match_name = '{safe}'"
    return _safe_query(
        WORLD_CUP_BASE
        + f"""
SELECT
  IFNULL(play_type, '未识别玩法') AS play_type,
  COUNT(*) AS bet_count,
  COUNT(DISTINCT member_key) AS members,
  SUM(turnover) AS turnover,
  SUM(valid_turnover) AS valid_turnover,
  SUM(profit_loss) AS profit_loss,
  SAFE_DIVIDE(SUM(profit_loss), NULLIF(SUM(valid_turnover), 0)) AS rtp
FROM wc
{where}
GROUP BY play_type
ORDER BY valid_turnover DESC
LIMIT 30;
"""
    )


def _load_players(match_name: str | None = None, limit: int = 50) -> pd.DataFrame:
    where = ""
    if match_name and match_name != "全部赛事":
        safe = match_name.replace("'", "\\'")
        where = f"WHERE match_name = '{safe}'"
    return _safe_query(
        WORLD_CUP_BASE
        + f"""
SELECT
  member_id AS `会员账号`,
  ANY_VALUE(agent_name) AS `代理`,
  COUNT(*) AS `注单数`,
  COUNT(DISTINCT match_name) AS `投注赛事数`,
  SUM(turnover) AS `流水`,
  SUM(valid_turnover) AS `有效投注`,
  SUM(profit_loss) AS `会员盈亏`,
  SAFE_DIVIDE(SUM(profit_loss), NULLIF(SUM(valid_turnover), 0)) AS `RTP`
FROM wc
{where}
GROUP BY member_key, member_id
ORDER BY `有效投注` DESC
LIMIT {int(limit)};
"""
    )


def _load_recent_bets(match_name: str | None = None, limit: int = 100) -> pd.DataFrame:
    where = ""
    if match_name and match_name != "全部赛事":
        safe = match_name.replace("'", "\\'")
        where = f"WHERE match_name = '{safe}'"
    return _safe_query(
        WORLD_CUP_BASE
        + f"""
SELECT
  bet_time AS `下注时间`,
  member_id AS `会员账号`,
  match_name AS `赛事`,
  provider AS `场馆`,
  game_name AS `游戏`,
  play_type AS `玩法`,
  turnover AS `下注金额`,
  valid_turnover AS `有效投注`,
  profit_loss AS `盈亏`,
  bet_status AS `状态`
FROM wc
{where}
ORDER BY bet_time DESC
LIMIT {int(limit)};
"""
    )


def _summary_brief(summary: pd.Series) -> list[str]:
    items: list[str] = []
    turnover = float(summary.get("turnover") or 0)
    profit = float(summary.get("profit_loss") or 0)
    rtp = float(summary.get("rtp") or 0)
    bets = int(summary.get("bet_count") or 0)
    members = int(summary.get("members") or 0)

    items.append(f"世界杯目前累计 {bets:,} 笔注单，参与会员 {members:,} 人，流水 {_fmt_num(turnover)}。")
    if profit >= 0:
        items.append(f"平台当前为盈利状态，累计会员盈亏 {_fmt_num(profit)}。")
    else:
        items.append(f"平台当前为亏损状态，累计会员盈亏 {_fmt_num(profit)}，建议优先查看高投注赛事与高RTP会员。")
    if rtp >= 0.98:
        items.append(f"整体 RTP {_fmt_pct(rtp)} 偏高，建议风控关注异常集中投注。")
    else:
        items.append(f"整体 RTP {_fmt_pct(rtp)}，目前处于可观察区间。")
    return items


def render_worldcup_overview() -> None:
    apply_theme()
    hero("⚽ 世界杯专区", "世界杯投注、赛事、玩家与平台盈亏监控", VERSION)

    summary_df = _load_summary()
    if summary_df.empty:
        alert("暂时没有读取到世界杯投注数据。请确认 raw_bet_detail 已导入，并且投注详情包含 世界杯2026。", "warning")
        render_worldcup_rules()
        return

    s = summary_df.iloc[0]
    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        metric_card("总流水", _fmt_num(s.get("turnover")), "世界杯投注总下注金额", icon="💰")
    with c2:
        metric_card("有效投注", _fmt_num(s.get("valid_turnover")), "可用于盈亏分析", icon="🎯")
    with c3:
        metric_card("会员盈亏", _fmt_num(s.get("profit_loss")), "正数=会员赢，负数=会员输", icon="📉")
    with c4:
        metric_card("投注会员", _fmt_num(s.get("members")), "参与世界杯投注会员", icon="👥")
    with c5:
        metric_card("RTP", _fmt_pct(s.get("rtp")), "会员盈亏 / 有效投注", icon="⚠️")

    section("AI经营摘要", "规则版摘要，后续可接入 AI 助手。")
    brief(_summary_brief(s))

    daily = _load_daily()
    matches = _load_matches(limit=20)

    left, right = st.columns([1.3, 1])
    with left:
        section("世界杯每日走势", "按下注时间统计。")
        if not daily.empty:
            fig = px.line(daily, x="report_date", y=["turnover", "valid_turnover", "profit_loss"], markers=True)
            fig.update_layout(height=360, legend_title_text="指标")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("暂无每日走势资料。")

    with right:
        section("赛事流水Top20", "找出当前最需要监控的赛事。")
        if not matches.empty:
            show = matches[["match_name", "valid_turnover", "profit_loss", "members", "rtp"]].copy()
            show.columns = ["赛事", "有效投注", "会员盈亏", "会员数", "RTP"]
            st.dataframe(show, use_container_width=True, hide_index=True)
        else:
            st.info("暂无赛事资料。")

    section("赛事监控清单", "每场赛事的投注量、会员数、盈亏与 RTP。")
    if not matches.empty:
        show = matches.copy()
        show.columns = ["赛事", "开赛时间", "注单数", "会员数", "流水", "有效投注", "会员盈亏", "平均下注", "RTP"]
        st.dataframe(show, use_container_width=True, hide_index=True)


def render_match_monitor() -> None:
    apply_theme()
    hero("⚽ 比赛监控", "逐场查看流水、玩法、会员与近期注单", VERSION)

    matches = _load_matches(limit=300)
    if matches.empty:
        alert("暂无世界杯赛事资料。", "warning")
        return

    match_options = ["全部赛事"] + matches["match_name"].dropna().astype(str).tolist()
    selected = st.selectbox("选择赛事", match_options)

    play_df = _load_play_types(selected)
    players_df = _load_players(selected, limit=50)
    bets_df = _load_recent_bets(selected, limit=200)

    section("玩法分析", "看资金集中在哪些玩法。")
    if not play_df.empty:
        left, right = st.columns([1, 1])
        with left:
            fig = px.bar(play_df.head(15), x="valid_turnover", y="play_type", orientation="h", text="valid_turnover")
            fig.update_layout(height=430, yaxis={"categoryorder": "total ascending"})
            st.plotly_chart(fig, use_container_width=True)
        with right:
            show = play_df.copy()
            show.columns = ["玩法", "注单数", "会员数", "流水", "有效投注", "会员盈亏", "RTP"]
            st.dataframe(show, use_container_width=True, hide_index=True)
    else:
        st.info("暂无玩法资料。")

    section("会员排行", "当前赛事投注最高的会员。")
    if not players_df.empty:
        st.dataframe(players_df, use_container_width=True, hide_index=True)
    else:
        st.info("暂无会员排行。")

    section("近期注单", "最近200笔世界杯注单。")
    if not bets_df.empty:
        st.dataframe(bets_df, use_container_width=True, hide_index=True)
    else:
        st.info("暂无近期注单。")


def render_worldcup_players() -> None:
    apply_theme()
    hero("⚽ 世界杯玩家分析", "世界杯会员排行、代理贡献与风险线索", VERSION)

    players = _load_players(None, limit=100)
    if players.empty:
        alert("暂无世界杯会员资料。", "warning")
        return

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        metric_card("投注会员", _fmt_num(players["会员账号"].nunique()), "世界杯参与会员", icon="👥")
    with c2:
        metric_card("Top100流水", _fmt_num(players["有效投注"].sum()), "前100会员有效投注", icon="🏆")
    with c3:
        metric_card("Top会员RTP", _fmt_pct(players["RTP"].max()), "最高RTP会员", icon="⚠️")
    with c4:
        metric_card("Top会员盈亏", _fmt_num(players["会员盈亏"].max()), "会员最高盈利", icon="🔥")

    section("世界杯会员Top100", "可用于VIP运营与风控初筛。")
    st.dataframe(players, use_container_width=True, hide_index=True)

    section("代理贡献", "按代理汇总世界杯有效投注与盈亏。")
    agent_df = players.groupby("代理", dropna=False).agg(
        会员数=("会员账号", "nunique"),
        有效投注=("有效投注", "sum"),
        会员盈亏=("会员盈亏", "sum"),
    ).reset_index().sort_values("有效投注", ascending=False)
    st.dataframe(agent_df.head(50), use_container_width=True, hide_index=True)


def render_worldcup_rules() -> None:
    apply_theme()
    hero("⚽ 世界杯识别规则", "说明系统如何从投注记录识别世界杯注单", VERSION)

    section("当前识别规则")
    st.markdown(
        """
- 来源表：`raw_bet_detail`
- 识别字段：`投注详情`
- 包含以下关键字会被视为世界杯注单：`世界杯2026`、`FIFA世界杯2026`、`World Cup 2026`
- 排除规则：`投注详情` 中含有 `panda` 的注单排除
- 赛事名称：优先从 `投注详情` 中自动抽取，例如 `巴西 v 日本`
- 串关注单：如果包含多场赛事，暂时归类为 `串关/多场`
        """
    )

    section("建议下一版")
    st.markdown(
        """
1. 建立 `dim_worldcup_match` 赛事维度表，把不同语言与写法统一成标准赛事名称。  
2. 建立 `fact_worldcup_bet`，把世界杯注单从 `raw_bet_detail` 独立成事实表。  
3. 串关注单拆单，把一张串关单拆到多场赛事，统计会更精准。  
4. 加入赛前/滚球/早盘分类，方便风控判断投注时点。  
        """
    )
