const categories = [
  { id: 'overview', label: '总览' },
  { id: 'rates', label: '利率债' },
  { id: 'credit', label: '信用债' },
  { id: 'convertible', label: '可转债' },
  { id: 'ust', label: '美债' },
  { id: 'commodities', label: '商品' }
];

const periodLabels = { day: '当日', week: '本周', month: '本月' };

const authoritativeSources = {
  overview: [
    { title: '中债收益率曲线与估值', publisher: '中国债券信息网 · 官方', url: 'https://yield.chinabond.com.cn/' },
    { title: 'Daily Treasury Yield Curve', publisher: 'U.S. Treasury · 官方', url: 'https://home.treasury.gov/resource-center/data-chart-center/interest-rates/TextView?type=daily_treasury_yield_curve' }
  ],
  rates: [
    { title: '中债收益率曲线与估值', publisher: '中国债券信息网 · 官方', url: 'https://yield.chinabond.com.cn/' },
    { title: '公开市场业务交易公告', publisher: '中国人民银行 · 官方', url: 'https://www.pbc.gov.cn/zhengcehuobisi/125207/125213/125431/125475/index.html' }
  ],
  credit: [
    { title: '中债收益率曲线与估值', publisher: '中国债券信息网 · 官方', url: 'https://yield.chinabond.com.cn/' },
    { title: '银行间市场数据与披露', publisher: '中国货币网 · 官方', url: 'https://www.chinamoney.com.cn/chinese/' }
  ],
  convertible: [
    { title: '中证转债指数（000832）', publisher: '中证指数 · 官方', url: 'https://www.csindex.com.cn/#/indices/family/detail?indexCode=000832' },
    { title: '债券行情与信息披露', publisher: '上海证券交易所 · 官方', url: 'https://bond.sse.com.cn/' }
  ],
  ust: [
    { title: 'Daily Treasury Par Yield Curve Rates', publisher: 'U.S. Treasury · 官方', url: 'https://home.treasury.gov/resource-center/data-chart-center/interest-rates/TextView?type=daily_treasury_yield_curve' },
    { title: 'FOMC statements and calendars', publisher: 'Federal Reserve · 官方', url: 'https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm' }
  ],
  commodities: [
    { title: 'Weekly Petroleum Status Report', publisher: 'U.S. EIA · 官方', url: 'https://www.eia.gov/petroleum/supply/weekly/' },
    { title: 'Gold futures market data', publisher: 'CME Group · 交易所', url: 'https://www.cmegroup.com/markets/metals/precious/gold.html' }
  ]
};

const chartCatalog = {
  rates: {
    title: '中国10年国债收益率', unit: '%', changeUnit: 'bp',
    dates: ['2026-09-01', '2026-09-14', '2026-09-15', '2026-09-16'],
    labels: ['09/01', '09/14', '09/15', '09/16'], values: [1.683, 1.682, 1.6815, 1.6785],
    note: '月内维持1.68%附近窄幅波动；收益率下行代表债券价格走强。',
    source: '新华财经 / 中债', sourceUrl: 'https://yield.chinabond.com.cn/'
  },
  convertible: {
    title: '中证转债指数', unit: '点', changeUnit: 'pct',
    dates: ['2026-09-01', '2026-09-14', '2026-09-15', '2026-09-16'],
    labels: ['09/01', '09/14', '09/15', '09/16'], values: [493.42, 480.04, 477.88, 480.67],
    note: '月内指数回撤，但最近三个交易日呈先抑后扬，说明机会更偏结构性。',
    source: '中证指数 / 新华财经', sourceUrl: 'https://www.csindex.com.cn/#/indices/family/detail?indexCode=000832'
  },
  ust: {
    title: '美国10年期国债收益率', unit: '%', changeUnit: 'bp',
    dates: ['2026-09-01', '2026-09-14', '2026-09-15', '2026-09-16'],
    labels: ['09/01', '09/14', '09/15', '09/16'], values: [4.757, 4.973, 5.004, 5.012],
    note: '月内明显上行并突破5%；收益率上行代表美债价格承压，不同来源的收盘与尾盘口径可能略有差异。',
    source: 'U.S. Treasury / Reuters', sourceUrl: 'https://home.treasury.gov/resource-center/data-chart-center/interest-rates/TextView?type=daily_treasury_yield_curve'
  },
  credit: {
    title: '信用债风险温度', type: 'bars',
    items: [
      { label: '利差保护', value: 28, display: '偏低' },
      { label: '配置力量', value: 46, display: '中性' },
      { label: '弱资质波动', value: 78, display: '偏高' }
    ],
    note: '研究框架示意，非官方市场指数；用于提示低利差环境下的风险收益特征。',
    source: '证券时报 / 中债', sourceUrl: 'https://www.stcn.com/article/detail/4183651.html'
  },
  commodities: {
    title: '商品对利率的传导强度', type: 'bars',
    items: [
      { label: '能源供给冲击', value: 84, display: '高' },
      { label: '通胀预期', value: 74, display: '偏高' },
      { label: '实际利率压制', value: 66, display: '偏高' }
    ],
    note: '研究框架示意，非价格指数；油价先影响通胀预期，再影响政策路径与债券收益率。',
    source: 'U.S. EIA / Reuters', sourceUrl: 'https://www.eia.gov/petroleum/supply/weekly/'
  }
};

