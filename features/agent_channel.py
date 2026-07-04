"""Agent and channel feature pages.

V6.4 moves agent/channel render implementations out of core.legacy.
Shared helpers still come from core.legacy during the transition, so behavior
stays identical while core.legacy continues to slim down.
"""

from __future__ import annotations

import core.legacy as _legacy

# Import every legacy helper, including private helpers used inside these pages.
globals().update({k: getattr(_legacy, k) for k in dir(_legacy) if not k.startswith("__")})

def render_channel_agent():
    agent = load_table('raw_agent_report')
    promo = load_table('raw_promotion_report')
    hero('渠道与代理', '查看代理与渠道表现；字段命名尽量保留原始字段。', latest_imported_at(agent, promo),
         basis='代理报表＋推广报表（后台导出·每月上传）',
         detail=(
             '**分析范围**：代理与渠道表现、代理分层、渠道结构。\n\n'
             '**数据来源（后台导出 → 上传）**：\n'
             '- 代理报表（报表中心→代理报表）\n'
             '- 推广报表（报表中心→推广报表）\n\n'
             '**更新方式**：手动上传（每月导出后于「数据上传」页上传）。完整对照见「数据说明」页。'
         ))

    agent, start, end, month = date_range_picker(agent, '日期', 'ag', default_last_days=None)
    if month and '日期' in promo.columns:
        promo['日期'] = to_datetime_safe(promo['日期'])
        promo = promo[promo['日期'].dt.strftime('%Y-%m') == month].copy()
    elif '日期' in promo.columns and start is not None and end is not None:
        promo['日期'] = to_datetime_safe(promo['日期'])
        promo = promo[(promo['日期'] >= start) & (promo['日期'] < end + pd.Timedelta(days=1))].copy()

    c1, c2, c3 = st.columns(3)
    with c1:
        agent = apply_multiselect(agent, '代理类型', '代理类型', 'ag_type')
    with c2:
        if '代理名称' in agent.columns:
            kw = st.text_input('搜索代理名称', key='ag_name_kw')
            if kw:
                agent = agent[agent['代理名称'].astype(str).str.contains(kw, case=False, na=False)].copy()
    with c3:
        if '一级' in promo.columns:
            lvl1 = [x for x in sorted(promo['一级'].dropna().astype(str).unique().tolist()) if x not in ('', 'nan', 'None')]
            if lvl1:
                sel = st.multiselect('一级', lvl1, default=[], key='promo_l1')
                if sel:
                    promo = promo[promo['一级'].astype(str).isin(sel)].copy()

    with st.expander('高级筛选', expanded=False):
        cc1, cc2, cc3 = st.columns(3)
        with cc1:
            if '二级' in promo.columns:
                promo = apply_multiselect(promo, '二级', '二级', 'promo_l2', default_all=False)
        with cc2:
            if '三级' in promo.columns:
                promo = apply_multiselect(promo, '三级', '三级', 'promo_l3', 'promo_l3' if False else 'promo_l3')
        with cc3:
            if '四级' in promo.columns:
                promo = apply_multiselect(promo, '四级', '四级', 'promo_l4', default_all=False)

    add_info_box([FilterNotice('一级渠道图表口径', '当前“TOP 一级渠道”直接使用推广报表原始字段【一级】；二级 / 三级 / 四级先收在高级筛选。')])

    ca_winloss = safe_sum(agent, '公司输赢')
    cols = st.columns(5)
    show_metric(cols[0], '活跃代理数', fmt_num(safe_nunique(agent, '代理名称')))
    show_metric(cols[1], '有效投注额', fmt_num(safe_sum(agent, '有效投注额')))
    show_metric(cols[2], '公司输赢', fmt_num(ca_winloss), tone=tone_by_sign(ca_winloss))
    show_metric(cols[3], '代理佣金', fmt_num(safe_sum(agent, '代理佣金')), tone='warn')
    show_metric(cols[4], '推广收入', fmt_num(safe_sum(promo, '推广收入')))

    c1, c2 = st.columns(2)
    with c1:
        with st.container(border=True):
            section_header('TOP 代理（按有效投注额）')
            if {'代理名称', '有效投注额'}.issubset(agent.columns):
                top = agent.groupby('代理名称', as_index=False)['有效投注额'].sum().nlargest(10, '有效投注额').sort_values('有效投注额')
                fig = px.bar(top, y='代理名称', x='有效投注额', orientation='h', template=TEMPLATE,
                             color='有效投注额', color_continuous_scale='Blues')
                fig.update_layout(height=420, coloraxis_showscale=False)
                st.plotly_chart(fig, width='stretch')
    with c2:
        with st.container(border=True):
            section_header('TOP 一级渠道（来源：原始字段【一级】）')
            if {'一级', '有效投注额'}.issubset(promo.columns):
                top = promo.groupby('一级', as_index=False)['有效投注额'].sum().nlargest(10, '有效投注额').sort_values('有效投注额')
                fig = px.bar(top, y='一级', x='有效投注额', orientation='h', template=TEMPLATE,
                             color='有效投注额', color_continuous_scale='teal')
                fig.update_layout(height=420, coloraxis_showscale=False)
                st.plotly_chart(fig, width='stretch')

    c3, c4 = st.columns(2)
    with c3:
        with st.container(border=True):
            section_header('代理分层散点')
            if {'代理名称', '有效投注额', '公司输赢'}.issubset(agent.columns):
                grp = agent.groupby('代理名称', as_index=False).agg({'有效投注额': 'sum', '公司输赢': 'sum'})
                fig = px.scatter(grp, x='有效投注额', y='公司输赢', hover_name='代理名称', template=TEMPLATE,
                                 color='公司输赢', color_continuous_scale='RdYlGn')
                fig.add_hline(y=0, line_dash='dot', line_color='rgba(150,170,210,0.5)')
                fig.update_layout(height=420, coloraxis_showscale=False)
                st.plotly_chart(fig, width='stretch')
    with c4:
        with st.container(border=True):
            section_header('渠道结构（Sunburst）')
            if {'一级', '二级', '三级', '四级', '有效投注额'}.issubset(promo.columns):
                tmp = promo.copy()
                tmp[['一级', '二级', '三级', '四级']] = tmp[['一级', '二级', '三级', '四级']].fillna('空值')
                fig = px.sunburst(tmp, path=['一级', '二级', '三级', '四级'], values='有效投注额', template=TEMPLATE)
                fig.update_layout(height=420)
                st.plotly_chart(fig, width='stretch')


