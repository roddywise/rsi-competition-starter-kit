const fs = require("fs");
const path = require("path");
const pptxgen = require("pptxgenjs");
const html2pptx = require(
  "C:/Users/26812/.config/opencode/skills/document-skills/pptx/scripts/html2pptx.js"
);

const ROOT = __dirname;
const HTML_DIR = path.join(ROOT, "html-source");
const OUTPUT = path.join(ROOT, "智训引擎答辩.pptx");
const C = {
  navy: "#173247",
  teal: "#177E89",
  orange: "#D97A34",
  ink: "#233541",
  muted: "#60727E",
  paper: "#F4F7F8",
  pale: "#E6EFF2",
  white: "#FFFFFF",
  red: "#B14C3B",
  green: "#34745E",
};

const baseCss = `
* { box-sizing: border-box; }
html, body { width: 720pt; height: 405pt; margin: 0; padding: 0; }
body {
  display: flex; flex-direction: column; overflow: hidden;
  background: ${C.paper}; color: ${C.ink}; font-family: Arial, sans-serif;
}
.page { width: 720pt; height: 405pt; padding: 24pt 32pt 20pt; display: flex; flex-direction: column; }
.top { height: 18pt; display: flex; justify-content: space-between; align-items: center; margin-bottom: 12pt; }
.brand { color: ${C.teal}; font-size: 9pt; font-weight: bold; margin: 0; }
.page-no { color: ${C.muted}; font-size: 8pt; margin: 0; }
.title { color: ${C.navy}; font-size: 25pt; line-height: 1.1; margin: 0 0 5pt; }
.subtitle { color: ${C.muted}; font-size: 11pt; line-height: 1.2; margin: 0; }
.content { flex: 1; display: flex; flex-direction: column; gap: 9pt; min-height: 0; }
.footer { height: 13pt; margin-top: 7pt; border-top: 1px solid ${C.pale}; padding-top: 4pt; }
.footer p { color: ${C.muted}; font-size: 7pt; margin: 0; }
.row { display: flex; gap: 10pt; }
.card {
  background: ${C.white}; border-left: 4pt solid ${C.teal};
  border-radius: 6pt; padding: 10pt 12pt; display: flex; flex-direction: column; gap: 4pt;
}
.card h3 { color: ${C.navy}; font-size: 13pt; line-height: 1.15; margin: 0; }
.card p { color: ${C.ink}; font-size: 9pt; line-height: 1.25; margin: 0; }
.card .big { color: ${C.teal}; font-size: 22pt; line-height: 1; font-weight: bold; margin: 2pt 0; }
.accent { border-left-color: ${C.orange}; }
.tag { color: ${C.orange}; font-weight: bold; font-size: 8pt; margin: 0; }
.small { color: ${C.muted}; font-size: 8pt; line-height: 1.2; margin: 0; }
.pill { background: ${C.pale}; border-radius: 4pt; padding: 5pt 7pt; }
.flow { display: flex; align-items: stretch; gap: 7pt; }
.flow-card { flex: 1; background: ${C.white}; border-top: 4pt solid ${C.teal}; padding: 9pt; display: flex; flex-direction: column; gap: 5pt; }
.flow-card h3 { margin: 0; font-size: 11pt; color: ${C.navy}; }
.flow-card p { margin: 0; font-size: 8.5pt; line-height: 1.2; }
.arrow { width: 18pt; align-self: center; color: ${C.orange}; font-size: 16pt; font-weight: bold; }
.listbox { background: ${C.white}; padding: 10pt 13pt; border-radius: 6pt; }
ul { margin: 0; padding-left: 17pt; }
li { margin: 0 0 4pt; color: ${C.ink}; font-size: 9pt; line-height: 1.25; }
.matrix { display:flex; flex-direction:column; width:100%; background:${C.white}; border:1px solid #C9D5DB; }
.mrow { display:flex; }
.mcell { flex:1; padding:6pt 7pt; border-right:0.6pt solid #C9D5DB; border-bottom:0.6pt solid #C9D5DB; display:flex; align-items:center; }
.mcell p { color:${C.ink}; font-size:8pt; line-height:1.15; margin:0; }
.mhead { background:${C.navy}; }
.mhead .mcell p { color:${C.white}; font-weight:bold; text-align:center; }
.status { background: #FFF4E7; border-left: 5pt solid ${C.orange}; padding: 9pt 11pt; }
.status p { margin: 0; color: ${C.ink}; font-size: 9pt; line-height: 1.25; }
`;

