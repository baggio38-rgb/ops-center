"""世界杯专区。

v1.4.2 World Cup Center
- 统一世界杯识别规则：必须包含「世界杯2026(在加拿大、墨西哥&美国)」
- 排除 Panda 注单
- 修正会员盈亏 / 平台盈亏
- 新增按阶段、按比赛统计，从小组赛到冠军赛都能查看
"""

from __future__ import annotations

from typing import Any

import pandas as pd
import plotly.express as px
import streamlit as st

try:
    from components.ui import apply_theme, hero, metric_card, section, alert, brief
except Exception:
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
VERSION = "v1.4.2"
WORLD_CUP_KEYWORD = "世界杯2026(在加拿大、墨西哥&美国)"

# 注意：总览必须与 BigQuery 验证 SQL 一致。
# 规则：投注详情必须包含完整世界杯字串，并排除 panda。
WORLD_CUP_WHERE = f"""
`投注详情` IS NOT NULL
AND CAST(`投注详情` AS STRING) LIKE '%{WORLD_CUP_KEYWORD}%'
AND LOWER(CAST(`投注详情` AS STRING)) NOT LIKE '%panda%'
"""

WORLD_CUP_BASE = f"""
WITH wc AS (
  SELECT
    TRIM(CAST(`会员账号` AS STRING)) AS member_id,
    UPPER(REGEXP_REPLACE(TRIM(CAST(`会员账号` AS STRING)), r'[^A-Za-z0-9]', '')) AS member_key,
    IFNULL(TRIM(CAST(`上级代理名称` AS STRING)), '') AS agent_name,
    TRIM(CAST(`场馆名称` AS STRING)) AS provider,
    TRIM(CAST(`游戏名称` AS STRING)) AS game_name,
    IFNULL(TRIM(CAST(`玩法` AS STRING)), '未识别玩法') AS play_type,
    TRIM(CAST(`盘口` AS STRING)) AS handicap,
    TRIM(CAST(`状态` AS STRING)) AS bet_status,
    TRIM(CAST(`投注详情` AS STRING)) AS bet_detail,
    SAFE_CAST(`下注金额` AS FLOAT64) AS turnover,
    SAFE_CAST(`有效投注` AS FLOAT64) AS valid_turnover,
    SAFE_CAST(`盈亏` AS FLOAT64) AS profit_loss,
    -SAFE_CAST(`盈亏` AS FLOAT64) AS platform_profit_loss,
    SAFE_CAST(`手续费` AS FLOAT64) AS fee,
    COALESCE(
      SAFE.PARSE_DATETIME('%Y-%m-%d %H:%M:%S', TRIM(CAST(`下注时间` AS STRING))),
      SAFE.PARSE_DATETIME('%Y/%m/%d %H:%M:%S', TRIM(CAST(`下注时间` AS STRING)))
    ) AS bet_time,
    COALESCE(
      SAFE.PARSE_DATETIME('%Y-%m-%d %H:%M:%S', TRIM(CAST(`开赛时间` AS STRING))),
      SAFE.PARSE_DATETIME('%Y/%m/%d %H:%M:%S', TRIM(CAST(`开赛时间` AS STRING))),
      SAFE.PARSE_DATETIME('%Y-%m-%d %H:%M:%S', REGEXP_EXTRACT(CAST(`投注详情` AS STRING), r'足球\\((\\d{{4}}-\\d{{2}}-\\d{{2}} \\d{{2}}:\\d{{2}}:\\d{{2}})\\)'))
    ) AS match_time,
    CASE
      WHEN REGEXP_CONTAINS(LOWER(CONCAT(IFNULL(CAST(`游戏名称` AS STRING), ''), ' ', IFNULL(CAST(`投注详情` AS STRING), ''))), r'串关|parlay')
        THEN '串关/多场'
      ELSE COALESCE(
        REGEXP_REPLACE(
          REGEXP_EXTRACT(CAST(`投注详情` AS STRING), r'世界杯2026\\(在加拿大、墨西哥&美国\\)[\\r\\n]+([^\\r\\n]+)'),
          r'\\s+vs\\s+', ' v '
        ),
        '未识别赛事'
      )
    END AS match_name,
    CASE
      WHEN REGEXP_CONTAINS(LOWER(CONCAT(IFNULL(CAST(`游戏名称` AS STRING), ''), ' ', IFNULL(CAST(`投注详情` AS STRING), ''))), r'串关|parlay') THEN '串关/多场'
      WHEN DATE(COALESCE(
        SAFE.PARSE_DATETIME('%Y-%m-%d %H:%M:%S', TRIM(CAST(`开赛时间` AS STRING))),
        SAFE.PARSE_DATETIME('%Y/%m/%d %H:%M:%S', TRIM(CAST(`开赛时间` AS STRING))),
        SAFE.PARSE_DATETIME('%Y-%m-%d %H:%M:%S', REGEXP_EXTRACT(CAST(`投注详情` AS STRING), r'足球\\((\\d{{4}}-\\d{{2}}-\\d{{2}} \\d{{2}}:\\d{{2}}:\\d{{2}})\\)'))
      )) <= DATE '2026-06-27' THEN '小组赛'
      WHEN DATE(COALESCE(
        SAFE.PARSE_DATETIME('%Y-%m-%d %H:%M:%S', TRIM(CAST(`开赛时间` AS STRING))),
        SAFE.PARSE_DATETIME('%Y/%m/%d %H:%M:%S', TRIM(CAST(`开赛时间` AS STRING))),
        SAFE.PARSE_DATETIME('%Y-%m-%d %H:%M:%S', REGEXP_EXTRACT(CAST(`投注详情` AS STRING), r'足球\\((\\d{{4}}-\\d{{2}}-\\d{{2}} \\d{{2}}:\\d{{2}}:\\d{{2}})\\)'))
      )) BETWEEN DATE '2026-06-28' AND DATE '2026-07-03' THEN '32强'
      WHEN DATE(COALESCE(
        SAFE.PARSE_DATETIME('%Y-%m-%d %H:%M:%S', TRIM(CAST(`开赛时间` AS STRING))),
        SAFE.PARSE_DATETIME('%Y/%m/%d %H:%M:%S', TRIM(CAST(`开赛时间` AS STRING))),
        SAFE.PARSE_DATETIME('%Y-%m-%d %H:%M:%S', REGEXP_EXTRACT(CAST(`投注详情` AS STRING), r'足球\\((\\d{{4}}-\\d{{2}}-\\d{{2}} \\d{{2}}:\\d{{2}}:\\d{{2}})\\)'))
      )) BETWEEN DATE '2026-07-04' AND DATE '2026-07-07' THEN '16强'
      WHEN DATE(COALESCE(
        SAFE.PARSE_DATETIME('%Y-%m-%d %H:%M:%S', TRIM(CAST(`开赛时间` AS STRING))),
        SAFE.PARSE_DATETIME('%Y/%m/%d %H:%M:%S', TRIM(CAST(`开赛时间` AS STRING))),
        SAFE.PARSE_DATETIME('%Y-%m-%d %H:%M:%S', REGEXP_EXTRACT(CAST(`投注详情` AS STRING), r'足球\\((\\d{{4}}-\\d{{2}}-\\d{{2}} \\d{{2}}:\\d{{2}}:\\d{{2}})\\)'))
      )) BETWEEN DATE '2026-07-09' AND DATE '2026-07-11' THEN '8强'
      WHEN DATE(COALESCE(
        SAFE.PARSE_DATETIME('%Y-%m-%d %H:%M:%S', TRIM(CAST(`开赛时间` AS STRING))),
        SAFE.PARSE_DATETIME('%Y/%m/%d %H:%M:%S', TRIM(CAST(`开赛时间` AS STRING))),
        SAFE.PARSE_DATETIME('%Y-%m-%d %H:%M:%S', REGEXP_EXTRACT(CAST(`投注详情` AS STRING), r'足球\\((\\d{{4}}-\\d{{2}}-\\d{{2}} \\d{{2}}:\\d{{2}}:\\d{{2}})\\)'))
      )) BETWEEN DATE '2026-07-14' AND DATE '2026-07-15' THEN '半决赛'
      WHEN DATE(COALESCE(
        SAFE.PARSE_DATETIME('%Y-%m-%d %H:%M:%S', TRIM(CAST(`开赛时间` AS STRING))),
        SAFE.PARSE_DATETIME('%Y/%m/%d %H:%M:%S', TRIM(CAST(`开赛时间` AS STRING))),
        SAFE.PARSE_DATETIME('%Y-%m-%d %H:%M:%S', REGEXP_EXTRACT(CAST(`投注详情` AS STRING), r'足球\\((\\d{{4}}-\\d{{2}}-\\d{{2}} \\d{{2}}:\\d{{2}}:\\d{{2}})\\)'))
      )) = DATE '2026-07-18' THEN '季军赛'
      WHEN DATE(COALESCE(
        SAFE.PARSE_DATETIME('%Y-%m-%d %H:%M:%S', TRIM(CAST(`开赛时间` AS STRING))),
        SAFE.PARSE_DATETIME('%Y/%m/%d %H:%M:%S', TRIM(CAST(`开赛时间` AS STRING))),
        SAFE.PARSE_DATETIME('%Y-%m-%d %H:%M:%S', REGEXP_EXTRACT(CAST(`投注详情` AS STRING), r'足球\\((\\d{{4}}-\\d{{2}}-\\d{{2}} \\d{{2}}:\\d{{2}}:\\d{{2}})\\)'))
      )) = DATE '2026-07-19' THEN '冠军赛'
      ELSE '未识别阶段'
    END AS match_stage,
    CAST(`注单流水号` AS STRING) AS bet_id
  FROM `{PROJECT}.{DATASET}.raw_bet_detail`
  WHERE {WORLD_CUP_WHERE}
)
"""