def render_game_venue():
    venue = load_table('raw_game_report_venue')
    game = load_table('raw_game_analysis')
    hero('游戏与场馆', '查看原始字段【场馆名称】【游戏类型】【游戏名称】的规模与结果。', latest_imported_at(venue, game),
         basis='游戏报表(场馆)＋游戏分析（后台导出·每月上传）',
         detail=(
             '**分析范围**：各场馆与游戏类型的投注规模、有效投注、公司输赢。\n\n'
             '**数据来源（后台导出 → 上传）**：\n'
             '- 游戏报表(场馆)（报表中心→游戏报表(场馆)）\n'
             '- 游戏分析（报表中心→游戏分析，导出须选「日报」颗粒度）\n\n'
             '**更新方式**：手动上传。完整对照见「数据说明」页。'
         ))

    venue, start, end, month = date_range_picker(venue, '时间', 'gv', default_last_days=None)
    if month and '日期' in game.columns:
        game['日期'] = to_datetime_safe(game['日期'])
        game = game[game['日期'].dt.strftime('%Y-%m') == month].copy()
    elif '日期' in game.columns and start is not None and end is not None:
        game['日期'] = to_datetime_safe(game['日期'])
        game = game[(game['日期'] >= start) & (game['日期'] < end + pd.Timedelta(days=1))].copy()

    c1, c2 = st.columns(2)
    with c1:
        venue = apply_multiselect(venue, '场馆名称', '场馆名称', 'gv_venue')
    with c2:
        game = apply_multiselect(game, '游戏类型', '游戏类型', 'gv_type')

    notices = []
    if '站点名称' in venue.columns and safe_nunique(venue, '站点名称') <= 1:
        notices.append(FilterNotice('站点名称未设为主筛选', '当前样本中站点名称仅有单一值，不作为主筛选条件。'))
    add_info_box(notices)

    gv_winloss = safe_sum(venue, '公司输赢')
    cols = st.columns(4)
    show_metric(cols[0], '投注人数', fmt_num(safe_sum(venue, '投注人数')))
    show_metric(cols[1], '有效投注额', fmt_num(safe_sum(venue, '有效投注额')))
    show_metric(cols[2], '公司输赢', fmt_num(gv_winloss), tone=tone_by_sign(gv_winloss))
    show_metric(cols[3], '场馆数', fmt_num(safe_nunique(venue, '场馆名称')))

    c1, c2 = st.columns(2)
    with c1:
        with st.container(border=True):
            section_header('场馆有效投注额')
            if {'场馆名称', '有效投注额'}.issubset(venue.columns):
                grp = venue.groupby('场馆名称', as_index=False)['有效投注额'].sum().nlargest(15, '有效投注额').sort_values('有效投注额')
                fig = px.bar(grp, y='场馆名称', x='有效投注额', orientation='h', template=TEMPLATE,
                             color='有效投注额', color_continuous_scale='blues')
                fig.update_layout(height=430, coloraxis_showscale=False)
                st.plotly_chart(fig, width='stretch')
    with c2:
        with st.container(border=True):
            section_header('游戏类型结构（Treemap）')
            if {'游戏类型', '场馆名称', '有效投注额'}.issubset(game.columns):
                tmp = game.groupby(['游戏类型', '场馆名称'], as_index=False)['有效投注额'].sum()
                fig = px.treemap(tmp, path=['游戏类型', '场馆名称'], values='有效投注额', template=TEMPLATE)
                fig.update_layout(height=430)
                st.plotly_chart(fig, width='stretch')

    with st.container(border=True):
        section_header('游戏明细（原始字段）')
        table_cols = [c for c in ['日期', '游戏类型', '场馆名称', '游戏名称', '投注人数', '有效投注额', '公司输赢'] if c in game.columns]
        if table_cols:
            st.dataframe(game[table_cols].sort_values(table_cols[0], ascending=False), width='stretch', hide_index=True)


