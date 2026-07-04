"""Realtime and health monitoring feature pages.

V6.6 extracts monitoring-style pages from member/upload modules. The actual UI
logic is preserved, while shared helpers still come from core.legacy during the
transition.
"""

from __future__ import annotations

import core.legacy as _legacy
from features.upload_admin import _data_health_rows

# Import every legacy helper used by the moved page bodies.
globals().update({k: getattr(_legacy, k) for k in dir(_legacy) if not k.startswith("__")})

def render_realtime():
    rt = load_table('raw_realtime_bet')
    hero('实时波动', '查看实时投注分时波动、热度分布与异常变化。', latest_imported_at(rt),
         basis='即时注单（后台导出·上传）',
         detail=(
             '**分析范围**：实时投注分时波动、DAU 近似、时段热度与异常监测。\n\n'
             '**数据来源**：即时注单（报表中心→即时注单）。\n\n'
             '**更新方式**：手动上传（为时点快照，按需更新）。完整对照见「数据说明」页。'
         ))
    rt = parse_realtime_time(rt)
    if '日期' not in rt.columns or rt['日期'].isna().all():
        st.warning('实时投注表当前无法从字段【时间】拆出可用日期。常见原始格式应类似 `2026-01-31 23~24`；若 BigQuery 中该字段已被改写，请先确认原始值。')
        return

    rt, start, end, month = date_range_picker(rt, '日期', 'rt', default_last_days=None)
    if '游戏类型' in rt.columns:
        rt = apply_multiselect(rt, '游戏类型', '游戏类型', 'rt_type', default_all=True)
    if rt.empty:
        st.warning('当前筛选条件下无数据。')
        return

    daily_bettors_series = (
        rt.groupby('日期')['时段投注人数'].sum()
        if '时段投注人数' in rt.columns else pd.Series(dtype=float)
    )
    avg_daily_bettors = float(daily_bettors_series.mean()) if not daily_bettors_series.empty else None

    cols = st.columns(5)
    show_metric(
        cols[0], '日投注人次（DAU 近似）', fmt_num(avg_daily_bettors),
        help_text=tooltip_text('日投注人次（DAU 近似）'),
    )
    show_metric(cols[1], '时段投注人数', fmt_num(safe_sum(rt, '时段投注人数')))
    show_metric(cols[2], '投注金额', fmt_num(safe_sum(rt, '投注金额')))
    show_metric(cols[3], '有效投注额', fmt_num(safe_sum(rt, '有效投注额')))
    rt_winloss = safe_sum(rt, '公司输赢')
    show_metric(cols[4], '公司输赢', fmt_num(rt_winloss), tone=tone_by_sign(rt_winloss))

    # ── 时段异常监测：最新一天各时段 vs 前 7 日同时段均值，偏离 ±20% 自动标示 ──
    if {'日期', '时段', '有效投注额'}.issubset(rt.columns):
        with st.container(border=True):
            section_header('时段异常监测', '最新一天各时段有效投注额，对比前 7 日同时段均值；下跌 ≥20% 标红、上涨 ≥20% 标绿。')
            slot_daily = rt.groupby(['日期', '时段'], as_index=False)['有效投注额'].sum()
            latest_d = slot_daily['日期'].max()
            base = slot_daily[(slot_daily['日期'] < latest_d) &
                              (slot_daily['日期'] >= latest_d - pd.Timedelta(days=7))]
            cur = slot_daily[slot_daily['日期'] == latest_d]
            if base.empty or cur.empty:
                st.caption('当前筛选范围内数据不足（最新一天之前需要至少一天数据才能对比）。')
            else:
                base_avg = base.groupby('时段', as_index=False)['有效投注额'].mean().rename(columns={'有效投注额': '前7日均值'})
                cmp_df = pd.merge(cur[['时段', '有效投注额']], base_avg, on='时段', how='inner').rename(columns={'有效投注额': '最新一天'})
                cmp_df['偏离%'] = (cmp_df['最新一天'] - cmp_df['前7日均值']) / cmp_df['前7日均值'].replace(0, pd.NA) * 100
                cmp_df = cmp_df.dropna(subset=['偏离%']).copy()
                cmp_df['_h'] = pd.to_numeric(cmp_df['时段'].astype(str).str.extract(r'(\d{1,2})')[0], errors='coerce')
                cmp_df = cmp_df.sort_values('_h')
                drops = cmp_df[cmp_df['偏离%'] <= -20]
                spikes = cmp_df[cmp_df['偏离%'] >= 20]
                if drops.empty and spikes.empty:
                    st.markdown(
                        status_badge(f'{latest_d:%m-%d} 各时段流水均在前 7 日均值 ±20% 内，未见异常', 'good'),
                        unsafe_allow_html=True,
                    )
                else:
                    badges = []
                    for _, r in drops.iterrows():
                        badges.append(status_badge(
                            f'{r["时段"]} 时段流水 ▼{abs(r["偏离%"]):.0f}%（{fmt_num(r["最新一天"])} / 均值 {fmt_num(r["前7日均值"])}）', 'bad'))
                    for _, r in spikes.iterrows():
                        badges.append(status_badge(f'{r["时段"]} 时段流水 ▲{r["偏离%"]:.0f}%', 'good'))
                    st.markdown(f'<div class="badge-row">{"".join(badges)}</div>', unsafe_allow_html=True)
                figd = go.Figure()
                figd.add_trace(go.Bar(
                    x=cmp_df['时段'], y=cmp_df['最新一天'], name=f'{latest_d:%m-%d}',
                    marker_color=[RED if v <= -20 else (GREEN if v >= 20 else BLUE) for v in cmp_df['偏离%']],
                ))
                figd.add_trace(go.Scatter(
                    x=cmp_df['时段'], y=cmp_df['前7日均值'], name='前 7 日均值', mode='lines',
                    line=dict(color=AMBER, width=2, dash='dot'),
                ))
                figd.update_layout(height=300, template=TEMPLATE, hovermode='x unified',
                                   legend=dict(orientation='h', y=-0.25), xaxis_title=None, yaxis_title='有效投注额')
                st.plotly_chart(figd, width='stretch')

    if not daily_bettors_series.empty:
        with st.container(border=True):
            section_header('日投注人次趋势（DAU 近似）',
                           '按日加总各时段「时段投注人数」，叠加 7 日移动平均看趋势。注意：会员可能跨时段重复计入，是 DAU 的近似。')
            daily_b = daily_bettors_series.reset_index()
            daily_b.columns = ['日期', '日投注人次']
            daily_b = daily_b.sort_values('日期')
            daily_b['7日均值'] = daily_b['日投注人次'].rolling(window=7, min_periods=1).mean()
            fig_dau = go.Figure()
            fig_dau.add_trace(go.Bar(
                x=daily_b['日期'], y=daily_b['日投注人次'],
                name='日投注人次', marker_color=CYAN, opacity=0.55,
            ))
            fig_dau.add_trace(go.Scatter(
                x=daily_b['日期'], y=daily_b['7日均值'],
                name='7 日均值', mode='lines',
                line=dict(color=AMBER, width=2.5, shape='spline', smoothing=0.6),
            ))
            fig_dau.update_layout(
                height=340, template=TEMPLATE, hovermode='x unified',
                legend=dict(orientation='h', y=-0.2),
                xaxis_title=None, yaxis_title='人次',
            )
            st.plotly_chart(fig_dau, width='stretch')

    c1, c2 = st.columns(2)
    with c1:
        with st.container(border=True):
            section_header('按日期趋势')
            daily = rt.groupby('日期', as_index=False).agg({'有效投注额': 'sum', '公司输赢': 'sum'})
            fig = px.line(daily.melt(id_vars='日期', var_name='指标', value_name='值'), x='日期', y='值', color='指标', template=TEMPLATE,
                          color_discrete_sequence=[CYAN, RED])
            fig.update_traces(line=dict(width=2.5, shape='spline', smoothing=0.6))
            fig.update_layout(height=380, hovermode='x unified', xaxis_title=None,
                              legend=dict(orientation='h', y=-0.18))
            st.plotly_chart(fig, width='stretch')
    with c2:
        with st.container(border=True):
            section_header('时段热度图')
            if '时段' in rt.columns and '游戏类型' in rt.columns:
                heat = rt.groupby(['游戏类型', '时段'], as_index=False)['有效投注额'].sum()
                if not heat.empty:
                    pivot = heat.pivot(index='游戏类型', columns='时段', values='有效投注额').fillna(0)

                    def _hour_key(val):
                        s = str(val)
                        m = re.match(r'(\d{1,2})', s)
                        return int(m.group(1)) if m else 99

                    ordered_cols = sorted(list(pivot.columns), key=_hour_key)
                    pivot = pivot.reindex(columns=ordered_cols)

                    fig = go.Figure(
                        data=go.Heatmap(
                            z=pivot.values,
                            x=list(pivot.columns),
                            y=list(pivot.index),
                            colorscale='YlOrRd',
                            hovertemplate='时段:%{x}<br>游戏类型:%{y}<br>有效投注额:%{z:,.0f}<extra></extra>',
                            colorbar=dict(title='金额', thickness=14),
                            xgap=1,
                            ygap=1,
                        )
                    )
                    fig.update_layout(
                        template=TEMPLATE,
                        height=450,
                        margin=dict(l=20, r=20, t=10, b=20),
                        xaxis=dict(title='时段', tickangle=-45, automargin=True),
                        yaxis=dict(title='游戏类型', automargin=True),
                    )
                    st.plotly_chart(fig, width='stretch')


