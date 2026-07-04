"""Member value feature pages.

V6.3 moves member-value render implementations out of core.legacy.
Shared helpers still come from core.legacy during the transition, so behavior
stays identical while core.legacy continues to slim down.
"""

from __future__ import annotations

import core.legacy as _legacy

# Import every legacy helper, including private helpers used inside these pages.
globals().update({k: getattr(_legacy, k) for k in dir(_legacy) if not k.startswith("__")})

def render_member_value():
    member = load_table('raw_member_report')
    top = load_table('raw_top_report')
    hero('会员价值', '查看会员结构、高价值用户集中度、VIP 分布与月快照状态。', latest_imported_at(member, top),
         basis='会员报表＋TOP报表（后台导出·每月上传）',
         detail=(
             '**分析范围**：会员结构、VIP 分布、ARPU、高价值用户集中度与月度留存。\n\n'
             '**数据来源（后台导出 → 上传）**：\n'
             '- 会员报表（报表中心→会员报表，须按注册时间、完整日期、全部页数导出）\n'
             '- TOP报表（报表中心→TOP报表）\n\n'
             '**计算口径**：会员身份＝会员账号＋代理（同名挂不同代理为不同人）；首存金额为一次性属性，统计前需去重。\n\n'
             '**更新方式**：手动上传。完整对照见「数据说明」页。'
         ))

    # 日期筛选统一用全站同款预设(全部/本月/上月/近7天/近30天/自订)，按「会员注册时间」筛
    if '注册时间' in member.columns:
        st.markdown('**按会员注册时间筛选**')
        member, _mv_s, _mv_e, _mv_m = date_range_picker(member, '注册时间', 'mv')

    top = get_snapshot_month(top)
    snap_options = [x for x in sorted(top['__snapshot_month__'].dropna().unique().tolist())]
    selected_snapshot = st.selectbox('TOP 快照月份', snap_options if snap_options else ['未提供快照字段'], key='mv_top_snapshot')
    if snap_options:
        top = top[top['__snapshot_month__'] == selected_snapshot].copy()

    member, notices, current = member_default_filters(member)
    # 统一会员去重键：账号+代理（同名挂不同代理=不同人），跨快照月也只算一次
    if '会员账号' in member.columns:
        if '代理' in member.columns:
            member['__member_key__'] = member['会员账号'].astype(str) + ' @ ' + member['代理'].astype(str)
        else:
            member['__member_key__'] = member['会员账号'].astype(str)
    add_info_box(notices)
    current_line = []
    for k, vals in current.items():
        if vals:
            current_line.append(f"{k}={' / '.join(vals)}")
    if current_line:
        st.caption('当前口径：' + '｜'.join(current_line))

    cols = st.columns(6)
    total_members = member_count(member)
    total_income = safe_sum(member, '公司收入')
    arpu_value = (total_income / total_members) if total_members else None
    # 首存金额是「一次性属性」(每月快照重复同一个值)，按行数会把同一人算 N 次→必须先按人去重再数
    member_unique = member.drop_duplicates('__member_key__') if '__member_key__' in member.columns else member
    first_dep_n = int((pd.to_numeric(member_unique['首存金额'], errors='coerce').fillna(0) > 0).sum()) if '首存金额' in member_unique.columns else 0
    show_metric(cols[0], '会员总数', fmt_num(total_members))
    show_metric(cols[1], '首存人数', fmt_num(first_dep_n))
    show_metric(cols[2], '总有效投注额', fmt_num(safe_sum(member, '有效投注额')))
    show_metric(cols[3], '公司收入', fmt_num(total_income), help_text=tooltip_text('公司收入'),
                tone=tone_by_sign(total_income))
    show_metric(cols[4], 'ARPU（用户均收）', fmt_num(arpu_value), help_text=tooltip_text('ARPU（用户均收）'),
                tone='accent')
    top_total = safe_sum(top, '有效投注额')
    top20_total = float(top.nlargest(20, '有效投注额')['有效投注额'].sum()) if {'有效投注额'}.issubset(top.columns) and not top.empty else 0
    top20_share = (top20_total / top_total) if top_total else None
    show_metric(cols[5], 'TOP20投注占比', fmt_pct(top20_share), help_text=tooltip_text('TOP20投注占比'))
    st.caption('口径：会员总数 / 首存人数 按「会员账号+代理」去重（每人算一次）；总有效投注额 / 公司收入 / ARPU '
               '为所选会员在数据库各月快照的**累计**值（投注额、公司收入是逐月数字，跨月相加=区间累计）。')

    c1, c2 = st.columns(2)
    with c1:
        with st.container(border=True):
            section_header('用户来源分布（原始字段）')
            if '用户来源' in member.columns and not member.empty:
                _md = member.drop_duplicates('__member_key__') if '__member_key__' in member.columns else member
                source_df = _md['用户来源'].fillna('空值').value_counts().reset_index()
                source_df.columns = ['用户来源', '会员数']
                fig = px.pie(source_df, names='用户来源', values='会员数', hole=0.58, template=TEMPLATE,
                             color_discrete_sequence=[PURPLE, BLUE, CYAN, GREEN, AMBER, RED])
                fig.update_traces(textinfo='percent', textfont_size=12,
                                  marker=dict(line=dict(color='rgba(7,15,30,0.9)', width=2)))
                fig.update_layout(
                    height=360,
                    legend=dict(orientation='h', y=-0.12),
                    annotations=[dict(text=f'会员<br><b>{fmt_num(int(source_df["会员数"].sum()))}</b>',
                                      x=0.5, y=0.5, showarrow=False,
                                      font=dict(size=14, color='#f0f5ff'))],
                )
                st.plotly_chart(fig, width='stretch')
    with c2:
        with st.container(border=True):
            section_header('VIP等级分布（原始字段）')
            if 'VIP等级' in member.columns and not member.empty:
                _md = member.drop_duplicates('__member_key__') if '__member_key__' in member.columns else member
                vip_df = _md['VIP等级'].fillna('空值').astype(str).value_counts().reset_index()
                vip_df.columns = ['VIP等级', '会员数']
                fig = px.bar(vip_df, x='VIP等级', y='会员数', template=TEMPLATE, color='会员数', color_continuous_scale='Purples')
                fig.update_layout(height=360, coloraxis_showscale=False, xaxis_title=None)
                st.plotly_chart(fig, width='stretch')

    section_header('ARPU（用户均收）按 VIP 等级 / 用户来源切片',
                   'ARPU = SUM(公司收入) ÷ DISTINCT(会员账号+代理)。分析各层级会员与来源渠道的人均价值。')
    c_arpu1, c_arpu2 = st.columns(2)
    with c_arpu1, st.container(border=True):
        if {'VIP等级', '公司收入', '会员账号'}.issubset(member.columns) and not member.empty:
            tmp_vip = member[['VIP等级', '公司收入', '__member_key__']].copy()
            tmp_vip['VIP等级'] = tmp_vip['VIP等级'].fillna('空值').astype(str)
            arpu_vip = tmp_vip.groupby('VIP等级', as_index=False).agg(
                公司收入=('公司收入', 'sum'),
                会员数=('__member_key__', 'nunique'),
            )
            arpu_vip['ARPU'] = arpu_vip.apply(
                lambda r: r['公司收入'] / r['会员数'] if r['会员数'] else 0, axis=1
            )
            arpu_vip = arpu_vip.sort_values('VIP等级')
            fig = px.bar(
                arpu_vip, x='VIP等级', y='ARPU', template=TEMPLATE,
                color='ARPU', color_continuous_scale='Tealgrn',
                hover_data={'公司收入': ':,.0f', '会员数': ':,.0f', 'ARPU': ':,.0f'},
                title='按 VIP 等级',
            )
            fig.update_layout(height=320, coloraxis_showscale=False)
            st.plotly_chart(fig, width='stretch')
        else:
            st.caption('当前数据缺少 VIP等级 或 公司收入 字段，跳过此切片。')
    with c_arpu2, st.container(border=True):
        if {'用户来源', '公司收入', '会员账号'}.issubset(member.columns) and not member.empty:
            tmp_src = member[['用户来源', '公司收入', '__member_key__']].copy()
            tmp_src['用户来源'] = tmp_src['用户来源'].fillna('空值').astype(str)
            arpu_src = tmp_src.groupby('用户来源', as_index=False).agg(
                公司收入=('公司收入', 'sum'),
                会员数=('__member_key__', 'nunique'),
            )
            arpu_src['ARPU'] = arpu_src.apply(
                lambda r: r['公司收入'] / r['会员数'] if r['会员数'] else 0, axis=1
            )
            arpu_src = arpu_src.sort_values('ARPU', ascending=False)
            fig = px.bar(
                arpu_src, x='用户来源', y='ARPU', template=TEMPLATE,
                color='ARPU', color_continuous_scale='Blues',
                hover_data={'公司收入': ':,.0f', '会员数': ':,.0f', 'ARPU': ':,.0f'},
                title='按用户来源',
            )
            fig.update_layout(height=320, coloraxis_showscale=False)
            st.plotly_chart(fig, width='stretch')
        else:
            st.caption('当前数据缺少 用户来源 或 公司收入 字段，跳过此切片。')

    section_header('月快照状态')
    member_snapshot_ready = has_member_snapshot(member)
    status_cols = st.columns(1)
    show_metric(status_cols[0], 'TOP快照月份', selected_snapshot if snap_options else '未提供')

    retention = compute_monthly_retention(member)
    if member_snapshot_ready and retention is not None and not retention.empty:
        cols = st.columns(3)
        last_row = retention.iloc[-1]
        show_metric(cols[0], '次月活跃留存率', fmt_pct(last_row['次月活跃留存率']), tone='accent')
        show_metric(cols[1], '次月存款留存率', fmt_pct(last_row['次月存款留存率']), tone='accent')
        show_metric(cols[2], '首存用户次月留存率', fmt_pct(last_row['首存用户次月留存率']), tone='accent')
        with st.container(border=True):
            fig = px.line(
                retention.melt(
                    id_vars=['月份', '次月'],
                    value_vars=['次月活跃留存率', '次月存款留存率', '首存用户次月留存率'],
                    var_name='指标',
                    value_name='值'
                ),
                x='月份', y='值', color='指标', template=TEMPLATE
            )
            fig.update_traces(line=dict(width=2.5, shape='spline', smoothing=0.6))
            fig.update_layout(height=360, hovermode='x unified', xaxis_title=None,
                              legend=dict(orientation='h', y=-0.18))
            st.plotly_chart(fig, width='stretch')
        st.caption(
            f'留存数据来源：raw_member_report（会员报表 × 多月快照）。'
            f'显示期间：{last_row["月份"]}→{last_row["次月"]}。'
            f'筛选条件已套用（见上方"当前口径"）。详细计算方式请展开下方「本页指标口径说明」。'
            f'⚠️ 若最新月份（{last_row["次月"]}）的快照是月中导入、还不是整月数据，'
            f'最后一个数据点的留存率会偏低，仅供参考，等整月导齐再看准。'
        )

    with st.expander('公司收入口径与月度校验', expanded=False):
        st.write('当前“公司收入”直接汇总会员报表原始字段【公司收入】，前端不做二次推导。')
        if '注册时间' in member.columns and '公司收入' in member.columns and not member.empty:
            tmp = member.copy()
            tmp['注册月份'] = tmp['注册时间'].dt.strftime('%Y-%m')
            check = tmp.groupby('注册月份', as_index=False).agg(
                会员数=('__member_key__', 'nunique'),
                有效投注额=('有效投注额', 'sum'),
                公司收入=('公司收入', 'sum'),
            )
            st.dataframe(check, width='stretch', hide_index=True)

    render_metric_explainer(['公司收入', 'ARPU（用户均收）', 'TOP20投注占比', '次月活跃留存率', '次月存款留存率', '首存用户次月留存率'])