def render_agent_member_matrix():
    """代理 × 会员 明细 — 6/4 新增 (Miru 风控决策面板)"""
    member = load_table('raw_member_report')

    hero('代理 × 会员 明细', '各代理名下会员 KPI 与套利特征识别，支持风控决策。',
         latest_imported_at(member),
         basis='会员报表＋代理报表（后台导出·每月上传）',
         detail=(
             '**分析范围**：各代理名下会员 KPI、累积投注与套利特征识别。\n\n'
             '**数据来源（后台导出 → 上传）**：会员报表（报表中心→会员报表）＋代理报表（报表中心→代理报表）。\n\n'
             '**计算口径**：会员身份＝会员账号＋代理；累积投注、公司净为逐月数值，跨快照相加为区间累计。\n\n'
             '**更新方式**：手动上传。完整对照见「数据说明」页。'
         ))

    if member.empty:
        st.warning('暂无会员数据')
        return

    # 准备数据 (合最新 snapshot 累积口径)
    df = member.copy()
    for col in ['存款额', '取款额', '有效投注额', '公司输赢', '红利', '返水', '公司收入', '首存金额']:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

    # 代理为空标 (直客)
    df['代理'] = df['代理'].fillna('(直客)').replace('', '(直客)').astype(str)

    # ━━ 月份多选筛选 ━━
    if '_snapshot_month' in df.columns:
        all_months = sorted(df['_snapshot_month'].dropna().astype(str).unique().tolist())
        c1, c2 = st.columns([3, 1])
        with c1:
            sel_months = st.multiselect(
                '📅 月份筛选 (默认全部累积; 选某几月则只计该范围)',
                options=all_months, default=all_months, key='agent_matrix_months',
                help='会员报表是月度 snapshot, 所以筛选粒度是月, 不是日'
            )
        with c2:
            st.markdown(f'**已选**: {len(sel_months)} / {len(all_months)} 月')
        if sel_months:
            df = df[df['_snapshot_month'].astype(str).isin(sel_months)]
        else:
            st.warning('请至少选一个月份')
            return
        if df.empty:
            st.info('所选月份无数据')
            return

    # 累积到 (会员账号 × 代理) 层 — 跨月加总
    grp_member = df.groupby(['会员账号', '代理'], as_index=False).agg(
        VIP等级=('VIP等级', 'max'),
        累积存款=('存款额', 'sum'),
        累积取款=('取款额', 'sum'),
        累积有效投注=('有效投注额', 'sum'),
        累积公司输赢=('公司输赢', 'sum'),
        累积红利=('红利', 'sum'),
        累积返水=('返水', 'sum'),
        累积公司净收入=('公司收入', 'sum'),
        会员状态=('会员状态', 'last') if '会员状态' in df.columns else ('会员账号', 'count'),
        用户标签=('用户标签', 'last') if '用户标签' in df.columns else ('会员账号', 'count'),
        跨月数=('_snapshot_month', 'nunique') if '_snapshot_month' in df.columns else ('会员账号', 'count'),
    )

    # 红利依赖度 (红利+返水 / 投注)
    grp_member['红+返/投注%'] = (
        (grp_member['累积红利'] + grp_member['累积返水']) /
        grp_member['累积有效投注'].replace(0, 1) * 100
    ).round(2)
    grp_member['holding%'] = (
        grp_member['累积公司输赢'] / grp_member['累积有效投注'].replace(0, 1) * 100
    ).round(3)

    # 套利 flag
    grp_member['套利特征'] = (
        (grp_member['累积有效投注'] > 1_000_000) &
        (grp_member['累积公司输赢'].abs() / grp_member['累积有效投注'].replace(0, 1) < 0.005) &
        ((grp_member['累积红利'] + grp_member['累积返水']) > 10_000)
    )
    if '用户标签' in grp_member.columns:
        TAG_KEYWORDS = ['套利', '高风险', '多平台', '跨平台对打', '骗分', '专业玩家', '软件投注']
        # 避开 pandas 3.x + pyarrow 的 apply / map 不兼容 — 用 list comprehension
        grp_member['tag_命中'] = [
            ','.join([k for k in TAG_KEYWORDS if k in (str(x) if pd.notna(x) else '')]) or ''
            for x in grp_member['用户标签']
        ]
    else:
        grp_member['tag_命中'] = ''

    # ━━━━━━━━ 1. 代理总览 ━━━━━━━━
    section_header('1. 代理总览', '每个代理底下: 会员数 / 累积投注 / 累积净 / 红利占比 / 套利户数')
    grp_agent = grp_member.groupby('代理', as_index=False).agg(
        会员数=('会员账号', 'nunique'),
        累积投注=('累积有效投注', 'sum'),
        累积输赢=('累积公司输赢', 'sum'),
        累积红利=('累积红利', 'sum'),
        累积返水=('累积返水', 'sum'),
        累积公司净=('累积公司净收入', 'sum'),
        套利户数=('套利特征', 'sum'),
    )
    grp_agent['红+返/投注%'] = (
        (grp_agent['累积红利'] + grp_agent['累积返水']) /
        grp_agent['累积投注'].replace(0, 1) * 100
    ).round(2)
    grp_agent['holding%'] = (
        grp_agent['累积输赢'] / grp_agent['累积投注'].replace(0, 1) * 100
    ).round(3)
    # 排序: 累积投注 desc
    grp_agent = grp_agent.sort_values('累积投注', ascending=False)

    # KPI 摘要
    c1, c2, c3, c4 = st.columns(4)
    _arb_cnt = int(grp_agent['套利户数'].sum())
    show_metric(c1, '代理总数', fmt_num(grp_agent['代理'].nunique()))
    show_metric(c2, '会员总数', fmt_num(grp_agent['会员数'].sum()))
    show_metric(c3, '累积投注合计', fmt_num(grp_agent['累积投注'].sum()))
    show_metric(c4, '套利特征户数', fmt_num(_arb_cnt), tone='bad' if _arb_cnt else 'good',
                help_text='需要关注的风险会员数' if _arb_cnt else '未发现套利特征会员')

    # ── 套利特征会员明细（谁、归谁、为什么）──
    if _arb_cnt > 0:
        section_header(f'⚠️ 套利特征会员明细（{_arb_cnt} 个，就是上面那个数字的实际名单）',
                       '判定条件：累积有效投注 > 100 万　且　|holding| < 0.5%（庄家在这人身上几乎不赢不输）　且　红利+返水 > 1 万。'
                       '下面是被标记的会员、归哪个代理、关键数据——直接拿去查 / 处理。')
        arb = grp_member[grp_member['套利特征']].copy()
        arb['红利+返水'] = (arb['累积红利'].fillna(0) + arb['累积返水'].fillna(0))
        arb_cols = ['会员账号', '代理', 'VIP等级', '累积有效投注', 'holding%', '红利+返水',
                    '累积公司输赢', '累积公司净收入', 'tag_命中', '会员状态']
        arb_cols = [c for c in arb_cols if c in arb.columns]
        arb_show = arb[arb_cols].sort_values('累积有效投注', ascending=False)
        for c in ['累积有效投注', '红利+返水', '累积公司输赢', '累积公司净收入']:
            if c in arb_show.columns:
                arb_show[c] = arb_show[c].fillna(0).round(0).astype('int64')
        st.dataframe(arb_show, use_container_width=True, hide_index=True)
        st.caption('holding% 越接近 0 = 庄家在这人身上几乎没赢（套利典型）；红利+返水 = 这人累计拿走的红利+返水；'
                   'tag_命中 = 用户标签里命中的风险词（套利/高风险/多平台等）；空白代表只靠数据特征命中、标签没标。')

    # 搜索 / 排序
    search_q = st.text_input('🔍 搜代理名', '', key='agent_matrix_search', placeholder='例: newbee888')
    display_agent = grp_agent.copy()
    if search_q.strip():
        display_agent = display_agent[display_agent['代理'].str.contains(search_q.strip(), case=False, na=False)]

    # 排序
    sort_by = st.selectbox('排序', ['累积投注', '累积公司净', '会员数', '红+返/投注%', '套利户数'],
                          index=0, key='agent_matrix_sort')
    asc = st.checkbox('升序', value=False, key='agent_matrix_asc')
    display_agent = display_agent.sort_values(sort_by, ascending=asc)

    # 格式化数字
    show_df = display_agent.copy()
    for col in ['累积投注', '累积输赢', '累积红利', '累积返水', '累积公司净']:
        show_df[col] = show_df[col].round(0)
    st.markdown(f'**显示 {len(show_df)} / {len(grp_agent)} 个代理**')
    st.dataframe(show_df, use_container_width=True, hide_index=True, height=420,
                 column_config={
                     '累积投注': st.column_config.NumberColumn(format='%d'),
                     '累积输赢': st.column_config.NumberColumn(format='%d'),
                     '累积红利': st.column_config.NumberColumn(format='%d'),
                     '累积返水': st.column_config.NumberColumn(format='%d'),
                     '累积公司净': st.column_config.NumberColumn(format='%d'),
                 })

    # ━━━━━━━━ 2. 查询单一代理或会员 ━━━━━━━━
    section_header('2. 单查 代理 / 会员', '贴代理名 → 看该代理底下全部会员;贴会员账号 → 直接定位单一会员')

    c1, c2 = st.columns(2)
    with c1:
        sel_agent_input = st.text_input('🔍 输代理名 (例: newbee888)', '',
                                         key='agent_lookup', placeholder='留空则用下方下拉框选')
    with c2:
        sel_member_input = st.text_input('🔍 输会员账号 (例: yjno888)', '',
                                          key='member_lookup', placeholder='直接查会员明细')

    # 备用下拉框 (默认 100 大代理)
    agent_options = ['(用上方搜索框 / 选这里)'] + display_agent['代理'].head(200).tolist()
    sel_agent_dropdown = st.selectbox('或下拉选代理 (top 200 by 投注量)', agent_options, index=0,
                                       key='agent_matrix_select')

    # 决定要查的代理 (优先输入框 > 下拉)
    sel_agent = sel_agent_input.strip() if sel_agent_input.strip() else (
        sel_agent_dropdown if sel_agent_dropdown != '(用上方搜索框 / 选这里)' else None
    )

    # 单查会员模式 (优先级最高)
    if sel_member_input.strip():
        section_header(f'🎯 单一会员: {sel_member_input.strip()}', '')
        mem_q = sel_member_input.strip()
        mem_match = grp_member[grp_member['会员账号'].str.contains(mem_q, case=False, na=False)].copy()
        if mem_match.empty:
            st.warning(f'没找到会员账号 含 "{mem_q}" 的记录')
        else:
            st.markdown(f'找到 **{len(mem_match)}** 笔匹配:')
            cols = ['会员账号', '代理', 'VIP等级', '累积存款', '累积取款', '累积有效投注',
                    '累积公司输赢', '累积红利', '累积返水', '累积公司净收入',
                    'holding%', '红+返/投注%', '套利特征', '会员状态', '用户标签']
            cols = [c for c in cols if c in mem_match.columns]
            for c in ['累积存款', '累积取款', '累积有效投注', '累积公司输赢', '累积红利', '累积返水', '累积公司净收入']:
                if c in mem_match.columns:
                    mem_match[c] = mem_match[c].round(0)
            st.dataframe(mem_match[cols], use_container_width=True, hide_index=True)

            # 显示该会员 月度趋势 (跨月 snapshot)
            mem_acct_list = mem_match['会员账号'].unique().tolist()
            monthly = df[df['会员账号'].isin(mem_acct_list)].copy()
            if not monthly.empty and '_snapshot_month' in monthly.columns:
                section_header('该会员月度趋势', '')
                m_cols = ['_snapshot_month', '会员账号', 'VIP等级', '存款额', '取款额',
                          '有效投注额', '公司输赢', '红利', '返水', '公司收入', '会员状态']
                m_cols = [c for c in m_cols if c in monthly.columns]
                monthly_show = monthly[m_cols].sort_values(['会员账号', '_snapshot_month'])
                for c in ['存款额', '取款额', '有效投注额', '公司输赢', '红利', '返水', '公司收入']:
                    if c in monthly_show.columns:
                        monthly_show[c] = monthly_show[c].round(0)
                st.dataframe(monthly_show, use_container_width=True, hide_index=True)

    # 代理底下会员明细模式
    sub = None
    if sel_agent and sel_agent != '(用上方搜索框 / 选这里)':
        section_header(f'代理: {sel_agent} 名下全部会员', '')
        sub = grp_member[grp_member['代理'].str.contains(sel_agent, case=False, na=False)].copy()
        if sub.empty:
            st.warning(f'没找到代理 含 "{sel_agent}" 的会员')
            sub = None

    if sub is not None and not sub.empty:
        # 该代理 KPI
        c1, c2, c3, c4, c5 = st.columns(5)
        _sub_net = float(sub['累积公司净收入'].sum())
        _sub_arb = int(sub['套利特征'].sum())
        show_metric(c1, '会员数', fmt_num(sub['会员账号'].nunique()))
        show_metric(c2, '累积投注', fmt_num(sub['累积有效投注'].sum()))
        show_metric(c3, '累积公司净', fmt_num(_sub_net), tone=tone_by_sign(_sub_net))
        show_metric(c4, '套利户数', fmt_num(_sub_arb), tone='bad' if _sub_arb else None)
        tagged = (sub['tag_命中'].astype(str).str.len() > 0).sum() if 'tag_命中' in sub.columns else 0
        show_metric(c5, 'tag 命中数', fmt_num(tagged), tone='warn' if tagged else None)

        # 会员明细表
        cols_to_show = ['会员账号', 'VIP等级', '累积存款', '累积取款', '累积有效投注',
                        '累积公司输赢', '累积红利', '累积返水', '累积公司净收入',
                        'holding%', '红+返/投注%', '套利特征', '会员状态', '用户标签']
        cols_to_show = [c for c in cols_to_show if c in sub.columns]
        display_sub = sub[cols_to_show].copy()
        for c in ['累积存款', '累积取款', '累积有效投注', '累积公司输赢', '累积红利', '累积返水', '累积公司净收入']:
            if c in display_sub.columns:
                display_sub[c] = display_sub[c].round(0)
        display_sub = display_sub.sort_values('累积有效投注', ascending=False)
        st.dataframe(display_sub, use_container_width=True, hide_index=True)

        # ─── 该代理的「官方代理报表 月度 KPI」(直接拉 raw_agent_report) ───
        # 这才是跟包网商 customer service 提供的格式一致的口径
        st.markdown('---')
        st.markdown(f'**📊 该代理「官方代理报表」月度 KPI** (raw_agent_report 直接读取,跟包网商提供的格式一致)')
        try:
            agent_rep = load_table('raw_agent_report')
            if not agent_rep.empty:
                mask = (agent_rep['代理名称'].astype(str).str.lower() == sel_agent.lower()) | \
                       (agent_rep['代理编号'].astype(str).str.lower() == sel_agent.lower())
                ar = agent_rep[mask].copy()
                if not ar.empty:
                    ar['月'] = ar['日期'].astype(str).str[:7]
                    for col in ['注册人数','首存人数','投注人数','存款额','取款额',
                                '有效投注额','公司输赢','红利','返水','代理佣金',
                                '公司收入','提前结算','场馆费']:
                        if col in ar.columns:
                            ar[col] = pd.to_numeric(ar[col], errors='coerce').fillna(0)
                    grpcols = ['注册人数','首存人数','投注人数','存款额','取款额',
                               '有效投注额','公司输赢','红利','返水','代理佣金',
                               '公司收入','提前结算']
                    grpcols = [c for c in grpcols if c in ar.columns]
                    monthly = ar.groupby('月', as_index=False)[grpcols].sum()
                    for c in ['存款额','取款额','有效投注额','公司输赢','红利','返水',
                              '代理佣金','公司收入','提前结算']:
                        if c in monthly.columns:
                            monthly[c] = monthly[c].round(2)
                    st.dataframe(monthly, use_container_width=True, hide_index=True)
                    st.caption('注: 此处「公司收入」= 公司输赢 - 红利 - 返水 - 佣金 + 系统调整 + 提前结算 (后台口径). '
                               '包网商若再扣 场馆费 + 手续费 = 平台净盈利 (会小于公司收入).')
                else:
                    st.info(f'代理报表无 {sel_agent} 数据')
        except Exception as e:
            st.warning(f'代理报表查询失败: {e}')

    # ━━━━━━━━ 3. 全部会员表 ━━━━━━━━
    section_header('3. 全部会员表',
                  f'{len(grp_member)} 个会员 (跨所选月份),可搜寻 / 排序 / 筛 VIP / 筛代理')

    c1, c2, c3 = st.columns([2, 1, 1])
    with c1:
        mem_search = st.text_input('🔍 搜会员账号 / 代理名 (会员账号或代理名任一含关键词都显示)',
                                    '', key='all_mem_search',
                                    placeholder='例: yjno888 或 newbee888')
    with c2:
        vip_filter = st.selectbox('VIP 等级筛选', ['(全部)'] + sorted(grp_member['VIP等级'].dropna().astype(str).unique().tolist()),
                                   key='all_mem_vip')
    with c3:
        status_filter = st.selectbox('会员状态', ['(全部)', '启用', '禁用'],
                                      key='all_mem_status') if '会员状态' in grp_member.columns else '(全部)'

    all_mem = grp_member.copy()
    if mem_search.strip():
        q = mem_search.strip()
        all_mem = all_mem[
            all_mem['会员账号'].astype(str).str.contains(q, case=False, na=False) |
            all_mem['代理'].astype(str).str.contains(q, case=False, na=False)
        ]
    if vip_filter != '(全部)':
        all_mem = all_mem[all_mem['VIP等级'].astype(str) == vip_filter]
    if status_filter != '(全部)' and '会员状态' in all_mem.columns:
        all_mem = all_mem[all_mem['会员状态'].astype(str) == status_filter]

    mem_sort_by = st.selectbox(
        '排序', ['累积有效投注', '累积公司净收入', '累积红利', '累积存款', '累积取款', 'holding%'],
        index=0, key='all_mem_sort'
    )
    mem_asc = st.checkbox('升序', value=False, key='all_mem_asc')
    all_mem = all_mem.sort_values(mem_sort_by, ascending=mem_asc)

    st.markdown(f'**显示 {len(all_mem)} / {len(grp_member)} 个会员**')

    mem_cols = ['会员账号', '代理', 'VIP等级', '累积存款', '累积取款', '累积有效投注',
                '累积公司输赢', '累积红利', '累积返水', '累积公司净收入',
                'holding%', '红+返/投注%', '套利特征', '会员状态', '用户标签']
    mem_cols = [c for c in mem_cols if c in all_mem.columns]
    all_mem_show = all_mem[mem_cols].copy()
    for c in ['累积存款', '累积取款', '累积有效投注', '累积公司输赢',
              '累积红利', '累积返水', '累积公司净收入']:
        if c in all_mem_show.columns:
            all_mem_show[c] = all_mem_show[c].round(0)
    st.dataframe(all_mem_show, use_container_width=True, hide_index=True, height=500)

    # ━━━━━━━━ 4. 系统已 tag 但状态启用 ━━━━━━━━
    section_header('4. 系统已标记但状态启用的会员',
                  '用户标签命中 套利 / 高风险 / 多平台 / 跨平台对打 / 骗分 / 专业玩家 / 软件投注 的会员')

    if 'tag_命中' in grp_member.columns:
        tagged_df = grp_member[grp_member['tag_命中'].astype(str).str.len() > 0].copy()
        # 会员状态 = 启用
        if '会员状态' in tagged_df.columns:
            tagged_df = tagged_df[tagged_df['会员状态'].astype(str) == '启用']

        # 按累积投注降序
        tagged_df = tagged_df.sort_values('累积有效投注', ascending=False).head(100)

        st.markdown(f'共 **{len(tagged_df)}** 笔会员命中 tag 且状态启用 (top 100):')

        cols = ['会员账号', '代理', 'VIP等级', '累积有效投注', '累积公司输赢',
                '累积红利', '累积返水', '累积公司净收入', 'holding%',
                '红+返/投注%', '套利特征', 'tag_命中', '用户标签']
        cols = [c for c in cols if c in tagged_df.columns]
        for c in ['累积有效投注', '累积公司输赢', '累积红利', '累积返水', '累积公司净收入']:
            if c in tagged_df.columns:
                tagged_df[c] = tagged_df[c].round(0)
        st.dataframe(tagged_df[cols], use_container_width=True, hide_index=True)

        # 套利特征 + 启用 但 公司净亏 的清单
        st.markdown('---')
        st.markdown('**套利特征 + 状态启用 + 公司净亏损 的会员（建议优先处理）：**')
        action_df = tagged_df[
            (tagged_df['套利特征']) &
            (tagged_df['累积公司净收入'] < 0)
        ].sort_values('累积公司净收入').head(50)
        if action_df.empty:
            st.info('无符合条件 (套利特征 + 状态启用 + 公司净亏损)')
        else:
            st.dataframe(action_df[cols], use_container_width=True, hide_index=True)

    st.markdown('---')
    with st.expander('ℹ️ 字段说明 / 计算口径'):
        st.markdown('''
- **代理**: 取自 `raw_member_report.代理` 字段, 跨月相同 = 同一会员
- **累积**: 跨所有月份 snapshot 加总 (会员可能多月出现)
- **holding%** = 累积公司输赢 / 累积有效投注 × 100, **平台水位 1-1.5% 是正常**
- **红+返/投注%** = (累积红利 + 累积返水) / 累积有效投注 × 100, **正常会员 < 1.5%**
- **套利特征**: 累积投注 > 100 万 **且** |holding| < 0.5% **且** 红+返 > 1 万
- **tag 命中关键词**: 套利 / 高风险 / 多平台 / 跨平台对打 / 骗分 / 专业玩家 / 软件投注
- **状态启用**: 即「会员状态 = 启用」, 表示账户没被禁用
- **直客**: `代理` 字段为空 / null, 归入「(直客)」
''')