const els = {
  date: document.querySelector('#dateSelect'),
  dateLabel: document.querySelector('#dateControlLabel'),
  dateControl: document.querySelector('.date-control'),
  period: document.querySelector('#periodSwitch'),
  tabs: document.querySelector('#categoryTabs'),
  status: document.querySelector('#statusText'),
  title: document.querySelector('#marketTitle'),
  asOf: document.querySelector('#asOfDate'),
  grid: document.querySelector('#metricGrid'),
  commentary: document.querySelector('#commentary'),
  watch: document.querySelector('#watchPoint'),
  sources: document.querySelector('#sourceList'),
  refresh: document.querySelector('#refreshButton'),
  template: document.querySelector('#metricTemplate'),
  updated: document.querySelector('#updatedAt'),
  clock: document.querySelector('#clock'),
  shortAnswer: document.querySelector('#shortAnswer'),
  logic: document.querySelector('#logicGrid'),
  qa: document.querySelector('#qaList'),
  copy: document.querySelector('#copyAnswer'),
  openDetail: document.querySelector('#openDetail'),
  chartEntry: document.querySelector('#chartEntry'),
  chartEntryTitle: document.querySelector('#chartEntryTitle'),
  chartEntryVisual: document.querySelector('#chartEntryVisual'),
  detailDialog: document.querySelector('#detailDialog'),
  closeDetail: document.querySelector('#closeDetail'),
  detailPeriod: document.querySelector('#detailPeriod'),
  detailTitle: document.querySelector('#detailTitle'),
  detailThesis: document.querySelector('#detailThesis'),
  chartGrid: document.querySelector('#chartGrid'),
  chartAsOf: document.querySelector('#chartAsOf'),
  detailLogic: document.querySelector('#detailLogic'),
  detailSources: document.querySelector('#detailSourceList'),
  installButton: document.querySelector('#installButton'),
  installDialog: document.querySelector('#installDialog'),
  closeInstall: document.querySelector('#closeInstall')
};

let archive;
let periodArchive;
let marketHistory;
let activeCategory = 'overview';
let activePeriod = 'day';
let selectedDay = '';
const pendingSources = new Map();
let deferredInstallPrompt;
let chartCounter = 0;

const directionLabels = { up: '↑ 上行', down: '↓ 下行', flat: '— 中性' };