# 1 finance page implementation moved to features/finance_results.py



def render_bet_analysis():
    hero(
        '投注分析',
        '基于当月全部投注注单，按场馆、游戏类型、VIP 等级三大维度分析。所有汇总通过 BigQuery 聚合查询，不下载明细。',
        '',
        basis='注单明细（按月表）；来源待确认，目前库内仅含 4 月',
        detail=(
            '**分析范围**：按场馆、游戏类型、VIP 等级三维度的注单聚合分析。\n\n'
            '**数据来源**：注单明细按月表（raw_bet_detail_YYYY_MM），经 BigQuery 聚合，不下载明细。\n\n'
            '**注意**：此报表来源尚未确认、目前库内仅含 2026 年 4 月。需补全请先确认后台导出位置。完整对照见「数据说明」页。'
        )
    )

    # 动态发现已导入的月份表(raw_bet_detail_YYYY_MM);新月份注单进 BigQuery 后自动出现在选单
    BET_TABLE = 'raw_bet_detail_2026_04'  # 兜底默认
    bet_month_label = '2026-04'
    try:
        # 直接走 client：query_bq 的 normalize 会把 table_name 字串列强转数字成 NaN
        _tbls = get_bq_client().query(
            f"SELECT table_name FROM `{BQ_PREFIX}.INFORMATION_SCHEMA.TABLES` "
            "WHERE table_name LIKE 'raw_bet_detail_%' ORDER BY table_name"
        ).to_dataframe()
        _month_map = {}
        for _t in _tbls['table_name'].astype(str).tolist():
            _m = re.match(r'raw_bet_detail_(\d{4})_(\d{2})$', _t)
            if _m:
                _month_map[f'{_m.group(1)}-{_m.group(2)}'] = _t
        if _month_map:
            _opts = sorted(_month_map.keys())
            mc1, mc2 = st.columns([1, 4])
            with mc1:
                bet_month_label = st.selectbox('📅 注单月份', _opts, index=len(_opts) - 1, key='bet_month')
            with mc2:
                st.markdown(
                    f'<div style="padding-top:1.8rem;color:#9fc1d9;">已导入月份：<b>{", ".join(_opts)}</b>'
                    '（新月份注单导入 BigQuery 后自动出现在选单）</div>',
                    unsafe_allow_html=True,
                )
            BET_TABLE = _month_map[bet_month_label]
            # 切换月份时清掉旧筛选状态,避免选项与新表不一致报错
            if st.session_state.get('_bet_month_prev') != bet_month_label:
                for _k in ('bet_type', 'bet_vip', 'bet_venue', 'bet_date'):
                    st.session_state.pop(_k, None)
                st.session_state['_bet_month_prev'] = bet_month_label
    except Exception:
        pass

    # 表是否存在 — 时间戳用 SQL 端 FORMAT 成字串,避免 normalize_dataframe 把 timestamp 转成数字再 lossy 还原
    try:
        meta = query_bq(
            "SELECT COUNT(*) AS n, "
            "FORMAT_TIMESTAMP('%Y-%m-%d', MIN(`下注时间`)) AS min_t, "
            "FORMAT_TIMESTAMP('%Y-%m-%d', MAX(`下注时间`)) AS max_t "
            f"FROM `{BQ_PREFIX}.{BET_TABLE}`"
        )
    except Exception as e:
        st.error(f'投注详情数据尚未导入 BigQuery（{BET_TABLE}）。错误：{e}')
        return

    if meta.empty or int(meta.iloc[0]['n']) == 0:
        st.warning('暂无投注数据')
        return

    total_bets = int(meta.iloc[0]['n'])
    min_t = meta.iloc[0]['min_t']
    max_t = meta.iloc[0]['max_t']

    range_str = ''
    if min_t and max_t and str(min_t) != 'nan' and str(max_t) != 'nan':
        range_str = f"{min_t} ~ {max_t}"
    st.info(
        f'📌 **数据范围：{range_str}** | 📌 **注单数：{total_bets:,}** | '
        f'📌 **盈亏口径**：负数 = 平台赢；正数 = 平台输（玩家赢）'
    )

    # ── 筛选条件 ──────────────────────────────────────────
    section_header('筛选条件', '下方所有图表 / 表格 都依据此筛选条件计算（直接走 BigQuery WHERE，速度不变）')

    # 取候选清单
    opt_q = (
        f"SELECT `场馆类型` AS venue_type, `VIP等级` AS vip_label, `场馆名称` AS venue "
        f"FROM `{BQ_PREFIX}.{BET_TABLE}` GROUP BY `场馆类型`, `VIP等级`, `场馆名称`"
    )
    opt_df = query_bq(opt_q)

    type_opts = sorted([t for t in opt_df['venue_type'].dropna().unique() if t])
    vip_opts = sorted(
        [v for v in opt_df['vip_label'].dropna().unique() if v],
        key=lambda x: int(x) if str(x).isdigit() else 99
    )
    venue_opts = sorted([v for v in opt_df['venue'].dropna().unique() if v])

    # session_state 默认值初始化(只在第一次)
    if 'bet_type' not in st.session_state:
        st.session_state['bet_type'] = list(type_opts)
    if 'bet_vip' not in st.session_state:
        st.session_state['bet_vip'] = list(vip_opts)
    if 'bet_venue' not in st.session_state:
        st.session_state['bet_venue'] = []

    # 全选 / 全清 快捷按钮(需先于 multiselect 渲染,以便修改 session_state)
    bc1, bc2, bc3, bc4, bc5, bc6 = st.columns([1, 1, 1, 1, 1, 1])
    with bc1:
        if st.button('类型 全选', use_container_width=True, key='bet_type_all_btn'):
            st.session_state['bet_type'] = list(type_opts)
            st.rerun()
    with bc2:
        if st.button('类型 全清', use_container_width=True, key='bet_type_clear_btn'):
            st.session_state['bet_type'] = []
            st.rerun()
    with bc3:
        if st.button('VIP 全选', use_container_width=True, key='bet_vip_all_btn'):
            st.session_state['bet_vip'] = list(vip_opts)
            st.rerun()
    with bc4:
        if st.button('VIP 全清', use_container_width=True, key='bet_vip_clear_btn'):
            st.session_state['bet_vip'] = []
            st.rerun()
    with bc5:
        if st.button('场馆 全选', use_container_width=True, key='bet_venue_all_btn'):
            st.session_state['bet_venue'] = list(venue_opts)
            st.rerun()
    with bc6:
        if st.button('场馆 全清', use_container_width=True, key='bet_venue_clear_btn'):
            st.session_state['bet_venue'] = []
            st.rerun()

    fc1, fc2, fc3, fc4 = st.columns([1.2, 1.2, 1.4, 1.4])
    with fc1:
        # 日期 range 取自 BQ 的 min/max
        try:
            mn = pd.to_datetime(min_t).date() if min_t else None
            mx = pd.to_datetime(max_t).date() if max_t else None
        except Exception:
            mn, mx = None, None
        date_range = st.date_input(
            '下注日期范围', value=(mn, mx) if mn and mx else None,
            min_value=mn, max_value=mx, key='bet_date'
        )
    with fc2:
        sel_types = st.multiselect('场馆类型', type_opts, key='bet_type')
    with fc3:
        sel_vips = st.multiselect('VIP 等级', vip_opts, key='bet_vip')
    with fc4:
        sel_venues = st.multiselect('场馆名称（不选 = 全部）', venue_opts, key='bet_venue')

    # 组 WHERE
    where_parts = []
    if isinstance(date_range, tuple) and len(date_range) == 2 and all(date_range):
        where_parts.append(
            f"DATE(`下注时间`) BETWEEN DATE('{date_range[0]}') AND DATE('{date_range[1]}')"
        )
    def _sql_in(vals):  # 转义单引号，避免值含 ' 时断句/注入
        return ', '.join("'" + str(v).replace("'", "''") + "'" for v in vals)
    if sel_types and len(sel_types) < len(type_opts):
        where_parts.append(f"`场馆类型` IN ({_sql_in(sel_types)})")
    if sel_vips and len(sel_vips) < len(vip_opts):
        where_parts.append(f"`VIP等级` IN ({_sql_in(sel_vips)})")
    if sel_venues:
        where_parts.append(f"`场馆名称` IN ({_sql_in(sel_venues)})")

    where_clause = (' WHERE ' + ' AND '.join(where_parts)) if where_parts else ''

    if where_parts:
        # 重新算 KPI(命中筛选范围) 并提示
        sub_q = f"SELECT COUNT(*) AS n FROM `{BQ_PREFIX}.{BET_TABLE}`{where_clause}"
        sub_n = int(query_bq(sub_q).iloc[0]['n'])
        st.success(f'当前筛选命中 **{sub_n:,}** 笔注单（占全月 {sub_n/total_bets*100:.1f}%）')

    # ── 总览 KPI ───────────────────────────────────────────
    kpi_q = f"""
        SELECT
          COUNT(*) AS bets,
          SUM(`有效投注`) AS valid_bet,
          SUM(`下注金额`) AS bet_amount,
          SUM(`盈亏`) AS pnl,
          COUNT(DISTINCT `会员账号`) AS players
        FROM `{BQ_PREFIX}.{BET_TABLE}`{where_clause}
    """
    kpi = query_bq(kpi_q)
    bets_n = int(kpi.iloc[0]['bets'] or 0)  # 随筛选变动（与下面 4 张卡同口径）
    valid_bet = float(kpi.iloc[0]['valid_bet'] or 0)
    pnl = float(kpi.iloc[0]['pnl'] or 0)
    players = int(kpi.iloc[0]['players'] or 0)
    hold_pct = (-pnl / valid_bet * 100) if valid_bet else 0.0

    cols = st.columns(5)
    show_metric(cols[0], '注单总数', fmt_num(bets_n),
                help_text=None if where_parts else '全月（未加筛选）')
    show_metric(cols[1], '有效投注总额', fmt_num(valid_bet))
    show_metric(cols[2], '平台净盈亏',
                fmt_num(-pnl), delta='平台赢' if pnl < 0 else '平台输',
                tone=tone_by_sign(-pnl), delta_tone='up' if pnl < 0 else 'down')
    show_metric(cols[3], 'Hold % (净盈/有效投注)', f'{hold_pct:.2f}%', tone='accent')
    show_metric(cols[4], '参与玩家数', fmt_num(players))

    # ── 模块 1 — 场馆分析 ───────────────────────────────────
    section_header('模块 1 ─ 场馆分析', '按 场馆名称 切片，看流水分布、Hold%、玩家数')

    venue_q = f"""
        SELECT
          `场馆名称` AS venue,
          `场馆类型` AS venue_type,
          COUNT(*) AS bets,
          SUM(`有效投注`) AS valid_bet,
          SUM(`盈亏`) AS pnl,
          COUNT(DISTINCT `会员账号`) AS players,
          SAFE_DIVIDE(SUM(`有效投注`), COUNT(*)) AS avg_bet
        FROM `{BQ_PREFIX}.{BET_TABLE}`{where_clause}
        GROUP BY `场馆名称`, `场馆类型`
        ORDER BY valid_bet DESC
    """
    venue_df = query_bq(venue_q)
    venue_df = venue_df.rename(columns={
        'venue': '场馆', 'venue_type': '类型', 'bets': '注单数',
        'valid_bet': '有效投注', 'pnl': '盈亏', 'players': '玩家数', 'avg_bet': '单注均值'
    })
    venue_df['平台净盈亏'] = -venue_df['盈亏']
    venue_df['Hold%'] = (venue_df['平台净盈亏'] / venue_df['有效投注'] * 100).round(3)
    venue_df['流水占比%'] = (venue_df['有效投注'] / venue_df['有效投注'].sum() * 100).round(2)

    c1, c2 = st.columns([1.4, 1])
    with c1:
        with st.container(border=True):
            section_header('Top 15 场馆 — 有效投注 与 Hold%')
            top15 = venue_df.head(15).copy()
            fig = go.Figure()
            fig.add_trace(go.Bar(
                x=top15['场馆'],
                y=top15['有效投注'],
                name='有效投注',
                marker_color=BLUE,
                yaxis='y',
                hovertemplate='%{x}<br>有效投注 %{y:,.0f}<extra></extra>'
            ))
            fig.add_trace(go.Scatter(
                x=top15['场馆'],
                y=top15['Hold%'],
                name='Hold%',
                mode='lines+markers',
                marker_color=AMBER,
                yaxis='y2',
                hovertemplate='%{x}<br>Hold %{y:.2f}%<extra></extra>'
            ))
            fig.update_layout(
                template=TEMPLATE,
                height=440,
                xaxis_tickangle=-30,
                yaxis=dict(title='有效投注'),
                yaxis2=dict(title='Hold %', overlaying='y', side='right'),
                legend=dict(orientation='h', y=1.05, x=0.5, xanchor='center'),
                margin=dict(t=40, b=10),
            )
            st.plotly_chart(fig, use_container_width=True)

    with c2:
        with st.container(border=True):
            section_header('类型流水占比')
            type_pie = venue_df.groupby('类型', as_index=False)['有效投注'].sum().sort_values('有效投注', ascending=False)
            fig = px.pie(
                type_pie, names='类型', values='有效投注', hole=0.58,
                template=TEMPLATE,
                color_discrete_sequence=[BLUE, GREEN, PURPLE, CYAN, AMBER, RED, '#7AB7FF'],
            )
            fig.update_traces(textinfo='label+percent', textfont_size=12,
                              marker=dict(line=dict(color='rgba(7,15,30,0.9)', width=2)))
            fig.update_layout(height=440, legend=dict(orientation='h', y=-0.05))
            st.plotly_chart(fig, use_container_width=True)

    with st.container(border=True):
        section_header('全部场馆明细')
        show_df = venue_df[['场馆', '类型', '注单数', '有效投注', '平台净盈亏', 'Hold%', '玩家数', '单注均值', '流水占比%']].copy()
        st.dataframe(show_df, use_container_width=True, hide_index=True,
                     column_config={
                         '注单数': st.column_config.NumberColumn(format='%d'),
                         '有效投注': st.column_config.NumberColumn(format='%.0f'),
                         '平台净盈亏': st.column_config.NumberColumn(format='%.0f'),
                         '玩家数': st.column_config.NumberColumn(format='%d'),
                         '单注均值': st.column_config.NumberColumn(format='%.2f'),
                     })

    # ── 模块 2 — 游戏类型分析 ───────────────────────────────
    section_header('模块 2 ─ 游戏类型分析', '体育 / 真人 / 电子 / 棋牌 / 彩票 / 电竞 / 捕鱼 大类汇总')

    type_q = f"""
        SELECT
          `场馆类型` AS venue_type,
          COUNT(*) AS bets,
          SUM(`有效投注`) AS valid_bet,
          SUM(`盈亏`) AS pnl,
          COUNT(DISTINCT `会员账号`) AS players
        FROM `{BQ_PREFIX}.{BET_TABLE}`{where_clause}
        GROUP BY `场馆类型`
        ORDER BY valid_bet DESC
    """
    type_df = query_bq(type_q)
    type_df = type_df.rename(columns={
        'venue_type': '类型', 'bets': '注单数', 'valid_bet': '有效投注',
        'pnl': '盈亏', 'players': '玩家数'
    })
    type_df['平台净盈亏'] = -type_df['盈亏']
    type_df['Hold%'] = (type_df['平台净盈亏'] / type_df['有效投注'] * 100).round(3)
    type_df['人均流水'] = (type_df['有效投注'] / type_df['玩家数']).round(0)
    type_df['流水占比%'] = (type_df['有效投注'] / type_df['有效投注'].sum() * 100).round(2)

    c1, c2 = st.columns(2)
    with c1:
        with st.container(border=True):
            section_header('类型 × Hold% 对比')
            fig = px.bar(
                type_df, x='类型', y='Hold%', text='Hold%',
                color='Hold%', color_continuous_scale='RdYlGn_r',
                template=TEMPLATE,
            )
            fig.update_traces(texttemplate='%{text:.2f}%', textposition='outside')
            fig.update_layout(height=380, coloraxis_showscale=False, xaxis_title=None)
            st.plotly_chart(fig, use_container_width=True)

    with c2:
        with st.container(border=True):
            section_header('类型 × 人均流水(玩家深度)')
            fig = px.bar(
                type_df, x='类型', y='人均流水', text='玩家数',
                color='人均流水', color_continuous_scale='Blues',
                template=TEMPLATE,
            )
            fig.update_traces(texttemplate='%{text:,d} 人', textposition='outside')
            fig.update_layout(height=380, coloraxis_showscale=False, xaxis_title=None)
            st.plotly_chart(fig, use_container_width=True)

    st.dataframe(
        type_df[['类型', '注单数', '有效投注', '平台净盈亏', 'Hold%', '玩家数', '人均流水', '流水占比%']],
        use_container_width=True, hide_index=True,
        column_config={
            '注单数': st.column_config.NumberColumn(format='%d'),
            '有效投注': st.column_config.NumberColumn(format='%.0f'),
            '平台净盈亏': st.column_config.NumberColumn(format='%.0f'),
            '玩家数': st.column_config.NumberColumn(format='%d'),
            '人均流水': st.column_config.NumberColumn(format='%.0f'),
        }
    )

    # ── 模块 3 — VIP 等级分析 ───────────────────────────────
    section_header('模块 3 ─ VIP 等级分析', 'VIP 0~10 流水分布、活动让利 cap 校准、Top 大户')

    vip_q = f"""
        SELECT
          SAFE_CAST(`VIP等级` AS INT64) AS vip_n,
          `VIP等级` AS vip_label,
          COUNT(*) AS bets,
          SUM(`有效投注`) AS valid_bet,
          SUM(`盈亏`) AS pnl,
          COUNT(DISTINCT `会员账号`) AS players
        FROM `{BQ_PREFIX}.{BET_TABLE}`{where_clause}
        GROUP BY `VIP等级`
        ORDER BY vip_n
    """
    vip_df = query_bq(vip_q)
    vip_df = vip_df.rename(columns={
        'vip_label': 'VIP', 'bets': '注单数', 'valid_bet': '有效投注',
        'pnl': '盈亏', 'players': '玩家数'
    })
    vip_df['平台净盈亏'] = -vip_df['盈亏']
    vip_df['Hold%'] = (vip_df['平台净盈亏'] / vip_df['有效投注'] * 100).round(3)
    vip_df['人均流水'] = (vip_df['有效投注'] / vip_df['玩家数']).round(0)
    vip_df['流水占比%'] = (vip_df['有效投注'] / vip_df['有效投注'].sum() * 100).round(2)

    c1, c2 = st.columns(2)
    with c1:
        with st.container(border=True):
            section_header('VIP × 流水占比 + 玩家数')
            fig = make_subplots(specs=[[{'secondary_y': True}]])
            fig.add_trace(
                go.Bar(x=vip_df['VIP'].astype(str), y=vip_df['有效投注'], name='有效投注', marker_color=BLUE),
                secondary_y=False
            )
            fig.add_trace(
                go.Scatter(x=vip_df['VIP'].astype(str), y=vip_df['玩家数'], name='玩家数',
                           mode='lines+markers', marker_color=AMBER),
                secondary_y=True
            )
            fig.update_xaxes(title='VIP 等级')
            fig.update_yaxes(title='有效投注', secondary_y=False)
            fig.update_yaxes(title='玩家数', secondary_y=True)
            fig.update_layout(template=TEMPLATE, height=400,
                              legend=dict(orientation='h', y=1.05, x=0.5, xanchor='center'))
            st.plotly_chart(fig, use_container_width=True)

    with c2:
        with st.container(border=True):
            section_header('VIP × Hold% 走势')
            fig = px.line(
                vip_df, x='VIP', y='Hold%', markers=True, text='Hold%',
                template=TEMPLATE,
            )
            fig.update_traces(line_color=GREEN, marker_size=10, texttemplate='%{text:.2f}%', textposition='top center')
            fig.add_hline(y=0, line_color='rgba(150,170,210,0.5)', line_dash='dash',
                          annotation_text='平台不输不赢 (Hold=0)', annotation_position='right')
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)

    st.dataframe(
        vip_df[['VIP', '注单数', '有效投注', '平台净盈亏', 'Hold%', '玩家数', '人均流水', '流水占比%']],
        use_container_width=True, hide_index=True,
        column_config={
            '注单数': st.column_config.NumberColumn(format='%d'),
            '有效投注': st.column_config.NumberColumn(format='%.0f'),
            '平台净盈亏': st.column_config.NumberColumn(format='%.0f'),
            '玩家数': st.column_config.NumberColumn(format='%d'),
            '人均流水': st.column_config.NumberColumn(format='%.0f'),
        }
    )

    # ── VIP × 类型 交叉(老板让利 cap 校准用) ─────────────
    section_header('VIP × 场馆类型 流水交叉表',
                   '让利 cap 校准:体育 0.5% / 真人 0.3% / 老虎机 0.4% — 这张表 看 高 VIP 主要玩什么场馆')

    cross_q = f"""
        SELECT
          SAFE_CAST(`VIP等级` AS INT64) AS vip_n,
          `VIP等级` AS vip_label,
          `场馆类型` AS venue_type,
          SUM(`有效投注`) AS valid_bet
        FROM `{BQ_PREFIX}.{BET_TABLE}`{where_clause}
        GROUP BY `VIP等级`, `场馆类型`
        ORDER BY vip_n, venue_type
    """
    cross_df = query_bq(cross_q)
    cross_df = cross_df.rename(columns={'vip_label': 'VIP', 'venue_type': '类型', 'valid_bet': '有效投注'})
    cross_pivot = cross_df.pivot_table(
        index='VIP', columns='类型', values='有效投注', aggfunc='sum', fill_value=0
    )
    # row total 排序 by VIP 数字
    cross_pivot.index = pd.Categorical(
        cross_pivot.index,
        categories=sorted(cross_pivot.index, key=lambda x: int(x) if str(x).isdigit() else 99)
    )
    cross_pivot = cross_pivot.sort_index()

    with st.container(border=True):
        fig = px.imshow(
            cross_pivot.values,
            x=cross_pivot.columns.tolist(),
            y=[f'VIP{v}' for v in cross_pivot.index.tolist()],
            color_continuous_scale='Blues',
            aspect='auto',
            text_auto='.2s',
        )
        fig.update_layout(
            template=TEMPLATE, height=460,
            title='VIP × 场馆类型 — 有效投注热力图',
        )
        st.plotly_chart(fig, use_container_width=True)
    # pandas 2.1+ DataFrame.applymap deprecated → 改 .map(DataFrame.map 是 2.1+ 新增)
    try:
        cross_display = cross_pivot.map(lambda v: f'{v:,.0f}')
    except (AttributeError, TypeError):
        cross_display = cross_pivot.applymap(lambda v: f'{v:,.0f}')
    st.dataframe(cross_display, use_container_width=True)

    # ── Top 100 大户 ─────────────────────────────────────
    section_header(f'Top 100 大户(按 {bet_month_label} 有效投注)')
    top_q = f"""
        SELECT
          `会员账号` AS member,
          `VIP等级` AS vip_label,
          COUNT(*) AS bets,
          SUM(`有效投注`) AS valid_bet,
          SUM(`盈亏`) AS pnl,
          COUNT(DISTINCT `场馆名称`) AS venues
        FROM `{BQ_PREFIX}.{BET_TABLE}`{where_clause}
        GROUP BY `会员账号`, `VIP等级`
        ORDER BY valid_bet DESC
        LIMIT 100
    """
    top_df = query_bq(top_q)
    top_df = top_df.rename(columns={
        'member': '会员', 'vip_label': 'VIP', 'bets': '注单数',
        'valid_bet': '有效投注', 'pnl': '盈亏', 'venues': '场馆数'
    })
    top_df['平台净盈亏'] = -top_df['盈亏']
    top_df['Hold%'] = (top_df['平台净盈亏'] / top_df['有效投注'] * 100).round(2)

    # Top 大户 流水集中度
    top_total = top_df['有效投注'].sum()
    pct_concentration = top_total / valid_bet * 100 if valid_bet else 0
    st.markdown(
        f'**Top 100 大户 合计 {fmt_num(top_total)} 流水 占全平台 {pct_concentration:.1f}%** '
        f'(全平台 {fmt_num(valid_bet)})'
    )

    st.dataframe(
        top_df[['会员', 'VIP', '注单数', '有效投注', '平台净盈亏', 'Hold%', '场馆数']],
        use_container_width=True, hide_index=True,
        column_config={
            '注单数': st.column_config.NumberColumn(format='%d'),
            '有效投注': st.column_config.NumberColumn(format='%.0f'),
            '平台净盈亏': st.column_config.NumberColumn(format='%.0f'),
        }
    )

    # ── 口径说明 ──────────────────────────────────────────
    with st.expander('本页指标口径说明', expanded=False):
        st.markdown(f'''
- **数据来源**：`{BQ_PREFIX}.{BET_TABLE}`({bet_month_label} 全月投注注单, {total_bets:,} 笔)
- **月份选单**：自动扫描 BigQuery 中的 `raw_bet_detail_YYYY_MM` 表,新月份注单导入后即出现,无需改代码
- **盈亏口径**:原始 `盈亏` 列 是从 玩家视角 看(玩家赢=正,玩家输=负)。 面板「平台净盈亏」 = − `盈亏` (平台赢=正)
- **Hold %** = 平台净盈亏 / 有效投注 × 100
- **有效投注** ≠ 下注金额(扣 走盘 / 和局退本金 / 不计入活动 玩法)
- **VIP** = 该笔注单产生时玩家的 VIP 等级(月内升降级会按当时记录)
- **VIP × 类型 交叉表** 直接对照 老板 5/5 让利 cap:体育 0.5% / 真人 0.3% / 老虎机 0.4% — 看 高 VIP 主玩什么 → 让利成本最大重心在哪
- **Top 100 大户**:全平台当月总流水的集中度,集中度高表示「少数大户撑起大多数流水」
''')