def render_new_member_analysis():
    hero('新注册分析',
         '直接从数据库读你已上传的会员数据，看新注册从哪来、谁带的、质量如何（按会员账号+代理去重）。'
         '要分析新数据？先把会员报表丢进顶部「数据上传」页存一下，这页就读得到。',
         basis='会员报表（口径为注册数的非代理部分·后台导出上传）',
         detail=(
             '**分析范围**：新注册来源、带来的代理、渠道／域名、质量（有无首存）与每日走势。\n\n'
             '**数据来源**：会员报表（报表中心→会员报表，须按注册时间、完整日期、全部页数导出）。\n\n'
             '**计算口径**：去重按会员账号＋代理；平台「注册数」对应会员报表的「非代理」部分。\n\n'
             '**更新方式**：手动上传（上传时会自动做完整度校验）。完整对照见「数据说明」页。'
         ))

    try:
        raw = load_table('raw_member_report')
    except Exception as e:
        st.error(f'读数据库失败：{str(e)[:120]}')
        return
    if raw is None or raw.empty or '会员账号' not in raw.columns:
        st.info('📭 数据库里还没有会员数据。\n\n'
                '先去顶部「数据上传」页，把后台下载的「会员报表」（密码 zip / 分好几份都行）拖进去存一下，'
                '再回这页，就会自动读出来分析——不用在这里上传。')
        return

    df = _nm_prepare(raw)
    if df.empty:
        st.warning('会员数据里没有可用的「注册时间」，无法做新注册分析。')
        return

    total_all = len(df)

    # ── 筛选器 ──
    section_header('筛选', '先圈范围，下面所有总览 / 走势 / 排行 / 交叉都跟着这里走。')
    fdf = _nm_date_filter(df)
    if fdf.empty:
        st.warning('当前日期范围内没有新注册。')
        return
    n_in_range = len(fdf)  # 日期范围内总数（下面的来源/渠道/域名/首存筛选会从这个数往下减）
    c1, c2 = st.columns([2, 1])
    with c1:
        if '用户来源' in fdf.columns:
            fdf = apply_multiselect(fdf, '用户来源', '用户来源（普代下线 / 直客 / 官代下线）',
                                    'nm_src2', options_df=df, auto_include_new=True)
    with c2:
        dep = st.radio('首存', ['全部', '只看有首存', '只看未充值'], horizontal=True, key='nm_dep')
    if dep == '只看有首存':
        fdf = fdf[fdf['有首存']].copy()
    elif dep == '只看未充值':
        fdf = fdf[~fdf['有首存']].copy()
    c3, c4 = st.columns(2)
    with c3:
        if '注册来源' in fdf.columns:
            fdf = apply_multiselect(fdf, '注册来源', '渠道 / 注册来源（多选）',
                                    'nm_chan2', options_df=df, auto_include_new=True)
    with c4:
        fdf = apply_multiselect(fdf, '域名', '域名（多选）', 'nm_dom2',
                                options_df=df, auto_include_new=True)

    if fdf.empty:
        st.warning('当前筛选下没有数据，放宽一下条件。')
        return

    n = len(fdf)
    has = int(fdf['有首存'].sum())
    fd_sum = float(fdf['首存额'].sum())
    n_zhike = int((fdf['代理n'] == '(直客/无代理)').sum())
    n_agent_mem = n - n_zhike
    n_agents = int(fdf[fdf['代理n'] != '(直客/无代理)']['代理n'].nunique())
    uniq_acct = int(fdf['会员账号'].nunique())

    section_header('总览', f'当前筛选：{n} 个新注册（本次上传共 {total_all} 个）')
    if n < n_in_range:
        st.caption(f'⚠️ 日期范围内本有 {n_in_range} 个，下面的「用户来源 / 渠道 / 域名 / 首存」筛选又减掉了 '
                   f'{n_in_range - n} 个，所以总览显示 {n} 个。想看完整 {n_in_range} 个，把这几个筛选都留在「全选」。')
    st.caption('💡 口径提醒：此处「新注册」按『会员账号＋代理』计算（同一账号挂在多个代理下会分别计入），'
               '因此可能比运营日报 / Daybook 的「注册数」（按唯一账号去重）略高。'
               '想知道实际新增了多少「人」→ 以运营日报的去重数为准；想看各代理 / 渠道各拉来多少 → 看这页。')
    mc = st.columns(6)
    show_metric(mc[0], '新注册（账号+代理）', fmt_num(n),
                help_text='按「会员账号＋代理」算：同一账号挂在多个代理下会分别计入，'
                          '用来把人头归到对应代理 / 渠道。')
    show_metric(mc[1], '唯一账号（人）', fmt_num(uniq_acct),
                help_text='去重到「人」（不分代理）。对应平台报表 / Daybook 的注册数。'
                          f'比左边少 {n - uniq_acct}，差额=同一账号挂在多个代理下。')
    show_metric(mc[2], '有首存（充值）', f'{has}（{has / n * 100:.0f}%）', tone='good')
    show_metric(mc[3], '未充值（注册了没充值）', f'{n - has}（{(n - has) / n * 100:.0f}%）',
                tone='warn' if n and (n - has) / n > 0.5 else None)
    show_metric(mc[4], '首存总额', fmt_num(round(fd_sum)))
    show_metric(mc[5], '代理带 / 直客', f'{n_agent_mem} / {n_zhike}',
                help_text=f'有产出代理 {n_agents} 个')

    # ── 每日走势 ──
    section_header('每日新注册走势', '绿=有首存、红=未充值；某天明显高出就是暴增日。')
    daily = (fdf.groupby('注册日')
             .agg(新注册=('会员账号', 'size'), 有首存=('有首存', 'sum')).reset_index())
    daily['未充值'] = daily['新注册'] - daily['有首存']
    fig = go.Figure()
    fig.add_bar(x=daily['注册日'], y=daily['有首存'], name='有首存', marker_color='#2dd4a7')
    fig.add_bar(x=daily['注册日'], y=daily['未充值'], name='未充值', marker_color='#fb7185')
    fig.update_layout(barmode='stack', template='plotly_dark', height=320,
                      paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                      margin=dict(l=10, r=10, t=10, b=10),
                      legend=dict(orientation='h', y=1.1, x=0))
    st.plotly_chart(fig, use_container_width=True)

    # ── 获客质量诊断：直客vs代理 价值对比 + 代理质量分层榜 ──
    _nm_value_by_source(fdf)
    _nm_quality_board(fdf)
    _nm_funnel_ttf(fdf)
    _nm_cohort_pl(fdf)

    # ── 其他来源排行 ──
    section_header('其他来源排行 — 邀请码 / 渠道 / 域名',
                   '各看注册数、有首存、首存额、未充值率。代理质量看上面的「分层榜」。')
    rc1, rc2 = st.columns(2)
    with rc1:
        ic = fdf[fdf['邀请码'].notna()].copy()
        if not ic.empty:
            full = (ic.groupby('邀请码')
                    .agg(注册数=('会员账号', 'size'), 有首存=('有首存', 'sum'), 首存额=('首存额', 'sum'),
                         对应代理=('代理n', lambda s: s.value_counts().index[0]))
                    .sort_values('注册数', ascending=False))
            ic_total = int(full['注册数'].sum())
            ic_groups = len(full)
            g = full.head(20).reset_index()
            g['未充值率'] = ((g['注册数'] - g['有首存']) / g['注册数'] * 100).round(0).astype(int).astype(str) + '%'
            g['首存额'] = g['首存额'].round(0).astype(int)
            st.markdown('**邀请码排行（含对应代理）**')
            st.dataframe(g, use_container_width=True, hide_index=True)
            if ic_groups > 20:
                shown = int(g['注册数'].sum())
                st.caption(f'共 {ic_groups} 个邀请码、{ic_total} 个带码注册；上表为前 20 名（{shown} 个），'
                           f'其余 {ic_groups - 20} 个合计 {ic_total - shown} 个（长尾，未列出）。'
                           f'另有未带邀请码的注册不在此表。')
            else:
                st.caption(f'共 {ic_groups} 个邀请码、{ic_total} 个带码注册（已全部列出）。另有未带邀请码的注册不在此表。')
        else:
            st.markdown('**邀请码排行**')
            st.caption('这批数据里没有带邀请码的注册。')
    with rc2:
        _nm_rank(fdf, '注册来源', '渠道 / 注册来源排行')
    _nm_rank(fdf, '域名', '域名排行')

    # ── 交叉分析 ──
    section_header('交叉分析', '任选两个维度交叉，看「哪个代理走哪个渠道」「哪个域名质量好」这种。')
    dim_map = {'代理': '代理n', '渠道': '注册来源', '域名': '域名',
               '用户来源': '用户来源', '地区': '地区名称', '邀请码': '邀请码'}
    dim_map = {k: v for k, v in dim_map.items() if v in fdf.columns}
    dim_names = list(dim_map.keys())
    xc1, xc2, xc3 = st.columns(3)
    with xc1:
        dimA = st.selectbox('维度 A（行）', dim_names, index=0, key='nm_xa')
    with xc2:
        dimB = st.selectbox('维度 B（列）', dim_names, index=min(1, len(dim_names) - 1), key='nm_xb')
    with xc3:
        xmetric = st.selectbox('交叉看什么', ['注册数', '有首存数', '首存额'], key='nm_xm')
    ca, cb = dim_map[dimA], dim_map[dimB]
    base = fdf.copy()
    ra = base[ca].fillna('(空)').astype(str)
    rb = base[cb].fillna('(空)').astype(str)
    if xmetric == '注册数':
        piv = pd.crosstab(ra, rb)
    elif xmetric == '有首存数':
        piv = pd.crosstab(ra, rb, values=base['有首存'].astype(int), aggfunc='sum').fillna(0).astype(int)
    else:
        piv = pd.crosstab(ra, rb, values=base['首存额'], aggfunc='sum').fillna(0).round(0).astype(int)
    top_rows = piv.sum(axis=1).sort_values(ascending=False).head(15).index
    top_cols = piv.sum(axis=0).sort_values(ascending=False).head(15).index
    piv = piv.loc[top_rows, top_cols]
    st.caption(f'{dimA} × {dimB} — {xmetric}（各取前 15，按总量排）')
    st.dataframe(piv, use_container_width=True)

    # ── 查单一代理 ──
    section_header('查单一代理', '输入或选一个代理账号，看他名下新增了哪些会员、多少充值。')
    agent_opts = ['(选一个)'] + fdf[fdf['代理n'] != '(直客/无代理)']['代理n'].value_counts().index.tolist()
    pick = st.selectbox('代理账号', agent_opts, key='nm_pick_agent')
    if pick != '(选一个)':
        sub = fdf[fdf['代理n'] == pick].copy()
        am = st.columns(4)
        show_metric(am[0], '新增会员', fmt_num(len(sub)))
        show_metric(am[1], '有首存', f"{int(sub['有首存'].sum())}", tone='good')
        show_metric(am[2], '未充值', f"{int((~sub['有首存']).sum())}", tone='warn')
        show_metric(am[3], '首存总额', fmt_num(round(float(sub['首存额'].sum()))))
        detail_cols = [c for c in ['会员账号', '注册时间', '首存额', '注册来源', '域名', '邀请码',
                                   '地区名称', '用户来源', 'VIP等级', '会员状态']
                       if c in sub.columns]
        st.dataframe(sub[detail_cols].sort_values('首存额', ascending=False),
                     use_container_width=True, hide_index=True)