const dailyInterview = {
  overview: {
    short: '如果面试官问我最近的固收市场，我会概括为“国内债市偏强、海外债市承压、转债以结构性机会为主”。国内10年国债收益率在1.68%附近，弱需求和央行流动性形成支撑；美债10年期升破5%，核心是能源通胀和鹰派政策预期。信用债利差已低，继续下沉的性价比一般；转债成交回升，但更应关注正股、估值和条款。',
    logic: [
      { label: '市场走势', text: '先比较国内利率债、美债与转债方向，突出中外分化和结构性机会。' },
      { label: '核心驱动', text: '国内看基本面与流动性，海外看通胀与政策，转债再叠加权益和估值。' },
      { label: '配置判断', text: '利率债中性略多，信用重质量，转债自下而上，并保留反向风险。' }
    ],
    qa: [
      { q: '为什么国内债市和美债会背离？', a: '增长、通胀和货币政策周期不同。国内需求偏弱且流动性相对稳定，美国则受到能源通胀和继续加息预期影响。' },
      { q: '目前最值得跟踪的三个变量是什么？', a: '国内资金面和增量政策、美国核心通胀与美联储路径、原油价格及其对通胀预期的传导。' }
    ]
  },
  rates: {
    short: '我对当前国内利率债的判断是偏强但空间有限。10年国债收益率在1.68%附近，融资需求和内需偏弱、银行配置需求与央行对冲为债市提供支撑；但税期、政府债供给和政策预期限制收益率继续下行。策略上我会保留中等久期，以票息和骑乘为主，等待调整而不是在低位追涨。',
    logic: [
      { label: '基本面', text: '融资需求与内需偏弱，决定收益率大幅上行的基础不强。' },
      { label: '资金面', text: '央行持续对冲，但税期和政府债缴款仍可能造成阶段性收紧。' },
      { label: '估值面', text: '绝对收益率已低，进一步下行需要经济或政策超预期催化。' }
    ],
    qa: [
      { q: '央行净投放为什么不等于资金面一定宽松？', a: '净投放往往是在对冲税期、缴款和回表等资金缺口。若需求端抽水更强，净投放后资金价格仍可能上行。' },
      { q: '收益率低位时如何做利率债？', a: '降低单边久期暴露，更多依靠票息、骑乘和曲线交易，并在政策或供给扰动带来的调整中配置。' }
    ]
  },
  credit: {
    short: '当前信用债更适合“票息优先、谨慎下沉”。利率债偏强对高等级信用债有支撑，但信用利差已处历史低位，季末回表和资金波动会削弱配置力量。我的选择会偏向中高评级、流动性较好的品种；优质主体可以适度拉长到3至5年，弱资质主体则要重点看现金流、到期压力和再融资渠道。',
    logic: [
      { label: '收益来源', text: '当前回报更多来自持有票息，而不是期待信用利差继续压缩。' },
      { label: '主要风险', text: '低利差意味着保护不足，资金波动和负面事件更容易造成净价回撤。' },
      { label: '配置方向', text: '中高评级优先，弱主体必须做个券现金流和再融资分析。' }
    ],
    qa: [
      { q: '如何判断信用下沉是否划算？', a: '比较额外利差能否覆盖预期损失、流动性折价和估值波动，同时检查发行人自由现金流与债务到期分布。' },
      { q: '信用利差为什么会在利率债上涨时走阔？', a: '信用债还受赎回、流动性和风险偏好影响。若资金紧张或机构被动卖出，利差走阔可能抵消无风险利率下行。' }
    ]
  },
  convertible: {
    short: '当前转债市场更像结构性行情，而不是整体性机会。指数和成交额能反映情绪，但真正的收益来自正股催化、转债估值和条款三者匹配。我的筛选顺序是先看正股景气与估值，再看转股溢价率、债底、剩余期限和强赎保护；对高价、高溢价和临近强赎的品种会更谨慎。',
    logic: [
      { label: '正股', text: '决定转债方向和上涨空间，是高弹性品种最重要的收益来源。' },
      { label: '估值', text: '转股溢价率决定正股涨幅能否传导，债底决定下行保护。' },
      { label: '条款', text: '强赎、回售和下修会改变收益兑现路径，不能只看价格。' }
    ],
    qa: [
      { q: '低价转债为什么不一定安全？', a: '低价可能来自正股基本面差、信用风险或到期压力，需要同时看债底、偿债能力、回售和下修可能性。' },
      { q: '正股上涨，转债为什么可能不跟？', a: '若转股溢价率过高、剩余期限短或市场担忧强赎，正股上涨可能先被估值压缩吸收，转债Beta就会偏低。' }
    ]
  },
  ust: {
    short: '我对当前美债偏谨慎。美联储加息后，2年期与10年期收益率均处高位，说明市场在重估更高更久的政策路径。短端主要看美联储和通胀，长端还叠加财政供给与期限溢价。5%左右的10年期收益率提高了配置价值，但在能源通胀没有明显缓和前，更适合分批进入，而不是直接押注收益率见顶。',
    logic: [
      { label: '短端', text: '对政策利率和核心通胀最敏感，反映后续加息或降息预期。' },
      { label: '长端', text: '除政策外还反映财政供给、长期通胀和期限溢价。' },
      { label: '策略', text: '绝对收益率有吸引力，但需要通胀和油价配合才能确认顶部。' }
    ],
    qa: [
      { q: '为什么美联储加息后长端仍可能上行？', a: '如果通胀、财政赤字和供给风险持续，期限溢价会抬升，短期紧缩不足以压住长端。' },
      { q: '美债收益率见顶需要哪些信号？', a: '核心通胀连续回落、就业明显降温、油价下跌以及国债拍卖需求改善，至少需要其中几项共同出现。' }
    ]
  },
  commodities: {
    short: '商品对固收最重要的是通胀传导。原油主要受供给和地缘风险驱动，高油价会抬升通胀预期并推迟货币宽松；黄金则同时受到避险需求支撑和实际利率、美元上升压制。因此我不会简单判断黄金与原油同涨同跌，而会分别用“供给—需求”和“实际利率—美元—避险”框架分析。',
    logic: [
      { label: '原油', text: '供给冲击是短期主线，并通过通胀影响全球债券收益率。' },
      { label: '黄金', text: '避险和通胀利多，实际利率与美元利空，取决于相对强弱。' },
      { label: '债市传导', text: '商品先改变通胀预期，再改变货币政策路径和名义收益率。' }
    ],
    qa: [
      { q: '为什么油价上涨但黄金可能下跌？', a: '油价推高通胀后可能促使央行更鹰派，实际利率和美元上升会压制黄金，抵消其通胀与避险属性。' },
      { q: '商品如何影响中国债市？', a: '输入性通胀会抬升PPI并限制宽松空间，但高成本也可能压制需求，最终要结合增长与政策反应判断。' }
    ]
  }
};

function formatDate(date) {
  return new Intl.DateTimeFormat('zh-CN', { year: 'numeric', month: '2-digit', day: '2-digit', weekday: 'short' })
    .format(new Date(`${date}T12:00:00+08:00`));
}

function formatGeneratedAt(value) {
  if (!value) return '时间待确认';
  return new Intl.DateTimeFormat('zh-CN', {
    timeZone: 'Asia/Shanghai', month: '2-digit', day: '2-digit',
    hour: '2-digit', minute: '2-digit', hour12: false
  }).format(new Date(value));
}