def render_data_health():
    import datetime as _dt
    hero('数据健康',
         '一览各报表数据更新到几号、是否滞后，便于及时补数与交接。绿＝最新，黄＝稍旧，红＝需尽快更新。',
         source_badge='数据健康检查')
    today = _dt.date.today()
    cur_ym = (today.year, today.month)

    def _ym(s):
        s = str(s)
        if len(s) >= 7 and s[4] == '-':
            return (int(s[:4]), int(s[5:7]))
        if len(s) >= 6 and s[:6].isdigit():
            return (int(s[:4]), int(s[4:6]))
        return None

    def _month_gap(s):
        ym = _ym(s)
        if not ym:
            return None
        return (cur_ym[0] - ym[0]) * 12 + (cur_ym[1] - ym[1])

    out = []
    red = yellow = 0
    for name, kind, max_d, n in _data_health_rows():
        if not max_d or max_d == 'None':
            status, note = '❌ 无数据', '表为空或查询失败'
            red += 1
        elif kind == 'auto':
            try:
                d = _dt.date.fromisoformat(max_d)
                gap = (today - d).days
            except Exception:
                gap = None
            if gap is None:
                status, note = '⚠️ 待查', '日期解析失败'
                yellow += 1
            elif gap <= 1:
                status, note = '✅ 最新', '自动更新中'
            elif gap <= 3:
                status, note = f'⚠️ 滞后 {gap} 天', '检查排程是否正常'
                yellow += 1
            else:
                status, note = f'❌ 滞后 {gap} 天', '排程可能失败，需检查'
                red += 1
        else:  # manual
            mg = _month_gap(max_d)
            if mg is None:
                status, note = '⚠️ 待查', '日期解析失败'
                yellow += 1
            elif mg <= 0:
                status, note = '✅ 本月已更新', '手动上传'
            elif mg == 1:
                status, note = '⚠️ 只到上月', '本月待上传'
                yellow += 1
            else:
                status, note = f'❌ 落后 {mg} 个月', '需补上传'
                red += 1
        cat = '🤖 自动' if kind == 'auto' else '📤 手动上传'
        out.append({'报表': name, '类别': cat, '数据最新': max_d or '—',
                    '状态': status, '说明': note, '_sev': (2 if status.startswith('❌') else 1 if status.startswith('⚠️') else 0)})

    if red:
        st.error(f'有 {red} 张表需尽快更新（红）。', icon='🚨')
    elif yellow:
        st.warning(f'有 {yellow} 张表稍旧（黄），其余正常。', icon='⚠️')
    else:
        st.success('所有数据均为最新 ✅', icon='✅')

    df = pd.DataFrame(out).sort_values('_sev', ascending=False).drop(columns='_sev')
    st.dataframe(df, use_container_width=True, hide_index=True)
    st.caption('判定：自动表期望更新到昨日（滞后>3天标红）；手动表期望本月已上传（只到上月标黄、更早标红）。'
               '需要补哪些、从后台哪里导，见「数据说明」页。缓存 10 分钟，刷新页面可重查。')
