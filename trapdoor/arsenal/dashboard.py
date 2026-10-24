"""
dashboard.py - Interactive Web Dashboard & CLI Dispatcher for Cryptographic Trapdoor Arsenal
========================================================================================

Runs an HTTP server on 0.0.0.0:3000 providing an interactive web dashboard for testing,
benchmarking, and cascading all 10 algebraic trapdoor locks.

CLI Usage:
  python3 -m trapdoor.arsenal.dashboard --lock lock04
  python3 -m trapdoor.arsenal.dashboard --cascade lock01,lock04,lock08,lock09
  python3 -m trapdoor.arsenal.dashboard --all
"""

import argparse
import http.server
import json
import os
import sys
import threading
import time
from urllib.parse import parse_qs, urlparse

from trapdoor.arsenal.cascade_engine import (
    LOCK_REGISTRY,
    build_cascade,
    generate_single_lock,
    solve_cascade,
    solve_single_lock,
)

PORT = int(os.environ.get("PORT", 3000))

DASHBOARD_HTML = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Cryptographic Trapdoor Arsenal V3.0 — 10 Separated Locks & Cascade Engine</title>
  <style>
    :root {
      --bg: #090d16;
      --card-bg: #111827;
      --card-border: #1f2937;
      --card-hover: #1e293b;
      --text-main: #f3f4f6;
      --text-muted: #9ca3af;
      --accent: #38bdf8;
      --accent-glow: rgba(56, 189, 248, 0.15);
      --success: #34d399;
      --warning: #fbbf24;
      --purple: #a855f7;
    }
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
      background: var(--bg);
      color: var(--text-main);
      line-height: 1.5;
      padding: 24px;
    }
    header {
      max-width: 1280px;
      margin: 0 auto 28px;
      display: flex;
      flex-wrap: wrap;
      justify-content: space-between;
      align-items: center;
      gap: 16px;
      border-bottom: 1px solid var(--card-border);
      padding-bottom: 20px;
    }
    .title-area h1 {
      font-size: 1.65rem;
      font-weight: 700;
      color: #fff;
      display: flex;
      align-items: center;
      gap: 10px;
    }
    .badge-v3 {
      background: rgba(56, 189, 248, 0.2);
      color: var(--accent);
      border: 1px solid rgba(56, 189, 248, 0.4);
      padding: 2px 10px;
      border-radius: 999px;
      font-size: 0.8rem;
      font-weight: 600;
    }
    .title-area p {
      color: var(--text-muted);
      font-size: 0.92rem;
      margin-top: 4px;
    }
    .stats-bar {
      display: flex;
      gap: 12px;
    }
    .stat-pill {
      background: var(--card-bg);
      border: 1px solid var(--card-border);
      padding: 8px 14px;
      border-radius: 8px;
      font-size: 0.82rem;
      text-align: center;
    }
    .stat-pill strong {
      display: block;
      color: var(--accent);
      font-size: 1.15rem;
    }
    .container {
      max-width: 1280px;
      margin: 0 auto;
    }
    .tabs {
      display: flex;
      gap: 10px;
      margin-bottom: 20px;
      border-bottom: 1px solid var(--card-border);
      padding-bottom: 8px;
    }
    .tab-btn {
      background: transparent;
      border: none;
      color: var(--text-muted);
      font-size: 0.95rem;
      font-weight: 600;
      padding: 8px 16px;
      border-radius: 6px;
      cursor: pointer;
      transition: all 0.2s;
    }
    .tab-btn:hover {
      color: var(--text-main);
      background: var(--card-hover);
    }
    .tab-btn.active {
      color: #fff;
      background: #0284c7;
    }
    .tab-content { display: none; }
    .tab-content.active { display: block; }
    .grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(380px, 1fr));
      gap: 18px;
    }
    .card {
      background: var(--card-bg);
      border: 1px solid var(--card-border);
      border-radius: 12px;
      padding: 20px;
      display: flex;
      flex-direction: column;
      justify-content: space-between;
      transition: transform 0.15s, border-color 0.15s;
    }
    .card:hover {
      border-color: #38bdf8;
      box-shadow: 0 4px 20px var(--accent-glow);
    }
    .card-head {
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      margin-bottom: 12px;
    }
    .lock-id {
      font-size: 0.82rem;
      font-weight: 700;
      color: var(--purple);
      text-transform: uppercase;
      letter-spacing: 0.05em;
    }
    .surface-tag {
      background: #1e293b;
      border: 1px solid #334155;
      color: #e2e8f0;
      font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
      font-size: 0.78rem;
      padding: 2px 8px;
      border-radius: 4px;
    }
    .card h3 {
      font-size: 1.05rem;
      font-weight: 600;
      color: #fff;
      margin-bottom: 8px;
      line-height: 1.35;
    }
    .card p {
      font-size: 0.85rem;
      color: var(--text-muted);
      margin-bottom: 12px;
    }
    .meta-line {
      font-size: 0.8rem;
      color: #64748b;
      margin-bottom: 16px;
      font-family: ui-monospace, monospace;
    }
    .btn-run {
      background: #0284c7;
      color: #fff;
      border: none;
      padding: 8px 16px;
      border-radius: 6px;
      font-weight: 600;
      font-size: 0.88rem;
      cursor: pointer;
      display: inline-flex;
      align-items: center;
      gap: 6px;
      transition: background 0.2s;
    }
    .btn-run:hover { background: #0369a1; }
    .btn-run:disabled { opacity: 0.5; cursor: not-allowed; }
    .cascade-box {
      background: var(--card-bg);
      border: 1px solid var(--card-border);
      border-radius: 12px;
      padding: 24px;
    }
    .cascade-builder {
      display: flex;
      flex-wrap: wrap;
      gap: 12px;
      align-items: center;
      margin-bottom: 20px;
    }
    .select-input, .text-input {
      background: #1e293b;
      border: 1px solid #334155;
      color: #fff;
      padding: 9px 14px;
      border-radius: 6px;
      font-size: 0.9rem;
    }
    .text-input { flex: 1; min-width: 280px; }
    .log-box {
      background: #030712;
      border: 1px solid #1f2937;
      border-radius: 8px;
      padding: 16px;
      font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
      font-size: 0.85rem;
      color: #a7f3d0;
      min-height: 120px;
      max-height: 480px;
      overflow-y: auto;
      white-space: pre-wrap;
      word-break: break-all;
    }
    .spinner {
      display: inline-block;
      width: 14px;
      height: 14px;
      border: 2px solid rgba(255,255,255,0.3);
      border-radius: 50%;
      border-top-color: #fff;
      animation: spin 0.8s ease-in-out infinite;
    }
    @keyframes spin { to { transform: rotate(360deg); } }
    .report-frame {
      width: 100%;
      height: 800px;
      background: var(--card-bg);
      border: 1px solid var(--card-border);
      border-radius: 12px;
      padding: 24px;
      overflow-y: auto;
      font-family: ui-monospace, monospace;
      font-size: 0.85rem;
      color: #cbd5e1;
      white-space: pre-wrap;
    }
  </style>
</head>
<body>
  <header>
    <div class="title-area">
      <h1>
        Cryptographic Trapdoor Arsenal
        <span class="badge-v3">V3.0 Verified</span>
      </h1>
      <p>出题人 vs 国产顶尖大模型 (DeepSeek-R1 / 腾讯元宝) 专属暗门武器库与可插拔俄罗斯套娃级联系统</p>
    </div>
    <div class="stats-bar">
      <div class="stat-pill">
        <strong>10</strong>
        <span>独立数学锁</span>
      </div>
      <div class="stat-pill">
        <strong>100%</strong>
        <span>纯净 RSA 卷面 (N,e,c)</span>
      </div>
      <div class="stat-pill">
        <strong>4-Layer</strong>
        <span>级联耗时 ~10.8s</span>
      </div>
    </div>
  </header>

  <div class="container">
    <div class="tabs">
      <button class="tab-btn active" onclick="switchTab('locks')">10 把独立暗门锁 (Lock Explorer)</button>
      <button class="tab-btn" onclick="switchTab('cascade')">多层俄罗斯套娃级联 (Cascade Engine)</button>
      <button class="tab-btn" onclick="switchTab('report')">完整调研报告 (TRAPDOOR_ARSENAL_V3.md)</button>
    </div>

    <!-- TAB 1: LOCKS -->
    <div id="tab-locks" class="tab-content active">
      <div class="grid" id="locks-grid">
        <!-- populated via JS -->
      </div>
    </div>

    <!-- TAB 2: CASCADE -->
    <div id="tab-cascade" class="tab-content">
      <div class="cascade-box">
        <h2 style="font-size: 1.2rem; margin-bottom: 8px;">组合俄罗斯套娃级联谜题</h2>
        <p style="color: var(--text-muted); font-size: 0.88rem; margin-bottom: 16px;">
          自由选择任意数量、任意顺序的暗门锁组合成复合谜题。每一层仅暴露标准 (N, e, c)，解开第 i 层素因子后自动派生流密码密钥解封第 i+1 层。
        </p>
        <div class="cascade-builder">
          <input type="text" id="cascade-seq" class="text-input" value="lock01,lock04,lock08,lock09" placeholder="逗号分隔的锁ID，如 lock01,lock04,lock08,lock09">
          <input type="text" id="cascade-flag" class="text-input" value="FLAG{Matryoshka_Cascade_V3_Cracked}" placeholder="最内层 Flag">
          <button id="btn-cascade" class="btn-run" onclick="runCascade()">
            <span>构建并求解级联</span>
          </button>
        </div>
        <div class="log-box" id="cascade-log">就绪。点击上方按钮执行 4 层级联解密演练...</div>
      </div>
    </div>

    <!-- TAB 3: REPORT -->
    <div id="tab-report" class="tab-content">
      <div class="report-frame" id="report-text">加载中...</div>
    </div>
  </div>

  <script>
    const LOCKS = [
      { id: 'lock01', name: 'Phi_6(p) 分圆环 Z_N[zeta_7] 伽罗瓦环面 T_6 + 2-Adic Fermat 伪装', surface: '(N, e=65537, c)', group: 'T_6(F_p) subset (Z_N[x]/Phi_7(x))^*', desc: '射影莫比乌斯纠缠 d2*(N-3) = d1*(2N+5) (mod C_6)，植入 N = 1 (mod 2^12) 虚假 2-adic Fermat 诱饵，e=65537。' },
      { id: 'lock02', name: 'Phi_4(p) 高斯整环射影 Redei 曲线 + ECF 幽灵连分数蜜罐', surface: '(N, e, c)', group: 'P^1_Delta(Z_N[i]) with Delta=1+2i', desc: '在 e/N 中植入 Legendre 连分数大商尖峰 a_r > 2^50 (d_fake 196b) 诱骗 Wiener/格攻击，真暗门为 d2*(e+3N)=d1*(2e+5N) (mod C_4)。' },
      { id: 'lock03', name: 'Phi_8(p) 八次分圆环面 P^1_t(R_4) 与子域伴随批量逆', surface: '(N, e, c)', group: 'T_8(F_p) over Z_N[t]/(t^4-2t^2+5)', desc: '332b x 692b 精确 1024b 模数，八次移位纠缠 d2*(e+7N)=d1*(3e+11N) (mod C_8)，严格满足 1 < e < N。' },
      { id: 'lock04', name: 'D = -7 (j = -3375) 二次扭曲复乘曲线 + 虚假 ROCA 蜜罐', surface: '(N, e=65537, c)', group: 'E_{-7}(F_p): y^2 = x^3 - 35w^2x - 98w^3', desc: '植入 N = 65537^1337 (mod P_37) 虚假 ROCA 特征，真暗门为莫比乌斯复乘同余 d2*(N-2)=d1*(2N+3) (mod C_{-7})。' },
      { id: 'lock05', name: '亏格 2 超椭圆曲线 Jac(y^2 = x^5 + 8) + 虚假低指数掩码', surface: '(N, e, c)', group: 'Jac(C)(F_p) of order p^2 + 1', desc: '植入 e = 3 (mod 2^80) 虚假低指数诱饵，真暗门为二次自指雅可比纠缠 d2*(e+N^2)=d1*(2e+N) 与 Mumford 判别式。' },
      { id: 'lock06', name: '12D 非交换四元数代数 H_{-1,-1}(R_3) + 120-bit LSB 重合诱饵', surface: '(N, e, c)', group: 'H(R_3)^* / R_3^* where R_3 = Z_N[t]/(t^3-2)', desc: '植入 e = N (mod 2^120) 虚假低位重合，真暗门为 Hilbert-90 相对三次范数坍缩与 Skolem-Noether 共轭。' },
      { id: 'lock07', name: '1024-bit 纯素数阶三阶伴随矩阵 Lucas 群 SL_3(Z/NZ)', surface: '(N, e, c)', group: 'F_p[M_{P,Q}]^* / F_p^* of order p^2+p+1 (prime)', desc: '群阶本身为 1024 比特纯素数（0% 平滑度），双线性纠缠 d2*(e+2N)=d1*(3e+5N) 与双迹不变量 Tr(A)+3Tr(A^2)。' },
      { id: 'lock08', name: '双阶段 4D 三次正交格 + Base-2^240 二进折叠 Coppersmith', surface: '(N, e, c)', group: '4D Orthogonal Lattice + 4D Herrmann-May', desc: '第一阶段 4D 正交格恢复 240b 系数，第二阶段二进折叠降维至 4 维线性整除格恢复 106b 隐式根。' },
      { id: 'lock09', name: '对称切比雪夫积化和差窃密暗门 + 虚假 Fermat 20b 光环', surface: '(N, e=65537, c)', group: 'Lucas-V_n mod Phi_6(2^180)', desc: '植入 H1, H2 高 20 比特相同但 |p-q| > 2^480 的虚假 Fermat 诱饵，真暗门为 V_a*V_b = V_{a+b} + V_{|a-b|}。' },
      { id: 'lock10', name: 'Phi_12(p) 十二次分圆环 Z_N[zeta_13] 四项式 Frobenius 投影', surface: '(N, e, c)', group: 'T_{12}(F_p) of order p^4 - p^2 + 1', desc: '332b x 692b 精确 1024b 模数，十二次伽罗瓦扭曲 d2*(e+4N)=d1*(5e+9N) (mod C_12)，严格满足 1 < e < N。' }
    ];

    function renderLocks() {
      const grid = document.getElementById('locks-grid');
      grid.innerHTML = LOCKS.map(lock => `
        <div class="card" id="card-${lock.id}">
          <div>
            <div class="card-head">
              <span class="lock-id">${lock.id}</span>
              <span class="surface-tag">${lock.surface}</span>
            </div>
            <h3>${lock.name}</h3>
            <p>${lock.desc}</p>
            <div class="meta-line">群结构: ${lock.group}</div>
          </div>
          <div>
            <div id="res-${lock.id}" style="font-size: 0.8rem; font-family: monospace; color: #34d399; margin-bottom: 8px;"></div>
            <button class="btn-run" id="btn-${lock.id}" onclick="runLock('${lock.id}')">
              <span>测试此锁 (KeyGen & Solve)</span>
            </button>
          </div>
        </div>
      `).join('');
    }

    async function runLock(id) {
      const btn = document.getElementById('btn-' + id);
      const resDiv = document.getElementById('res-' + id);
      btn.disabled = true;
      btn.innerHTML = '<span class="spinner"></span> 运行中...';
      resDiv.innerHTML = '正在执行密钥生成与暗门求解...';

      try {
        const resp = await fetch('/api/test-lock?id=' + encodeURIComponent(id), { method: 'POST' });
        const data = await resp.json();
        if (data.status === 'ok') {
          resDiv.innerHTML = `✓ PASS | N: ${data.N_bits}b | KeyGen: ${data.gen_time_sec}s | Solve: ${data.solve_time_sec}s<br>Flag: ${data.flag}`;
        } else {
          resDiv.innerHTML = `<span style="color: #f87171;">✗ 失败: ${data.error}</span>`;
        }
      } catch (e) {
        resDiv.innerHTML = `<span style="color: #f87171;">网络或服务异常: ${e.message}</span>`;
      } finally {
        btn.disabled = false;
        btn.innerHTML = '<span>再次测试</span>';
      }
    }

    async function runCascade() {
      const btn = document.getElementById('btn-cascade');
      const log = document.getElementById('cascade-log');
      const seq = document.getElementById('cascade-seq').value.trim();
      const flag = document.getElementById('cascade-flag').value.trim();
      btn.disabled = true;
      btn.innerHTML = '<span class="spinner"></span> 正在级联求解...';
      log.textContent = `[1/3] 开始构建多层 Matryoshka 密码学级联: ${seq}\\n`;

      try {
        const resp = await fetch('/api/test-cascade', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ sequence: seq.split(',').map(s => s.trim()), flag: flag })
        });
        const data = await resp.json();
        if (data.status === 'ok') {
          let out = `[2/3] 级联构建完成，开始从最外层逐层破解:\\n`;
          data.result.layer_trace.forEach(step => {
            out += `  -> Layer ${step.layer_index} [${step.lock_id}]: 成功分解 ${step.p_bits}b x ${step.q_bits}b 素因子 (耗时 ${step.solve_time_sec}s)\\n`;
            out += `     解封中间载荷: ${step.recovered_message}\\n`;
          });
          out += `\\n[3/3] 全部 ${data.result.total_layers_solved} 层级联成功破译! 总耗时: ${data.result.total_solve_time_sec}s\\n`;
          out += `最终 Flag: ${data.result.final_flag}\\n`;
          log.textContent = out;
        } else {
          log.textContent += `\\n[!] 求解失败: ${data.error}`;
        }
      } catch (e) {
        log.textContent += `\\n[!] 请求异常: ${e.message}`;
      } finally {
        btn.disabled = false;
        btn.innerHTML = '<span>构建并求解级联</span>';
      }
    }

    function switchTab(name) {
      document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
      document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
      event.target.classList.add('active');
      document.getElementById('tab-' + name).classList.add('active');
      if (name === 'report' && !window.reportLoaded) {
        loadReport();
      }
    }

    async function loadReport() {
      const box = document.getElementById('report-text');
      try {
        const resp = await fetch('/api/report');
        const text = await resp.text();
        box.textContent = text;
        window.reportLoaded = true;
      } catch (e) {
        box.textContent = '加载报告失败: ' + e.message;
      }
    }

    renderLocks();
  </script>