function historyNumber(record, path) {
  let value = record;
  path.forEach(key => { value = value?.[key]; });
  if (value === null || value === undefined || value === '') return null;
  return Number.isFinite(Number(value)) ? Number(value) : null;
}

function chartSeries(path) {
  return marketHistory.days
    .map(day => ({ date: day.date, value: historyNumber(day, path) }))
    .filter(point => Number.isFinite(point.value))
    .sort((a, b) => a.date.localeCompare(b.date))
    .slice(-31);
}

function hydrateCharts() {
  const configs = {
    rates: ['rates', 'cn10'],
    credit: ['credit', 'mtn3_spread'],
    convertible: ['convertible', 'close'],
    ust: ['ust', '10y'],
    commodities: ['commodities', 'gold', 'price']
  };
  Object.entries(configs).forEach(([key, path]) => {
    const points = chartSeries(path);
    if (!points.length) return;
    Object.assign(chartCatalog[key], {
      type: 'line',
      dates: points.map(point => point.date),
      labels: points.map(point => point.date.slice(5).replace('-', '/')),
      values: points.map(point => point.value)
    });
    delete chartCatalog[key].items;
  });
  Object.assign(chartCatalog.credit, {
    title: 'AAA中票3年信用利差', unit: ' BP', changeUnit: 'absolute',
    note: '中债AAA中票收益率减同期限国债收益率，用于观察高等级信用债相对估值。',
    source: '中国债券信息网', sourceUrl: 'https://yield.chinabond.com.cn/'
  });
  Object.assign(chartCatalog.commodities, {
    title: 'COMEX黄金连续合约', unit: '美元', changeUnit: 'pct',
    note: '自动任务抓取时点报价，不等同于交易所官方结算价。',
    source: 'CME / 东方财富行情', sourceUrl: 'https://www.cmegroup.com/markets/metals/precious/gold.html'
  });
}

function uniqueSources(markets) {
  const seen = new Set();
  return Object.values(markets).flatMap(market => market.sources ?? []).filter(source => {
    if (seen.has(source.url)) return false;
    seen.add(source.url);
    return true;
  }).slice(0, 5);
}

function mergeSources(sources = [], category = activeCategory) {
  const seen = new Set();
  return [...sources, ...(authoritativeSources[category] ?? [])].filter(source => {
    if (!source?.url || seen.has(source.url)) return false;
    seen.add(source.url);
    return true;
  }).slice(0, 7);
}

function sourceKind(source) {
  const publisher = source.publisher ?? '';
  if (/官方|中国债券信息网|中国人民银行|中证指数|中国货币网|Treasury|Federal Reserve|EIA|交易所/.test(publisher)) return '官方';
  if (/新华|Reuters|证券时报|Wall Street Journal|WSJ|Barron/.test(publisher)) return '权威媒体';
  return '市场数据';
}

function dailyOverview(day) {
  const markets = day.markets;
  const isLatest = day.date === archive.days[0]?.date;
  return {
    title: '固收市场总览',
    commentary: isLatest
      ? '国内利率债与转债偏强，美债在鹰派加息后承压，商品维持高波动；中外增长与通胀周期差异是当前最重要的市场主线。'
      : '国内利率债偏强整理，转债与海外利率资产分化；市场交易仍围绕资金、政策和海外通胀三条主线展开。',
    watch: '国内资金与政策增量、美国通胀和美联储路径、油价对全球利率的传导。',
    metrics: [
      markets.rates.metrics[0],
      markets.convertible.metrics[0],
      markets.ust.metrics.find(metric => metric.label.includes('10年')) ?? markets.ust.metrics[0],
      markets.commodities.metrics[0]
    ],
    sources: uniqueSources(markets),
    interview: dailyInterview.overview
  };
}

function renderTabs() {
  els.tabs.replaceChildren(...categories.map(category => {
    const button = document.createElement('button');
    button.type = 'button';
    button.className = 'tab-button';
    button.role = 'tab';
    button.textContent = category.label;
    button.dataset.category = category.id;
    button.setAttribute('aria-selected', String(category.id === activeCategory));
    button.addEventListener('click', () => {
      activeCategory = category.id;
      renderTabs();
      renderMarket();
    });
    return button;
  }));
}

function renderMetric(metric) {
  const card = els.template.content.firstElementChild.cloneNode(true);
  card.querySelector('.metric-label').textContent = metric.label;
  const direction = card.querySelector('.metric-direction');
  direction.textContent = directionLabels[metric.direction] ?? directionLabels.flat;
  direction.classList.add(`direction-${metric.direction ?? 'flat'}`);
  card.querySelector('.metric-value').textContent = metric.value;
  card.querySelector('.metric-change').textContent = metric.change;
  card.querySelector('.metric-note').textContent = metric.note;
  const link = card.querySelector('.metric-source');
  link.href = metric.sourceUrl;
  link.setAttribute('aria-label', `查看${metric.label}的${metric.source}原始来源`);
  link.textContent = `${metric.source} ↗`;
  return card;
}