function page(title, subtitle, pageNo, body, extraCss = "") {
  return `<!DOCTYPE html><html><head><meta charset="utf-8"><style>${baseCss}${extraCss}</style></head><body>
    <div class="page">
      <div class="top"><p class="brand">RSI · 智训引擎</p><p class="page-no">${pageNo} / 10</p></div>
      <div><h1 class="title">${title}</h1><p class="subtitle">${subtitle}</p></div>
      <div class="content">${body}</div>
      <div class="footer"><p>公开数据本地开发参考 · 非平台正式评分</p></div>
    </div></body></html>`;
}

function writeSlide(name, html) {
  const file = path.join(HTML_DIR, name);
  fs.writeFileSync(file, html, "utf8");
  return file;
}

async function main() {
  fs.mkdirSync(HTML_DIR, { recursive: true });
  const slides = [];
  slides.push({
    html: writeSlide(
      "slide-01-cover.html",
      `<!DOCTYPE html><html><head><meta charset="utf-8"><style>${baseCss}
      body { background: ${C.navy}; color: ${C.white}; }
      .page { padding: 30pt 36pt; justify-content: space-between; }
      .brand, .page-no { color: #A9D4D8; }
      .cover { display:flex; flex-direction:column; justify-content:center; flex:1; gap:13pt; border-left:7pt solid ${C.orange}; padding-left:24pt; }
      .cover h1 { color:${C.white}; font-size:38pt; line-height:1.05; margin:0; }
      .cover h2 { color:#B9DCE0; font-size:19pt; line-height:1.2; margin:0; }
      .cover p { color:#EAF2F5; font-size:11pt; line-height:1.3; margin:0; }
      .cover .tag { color:#FFC27E; font-size:10pt; }
      .footer { border-top-color:#355469; } .footer p { color:#A9D4D8; }
      </style></head><body><div class="page">
      <div class="top"><p class="brand">RSI · 工业模型自进化</p><p class="page-no">01 / 10</p></div>
      <div class="cover">
        <p class="tag">工业制造场景 · 受控自进化系统</p>
        <h1>智训引擎</h1>
        <h2>工业模型训练与受控超参数优化</h2>
        <p>统一接入 A 气体识别、B 轴承剩余寿命、C 发动机剩余寿命。</p>
        <p><b>开发验证稿 · 2026-11-22</b></p>
        <p>镜像已构建并通过容器测试；平台提交与试运行待完成。</p>
      </div>
      <div class="footer"><p>实验分数仅为本地开发参考，不是平台正式成绩</p></div>
      </div></body></html>`
    ),
  });
  slides.push({
    html: writeSlide(
      "slide-02-tasks.html",
      page(
        "三项工业任务，一套进化闭环",
        "工业模型从官方 CPU checkpoint 续训；评分对象是续训后的工业模型。",
        "02",
        `<div class="row" style="flex:1;">
          <div class="card" style="flex:1;">
            <p class="tag">A · 分类</p><h3>气体识别</h3><p class="big">6 类</p>
            <p>128 维传感器输入</p><p><b>Macro-F1 ↑</b></p><p class="small">验证批次与训练批次隔离，重点应对传感器漂移。</p>
          </div>
          <div class="card accent" style="flex:1;">
            <p class="tag">B · 回归</p><h3>轴承剩余寿命</h3><p class="big">分钟</p>
            <p>34 维双通道振动特征</p><p><b>RMSE / MAE ↓</b></p><p class="small">不使用健康等级伪标签；按整根轴承划分。</p>
          </div>
          <div class="card" style="flex:1;">
            <p class="tag">C · 回归</p><h3>发动机剩余寿命</h3><p class="big">循环</p>
            <p>24 维设置与传感器输入</p><p><b>RMSE ↓</b></p><p class="small">平台另报告 NASA 非对称分，寿命高估惩罚更大。</p>
          </div>
        </div>
        <div class="status"><p>每任务 10 轮优化与全队试运行额度是两件事；平台评测尚未由本队启动。</p></div>`
      ),
    ),
  });
  slides.push({
    html: writeSlide(
      "slide-03-architecture.html",
      page(
        "从父 checkpoint 到可审计候选",
        "单一镜像以 SDK 1.0.4 的 workspace.v2 协议支持分类与回归。",
        "03",
        `<div class="flow" style="flex:1;align-items:center;">
          <div class="flow-card"><h3>01 公开输入</h3><p>/data/train.jsonl</p><p>/data/validation.jsonl</p><p class="small">只读；隐藏标签不可见</p></div>
          <p class="arrow">→</p>
          <div class="flow-card"><h3>02 历史与提示</h3><p>rnd.history()</p><p>rnd.model()</p><p class="small">只传历史指标、白名单参数与漂移摘要</p></div>
          <p class="arrow">→</p>
          <div class="flow-card"><h3>03 CPU 续训</h3><p>rnd.parent.path()</p><p>NumPy MLP + Adam</p><p class="small">每轮输出新 checkpoint</p></div>
        </div>
        <div class="flow">
          <div class="flow-card"><h3>04 候选与证据</h3><p>checkpoint.npz</p><p>training/history + drift_report</p></div>
          <p class="arrow">→</p>
          <div class="flow-card"><h3>05 平台测量</h3><p>平台公开验证摘要</p><p>官方指标为唯一决策依据</p></div>
          <p class="arrow">→</p>
          <div class="flow-card"><h3>06 接受或回滚</h3><p>严格改善才接受</p><p>否则保留父模型</p></div>
        </div>`
      ),
    ),
  });
  slides.push({
    html: writeSlide(
      "slide-04-control.html",
      page(
        "受控进化：让模型提议，不让它越权",
        "首版把模型动作限制为可验证的超参数选择。",
        "04",
        `<div class="row">
          <div class="card" style="flex:1;"><p class="tag">输入</p><h3>最小上下文</h3><p>任务合同、最多 10 条历史主指标、白名单配置。</p><p class="small">不发送原始样本、答案、ID、meta 或历史自由文本。</p></div>
          <div class="card accent" style="flex:1;"><p class="tag">动作</p><h3>严格 JSON</h3><p>epochs / learning_rate / batch_size。</p><p class="small">不接受代码、Shell、路径或额外字段；无效响应固定回退。</p></div>
          <div class="card" style="flex:1;"><p class="tag">验证</p><h3>平台指标</h3><p>A Macro-F1 越高越好；B/C RMSE 越低越好。</p><p class="small">候选摘要无效或未严格改善时回滚。</p></div>
        </div>
        <div class="row">
          <div class="listbox" style="flex:1;">
            <h3 style="font-size:12pt;color:${C.navy};margin:0 0 5pt;">安全边界</h3>
            <ul><li>父 checkpoint SHA-256 必须由 SDK 校验。</li><li>候选写到独立 /workspace，产物上限保守按 64 MiB。</li><li>API Key 只进平台密钥栏，不进镜像或源码。</li><li>RPC 状态不明时停轮，不自动重试。</li></ul>
          </div>
        </div>`
      ),
    ),
  });
  slides.push({
    html: writeSlide(
      "slide-05-results.html",
      page(
        "平台试运行：A 明显改善，B/C 接近本地",
        "提交版本 v1 · Qwen/Qwen3.8-27B · 每任务 10/10 轮 · 试运行不计分",
        "05",
        `<div class="matrix">
           <div class="mrow mhead">
             <div class="mcell" style="flex:0.5;"><p>任务</p></div>
             <div class="mcell" style="flex:2.2;"><p>隐藏测试指标</p></div>
             <div class="mcell" style="flex:0.8;"><p>样本</p></div>
             <div class="mcell" style="flex:1.0;"><p>最终采用</p></div>
           </div>
           <div class="mrow">
             <div class="mcell" style="flex:0.5;"><p>A</p></div>
             <div class="mcell" style="flex:2.2;"><p>Accuracy 0.8690<br>Macro-F1 0.8642</p></div>
             <div class="mcell" style="flex:0.8;"><p>4,886</p></div>
             <div class="mcell" style="flex:1.0;"><p>第 10 轮</p></div>
           </div>
           <div class="mrow">
             <div class="mcell" style="flex:0.5;"><p>B</p></div>
             <div class="mcell" style="flex:2.2;"><p>MAE 503.61 分钟<br>RMSE 691.66 分钟</p></div>
             <div class="mcell" style="flex:0.8;"><p>200</p></div>
             <div class="mcell" style="flex:1.0;"><p>第 2 轮</p></div>
           </div>
           <div class="mrow">
             <div class="mcell" style="flex:0.5;"><p>C</p></div>
             <div class="mcell" style="flex:2.2;"><p>MAE 41.51 循环 · RMSE 56.22 循环<br>NASA 分 4.86×10¹⁰</p></div>
             <div class="mcell" style="flex:0.8;"><p>9,687</p></div>
             <div class="mcell" style="flex:1.0;"><p>第 1 轮</p></div>
           </div>
         </div>
         <div class="row">
           <div class="card" style="flex:1;"><p class="tag">A</p><h3>Macro-F1</h3><p class="big">0.8642</p><p class="small">本地公开验证 0.7166</p></div>
           <div class="card accent" style="flex:1;"><p class="tag">B</p><h3>RMSE</h3><p class="big">691.66</p><p class="small">分钟；本地 656.35</p></div>
           <div class="card" style="flex:1;"><p class="tag">C</p><h3>RMSE</h3><p class="big">56.22</p><p class="small">循环；本地 52.74</p></div>
         </div>
         <p class="small">平台真实隐藏测试指标，不是正式成绩。Token 42,197；运行约 A 46.5 / B 26.9 / C 212.2 分钟。</p>`
       )
      ),
    });
  slides.push({
    html: writeSlide(
      "slide-06-diagnostics.html",
      page(
        "聚合分数之外：哪些地方变差了？",
        "第一轮只作为基线流程验证；下一轮应针对薄弱点提出可证伪假设。",
        "06",
        `<div class="row" style="flex:1;">
          <div class="card accent" style="flex:1;">
            <p class="tag">A · 主要问题</p><h3>乙醛识别失效</h3><p class="big">0 / 109</p>
            <p>乙醛验证样本 109 条中，108 条被判为乙醇。</p>
            <p class="small">训练批次 1、验证批次 2；整体准确率不能掩盖漂移与类别盲点。</p>
          </div>
          <div class="card" style="flex:1;">
            <p class="tag">B · 子组风险</p><h3>Bearing1_4 退化</h3><p class="big">+40.44</p>
            <p>RMSE 从 241.98 升至 282.42 分钟。</p>
            <p class="small">总 RMSE 改善主要来自大样本 Bearing3_4；必须看分轴承结果。</p>
          </div>
          <div class="card" style="flex:1;">
            <p class="tag">C · 稳定性</p><h3>指标互相矛盾</h3><p class="big">RMSE ↓ / MAE ↑</p>
            <p>总体变化很小；FD002、FD004 没有同步改善。</p>
            <p class="small">下一轮应先验证可重复性，再尝试贴近 NASA 非对称惩罚。</p>
          </div>
        </div>`
      )
    ),
  });
  slides.push({
    html: writeSlide(
      "slide-07-drift.html",
      page(
        "漂移诊断：A/B 的公开 split 差异明显",
        "每轮仅比较公开训练/验证 inputs，使用 PSI + 标准化均值差，不读取标签或 meta。",
        "07",
        `<div class="matrix">
           <div class="mrow mhead">
             <div class="mcell"><p>任务</p></div><div class="mcell"><p>特征数</p></div><div class="mcell"><p>高漂移</p></div>
             <div class="mcell"><p>中漂移</p></div><div class="mcell"><p>Median PSI</p></div><div class="mcell"><p>最大 PSI</p></div>
           </div>
           <div class="mrow">
             <div class="mcell"><p>A</p></div><div class="mcell"><p>128</p></div><div class="mcell"><p>118</p></div>
             <div class="mcell"><p>10</p></div><div class="mcell"><p>0.6733</p></div><div class="mcell"><p>2.7306</p></div>
           </div>
           <div class="mrow">
             <div class="mcell"><p>B</p></div><div class="mcell"><p>34</p></div><div class="mcell"><p>32</p></div>
             <div class="mcell"><p>2</p></div><div class="mcell"><p>1.7083</p></div><div class="mcell"><p>10.6098</p></div>
           </div>
           <div class="mrow">
             <div class="mcell"><p>C</p></div><div class="mcell"><p>24</p></div><div class="mcell"><p>0</p></div>
             <div class="mcell"><p>0</p></div><div class="mcell"><p>0.0039</p></div><div class="mcell"><p>0.0094</p></div>
           </div>
         </div>
         <div class="row">
           <div class="card" style="flex:1;"><p class="tag">方法</p><h3>训练分位数分箱 PSI</h3><p>10 个训练分位边界；1e-6 平滑。</p></div>
           <div class="card accent" style="flex:1;"><p class="tag">A/B</p><h3>公开输入漂移</h3><p>A 118/128、B 32/34 特征达到高漂移阈值。</p></div>
           <div class="card" style="flex:1;"><p class="tag">解释边界</p><h3>不是隐藏集结论</h3><p>仅诊断公开 train/validation split，不外推隐藏集或线上数据。</p></div>
         </div>
         <p class="small">阈值属于项目诊断规则：高 PSI≥0.25 或 SMD≥1.0；不是官方评分公式。</p>`
       )
    ),
  });
  slides.push({
    html: writeSlide(
      "slide-08-resources.html",
      page(
        "资源与费用：本地很轻，云端已实测",
        "第 1 次试运行实际用量 42,197 Token；A/B/C 并行执行。",
        "08",
        `<div class="row">
          <div class="card" style="flex:1;"><p class="tag">A</p><h3>运行 2,790 s</h3><p class="big">CPU 3,508 s</p><p class="small">4,886 条隐藏样本</p></div>
          <div class="card" style="flex:1;"><p class="tag">B</p><h3>运行 1,617 s</h3><p class="big">CPU 1,799 s</p><p class="small">200 条隐藏样本</p></div>
          <div class="card" style="flex:1;"><p class="tag">C</p><h3>运行 12,733 s</h3><p class="big">CPU 19,729 s</p><p class="small">9,687 条隐藏样本</p></div>
        </div>
        <div class="row">
          <div class="status" style="flex:1;"><p><b>实际 Token：</b>输入 34,517，输出 7,680，合计 42,197；平台显示“已结算”。报告未展示具体金额。</p></div>
        </div>
        <div class="row">
          <div class="listbox" style="flex:1;"><ul><li>平台沙箱规格：2 核 CPU、4 GiB 内存。</li><li>C 的 CPU 用时最高，是资源优化重点。</li><li>试运行 1/10；正式评测 1/3。</li></ul></div>
        </div>`
      )
    ),
  });
  slides.push({
    html: writeSlide(
      "slide-09-delivery.html",
      page(
        "交付边界与当前风险",
        "代码、镜像、平台校验、首次试运行和正式版本选择已完成；正式评测已入队。",
        "09",
        `<div class="row">
          <div class="card" style="flex:1;"><p class="tag">已完成</p><h3>端到端跑通</h3><p>SDK 1.0.4；镜像 40.2 MB；单镜像 A/B/C；漂移报告与回滚；试运行 1/10 完成，42,197 Token。</p><p class="small">Harness 17 项；SDK 离线 18 项；A/C 各9、B核心10项通过。</p></div>
          <div class="card accent" style="flex:1;"><p class="tag">进行中</p><h3>第 1 次正式评测</h3><p>v1 已选为正式版本并锁定；正式评测 1/3，当前排队。</p><p class="small">正式成绩待公布，不能与试运行指标混用。</p></div>
        </div>
        <div class="listbox"><h3 style="font-size:12pt;color:${C.navy};margin:0 0 5pt;">当前不能声称的事</h3>
          <ul><li>尚未获得正式评测成绩或排名。</li><li>源码仓库与 SwanLab 仍为私有，评委访问权限未配置。</li><li>B 官方包的两项打包测试依赖缺失脚本，训练核心测试仍通过。</li><li>试运行只覆盖一次提交版本，不代表 10 轮以外仍稳定。</li></ul>
        </div>`
      )
    ),
  });
  slides.push({
    html: writeSlide(
      "slide-10-next.html",
      page(
        "下一步：复核报告，决定正式版本与正式评测",
        "试运行已完成；正式评测需要新的明确授权。",
        "10",
        `<div class="flow" style="flex:1;align-items:center;">
          <div class="flow-card"><h3>1 · 复核报告</h3><p>核对 A/B/C 隐藏指标、10 轮记录和 Token。</p><p>确认异常与可复现性。</p></div>
          <p class="arrow">→</p>
          <div class="flow-card"><h3>2 · 修正访问权限</h3><p>源码仓库与 SwanLab 需对评委可访问。</p><p>否则链接无效。</p></div>
          <p class="arrow">→</p>
          <div class="flow-card"><h3>3 · 选正式版本</h3><p>v1 已选为正式版本。</p><p>第 1 次正式评测已入队，1/3。</p></div>
          <p class="arrow">→</p>
          <div class="flow-card"><h3>4 · 更新材料</h3><p>把正式成绩、用量与异常补进报告和 PPT。</p><p>不把试运行写成正式成绩。</p></div>
        </div>
        <div class="status"><p>截至 2026-11-22：v1 已选正式版本；试运行 1/10；正式评测 1/3（第 1 次已入队，成绩待公布）；Token 42,197。</p></div>`
      )
    ),
  });

  const pptx = new pptxgen();
  pptx.defineLayout({ name: "RSI_16x9", width: 10, height: 5.625 });
  pptx.layout = "RSI_16x9";
  pptx.author = "智训引擎参赛团队";
  pptx.subject = "工业制造场景下的受控模型训练与超参数优化";
  pptx.title = "智训引擎";
  pptx.company = "参赛团队";
  pptx.theme = { headFontFace: "Arial", bodyFontFace: "Arial", lang: "zh-CN" };
  const tmpDir = path.join(ROOT, "tmp");
  fs.mkdirSync(tmpDir, { recursive: true });

  for (const item of slides) {
    await html2pptx(item.html, pptx, { tmpDir });
  }

  await pptx.writeFile({ fileName: OUTPUT });
  console.log(`Created ${OUTPUT}`);
}

main().catch(error => {
  console.error(error);
  process.exitCode = 1;
});