# 1 finance page implementation moved to features/finance_results.py



def render_cs_analysis():
    """客服对话分析 — 6/5 新增 (Miru 客服质量决策面板)"""
    cs = load_table('raw_cs_conversations')
    hero('客服分析', '5 月包网商前线客服对话数据 — 客服效率 / 满意度 / 时段 / 会员侧。',
         latest_imported_at(cs),
         basis='客服对话（客服系统导出）＋会员报表（VIP 关联）',
         detail=(
             '**分析范围**：客服效率、满意度、时段／星期分布、服务主题与会员侧 VIP 关联。\n\n'
             '**数据来源**：\n'
             '- 客服对话（非后台报表，由客服系统导出 xlsx）\n'
             '- 会员报表（用于会员侧 VIP 关联）\n\n'
             '**更新方式**：人工提供后于「数据上传」页上传。完整对照见「数据说明」页。'
         ))

    if cs.empty:
        st.warning('暂无客服对话数据')
        return

    # 准备时间
    if '开始时间' in cs.columns:
        cs['开始时间'] = to_datetime_safe(cs['开始时间'])
        cs['日期'] = cs['开始时间'].dt.date
        cs['小时'] = cs['开始时间'].dt.hour
        cs['星期'] = cs['开始时间'].dt.dayofweek
        cs['星期'] = cs['星期'].map({0: '周一', 1: '周二', 2: '周三', 3: '周四', 4: '周五', 5: '周六', 6: '周日'})

    for c in ['首次响应', '平均响应', '总时长', '访客消息数', '客服消息数', '对话回合数']:
        if c in cs.columns:
            cs[c] = pd.to_numeric(cs[c], errors='coerce')

    # 日期筛选
    cs_filt, _, _, _ = date_range_picker(cs, '开始时间', 'cs', default_last_days=None)
    if cs_filt.empty:
        st.info('该范围无对话数据')
        return

    # KPI
    total_conv = len(cs_filt)
    unique_agents = cs_filt['接待客服'].nunique() if '接待客服' in cs_filt.columns else 0
    unique_members = member_count(cs_filt)
    avg_first_resp = safe_mean(cs_filt, '首次响应')
    avg_total_time = safe_mean(cs_filt, '总时长')
    rated_mask = cs_filt['满意度评价'].astype(str) != '未评价' if '满意度评价' in cs_filt.columns else None
    rated_count = rated_mask.sum() if rated_mask is not None else 0
    unhappy_count = (cs_filt['满意度评价'].astype(str) == '非常不满意').sum() if '满意度评价' in cs_filt.columns else 0

    c1, c2, c3, c4 = st.columns(4)
    show_metric(c1, '对话总数', fmt_num(total_conv))
    show_metric(c2, '接待客服数', fmt_num(unique_agents))
    show_metric(c3, '涉及会员数', fmt_num(unique_members))
    show_metric(c4, '平均首次响应 (秒)', f'{avg_first_resp:.1f}')

    c5, c6, c7, c8 = st.columns(4)
    show_metric(c5, '平均总时长 (秒)', f'{avg_total_time:.0f}')
    show_metric(c6, '已评价对话', fmt_num(rated_count))
    rate_pct = (rated_count / total_conv * 100) if total_conv else 0
    show_metric(c7, '评价率', f'{rate_pct:.1f}%')
    show_metric(c8, '非常不满意', fmt_num(unhappy_count), tone='bad' if unhappy_count else None)

    # ━━━ 满意度分布 ━━━
    if '满意度评价' in cs_filt.columns:
        with st.container(border=True):
            section_header('满意度分布', '')
            sat_grp = cs_filt.groupby('满意度评价').size().reset_index(name='笔数').sort_values('笔数', ascending=False)
            sat_grp['占比%'] = (sat_grp['笔数'] / sat_grp['笔数'].sum() * 100).round(2)
            c1, c2 = st.columns([1, 2])
            with c1:
                st.dataframe(sat_grp, use_container_width=True, hide_index=True)
            with c2:
                fig = px.pie(sat_grp, names='满意度评价', values='笔数', height=300, hole=0.5,
                             color='满意度评价',
                             color_discrete_map={'非常满意': GREEN, '满意': CYAN, '一般': BLUE,
                                                 '不满意': AMBER, '非常不满意': RED, '未评价': '#64748b'})
                fig.update_traces(textinfo='percent', marker=dict(line=dict(color='rgba(7,15,30,0.9)', width=2)))
                fig.update_layout(margin=dict(l=20, r=20, t=20, b=20))
                st.plotly_chart(fig, use_container_width=True)

    # ━━━ 客服效率排行 ━━━
    if '接待客服' in cs_filt.columns:
        section_header('客服效率排行', '按接待量降序，对比各客服的响应速度、对话时长与满意度。')
        agg = cs_filt.groupby('接待客服').agg(
            接待量=('对话ID', 'count'),
            平均首次响应秒=('首次响应', 'mean'),
            平均响应秒=('平均响应', 'mean'),
            平均总时长秒=('总时长', 'mean'),
            平均对话回合=('对话回合数', 'mean'),
        ).reset_index()
        # 满意度
        sat = cs_filt[cs_filt['满意度评价'].astype(str) != '未评价'].groupby('接待客服').agg(
            已评价数=('对话ID', 'count'),
            非常满意=('满意度评价', lambda x: (x == '非常满意').sum()),
            非常不满意=('满意度评价', lambda x: (x == '非常不满意').sum()),
        ).reset_index()
        agg = pd.merge(agg, sat, on='接待客服', how='left').fillna(0)
        agg['好评率%'] = (agg['非常满意'] / agg['已评价数'].replace(0, 1) * 100).round(1)
        for c in ['平均首次响应秒', '平均响应秒', '平均总时长秒', '平均对话回合']:
            agg[c] = agg[c].round(1)
        for c in ['已评价数', '非常满意', '非常不满意']:
            agg[c] = agg[c].astype(int)
        agg = agg.sort_values('接待量', ascending=False)
        st.dataframe(agg, use_container_width=True, hide_index=True)

    # ━━━ 时段分布 ━━━
    hr_c1, hr_c2 = st.columns(2)
    with hr_c1:
        if '小时' in cs_filt.columns:
            with st.container(border=True):
                section_header('小时分布', '接客高峰时段，对照客服排班是否合理。')
                hr_grp = cs_filt.groupby('小时').size().reset_index(name='对话数')
                fig = px.bar(hr_grp, x='小时', y='对话数', color='对话数', color_continuous_scale='Blues', height=300)
                fig.update_layout(margin=dict(l=40, r=40, t=20, b=40), coloraxis_showscale=False)
                st.plotly_chart(fig, use_container_width=True)
    with hr_c2:
        if '星期' in cs_filt.columns:
            with st.container(border=True):
                section_header('星期分布', '')
                wk_grp = cs_filt.groupby('星期').size().reset_index(name='对话数')
                order = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
                wk_grp['order'] = wk_grp['星期'].map({d: i for i, d in enumerate(order)})
                wk_grp = wk_grp.sort_values('order')
                fig = px.bar(wk_grp, x='星期', y='对话数', color='对话数', color_continuous_scale='Greens', height=300)
                fig.update_layout(margin=dict(l=40, r=40, t=20, b=40), coloraxis_showscale=False, xaxis_title=None)
                st.plotly_chart(fig, use_container_width=True)

    # ━━━ 服务主题 ━━━
    if '服务主题' in cs_filt.columns:
        section_header('服务主题分布 (Top 20)', '客服主动 / 系统打的主题标签')
        theme_grp = cs_filt[cs_filt['服务主题'].notna()].groupby('服务主题').size().reset_index(name='笔数').sort_values('笔数', ascending=False).head(20)
        if not theme_grp.empty:
            st.dataframe(theme_grp, use_container_width=True, hide_index=True)
        else:
            st.info('5 月对话基本没标服务主题 — 这本身是 QC 问题点 (无法按主题分流追踪)')

    # ━━━ 不满意案件 deep dive ━━━
    if '满意度评价' in cs_filt.columns:
        section_header('非常不满意 / 不满意 案件',
                      '主因 = 服务主题(优先) > 评价内容关键词 > 对话内容(去模板) ;点开看完整对话')
        bad = cs_filt[cs_filt['满意度评价'].astype(str).isin(['非常不满意', '不满意'])].copy()
        if bad.empty:
            st.info('该范围无不满意案件')
        else:
            # 主因分布
            if '_extracted_issue' in bad.columns:
                from collections import Counter
                issue_cnt = Counter()
                for s in bad['_extracted_issue'].dropna().astype(str):
                    if s and s != '(未匹配)':
                        for cat in s.split(','):
                            issue_cnt[cat.strip()] += 1
                if issue_cnt:
                    st.markdown('**主因分布:**')
                    iss_df = pd.DataFrame(issue_cnt.most_common(), columns=['主因', '案件数'])
                    c1, c2 = st.columns([1, 1])
                    with c1:
                        st.dataframe(iss_df, use_container_width=True, hide_index=True, height=240)
                    with c2:
                        fig = px.bar(iss_df.head(10), x='案件数', y='主因', orientation='h',
                                     color='案件数', color_continuous_scale='Reds', height=240)
                        fig.update_layout(margin=dict(l=20, r=20, t=10, b=10),
                                          yaxis={'categoryorder': 'total ascending'})
                        st.plotly_chart(fig, use_container_width=True)

            # 表格
            cols = ['开始时间', '会员账号', '接待客服', '满意度评价', '_extracted_issue',
                    '评价内容', '服务主题', '首次响应', '平均响应', '总时长', '对话回合数', '对话ID']
            cols = [c for c in cols if c in bad.columns]
            bad_show = bad[cols].copy()
            if '_extracted_issue' in bad_show.columns:
                bad_show = bad_show.rename(columns={'_extracted_issue': '主因'})
            if '开始时间' in bad_show.columns:
                bad_show = bad_show.sort_values('开始时间', ascending=False)
            st.dataframe(bad_show, use_container_width=True, hide_index=True)

            # 完整对话 — 支持: 1) 贴对话ID(查全部对话) 2) 下拉选(只看不满意)
            if '对话ID' in bad.columns and '对话内容' in bad.columns:
                st.markdown('**👇 查看完整对话内容** (贴对话 ID 或下拉选)')

                bad_sorted = bad.sort_values('开始时间', ascending=False).reset_index(drop=True)
                option_labels = []
                for i in range(len(bad_sorted)):
                    r = bad_sorted.iloc[i]
                    t_str = r['开始时间'].strftime('%m-%d %H:%M') if pd.notna(r['开始时间']) else '?'
                    label = f"{i+1}. {t_str} | {r['会员账号'] or '匿名'} | {r['接待客服']} | {r.get('_extracted_issue') or r.get('服务主题') or '(无主因)'}"
                    option_labels.append(label)

                c_id, c_dd = st.columns([2, 3])
                with c_id:
                    paste_id = st.text_input('贴对话 ID (可查全部 2535 笔,不限不满意)', '',
                                              key='cs_paste_id',
                                              placeholder='例: fabf3ffbb53b47de8b56d076181cebe2')
                with c_dd:
                    sel = st.selectbox('或从「不满意」下拉选', ['(请选择)'] + option_labels, key='cs_bad_select')

                # 找 row
                selected_row = None
                convo_key_id = 'none'
                if paste_id.strip():
                    q = paste_id.strip()
                    match = cs_filt[cs_filt['对话ID'].astype(str).str.contains(q, case=False, na=False)]
                    if match.empty:
                        st.warning(f'没找到对话 ID 含 "{q}" 的对话')
                    else:
                        if len(match) > 1:
                            st.info(f'找到 {len(match)} 笔匹配,显示第 1 笔. ID 完整些可以唯一定位')
                        selected_row = match.iloc[0]
                        convo_key_id = f'paste_{q[:20]}'
                elif sel != '(请选择)':
                    idx = option_labels.index(sel)
                    selected_row = bad_sorted.iloc[idx]
                    convo_key_id = f'dropdown_{idx}'

                if selected_row is not None:
                    c1, c2, c3 = st.columns(3)
                    with c1: st.metric('会员账号', selected_row['会员账号'] or '匿名')
                    with c2: st.metric('接待客服', selected_row['接待客服'])
                    with c3: st.metric('满意度', selected_row['满意度评价'])
                    c4, c5, c6 = st.columns(3)
                    with c4: st.metric('首次响应 (秒)', f"{selected_row['首次响应']:.0f}" if pd.notna(selected_row['首次响应']) else '-')
                    with c5: st.metric('总时长 (秒)', f"{selected_row['总时长']:.0f}" if pd.notna(selected_row['总时长']) else '-')
                    with c6: st.metric('对话回合', f"{selected_row['对话回合数']:.0f}" if pd.notna(selected_row['对话回合数']) else '-')
                    if selected_row.get('评价内容'):
                        st.markdown(f"**客户评价内容:** {selected_row['评价内容']}")
                    if selected_row.get('服务主题'):
                        st.markdown(f"**服务主题:** {selected_row['服务主题']}")
                    issue = selected_row.get('_extracted_issue')
                    if issue and str(issue).strip() and str(issue) != '(未匹配)':
                        st.markdown(f"**抽取主因:** {issue}")
                    st.markdown('---')
                    st.markdown('**对话全文：**')
                    convo = str(selected_row.get('对话内容') or '').replace('&nbsp;', ' ')
                    st.text_area('对话全文', value=convo, height=400, label_visibility='collapsed',
                                 key=f'cs_convo_{convo_key_id}')

    # ━━━ 会员侧 join (会员账号 → BQ raw_member_report) ━━━
    if '会员账号' in cs_filt.columns:
        section_header('会员侧分析 — VIP 等级 × 问题量', '对话会员账号关联会员表，分析各 VIP 等级的客诉分布。')
        try:
            member = load_table('raw_member_report')
            if not member.empty and 'VIP等级' in member.columns:
                # 取最新月份的 VIP
                latest_vip = member.sort_values('_snapshot_month').groupby('会员账号').tail(1)[['会员账号', 'VIP等级', '代理', '用户标签']]
                merged_cs = pd.merge(cs_filt, latest_vip, on='会员账号', how='left')
                vip_grp = merged_cs.groupby('VIP等级', dropna=False).size().reset_index(name='对话数').sort_values('对话数', ascending=False)
                vip_grp['VIP等级'] = vip_grp['VIP等级'].fillna('(未匹配)').astype(str)
                c1, c2 = st.columns([1, 2])
                with c1:
                    st.dataframe(vip_grp, use_container_width=True, hide_index=True)
                with c2:
                    fig = px.bar(vip_grp, x='VIP等级', y='对话数', color='对话数',
                                 color_continuous_scale='Oranges', height=320)
                    fig.update_layout(margin=dict(l=40, r=20, t=20, b=40))
                    st.plotly_chart(fig, use_container_width=True)
                match_rate = (vip_grp[vip_grp['VIP等级'] != '(未匹配)']['对话数'].sum() / vip_grp['对话数'].sum() * 100) if vip_grp['对话数'].sum() else 0
                st.caption(f'会员账号匹配率: {match_rate:.1f}% (未匹配多半是访客未登入)')
            else:
                st.info('会员表无 VIP等级 字段,无法 join')
        except Exception as e:
            st.warning(f'会员侧 join 失败: {e}')

    # ━━━ 关键词热点 ━━━
    if '对话内容' in cs_filt.columns:
        section_header('对话关键词热点 (Top 25)', '只扫会员发言(已剔除系统提醒+客服模板开场),看真实问题集中在哪')
        KEYWORDS = ['充值', '提款', '红利', '彩金', '活动', '登录', '登入', '密码', '注册',
                    '验证', '体育', '真人', '电子', '老虎机', '棋牌', '彩票',
                    '风控', '冻结', '禁用', '解封', '套利', '客诉', '投诉',
                    '代理', '佣金', 'VIP', '返水', 'USDT', '虚拟币',
                    'APP', '下载', '链接']
        member_text = cs_filt.apply(
            lambda r: cs_member_text(r['对话内容'], r['接待客服'] if '接待客服' in cs_filt.columns else ''),
            axis=1)
        kw_counts = {}
        for kw in KEYWORDS:
            # 关键词当纯文本匹配(regex=False),大小写不敏感,APP/app 合并成一条
            cnt = member_text.str.contains(kw, case=False, na=False, regex=False).sum()
            if cnt > 0:
                kw_counts[kw] = int(cnt)
        kw_df = pd.DataFrame(list(kw_counts.items()), columns=['关键词', '对话数']).sort_values('对话数', ascending=False).head(25)
        if not kw_df.empty:
            fig = px.bar(kw_df, x='关键词', y='对话数', color='对话数',
                         color_continuous_scale='Viridis', height=380)
            fig.update_layout(margin=dict(l=40, r=20, t=20, b=80))
            st.plotly_chart(fig, use_container_width=True)
            st.caption(f'基于 {len(cs_filt)} 笔对话的会员发言统计 (每个关键词 = 有多少笔对话的会员提到过它)')

    st.markdown('---')
    with st.expander('ℹ️ 字段说明 / 数据来源'):
        st.markdown('''
- **数据来源**: 包网商提供的 `5月客服对话.xlsx` (32 sheets / 2,535 对话 / 31 天 / 57 客服)
- **首次响应** = 客服第一次回覆的延迟秒数
- **平均响应** = 客服每次回覆的平均延迟秒数
- **总时长** = 整段对话从开始到结束的秒数
- **对话回合数** = 双方互动的轮次
- **评价率** = 已评价对话 / 总对话 (基准: 包网商客服评价率 ~12%,远低于自营 CS 标杆 30%+)
- **会员侧 join** = 把对话的「会员账号」对应到 `raw_member_report` 取 VIP 等级 (未匹配的是访客未登入或会员账号不一致)
- **关键词热点** = 先剔除「系统自动提醒 + 客服模板开场」,只扫**会员发言**,再用业务关键词计数 (非 NLP 聚类,是 keyword count;不去模板会被开场白里的 提款/返水/VIP 等词顶到天花板)
''')