function renderSources(sources) {
  if (!sources?.length) {
    els.sources.innerHTML = '<span class="source-empty">当前没有可用来源。</span>';
    return;
  }
  els.sources.replaceChildren(...sources.map(source => {
    const link = document.createElement('a');
    link.className = 'source-link';
    link.href = source.url;
    link.target = '_blank';
    link.rel = 'noopener noreferrer';
    const title = document.createElement('span');
    title.textContent = source.title;
    const meta = document.createElement('span');
    meta.className = 'source-meta';
    const badge = document.createElement('b');
    badge.className = 'source-badge';
    badge.textContent = sourceKind(source);
    const publisher = document.createElement('span');
    publisher.textContent = `${source.publisher} ↗`;
    meta.append(badge, publisher);
    link.append(title, meta);
    return link;
  }));
}

function visibleSeries(chart) {
  const zipped = chart.values.map((value, index) => ({
    value, date: chart.dates[index], label: chart.labels[index]
  }));
  if (activePeriod === 'week') {
    const asOf = periodArchive.week.asOf;
    const start = new Date(`${asOf}T00:00:00Z`);
    start.setUTCDate(start.getUTCDate() - ((start.getUTCDay() + 6) % 7));
    const startDate = start.toISOString().slice(0, 10);
    const filtered = zipped.filter(point => point.date >= startDate && point.date <= asOf);
    return filtered.length ? filtered : zipped.slice(-1);
  }
  if (activePeriod === 'month') {
    const asOf = periodArchive.month.asOf;
    const startDate = `${asOf.slice(0, 7)}-01`;
    const filtered = zipped.filter(point => point.date >= startDate && point.date <= asOf);
    return filtered.length ? filtered : zipped.slice(-1);
  }
  if (activePeriod === 'day') {
    const cutoff = currentView().date;
    const filtered = zipped.filter(point => point.date <= cutoff).slice(-8);
    return filtered.length ? filtered : zipped.slice(0, 1);
  }
  return zipped;
}

function chartChange(chart, points) {
  if (points.length < 2) return `最新 ${points[0]?.value ?? '—'}${chart.unit}`;
  const first = points[0].value;
  const last = points.at(-1).value;
  if (chart.changeUnit === 'bp') {
    const value = (last - first) * 100;
    return `${value >= 0 ? '+' : '−'}${Math.abs(value).toFixed(2)} BP`;
  }
  if (chart.changeUnit === 'pct') {
    const value = (last / first - 1) * 100;
    return `${value >= 0 ? '+' : '−'}${Math.abs(value).toFixed(2)}%`;
  }
  if (chart.changeUnit === 'absolute') {
    const value = last - first;
    return `${value >= 0 ? '+' : '−'}${Math.abs(value).toFixed(2)}${chart.unit}`;
  }
  return `${last}${chart.unit}`;
}

function svgElement(name, attributes = {}) {
  const element = document.createElementNS('http://www.w3.org/2000/svg', name);
  Object.entries(attributes).forEach(([key, value]) => element.setAttribute(key, value));
  return element;
}

function buildLineChart(chart, compact = false) {
  const points = visibleSeries(chart);
  const width = compact ? 520 : 620;
  const height = compact ? 84 : 235;
  const left = compact ? 5 : 48;
  const right = compact ? 5 : 20;
  const top = compact ? 7 : 32;
  const bottom = compact ? 7 : 42;
  const values = points.map(point => point.value);
  const rawMin = Math.min(...values);
  const rawMax = Math.max(...values);
  const padding = Math.max((rawMax - rawMin) * 0.22, Math.abs(rawMax || 1) * 0.0008);
  const min = rawMin - padding;
  const max = rawMax + padding;
  const x = index => left + (points.length === 1 ? 0 : index * (width - left - right) / (points.length - 1));
  const y = value => top + (max - value) * (height - top - bottom) / (max - min || 1);
  const path = points.map((point, index) => `${index ? 'L' : 'M'} ${x(index)} ${y(point.value)}`).join(' ');
  const area = `${path} L ${x(points.length - 1)} ${height - bottom} L ${x(0)} ${height - bottom} Z`;
  const svg = svgElement('svg', { viewBox: `0 0 ${width} ${height}`, role: compact ? 'presentation' : 'img', class: compact ? '' : 'line-chart' });

  const gradientId = `chartArea-${++chartCounter}`;
  const defs = svgElement('defs');
  const gradient = svgElement('linearGradient', { id: gradientId, x1: '0', x2: '0', y1: '0', y2: '1' });
  gradient.append(
    svgElement('stop', { offset: '0%', 'stop-color': '#2563a6', 'stop-opacity': '.24' }),
    svgElement('stop', { offset: '100%', 'stop-color': '#2563a6', 'stop-opacity': '0' })
  );
  defs.append(gradient);
  svg.append(defs);

  if (!compact) {
    [top, (top + height - bottom) / 2, height - bottom].forEach(lineY => {
      svg.append(svgElement('line', { x1: left, x2: width - right, y1: lineY, y2: lineY, class: 'chart-axis' }));
    });
  }
  svg.append(svgElement('path', { d: area, fill: `url(#${gradientId})`, class: 'chart-area' }));
  svg.append(svgElement('path', { d: path, class: 'chart-line' }));

  points.forEach((point, index) => {
    svg.append(svgElement('circle', { cx: x(index), cy: y(point.value), r: compact ? 3.6 : 4.8, class: 'chart-dot' }));
    if (!compact) {
      const dateLabel = svgElement('text', { x: x(index), y: height - 14, 'text-anchor': 'middle', class: 'chart-label' });
      dateLabel.textContent = point.label;
      svg.append(dateLabel);
      if (index === 0 || index === points.length - 1) {
        const valueLabel = svgElement('text', {
          x: x(index), y: Math.max(16, y(point.value) - 13),
          'text-anchor': index === 0 ? 'start' : 'end', class: 'chart-value'
        });
        valueLabel.textContent = `${point.value}${chart.unit}`;
        svg.append(valueLabel);
      }
    }
  });
  return svg;
}