STAGE_ORDER_SQL = """
CASE match_stage
  WHEN '小组赛' THEN 1
  WHEN '32强' THEN 2
  WHEN '16强' THEN 3
  WHEN '8强' THEN 4
  WHEN '半决赛' THEN 5
  WHEN '季军赛' THEN 6
  WHEN '冠军赛' THEN 7
  WHEN '串关/多场' THEN 8
  ELSE 99
END
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


def _safe_sql_text(value: str) -> str:
    return str(value).replace("'", "''")


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
  COUNT(DISTINCT CASE WHEN match_name NOT IN ('串关/多场', '未识别赛事') THEN match_name END) AS matches,
  SUM(turnover) AS turnover,
  SUM(valid_turnover) AS valid_turnover,
  SUM(profit_loss) AS member_profit_loss,
  -SUM(profit_loss) AS platform_profit_loss,
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
  SUM(profit_loss) AS member_profit_loss,
  -SUM(profit_loss) AS platform_profit_loss,
  SAFE_DIVIDE(SUM(profit_loss), NULLIF(SUM(valid_turnover), 0)) AS rtp
FROM wc
WHERE bet_time IS NOT NULL
GROUP BY report_date
ORDER BY report_date;
"""
    )


def _load_matches(stage: str = "全部阶段", limit: int = 300) -> pd.DataFrame:
    where = ""
    if stage and stage != "全部阶段":
        where = f"WHERE match_stage = '{_safe_sql_text(stage)}'"
    return _safe_query(
        WORLD_CUP_BASE
        + f"""
SELECT
  match_stage,
  match_name,
  MIN(match_time) AS match_time,
  COUNT(*) AS bet_count,
  COUNT(DISTINCT member_key) AS members,
  SUM(turnover) AS turnover,
  SUM(valid_turnover) AS valid_turnover,
  SUM(profit_loss) AS member_profit_loss,
  -SUM(profit_loss) AS platform_profit_loss,
  AVG(turnover) AS avg_bet,
  SAFE_DIVIDE(SUM(profit_loss), NULLIF(SUM(valid_turnover), 0)) AS rtp
FROM wc
{where}
GROUP BY match_stage, match_name
ORDER BY {STAGE_ORDER_SQL}, match_time, valid_turnover DESC
LIMIT {int(limit)};
"""
    )