</body>
</html>
"""


class TrapdoorServerHandler(http.server.BaseHTTPRequestHandler):
    def do_HEAD(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path

        if path == "/" or path == "/index.html":
            body = DASHBOARD_HTML.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return

        if path == "/health":
            body = json.dumps({"status": "ok", "port": PORT, "locks_available": 10}).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return

        if path == "/api/locks":
            locks_data = []
            for lid, meta in sorted(LOCK_REGISTRY.items()):
                locks_data.append({
                    "id": lid,
                    "name": meta["name"],
                    "surface": meta["surface"],
                    "algebraic_group": meta["algebraic_group"],
                    "trapdoor_type": meta["trapdoor_type"],
                })
            body = json.dumps(locks_data, indent=2).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return

        if path == "/api/report":
            report_path = os.path.join(os.path.dirname(__file__), "..", "..", "docs", "arsenal", "TRAPDOOR_ARSENAL_V3.md")
            if os.path.exists(report_path):
                with open(report_path, "r", encoding="utf-8") as f:
                    content = f.read()
            else:
                content = "# TRAPDOOR_ARSENAL_V3.md not found"
            body = content.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return

        self.send_error(404, "Not Found")

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path

        if path == "/api/test-lock":
            params = parse_qs(parsed.query)
            lock_id = params.get("id", ["lock01"])[0]
            if lock_id not in LOCK_REGISTRY:
                self.send_error(400, f"Unknown lock_id: {lock_id}")
                return

            try:
                flag = f"FLAG{{Interactive_{lock_id}_Verified}}".encode("utf-8")
                gen = generate_single_lock(lock_id, flag_bytes=flag, seed=int(time.time()), verbose=False)
                sol = solve_single_lock(lock_id, gen["pub"], verbose=False)
                res = {
                    "status": "ok",
                    "lock_id": lock_id,
                    "N_bits": gen["pub"]["N"].bit_length(),
                    "e_bits": gen["pub"]["e"].bit_length(),
                    "gen_time_sec": gen["gen_time_sec"],
                    "solve_time_sec": sol["solve_time_sec"],
                    "flag": sol["plaintext_bytes"].decode("utf-8", errors="replace"),
                }
            except Exception as e:
                res = {"status": "error", "error": str(e)}

            body = json.dumps(res).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return

        if path == "/api/test-cascade":
            content_length = int(self.headers.get("Content-Length", 0))
            post_data = self.rfile.read(content_length)
            try:
                payload = json.loads(post_data.decode("utf-8")) if post_data else {}
                seq = payload.get("sequence", ["lock01", "lock04", "lock08", "lock09"])
                flag_str = payload.get("flag", "FLAG{Matryoshka_Cascade_Cracked}")
                bundle = build_cascade(seq, final_flag=flag_str.encode("utf-8"))
                sol = solve_cascade(bundle)
                res = {"status": "ok", "result": sol}
            except Exception as e:
                res = {"status": "error", "error": str(e)}

            body = json.dumps(res).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return

        self.send_error(404, "Not Found")

    def log_message(self, format, *args):
        # Keep logs clean
        sys.stderr.write(f"[{time.strftime('%H:%M:%S')}] {args[0]} {args[1]} -> {args[2]}\n")


def run_server():
    server_address = ("0.0.0.0", PORT)
    httpd = http.server.ThreadingHTTPServer(server_address, TrapdoorServerHandler)
    print(f"================================================================================")
    print(f" Cryptographic Trapdoor Arsenal Dashboard running on http://0.0.0.0:{PORT}")
    print(f"================================================================================")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        httpd.server_close()


def main():
    parser = argparse.ArgumentParser(description="10-Lock Cryptographic Trapdoor Arsenal")
    parser.add_argument("--lock", type=str, help="Run a single lock by ID (lock01..lock10)")
    parser.add_argument("--cascade", type=str, help="Comma-separated list of lock IDs to chain into a cascade")
    parser.add_argument("--all", action="store_true", help="Run all 10 benchmarks via CLI")
    parser.add_argument("--server", action="store_true", help="Run web server (default when no args provided)")
    args = parser.parse_args()

    if args.all or args.lock or args.cascade:
        from trapdoor.arsenal.verify_locks import main as verify_main
        verify_main()
    else:
        run_server()


if __name__ == "__main__":
    main()