function buildBars(chart, compact = false) {
  const wrap = document.createElement('div');
  wrap.className = 'risk-bars';
  chart.items.forEach(item => {
    const row = document.createElement('div');
    row.className = 'risk-row';
    if (compact) row.classList.add('is-compact');
    const label = document.createElement('span');
    label.textContent = compact ? '' : item.label;
    const track = document.createElement('div');
    track.className = 'risk-track';
    const fill = document.createElement('div');
    fill.className = 'risk-fill';
    fill.style.width = `${item.value}%`;
    track.append(fill);
    const value = document.createElement('strong');
    value.textContent = compact ? '' : item.display;
    row.append(label, track, value);
    wrap.append(row);
  });
  return wrap;
}

function buildChartCard(chart, wide = false) {
  const card = document.createElement('article');
  card.className = `chart-card${wide ? ' is-wide' : ''}`;
  const head = document.createElement('div');
  head.className = 'chart-card-head';
  const title = document.createElement('strong');
  title.textContent = chart.title;
  const change = document.createElement('span');
  change.textContent = chart.type === 'bars' ? '分析框架' : chartChange(chart, visibleSeries(chart));
  head.append(title, change);
  const visual = chart.type === 'bars' ? buildBars(chart) : buildLineChart(chart);
  const note = document.createElement('p');
  note.className = 'chart-note';
  note.append(document.createTextNode(`${chart.note} `));
  const source = document.createElement('a');
  source.href = chart.sourceUrl;
  source.target = '_blank';
  source.rel = 'noopener noreferrer';
  source.textContent = `来源：${chart.source} ↗`;
  note.append(source);
  card.append(head, visual, note);
  return card;
}

function chartsForCategory(category) {
  return category === 'overview'
    ? [chartCatalog.rates, chartCatalog.convertible, chartCatalog.ust]
    : [chartCatalog[category]];
}

function renderChartEntry() {
  const chart = activeCategory === 'overview' ? chartCatalog.rates : chartCatalog[activeCategory];
  els.chartEntryTitle.textContent = activeCategory === 'overview' ? '中外利率与转债，三张图看主线' : chart.title;
  els.chartEntryVisual.replaceChildren(chart.type === 'bars' ? buildBars(chart, true) : buildLineChart(chart, true));
}

function buildSourceLinks(sources) {
  return sources.map(source => {
    const link = document.createElement('a');
    link.className = 'source-link';
    link.href = source.url;
    link.target = '_blank';
    link.rel = 'noopener noreferrer';
    const title = document.createElement('span');
    title.textContent = source.title;
    const meta = document.createElement('span');
    meta.className = 'source-meta';
    const badge = document.createElement('b');
    badge.className = 'source-badge';
    badge.textContent = sourceKind(source);
    const publisher = document.createElement('span');
    publisher.textContent = `${source.publisher} ↗`;
    meta.append(badge, publisher);
    link.append(title, meta);
    return link;
  });
}

function openDetail() {
  const view = currentView();
  const market = view.markets[activeCategory];
  const interview = market.interview ?? dailyInterview[activeCategory] ?? dailyInterview.overview;
  els.detailPeriod.textContent = `${periodLabels[activePeriod]} · ${activePeriod === 'day' ? formatDate(view.date) : view.range}`;
  els.detailTitle.textContent = market.title;
  els.detailThesis.textContent = market.commentary;
  els.chartAsOf.textContent = `所选口径：${periodLabels[activePeriod]} · 数据截至 ${activePeriod === 'day' ? view.date : view.asOf}`;
  const charts = chartsForCategory(activeCategory);
  els.chartGrid.replaceChildren(...charts.map(chart => buildChartCard(chart, charts.length === 1)));
  els.detailLogic.replaceChildren(...interview.logic.map(item => {
    const card = document.createElement('article');
    const label = document.createElement('span');
    label.textContent = item.label;
    const text = document.createElement('p');
    text.textContent = item.text;
    card.append(label, text);
    return card;
  }));
  els.detailSources.replaceChildren(...buildSourceLinks(mergeSources(market.sources, activeCategory)));
  els.detailDialog.showModal();
}