def render_agent_market_monthly():
    hero('市代月度结算',
         '市场代理每月的 产值 / 输赢 / 红利 / 返水 / 集团分成 / 发放佣金 / 平台净营利 / 累计挂账，可看走势、两月对比。',
         source_badge='数据源：市代「整理资料」(自助上传)',
         basis='市代「整理资料」表（数据上传页拖 xlsx 即入库；月份读表内「月份」栏）',
         detail=(
             '**分析范围**：市场代理每月的产值、输赢、红利/返水、集团分成、发放佣金、平台净营利、累计挂账，'
             '含月度走势与两月对比。\n\n'
             '**数据来源**：市代「整理资料」表（每代理每月一行），自助上传至「数据上传」页 → `raw_agent_settlement_monthly`，按月份去重。\n\n'
             '**跟「代理佣金」页的区别**：那页是「代理佣金 单线/团队」+ 平哥结算月报（不同数据源）；这页只用你上传的市代月度表。'))
    try:
        am = load_table('raw_agent_settlement_monthly')
    except Exception:
        am = pd.DataFrame()
    if am is None or am.empty or '月份' not in am.columns:
        st.info('📭 尚无市代月度数据。请到「🗂 数据上传」页把市代「整理资料」xlsx 拖进去，这页就读得到。')
        return
    am_months = sorted(am['月份'].astype(str).unique().tolist(), reverse=True)

    section_header('单月总览', '选月份看当月各代理合计')
    sel_am = st.selectbox('📅 月份', am_months, key='amp_month')
    cur = am[am['月份'].astype(str) == sel_am].copy()
    for c in ('注册人数', '首存人数', '活跃人数', '总充', '总提', '有效投注额', '总输赢',
              '红利', '返水', '集团分成', '发放佣金', '平台净营利', '累计挂账额度'):
        if c in cur.columns:
            cur[c] = pd.to_numeric(cur[c], errors='coerce')

    def _s(c):
        return float(cur[c].sum()) if c in cur.columns else 0.0
    k1 = st.columns(4)
    show_metric(k1[0], '市场代理数', fmt_num(cur['代理帐号'].nunique()))
    show_metric(k1[1], '有效投注额', fmt_num(round(_s('有效投注额'))))
    show_metric(k1[2], '发放佣金', fmt_num(round(_s('发放佣金'))), tone='warn')
    show_metric(k1[3], '平台净营利', fmt_num(round(_s('平台净营利'))), tone=tone_by_sign(_s('平台净营利')))
    k2 = st.columns(4)
    show_metric(k2[0], '累计挂账（合计）', fmt_num(round(_s('累计挂账额度'))), tone='warn',
                help_text='截至该月各市场代理的累计挂账余额合计（负值＝代理端尚有赤字）')
    show_metric(k2[1], '集团分成', fmt_num(round(_s('集团分成'))))
    show_metric(k2[2], '红利', fmt_num(round(_s('红利'))), tone='warn')
    show_metric(k2[3], '返水', fmt_num(round(_s('返水'))), tone='warn')

    section_header('各市场代理明细', f'{sel_am} · 按平台净营利排序')
    disp_cols = [c for c in ['代理名称', '代理帐号', '活跃人数', '总充', '有效投注额', '总输赢',
                             '红利', '返水', '集团分成', '发放佣金', '平台净营利', '累计挂账额度', '发展情况']
                 if c in cur.columns]
    sort_col = '平台净营利' if '平台净营利' in cur.columns else disp_cols[0]
    st.dataframe(cur[disp_cols].sort_values(sort_col, ascending=False), width='stretch', hide_index=True)

    # 月度走势
    am2 = am.copy()
    for c in ('有效投注额', '总输赢', '红利', '返水', '集团分成', '发放佣金', '平台净营利', '累计挂账额度'):
        if c in am2.columns:
            am2[c] = pd.to_numeric(am2[c], errors='coerce')
    trend = (am2.groupby('月份')
             .agg(发放佣金=('发放佣金', 'sum'), 平台净营利=('平台净营利', 'sum'),
                  累计挂账=('累计挂账额度', 'sum'), 有效投注额=('有效投注额', 'sum'))
             .reset_index().sort_values('月份'))
    section_header('月度走势', '各月合计（你上传的全部月份）')
    c_a, c_b = st.columns(2)
    with c_a:
        with st.container(border=True):
            fig = px.bar(trend, x='月份', y=['发放佣金', '平台净营利'], barmode='group',
                         template=TEMPLATE, title='发放佣金 vs 平台净营利')
            fig.update_layout(height=320, legend_title_text='', xaxis_title=None, yaxis_title=None)
            st.plotly_chart(fig, width='stretch')
    with c_b:
        with st.container(border=True):
            fig2 = px.line(trend, x='月份', y='累计挂账', markers=True, template=TEMPLATE, title='累计挂账走势')
            fig2.update_layout(height=320, xaxis_title=None, yaxis_title=None)
            st.plotly_chart(fig2, width='stretch')

    # 两月对比
    section_header('两月对比', '选两个月，看整体与各代理的变化（变化 = B − A）')
    cc = st.columns(2)
    ma = cc[0].selectbox('A 月（基准）', am_months, index=min(1, len(am_months) - 1), key='amp_cmpA')
    mb = cc[1].selectbox('B 月（对比）', am_months, index=0, key='amp_cmpB')

    def _msum(m, c):
        d = am2[am2['月份'].astype(str) == m]
        return float(pd.to_numeric(d[c], errors='coerce').sum()) if c in d.columns and len(d) else 0.0
    cmp_rows = []
    for c in ['有效投注额', '总输赢', '红利', '返水', '集团分成', '发放佣金', '平台净营利', '累计挂账额度']:
        if c in am2.columns:
            a, b = _msum(ma, c), _msum(mb, c)
            cmp_rows.append({'指标': c, ma: round(a), mb: round(b), '变化(B−A)': round(b - a)})
    st.dataframe(pd.DataFrame(cmp_rows), width='stretch', hide_index=True)

    keyc = '平台净营利' if '平台净营利' in am2.columns else '发放佣金'
    da = am2[am2['月份'].astype(str) == ma][['代理帐号', '代理名称', keyc]].rename(columns={keyc: f'A({ma})'})
    db = am2[am2['月份'].astype(str) == mb][['代理帐号', keyc]].rename(columns={keyc: f'B({mb})'})
    mg = pd.merge(da, db, on='代理帐号', how='outer')
    mg[f'A({ma})'] = pd.to_numeric(mg[f'A({ma})'], errors='coerce').fillna(0)
    mg[f'B({mb})'] = pd.to_numeric(mg[f'B({mb})'], errors='coerce').fillna(0)
    mg['变化'] = mg[f'B({mb})'] - mg[f'A({ma})']
    mg = mg.sort_values('变化', ascending=False)
    section_header('各代理变化', f'{keyc}：{ma} → {mb}（涨幅排前、跌幅排后）')
    st.dataframe(mg, width='stretch', hide_index=True,
                 column_config={f'A({ma})': st.column_config.NumberColumn(format='%.0f'),
                                f'B({mb})': st.column_config.NumberColumn(format='%.0f'),
                                '变化': st.column_config.NumberColumn(format='%.0f')})