# ── 电访召回（会员召回电话）：上传当月「撥打紀錄總表」Excel，自动出漏斗 + 各专员 + ROI ──
_WINBACK_SKIP_SHEETS = {'话术', '统计结果'}




def render_winback():
    hero('电访召回',
         '会员召回电话的成效。数据存进数据库、这页从库里读——要新增月份，去顶部「数据上传」把那份「撥打紀錄總表」拖进去存一次即可；这页就能单月看明细、多月看趋势。',
         basis='撥打紀錄總表（电访团队提供·上传）',
         detail=(
             '**分析范围**：电访召回漏斗（名单／接通／有效通话／七天回登／召回充值）、各专员表现与月度对比。\n\n'
             '**数据来源**：撥打紀錄總表（非后台报表，由电访团队提供 xlsx）。\n\n'
             '**更新方式**：人工提供后于「数据上传」页上传（按月份刷新）。完整对照见「数据说明」页。'
         ))

    try:
        wb = load_table('raw_winback')
    except Exception:
        wb = None
    stored = []
    if wb is not None and not wb.empty and '月份' in wb.columns:
        for c in ['名单数', '已播数', '接通数', '有效通话', '申请彩金', '七天回登', '召回充值']:
            if c in wb.columns:
                wb[c] = pd.to_numeric(wb[c], errors='coerce').fillna(0)
        for ym, g in wb.groupby('月份'):
            s = str(ym)
            lab = f"{s.split('-')[0]}年{int(s.split('-')[1])}月" if '-' in s and s.split('-')[1].isdigit() else s
            stored.append((s, lab, g.reset_index(drop=True)))
        stored.sort(key=lambda x: x[0])

    with st.expander('📤 临时看一份（只看、不写库）'):
        files = st.file_uploader('上传「撥打紀錄總表」（.xlsx，可多个）', type=['xlsx'],
                                 accept_multiple_files=True, key='winback_upload')
    adhoc = []
    if files:
        for f in files:
            try:
                df, meta = parse_winback_file(f)
                if not df.empty:
                    adhoc.append((_winback_label(meta, f.name), meta.get('month', ''), df))
            except Exception as e:
                st.warning(f'{f.name}：{e}')

    if adhoc:
        adhoc.sort(key=lambda x: x[1] or x[0])
        labeled = [(lab, df) for lab, _ym, df in adhoc]
        st.caption('当前显示：临时上传的档（未写入数据库；要永久存请去「数据上传」页）。')
    elif stored:
        labeled = [(lab, df) for _ym, lab, df in stored]
    else:
        st.info('📭 数据库里还没有电访数据。\n\n'
                '去顶部「数据上传」页，把后台那份「撥打紀錄總表（X月）.xlsx」拖进去存一下，再回这页就能看——'
                '存一次永久留底，不用每次重传。（也可以用上面「临时看一份」先看效果。）')
        return

    if len(labeled) == 1:
        _winback_month_view(labeled[0][1], labeled[0][0])
        return

    _winback_compare_view(labeled)
    section_header('单月明细', '选一个月看完整漏斗与各专员表现。')
    pick = st.selectbox('选择月份', [lab for lab, _ in labeled],
                        index=len(labeled) - 1, key='winback_pick')
    _winback_month_view(dict(labeled)[pick], pick)


# ══════════════════════════════════════════════════════════════
# 数据上传页 — 自助把月度报表写进 BigQuery
# 复用 import_tool 的解析/清洗逻辑；写入走 get_bq_client() 的服务账号。
# 铁律：只「追加」+ 用 _source_file 防重复，绝不覆盖/删除既有数据。
# 注：标准 10 张月报先上（append 安全）；红利/客服对话之后补（需 read-modify-write）。
# ══════════════════════════════════════════════════════════════