function renderInterview(interview) {
  const content = interview ?? dailyInterview[activeCategory] ?? dailyInterview.overview;
  els.shortAnswer.textContent = content.short;
  els.logic.replaceChildren(...content.logic.map(item => {
    const card = document.createElement('article');
    card.className = 'logic-card';
    const label = document.createElement('span');
    label.textContent = item.label;
    const text = document.createElement('p');
    text.textContent = item.text;
    card.append(label, text);
    return card;
  }));
  els.qa.replaceChildren(...content.qa.map((item, index) => {
    const detail = document.createElement('details');
    detail.className = 'qa-item';
    if (index === 0) detail.open = true;
    const summary = document.createElement('summary');
    summary.textContent = item.q;
    const answer = document.createElement('p');
    answer.textContent = item.a;
    detail.append(summary, answer);
    return detail;
  }));
}

function pendingDay(date) {
  const markets = Object.fromEntries(categories.map(category => {
    const sources = pendingSources.get(`${date}:${category.id}`) ?? [];
    return [category.id, {
      title: category.label === '总览' ? '固收市场总览' : category.label,
      commentary: '该交易日尚未进入核验归档。页面可以聚合公开来源，但核验前不会生成精确行情结论。',
      watch: '先检查来源日期与行情时点，再补充收盘值、驱动和风险判断。',
      metrics: [
        { label: '归档状态', value: '待核验', change: '未生成数值', direction: 'flat', note: '避免把未交叉确认的网页片段写成收盘行情', source: '查看候选来源', sourceUrl: sources[0]?.url ?? 'https://www.cnfin.com/' },
        { label: '自动来源', value: sources.length ? `${sources.length} 条` : '待采集', change: '公开网页候选', direction: 'flat', note: '点击“刷新来源”启动当日网页聚合', source: '来源列表', sourceUrl: sources[0]?.url ?? 'https://www.cnfin.com/' }
      ],
      sources,
      interview: dailyInterview[category.id]
    }];
  }));
  return { date, verified: false, markets };
}

function currentDay() {
  const rawDay = archive.days.find(item => item.date === els.date.value) ?? pendingDay(els.date.value);
  if (!rawDay.markets.overview && rawDay.verified) {
    rawDay.markets.overview = dailyOverview(rawDay);
  }
  return rawDay;
}

function currentView() {
  return activePeriod === 'day' ? currentDay() : periodArchive[activePeriod];
}

function renderMarket() {
  const view = currentView();
  const market = view.markets[activeCategory];
  els.status.textContent = view.verified
    ? `${periodLabels[activePeriod]} · 已核验`
    : '自动来源 · 待核验';
  els.title.textContent = market.title;
  els.asOf.textContent = activePeriod === 'day'
    ? formatDate(view.date)
    : `${view.range} · 截至${view.asOf.slice(5).replace('-', '月')}日`;
  els.grid.replaceChildren(...market.metrics.map(renderMetric));
  els.commentary.textContent = market.commentary;
  els.watch.textContent = market.watch;
  renderInterview(market.interview ?? dailyInterview[activeCategory]);
  renderSources(mergeSources(market.sources, activeCategory));
  renderChartEntry();
}

function setPeriod(period) {
  if (activePeriod === 'day') selectedDay = els.date.value;
  activePeriod = period;
  els.period.querySelectorAll('.period-button').forEach(button => {
    button.setAttribute('aria-selected', String(button.dataset.period === activePeriod));
  });
  const isDay = activePeriod === 'day';
  els.dateLabel.textContent = isDay ? '交易日' : '统计截止日';
  els.dateControl.classList.toggle('is-locked', !isDay);
  els.date.readOnly = !isDay;
  els.date.value = isDay ? selectedDay : periodArchive[activePeriod].asOf;
  els.refresh.hidden = !isDay;
  renderMarket();
}

function getDateWindow(date) {
  const start = date.replaceAll('-', '') + '000000';
  const next = new Date(`${date}T00:00:00Z`);
  next.setUTCDate(next.getUTCDate() + 1);
  const end = next.toISOString().slice(0, 10).replaceAll('-', '') + '000000';
  return { start, end };
}