def _load_stage_summary() -> pd.DataFrame:
    return _safe_query(
        WORLD_CUP_BASE
        + f"""
SELECT
  match_stage,
  COUNT(*) AS bet_count,
  COUNT(DISTINCT member_key) AS members,
  COUNT(DISTINCT match_name) AS matches,
  SUM(turnover) AS turnover,
  SUM(valid_turnover) AS valid_turnover,
  SUM(profit_loss) AS member_profit_loss,
  -SUM(profit_loss) AS platform_profit_loss,
  SAFE_DIVIDE(SUM(profit_loss), NULLIF(SUM(valid_turnover), 0)) AS rtp
FROM wc
GROUP BY match_stage
ORDER BY {STAGE_ORDER_SQL};
"""
    )


def _load_play_types(match_name: str | None = None) -> pd.DataFrame:
    where = ""
    if match_name and match_name != "全部赛事":
        where = f"WHERE match_name = '{_safe_sql_text(match_name)}'"
    return _safe_query(
        WORLD_CUP_BASE
        + f"""
SELECT
  IFNULL(play_type, '未识别玩法') AS play_type,
  COUNT(*) AS bet_count,
  COUNT(DISTINCT member_key) AS members,
  SUM(turnover) AS turnover,
  SUM(valid_turnover) AS valid_turnover,
  SUM(profit_loss) AS member_profit_loss,
  -SUM(profit_loss) AS platform_profit_loss,
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
        where = f"WHERE match_name = '{_safe_sql_text(match_name)}'"
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
  -SUM(profit_loss) AS `平台盈亏`,
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
        where = f"WHERE match_name = '{_safe_sql_text(match_name)}'"
    return _safe_query(
        WORLD_CUP_BASE
        + f"""
SELECT
  bet_time AS `下注时间`,
  member_id AS `会员账号`,
  match_stage AS `阶段`,
  match_name AS `赛事`,
  provider AS `场馆`,
  game_name AS `游戏`,
  play_type AS `玩法`,
  turnover AS `下注金额`,
  valid_turnover AS `有效投注`,
  profit_loss AS `会员盈亏`,
  platform_profit_loss AS `平台盈亏`,
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
    platform_profit = float(summary.get("platform_profit_loss") or 0)
    member_profit = float(summary.get("member_profit_loss") or 0)
    rtp = float(summary.get("rtp") or 0)
    bets = int(summary.get("bet_count") or 0)
    members = int(summary.get("members") or 0)

    items.append(f"世界杯目前累计 {bets:,} 笔注单，参与会员 {members:,} 人，总流水 {_fmt_num(turnover)}。")
    if platform_profit >= 0:
        items.append(f"平台当前累计盈利 {_fmt_num(platform_profit)}，对应会员盈亏 {_fmt_num(member_profit)}。")
    else:
        items.append(f"平台当前累计亏损 {_fmt_num(platform_profit)}，建议优先查看高流水赛事与高RTP会员。")
    if rtp >= 0.98:
        items.append(f"整体 RTP {_fmt_pct(rtp)} 偏高，建议风控关注异常集中投注。")
    else:
        items.append(f"整体 RTP {_fmt_pct(rtp)}，目前处于可观察区间。")
    return items


def _format_money_columns(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    for col in ["流水", "有效投注", "会员盈亏", "平台盈亏", "平均下注"]:
        if col in out.columns:
            out[col] = out[col].apply(_fmt_num)
    if "RTP" in out.columns:
        out["RTP"] = out["RTP"].apply(_fmt_pct)
    return out


def render_worldcup_overview() -> None:
    apply_theme()
    hero("⚽ 世界杯专区", "世界杯投注、赛事、玩家与平台盈亏监控", VERSION)

    summary_df = _load_summary()
    if summary_df.empty:
        alert("暂时没有读取到世界杯投注数据。请确认 raw_bet_detail 已导入，并且投注详情包含完整字串。", "warning")
        render_worldcup_rules()
        return

    s = summary_df.iloc[0]
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    with c1:
        metric_card("总流水", _fmt_num(s.get("turnover")), "世界杯投注总下注金额", icon="💰")
    with c2:
        metric_card("有效投注", _fmt_num(s.get("valid_turnover")), "可用于盈亏分析", icon="🎯")
    with c3:
        metric_card("会员盈亏", _fmt_num(s.get("member_profit_loss")), "正数=会员赢，负数=会员输", icon="👤")
    with c4:
        metric_card("平台盈亏", _fmt_num(s.get("platform_profit_loss")), "正数=平台赢，负数=平台输", icon="🏦")
    with c5:
        metric_card("投注会员", _fmt_num(s.get("members")), "参与世界杯投注会员", icon="👥")
    with c6:
        metric_card("RTP", _fmt_pct(s.get("rtp")), "会员盈亏 / 有效投注", icon="⚠️")

    section("AI经营摘要", "规则版摘要，后续可接入 AI 助手。")
    brief(_summary_brief(s))

    daily = _load_daily()
    stages = _load_stage_summary()
    matches = _load_matches(limit=50)

    left, right = st.columns([1.25, 1])
    with left:
        section("世界杯每日走势", "按下注时间统计。")
        if not daily.empty:
            chart_df = daily.rename(columns={
                "turnover": "流水",
                "valid_turnover": "有效投注",
                "member_profit_loss": "会员盈亏",
                "platform_profit_loss": "平台盈亏",
            })
            fig = px.line(chart_df, x="report_date", y=["流水", "有效投注", "会员盈亏", "平台盈亏"], markers=True)
            fig.update_layout(height=380, legend_title_text="指标")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("暂无每日走势资料。")

    with right:
        section("阶段汇总", "从小组赛到冠军赛的整体表现。")
        if not stages.empty:
            show_stage = stages.rename(columns={
                "match_stage": "阶段",
                "bet_count": "注单数",
                "members": "会员数",
                "matches": "赛事数",
                "turnover": "流水",
                "valid_turnover": "有效投注",
                "member_profit_loss": "会员盈亏",
                "platform_profit_loss": "平台盈亏",
                "rtp": "RTP",
            })
            st.dataframe(_format_money_columns(show_stage), use_container_width=True, hide_index=True)
        else:
            st.info("暂无阶段资料。")

    section("比赛排行榜", "按阶段与赛事列出每场世界杯投注数据。")
    if not matches.empty:
        show = matches.rename(columns={
            "match_stage": "阶段",
            "match_name": "赛事",
            "match_time": "开赛时间",
            "bet_count": "注单数",
            "members": "会员数",
            "turnover": "流水",
            "valid_turnover": "有效投注",
            "member_profit_loss": "会员盈亏",
            "platform_profit_loss": "平台盈亏",
            "avg_bet": "平均下注",
            "rtp": "RTP",
        })
        st.dataframe(_format_money_columns(show), use_container_width=True, hide_index=True)
    else:
        st.info("暂无赛事资料。")


def render_match_monitor() -> None:
    apply_theme()
    hero("⚽ 比赛监控", "逐场查看流水、玩法、会员与近期注单", VERSION)

    matches_all = _load_matches(limit=500)
    if matches_all.empty:
        alert("暂无世界杯赛事资料。", "warning")
        return

    stage_options = ["全部阶段"] + [x for x in ["小组赛", "32强", "16强", "8强", "半决赛", "季军赛", "冠军赛", "串关/多场", "未识别阶段"] if x in set(matches_all["match_stage"].astype(str))]
    selected_stage = st.selectbox("选择阶段", stage_options)
    matches = matches_all if selected_stage == "全部阶段" else matches_all[matches_all["match_stage"] == selected_stage]

    match_options = ["全部赛事"] + matches["match_name"].dropna().astype(str).tolist()
    selected = st.selectbox("选择赛事", match_options)

    if selected != "全部赛事":
        one = matches[matches["match_name"].astype(str) == selected]
        if not one.empty:
            row = one.iloc[0]
            c1, c2, c3, c4, c5, c6 = st.columns(6)
            with c1:
                metric_card("流水", _fmt_num(row.get("turnover")), icon="💰")
            with c2:
                metric_card("有效投注", _fmt_num(row.get("valid_turnover")), icon="🎯")
            with c3:
                metric_card("会员盈亏", _fmt_num(row.get("member_profit_loss")), icon="👤")
            with c4:
                metric_card("平台盈亏", _fmt_num(row.get("platform_profit_loss")), icon="🏦")
            with c5:
                metric_card("投注会员", _fmt_num(row.get("members")), icon="👥")
            with c6:
                metric_card("RTP", _fmt_pct(row.get("rtp")), icon="⚠️")

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
            show = play_df.rename(columns={
                "play_type": "玩法",
                "bet_count": "注单数",
                "members": "会员数",
                "turnover": "流水",
                "valid_turnover": "有效投注",
                "member_profit_loss": "会员盈亏",
                "platform_profit_loss": "平台盈亏",
                "rtp": "RTP",
            })
            st.dataframe(_format_money_columns(show), use_container_width=True, hide_index=True)
    else:
        st.info("暂无玩法资料。")

    section("会员排行", "当前赛事投注最高的会员。")
    if not players_df.empty:
        st.dataframe(_format_money_columns(players_df), use_container_width=True, hide_index=True)
    else:
        st.info("暂无会员排行。")

    section("近期注单", "最近200笔世界杯注单。")
    if not bets_df.empty:
        st.dataframe(bets_df, use_container_width=True, hide_index=True)
    else:
        st.info("暂无近期注单。")


def render_worldcup_database() -> None:
    apply_theme()
    hero("⚽ 世界杯资料库", "小组赛到冠军赛，每场投注数据总表", VERSION)

    matches = _load_matches(limit=1000)
    if matches.empty:
        alert("暂无世界杯比赛资料。", "warning")
        return

    q = st.text_input("搜索赛事 / 阶段", "")
    show = matches.copy()
    if q.strip():
        mask = show["match_name"].astype(str).str.contains(q.strip(), case=False, na=False) | show["match_stage"].astype(str).str.contains(q.strip(), case=False, na=False)
        show = show[mask]

    show = show.rename(columns={
        "match_stage": "阶段",
        "match_name": "赛事",
        "match_time": "开赛时间",
        "bet_count": "注单数",
        "members": "会员数",
        "turnover": "流水",
        "valid_turnover": "有效投注",
        "member_profit_loss": "会员盈亏",
        "platform_profit_loss": "平台盈亏",
        "avg_bet": "平均下注",
        "rtp": "RTP",
    })
    st.dataframe(_format_money_columns(show), use_container_width=True, hide_index=True)


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
    st.dataframe(_format_money_columns(players), use_container_width=True, hide_index=True)

    section("代理贡献", "按代理汇总世界杯有效投注与盈亏。")
    agent_df = players.groupby("代理", dropna=False).agg(
        会员数=("会员账号", "nunique"),
        有效投注=("有效投注", "sum"),
        会员盈亏=("会员盈亏", "sum"),
        平台盈亏=("平台盈亏", "sum"),
    ).reset_index().sort_values("有效投注", ascending=False)
    st.dataframe(_format_money_columns(agent_df.head(50)), use_container_width=True, hide_index=True)


def render_worldcup_rules() -> None:
    apply_theme()
    hero("⚽ 世界杯识别规则", "说明系统如何从投注记录识别世界杯注单", VERSION)

    section("当前识别规则")
    st.markdown(
        f"""
- 来源表：`raw_bet_detail`
- 识别字段：`投注详情`
- 必须包含完整字串：`{WORLD_CUP_KEYWORD}`
- 排除规则：`投注详情` 中含有 `panda` 的注单排除
- 会员盈亏：`SUM(盈亏)`
- 平台盈亏：`-SUM(盈亏)`
- 赛事名称：优先从 `投注详情` 中自动抽取，例如 `巴西 v 日本`
- 串关注单：保留在总览中，赛事统计会归类为 `串关/多场`
        """
    )

    section("BigQuery 验证 SQL")
    st.code(
        f"""
WITH worldcup AS (
  SELECT *
  FROM `{PROJECT}.{DATASET}.raw_bet_detail`
  WHERE `投注详情` LIKE '%{WORLD_CUP_KEYWORD}%'
    AND LOWER(`投注详情`) NOT LIKE '%panda%'
)
SELECT
  COUNT(*) AS bet_count,
  COUNT(DISTINCT `会员账号`) AS members,
  SUM(SAFE_CAST(`下注金额` AS FLOAT64)) AS turnover,
  SUM(SAFE_CAST(`有效投注` AS FLOAT64)) AS valid_turnover,
  SUM(SAFE_CAST(`盈亏` AS FLOAT64)) AS member_profit_loss,
  -SUM(SAFE_CAST(`盈亏` AS FLOAT64)) AS platform_profit_loss
FROM worldcup;
        """.strip(),
        language="sql",
    )