async function collectCandidates() {
  if (activePeriod !== 'day') return;
  const day = currentDay();
  const queries = {
    overview: '中国 债市 美债 可转债 黄金 原油',
    rates: '中国 国债 收益率 国债期货',
    credit: '中国 信用债 信用利差',
    convertible: '中证转债指数 可转债 收盘',
    ust: 'US Treasury yield Federal Reserve',
    commodities: 'gold oil commodities market'
  };
  const { start, end } = getDateWindow(day.date);
  const endpoint = new URL('https://api.gdeltproject.org/api/v2/doc/doc');
  endpoint.search = new URLSearchParams({
    query: queries[activeCategory], mode: 'ArtList', maxrecords: '8', format: 'json',
    startdatetime: start, enddatetime: end, sort: 'HybridRel'
  });

  els.refresh.disabled = true;
  els.refresh.innerHTML = '<span aria-hidden="true">↻</span> 正在采集';
  try {
    const response = await fetch(endpoint, { signal: AbortSignal.timeout(10000) });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const payload = await response.json();
    const candidates = (payload.articles ?? []).slice(0, 6).map(article => ({
      title: article.title, publisher: article.domain, url: article.url
    }));
    if (candidates.length) {
      pendingSources.set(`${day.date}:${activeCategory}`, candidates);
      if (!day.verified) renderMarket();
    }
    renderSources(mergeSources(candidates.length ? candidates : day.markets[activeCategory].sources, activeCategory));
    els.status.textContent = candidates.length
      ? `新增 ${candidates.length} 条自动来源 · 待核验`
      : '未发现新增来源 · 保留已核验归档';
  } catch (error) {
    renderSources(mergeSources(day.markets[activeCategory].sources, activeCategory));
    els.status.textContent = '自动采集暂不可用 · 已保留核验归档';
  } finally {
    els.refresh.disabled = false;
    els.refresh.innerHTML = '<span aria-hidden="true">↻</span> 刷新来源';
  }
}

async function copyAnswer() {
  const text = els.shortAnswer.textContent;
  try {
    await navigator.clipboard.writeText(text);
    els.copy.textContent = '已复制';
  } catch (error) {
    els.copy.textContent = '请手动复制';
  }
  window.setTimeout(() => { els.copy.textContent = '复制60秒回答'; }, 1500);
}

async function installApp() {
  if (deferredInstallPrompt) {
    deferredInstallPrompt.prompt();
    await deferredInstallPrompt.userChoice;
    deferredInstallPrompt = undefined;
    return;
  }
  els.installDialog.showModal();
}

function closeOnBackdrop(dialog, event) {
  if (event.target === dialog) dialog.close();
}

function initClock() {
  const update = () => {
    const time = new Intl.DateTimeFormat('zh-CN', { timeZone: 'Asia/Shanghai', hour: '2-digit', minute: '2-digit', hour12: false }).format(new Date());
    els.clock.textContent = `${time} · UTC+8`;
  };
  update();
  window.setInterval(update, 60000);
}

async function init() {
  const [dailyResponse, periodResponse, historyResponse] = await Promise.all([
    fetch('./data/daily.json', { cache: 'no-store' }),
    fetch('./data/periods.json', { cache: 'no-store' }),
    fetch('./data/market-history.json', { cache: 'no-store' })
  ]);
  if (!dailyResponse.ok || !periodResponse.ok || !historyResponse.ok) throw new Error('市场数据加载失败');
  archive = await dailyResponse.json();
  periodArchive = await periodResponse.json();
  marketHistory = await historyResponse.json();
  archive.days.sort((a, b) => b.date.localeCompare(a.date));
  hydrateCharts();
  selectedDay = archive.days[0].date;
  els.date.value = selectedDay;
  els.date.max = selectedDay;
  els.updated.textContent = `自动更新：${formatGeneratedAt(archive.generatedAt)} · 最新交易日 ${selectedDay}`;
  renderTabs();
  renderMarket();
  initClock();

  els.period.addEventListener('click', event => {
    const button = event.target.closest('.period-button');
    if (button) setPeriod(button.dataset.period);
  });
  els.date.addEventListener('change', () => {
    selectedDay = els.date.value;
    renderMarket();
    const weekday = new Date(`${els.date.value}T12:00:00+08:00`).getDay();
    if (weekday === 0 || weekday === 6) els.status.textContent = '非交易日 · 请选择工作日';
  });
  els.refresh.addEventListener('click', collectCandidates);
  els.copy.addEventListener('click', copyAnswer);
  els.openDetail.addEventListener('click', openDetail);
  els.chartEntry.addEventListener('click', openDetail);
  els.closeDetail.addEventListener('click', () => els.detailDialog.close());
  els.detailDialog.addEventListener('click', event => closeOnBackdrop(els.detailDialog, event));
  els.installButton.addEventListener('click', installApp);
  els.closeInstall.addEventListener('click', () => els.installDialog.close());
  els.installDialog.addEventListener('click', event => closeOnBackdrop(els.installDialog, event));

  window.addEventListener('beforeinstallprompt', event => {
    event.preventDefault();
    deferredInstallPrompt = event;
    els.installButton.textContent = '安装到手机';
  });
  window.addEventListener('appinstalled', () => {
    deferredInstallPrompt = undefined;
    els.installButton.textContent = '已安装';
    els.installButton.disabled = true;
  });

  if ('serviceWorker' in navigator) {
    navigator.serviceWorker.register('./sw.js').catch(() => {});
  }
}

init().catch(error => {
  els.status.textContent = error.message;
  els.commentary.textContent = '请稍后刷新页面。';
});
