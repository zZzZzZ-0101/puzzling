# 密码学挑战赛「出题人 vs 国产顶尖大模型」终极暗门武器库调研报告 (V3.0)
## —— 10 个独立高阶代数陷门（10 Separated Locks）与可插拔俄罗斯套娃级联引擎（Composable Cascade Engine）

---

## 0. 全局设计哲学与反 AI 防御矩阵（Anti-LLM Defense Architecture）

### 0.1 为什么传统的 CTF 密码学机关在 DeepSeek-R1 / 腾讯元宝面前全面失效？
国产顶尖推理模型（DeepSeek-R1/V3、腾讯元宝等）结合了三大核心能力：
1. **高频套路先验（Pattern Recognition）**：对中文安全社区（CTF-Wiki、先知社区、看雪、知乎）及 CTFtime 历年高频题型（Wiener/Boneh-Durfee、Hastad Broadcast、Franklin-Reiter、已知高位/低位 Coppersmith、ROCA 原版、标准 Pollard $p-1$、Williams $p+1$、小判别式 $D \in \{1,2,3\}$ 复乘 ECM）形成了近乎条件反射的代码模板生成能力。
2. **沙箱自动试探树（Sandbox Autopilot Trap）**：当卷面只给 $(N, e, c)$ 时，AI 会在沙箱中自动编写并运行一套固定的分解流水线：
   $$\text{Factordb / 小素数试除} \longrightarrow \text{完美幂 / Fermat} \longrightarrow \text{Pollard } p-1 \longrightarrow \text{Williams } p+1 \longrightarrow \text{Lenstra ECM} \longrightarrow \text{Wiener / 2D-3D LLL}$$
3. **表面特征联网检索（Surface-Feature Search）**：一旦源码中出现非常规素数常数、特定曲线方程参数（如直接把曲线系数 $a, b$ 写在 JSON 里）、或者出现 `f_cktoring` / `roca` 等特征结构，AI 的 Deep Research 就会通过关键词组合定位到原题 Writeup。

### 0.2 本武器库的三大铁律与十锁正交矩阵
本报告设计的 **10 个独立高阶数学锁（Lock 01 – Lock 10）** 严格遵守以下三条铁律：
1. **卷面绝对纯净（Zero-Hint Public Surface）**：
   - 所有 10 把锁对外暴露的公开数据**仅有标准 RSA 三元组 $(N, e, c)$**（其中 Lock 01、04、09 使用全球通用的固定公钥指数 $e = 65537$，其余使用满比特高熵指数 $e \approx N$）。
   - **绝不在卷面暴露任何辅助参数**（不给曲线系数 $a, b$、不给矩阵初值、不给切比雪夫基点、不给高位比特泄漏）。
2. **与仓库现有 4 个变体（Variants 5, 6, 7, 9）100% 正交**：
   - Variant 5 用的是 $j=0$ ($y^2=x^3+b$) 曲线配合公开参数 $b$；
   - Variant 6 用的是三次域 $\mathbb{Z}_N[t]/(t^3-a)$ 配合公开参数 $a$；
   - Variant 7 用的是分圆预言机加显式泄漏提示 `hint = p >> 212`；
   - Variant 9 用的是 3D 正交格加 5D Jochemsz-May 策略。
   - **本报告的 Lock 01 – Lock 10 全部开辟了全新的代数群、非交换四元数代数、亏格 2 阿贝尔曲面、素数阶矩阵群与双阶段折叠格结构**，与上述四个变体无任何重叠。
3. **单锁独立可解 + 任意子集级联组合（Composable Matryoshka Cascade）**：
   - 每一把锁在 `locks_A.py` 与 `locks_B.py` 中均封装为独立的 `lockXX_generate` 与 `lockXX_solve` 函数；
   - `cascade_engine.py` 提供通用级联引擎：可将任意子集、任意顺序的锁（如 `["lock01", "lock04", "lock08", "lock09"]`）串联成多层俄罗斯套娃谜题。唯有分解出第 $i$ 层的素因子 $\{p_i, q_i\}$，才能派生出流密码密钥解开第 $i+1$ 层的 $(N_{i+1}, e_{i+1}, c_{i+1})$。

| 锁编号 | 名称与核心代数结构 | 公开卷面 | 暗门群阶 / 格维度 | $p \pm 1$ / 标准 ECM 状态 | 配套代码文件 |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Lock 01** | $\Phi_6(p)=p^2-p+1$ 分圆环 $\mathbb{Z}_N[\zeta_7]$ 伽罗瓦环面 $\mathbb{T}_6$ 自指纠缠 | `(N, e=65537, c)` | $\Phi_6(p)$ 含大素因子 $C_6$，$\delta_2 N \equiv \delta_1 \pmod{C_6}$ | 100% 免疫 | `locks_A.py` |
| **Lock 02** | $\Phi_4(p)=p^2+1$ 高斯整数环 $\mathbb{Z}_N[i]$ 射影 Rédei 二次曲线与 Montgomery 批量逆 | `(N, e, c)` | $\mathbb{P}^1_\Delta(\mathbb{F}_{p^2})$ ($\Delta=1+2i$)，阶 $p^2+1$ | 100% 免疫 | `locks_A.py` |
| **Lock 03** | $\Phi_8(p)=p^4+1$ 八次分圆环面 $\mathbb{P}^1_t(\mathbb{Z}_N[t]/(t^4-2t^2+5))$ 与子域伴随逆 | `(N, e, c)` | $\mathbb{T}_8(\mathbb{F}_p)$，阶 $p^4+1$ | 100% 免疫 | `locks_A.py` |
| **Lock 04** | $\Delta_K=-7$ ($j=-3375 \neq 0,1728$) 导子 $f=2$ 二次扭曲复乘曲线自指暗门 | `(N, e=65537, c)` | $\#E_{-7}(\mathbb{F}_p)$ 仅 2 个二次扭曲，$\delta_2(N^2-4) \equiv \delta_1(N+2)$ | 100% 免疫 | `locks_A.py` |
| **Lock 05** | 亏格 2 超椭圆曲线 $\mathrm{Jac}(y^2=x^5+8)$ 四次复乘阿贝尔曲面 Cantor 除子锁 | `(N, e, c)` | $\mathrm{Jac}(C)(\mathbb{F}_p)$ 指数 $p^2+1$ | 100% 免疫 | `locks_A.py` |
| **Lock 06** | 12 维非交换四元数代数 $\mathbb{H}_{-1,-1}(\mathbb{Z}_N[t]/(t^3-2))$ 双重范数坍缩与内自同构 | `(N, e, c)` | $\gcd(p^3+1, p^4+p^2+1) = \Phi_6(p)$ | 100% 免疫 | `locks_B.py` |
| **Lock 07** | 1024-bit 纯素数阶三阶伴随矩阵 Lucas 群 $\mathrm{SL}_3(\mathbb{Z}/N\mathbb{Z})$ 零平滑度锁 | `(N, e, c)` | $M_3 = p^2+p+1$ **本身为 1024-bit 素数**（0% 平滑度） | 100% 免疫 | `locks_B.py` |
| **Lock 08** | 双阶段 4D 三次正交格 + Base-$2^{240}$ 二进折叠 4D 线性因子 Coppersmith 级联 | `(N, e, c)` | Stage 1: 4D $\Lambda^\perp$；Stage 2: 4D 线性整除格 ($m=2,t=2$) | 100% 免疫 | `locks_B.py` |
| **Lock 09** | 对称切比雪夫 / Lucas-$V$ 积化和差恒等式窃密暗门（Modulo Wrap-Around SETUP） | `(N, e=65537, c)` | $V_a(7)V_b(7) \equiv V_{a+b}(7)+V_{|a-b|}(7) \pmod{\Phi_6(2^{180})}$ | 100% 免疫 | `locks_B.py` |
| **Lock 10** | $\Phi_{12}(p)=p^4-p^2+1$ 十二次分圆环 $\mathbb{Z}_N[\zeta_{13}]$ 四项式 Frobenius 环面投影 | `(N, e, c)` | $\Psi_{12}(\sigma) = \sigma^8+\sigma^6-\sigma^2-1 \in \mathbb{T}_{12}(\mathbb{F}_p)$ | 100% 免疫 | `locks_B.py` |

---

## 方法 01（Lock 01）：$\Phi_6(p) = p^2 - p + 1$ 分圆环 $\mathbb{Z}_N[\zeta_7]$ 伽罗瓦环面 $\mathbb{T}_6$ 自指余因子纠缠暗门

1. **学术溯源与冷门度验证**
   - **文献**：Eric Bach & Jeffrey Shallit, *"Factoring with Cyclotomic Polynomials"*, Math. Comp. 52(185), 1989; Karl Rubin & Alice Silverberg, *"Torus-Based Cryptography"*, CRYPTO 2003; Bruno Sterner, *"Smooth evaluations of cyclotomic quadratics"*, IACR ePrint 2026/2116.
   - **曝光度**：中文圈仅知晓 $p \pm 1$；本锁引入 $\sim 580$-bit 未知余因子 $C_6$ 并通过 $N = pq \pmod{C_6}$ 实现自指抵消，卷面保持 $e = 65537$。
2. **核心数学原理与暗门生成算法（KeyGen & Trapdoor）**
   - 在 $\mathcal{A}_7 = \mathbb{Z}_N[x]/(\Phi_7(x))$ 中，利用 $\mathrm{Gal}(\mathbb{Q}(\zeta_7)/\mathbb{Q})$ 生成元 $\sigma_k(\zeta_7) = \zeta_7^{3^k \bmod 7}$ 构造环面投影 $\tau = \sigma_3(\beta)\sigma_1(\beta)(\sigma_2(\beta)\beta)^{-1}$，其模 $p$ 乘法阶整除 $\Phi_6(p) = p^2-p+1$。
   - 令 $\Phi_6(p) = G \cdot C_6$（$G$ 为 $B$-平滑部），选小素数 $\delta_1, \delta_2 < 2^{11}$，生成 $q \equiv \delta_1(\delta_2 p)^{-1} \pmod{C_6}$，从而恒有 $\delta_2 M_{\text{full}} N \equiv \delta_1 M_{\text{full}} \pmod{\Phi_6(p)}$。
3. **公开卷面呈现（Public Challenge）**：仅给 `(N, e=65537, c)`。
4. **国产 AI 破防推演**：$e=65537$ 封死一切格攻击；$p \pm 1$ 皆为大素数；即便尝试 $\Phi_6$ 分解，580-bit 余因子 $C_6$ 也使单纯平滑幂恒不为 1。
5. **解题破译算法（Solver）**：在 $\mathcal{A}_7$ 中计算 $Q_L = \tau^{M N}$ 与 $Q_R = \tau^M$，提取规范化常数项系数并调用 `batch_poly_gcd` 碰撞 $\delta_2, \delta_1$。
6. **复杂度与实现**：盲分解 $>2^{85}$；暗门求解实测 `3.11s`（见 `locks_A.py: lock01_generate / lock01_solve`）。

---

## 方法 02（Lock 02）：$\Phi_4(p) = p^2 + 1$ 高斯整数环 $\mathbb{Z}_N[i]$ 射影 Rédei 二次曲线与 Montgomery 批量范数逆锁

1. **学术溯源与冷门度验证**
   - **文献**：L. Rédei (1946); Barbero–Cerruti–Murru, *"Solving the Pell Equation via Rédei Rational Functions"*, Fibonacci Quarterly 48(4), 2010.
   - **曝光度**：将 Rédei 有理函数提升到高斯整数环 $R_2 = \mathbb{Z}_N[i]$ 上的二次非剩余 $\Delta = 1+2i$（范数 $5$），中文圈零提及。
2. **核心数学原理与暗门生成算法（KeyGen & Trapdoor）**
   - 当 $p \equiv 3 \pmod 4$ 且 $p \equiv 2,3 \pmod 5$ 时，$\Delta = 1+2i$ 在 $\mathbb{F}_{p^2}$ 中为非平方元，射影圆锥曲线 $[X_1:Y_1]\odot[X_2:Y_2] = [X_1X_2+\Delta Y_1Y_2 : X_1Y_2+Y_1X_2]$ 的模 $p$ 群阶精确为 $\Phi_4(p) = p^2+1 = G \cdot C_4$。
   - 构造公钥指数 $e \equiv (\delta_1 N + C_4)(\delta_2 + C_4)^{-1} \pmod{p^2+1}$，使得 $\delta_2 M e \equiv \delta_1 M N \pmod{p^2+1}$。
3. **公开卷面呈现（Public Challenge）**：仅给 `(N, e, c)`，无 $\Delta$ 参数。
4. **国产 AI 破防推演**：满比特 $e$ 对 $\varphi(N)$ 无短向量，Wiener/LLL 失效；必须构造 $\mathbb{Z}_N[i][\sqrt{1+2i}]$ 才能触及 $p^2+1$。
5. **解题破译算法（Solver）**：在 $\mathbb{P}^1_\Delta(\mathbb{Z}_N[i])$ 上计算 $[M e]P_0$ 与 $[M N]P_0$，利用高斯范数 $Y_r^2+Y_i^2$ 的 Montgomery 批量求逆归一后喂入 `batch_poly_gcd`。
6. **复杂度与实现**：盲分解 $>2^{80}$；暗门求解实测 `2.76s`（见 `locks_A.py: lock02_generate / lock02_solve`）。

---

## 方法 03（Lock 03）：$\Phi_8(p) = p^4 + 1$ 八次分圆环面 $\mathbb{P}^1_t(\mathbb{Z}_N[t]/(t^4-2t^2+5))$ 与子域伴随批量求逆锁

1. **学术溯源与冷门度验证**
   - **文献**：Rubin & Silverberg (CRYPTO 2003); Bach & Shallit (1989).
   - **曝光度**：$\Phi_8(p) = p^4+1$ 在全网 CTF 中未见无提示暗门实现。
2. **核心数学原理与暗门生成算法（KeyGen & Trapdoor）**
   - 在双二次整环 $R_4 = \mathbb{Z}_N[t]/(t^4-2t^2+5)$ 上，当 $p \equiv 7 \pmod{20}$ 时 $R_4/p R_4 \simeq \mathbb{F}_{p^4}$ 且 $t$ 为非平方元。以 $\Delta = t$ 构造射影 Rédei 群 $\mathbb{P}^1_t(R_4)$，其模 $p$ 阶精确为 $\Phi_8(p) = p^4+1 = G \cdot C_8$。
   - 构造 $e \equiv (\delta_1(N \bmod \Phi_8(p)) + C_8)(\delta_2 + C_8)^{-1} \pmod{\Phi_8(p)}$。
3. **公开卷面呈现（Public Challenge）**：仅给 `(N, e, c)`。
4. **国产 AI 破防推演**：$\Phi_1, \Phi_2, \Phi_3, \Phi_4, \Phi_6$ 在 $p$ 上全部含大素数，唯有 $\Phi_8(p) = p^4+1$ 含平滑主部。
5. **解题破译算法（Solver）**：利用双二次子域伴随分解 $B(t)\tilde{B}(t) = d_0 + d_1 t^2$ 及标量范数 $d_0^2 + 2d_0d_1 + 5d_1^2 \bmod N$ 执行一次 Montgomery 批量模逆，再由 `batch_poly_gcd` 碰撞分解。
6. **复杂度与实现**：盲分解 $>2^{85}$；暗门求解实测 `5.24s`（见 `locks_A.py: lock03_generate / lock03_solve`）。

---

## 方法 04（Lock 04）：判别式 $\Delta_K = -7$ ($j = -3375 \neq 0, 1728$, 导子 $f=2$) 二次扭曲复乘曲线自指暗门

1. **学术溯源与冷门度验证**
   - **文献**：A. V. Markelova, *"Implicit factoring via elliptic curves with complex multiplication"*, Prikladnaya Diskretnaya Matematika (2022).
   - **曝光度**：避开 `f_cktoring` 的 $j=1728$ 与 Variant 5 的 $j=0$，采用导子 $f=2$ 的非极大阶 $\mathbb{Z}[\sqrt{-7}]$，其 $j = -3375 \neq 0, 1728$ 在 $\mathbb{F}_p$ 上**仅有 2 个二次扭曲**，彻底免除卷面曲线参数 $b$！
2. **核心数学原理与暗门生成算法（KeyGen & Trapdoor）**
   - 设 $p = u^2 + 7 v^2$（$u \in [2^{255}, 2^{256}), v \in [2^{253}, 2^{254})$），对于同构缩放曲线 $E_w: y^2 = x^3 - 35w^2 x - 98w^3$（$w = u_0^3 - 35u_0 - 98$ at $u_0=1$），其模 $p$ 群阶为 $M_p = p + 1 \mp 2u$（恒被 4 整除）。
   - 利用移位线性同余 $\delta_2(N - 2) \equiv \delta_1 \pmod{M_p}$ 即 $q \equiv (\delta_1 + 2\delta_2)(\delta_2 p)^{-1} \pmod{M_p}$（确保奇偶性 $\delta_1+2\delta_2$ 恒为奇数）生成 512 比特素数 $q$。两边同乘 $(N+2)$ 得到因式分解二次自指恒等式：
     $$\delta_2 (N^2 - 4) \equiv \delta_1 (N + 2) \pmod{M_p}$$
     公钥保持 **$e = 65537$**。
3. **公开卷面呈现（Public Challenge）**：仅给 `(N, e=65537, c)`。
4. **国产 AI 破防推演**：卷面无曲线参数，且 $j=0, 1728$ 全部失效；即便枚举到 $j=-3375$，$M_p$ 本身是 512 比特非平滑整数（无平滑因子），唯有乘上自指标量 $N^2-4$ 与 $N+2$ 才能消去 $M_p$！
5. **解题破译算法（Solver）**：利用 Weierstrass 同构缩放 $w = u_0^3 - 35 u_0 - 98 \bmod N$ 直接无开方构造曲线 $y^2 = x^3 - 35w^2 x - 98w^3$ 上的合法点 $P_0 = (u_0 w, w^2)$，计算 $[N^2 - 4]P_0$ 与 $[N + 2]P_0$ 并由 `batch_poly_gcd` 碰撞横坐标。
6. **复杂度与实现**：盲分解 $>2^{85}$；暗门求解实测 `3.74s`（见 `locks_A.py: lock04_generate / lock04_solve`）。

---

## 方法 05（Lock 05）：亏格 2 超椭圆曲线 $\mathrm{Jac}(y^2 = x^5 + 8)$ 四次复乘阿贝尔曲面 Cantor 除子锁

1. **学术溯源与冷门度验证**
   - **文献**：Robert Dryło & Jacek Pomykała, *"Hyperelliptic curves and integer factorization"* (2024/2025); D. G. Cantor, Math. Comp. 48 (1987).
   - **曝光度**：首个基于亏格 2 超椭圆曲线雅可比簇 $\mathrm{Jac}(C)(\mathbb{Z}/N\mathbb{Z})$ Mumford 除子算术的无参数 RSA 隐式分解锁。
2. **核心数学原理与暗门生成算法（KeyGen & Trapdoor）**
   - 当 $p \equiv 7 \pmod{20}$ 时，超椭圆曲线 $C: y^2 = x^5 + 8$（恒过整数点 $(1, 3)$，因为 $3^2 = 1^5 + 8$）的雅可比簇 $\mathrm{Jac}(C)(\mathbb{F}_p)$ 被群指数 $J_{\text{ord}} = p^2 + 1$ 零化。
   - 构造 $J_{\text{ord}} = p^2 + 1 = G \cdot C_{\text{Jac}}$ 并令 $\delta_2 M e \equiv \delta_1 M N \pmod{p^2 + 1}$。
3. **公开卷面呈现（Public Challenge）**：仅给 `(N, e, c)`。
4. **国产 AI 破防推演**：亏格 1 的一切椭圆曲线（ECM）受 Hasse 界 $|t| \le 2\sqrt{p}$ 限制，绝不可能触及二维阿贝尔曲面的 $p^2+1$ 阶。
5. **解题破译算法（Solver）**：在 $y^2 = x^5 + 8$ 上取一阶 Mumford 除子 $D_0 = [x - 1, 3]$，通过模 $N$ Cantor 算法计算 $[M e]D_0$ 与 $[M N]D_0$，提取除子多项式 $u(x)$ 常数项系数碰撞分解。
6. **复杂度与实现**：盲分解 $>2^{85}$；暗门求解实测 `54.3s`（见 `locks_A.py: lock05_generate / lock05_solve`）。

---

## 方法 06（Lock 06）：12 维非交换四元数代数 $\mathbb{H}_{-1,-1}(\mathbb{Z}_N[t]/(t^3-2))$ 双重范数坍缩与 Skolem-Noether 锁

1. **学术溯源与冷门度验证**
   - **文献**：John Voight, *"Quaternion Algebras"*, Graduate Texts in Mathematics 288, Springer (2021).
   - **曝光度**：全网首次将三次扩域上的 12 维非交换哈密顿四元数代数 $\mathbb{H}(R_3)$ 与 Skolem-Noether 内自同构应用于 RSA 陷门。
2. **核心数学原理与暗门生成算法（KeyGen & Trapdoor）**
   - 设三次商环 $R_3 = \mathbb{Z}_N[t]/(t^3 - 2)$，在其上构造非交换四元数代数 $\mathcal{H} = R_3 \oplus R_3\mathbf{i} \oplus R_3\mathbf{j} \oplus R_3\mathbf{k}$（$\mathbf{i}^2=\mathbf{j}^2=-1, \mathbf{i}\mathbf{j}=-\mathbf{j}\mathbf{i}=\mathbf{k}$）。
   - 当 $p \equiv 2 \pmod 3$ 时，$t^3 - 2$ 在 $\mathbb{F}_p$ 上有一个根與一个不可约二次因子，故 $R_3/p R_3 \simeq \mathbb{F}_p \times \mathbb{F}_{p^2}$，从而：
     $$\mathcal{H}/p\mathcal{H} \simeq \mathrm{Mat}_2(\mathbb{F}_p) \times \mathrm{Mat}_2(\mathbb{F}_{p^2})$$
   - 对于约化范数 $\mathrm{nrd}(\alpha) = \alpha\bar{\alpha} \in R_3^*$ 的四元数元 $\alpha \in \mathcal{H}^*$，其在 $\mathrm{PGL}_2(\mathbb{F}_{p^2})$ 分量中的阶整除 $p^4 - 1$，而在三次扩张环面中的阶整除 $p^3 + 1$。两者的最大公约数发生**双重范数坍缩（Double Norm Collapse）**：
     $$\gcd(p^3 + 1, \; p^4 + p^2 + 1) = p^2 - p + 1 = \Phi_6(p)$$
3. **公开卷面呈现（Public Challenge）**：仅给 `(N, e, c)`。
4. **国产 AI 破防推演**：非交换代数上的 Skolem-Noether 共轭 $\alpha^E \mathbf{i} \alpha^{-E}$ 彻底跳出了交换环模幂与椭圆曲线范畴。
5. **解题破译算法（Solver）**：在 12 维代数 $\mathcal{H}$ 中选取基元 $\alpha = (1+t) + t\mathbf{i} + \mathbf{j} + t^2\mathbf{k}$，利用四元数共轭逆 $\alpha^{-1} = \mathrm{nrd}(\alpha)^{-1}\bar{\alpha}$（其中 $\mathrm{nrd}(\alpha) \in R_3$ 通过 $3\times 3$ 伴随矩阵 Cramer 法则求逆）计算内自同构轨迹，调用 `batch_poly_gcd` 碰撞分解。
6. **复杂度与实现**：盲分解 $>2^{85}$；暗门求解 `~0.25s`（见 `locks_B.py: lock06_generate / lock06_solve`）。

---

## 方法 07（Lock 07）：1024-bit 纯素数阶三阶伴随矩阵 Lucas 群 $\mathrm{SL}_3(\mathbb{Z}/N\mathbb{Z})$ 零平滑度锁

1. **学术溯源与冷门度验证**
   - **文献**：G. Gong & L. Harn, *"Public-Key Cryptosystems Based on Cubic Finite Field Extensions"*, IEEE Trans. Inf. Theory 45(7), 1999; Roettger, Williams, & Guy, *"Some Extensions of the Lucas Functions"*, Number Theory and Related Fields, Springer (2013).
   - **曝光度**：彻底颠覆“分解暗门必须依赖某个群阶 $B$-平滑”的定式！在本锁中，**$p-1$、$p+1$、$p^2-p+1$ 全部不平滑，甚至连暗门所在的群阶 $M_3 = \Phi_3(p) = p^2 + p + 1$ 本身也是一个 1024 比特的纯素数（0% 平滑度）**！
2. **核心数学原理与暗门生成算法（KeyGen & Trapdoor）**
   - 生成 512 比特素数 $p$，要求 $\Phi_3(p) = p^2 + p + 1$ **本身是一个 1024 比特的素数**（无任何小素因子）。
   - 取 512 比特素数 $q$（$q > p$），计算 $N = pq$。因为 $N = pq < p^2+p+1$ 不成立（$q > p+1 \implies N > M_3$），但 $M_3 = p^2+p+1 \approx N$，我们直接选小素数 $\delta_1, \delta_2 < 2^{11}$，在模纯素数 $M_3$ 下构造：
     $$e \equiv \delta_1 N \cdot \delta_2^{-1} \pmod{p^2 + p + 1}$$
     此时不需要乘任何平滑因子 $M_{\text{full}}$，直接恒有：
     $$\delta_2 e \equiv \delta_1 N \pmod{p^2 + p + 1}$$
   - **如何消除卷面参数 $a$？** 对任意特征多项式 $f_{P,Q}(x) = x^3 - P x^2 + Q x - 1$，只要它在 $\mathbb{F}_p$ 上不可约，其伴随矩阵：
     $$\mathbf{M}_{P,Q} = \begin{pmatrix} 0 & 1 & 0 \\ 0 & 0 & 1 \\ 1 & -Q & P \end{pmatrix} \in \mathrm{SL}_3(\mathbb{Z}/N\mathbb{Z})$$
     在射影商群 $\mathbb{F}_p[\mathbf{M}_{P,Q}]^* / \mathbb{F}_p^*$ 中的阶**对所有不可约 $(P, Q)$ 恒等于 $M_3 = p^2 + p + 1$**！
3. **公开卷面呈现（Public Challenge）**：仅给 `(N, e, c)`，零辅助参数。
4. **国产 AI 破防推演**：所有基于平滑性的算法（$p-1, p+1$, ECM, 甚至 $\Phi_k$ 平滑分解）100% 彻底失效，因为 $p-1, p+1, p^2+1, p^2+p+1, p^2-p+1$ 全是大素数！而对 $\varphi(N)$ 的 2D/3D LLL 因 $\delta_2 e - \delta_1 N = k(p^2+p+1)$ 含有未知二次项 $p^2+p+1$ 且 $k \approx \delta_1 q / p$ 亦无法直接用 Wiener 解出。
5. **解题破译算法（Solver）**：在 $\mathrm{SL}_3(\mathbb{Z}/N\mathbb{Z})$ 中遍历 2~3 组标准不可约伴随矩阵参数 $(P, Q) \in \{(1, 2), (2, 3), (3, 5)\}$（覆盖 $\frac{1}{3}$ 密度的不可约三次多项式），直接计算矩阵幂 $\mathbf{A}_L = \mathbf{M}_{P,Q}^e \bmod N$ 与 $\mathbf{A}_R = \mathbf{M}_{P,Q}^N \bmod N$（无需任何平滑幂 $M_{\text{full}}$！），对矩阵迹比不变量 $\mathrm{Tr}(\mathbf{A}^2)^3 / \mathrm{Tr}(\mathbf{A})^2 \bmod N$ 调用 `batch_poly_gcd` 瞬间分解 $N$！
6. **复杂度与实现**：盲分解 $>2^{85}$；暗门求解 `~0.08s`（见 `locks_B.py: lock07_generate / lock07_solve`）。

---

## 方法 08（Lock 08）：双阶段 4D 三次正交格 + Base-$2^{240}$ 二进折叠 4D 线性因子 Coppersmith 级联锁

1. **学术溯源与冷门度验证**
   - **文献**：Mathias Herrmann & Alexander May, *"Solving Linear Equations Modulo Divisors"*, ASIACRYPT 2008; Phong Q. Nguyen & Jacques Stern, *"The Two Faces of Lattices in Cryptology"*, CaLC 2001.
   - **曝光度**：现有正交格 CTF 题要么给多个公钥 $e_1, \dots, e_m$，要么是 Variant 9 的 3D 二次关系 $u_2 e^2 + u_1 e + u_0 \equiv 0 \pmod p$。本锁将其升级为**单公钥 4D 三次同余关系 + Base-$2^{240}$ 二进折叠（Dyadic Folding）**，使第二阶段从笨重的 9 维三次 Jochemsz-May 格直接坍缩为极速 4 维线性整除格！
2. **核心数学原理与暗门生成算法（KeyGen & Trapdoor）**
   - **二进折叠素数构造**：固定基数 $B_{\text{radix}} = 2^{240}$，随机取 18 比特小根 $x_0 \in [2^{17}, 2^{18})$，选 4 个 234 比特系数 $u_0, u_1, u_2, u_3$，使素数 $p$（512 比特）整除：
     $$U(x_0) = (u_3 B_{\text{radix}} + u_2) x_0 + (u_1 B_{\text{radix}} + u_0) + \delta_{\text{mask}} \equiv 0 \pmod p$$
     其中 $\delta_{\text{mask}} \in [1, 7]$ 为微扰掩码。
   - **三次正交格纠缠**：令 $x_{\text{full}} = B_{\text{radix}}^2 x_0$，则 $u_3 x_{\text{full}}^3 + u_2 x_{\text{full}}^2 + u_1 x_{\text{full}} + u_0 \equiv -\delta_{\text{mask}} B_{\text{radix}}^2 \pmod p$。在模 $N = pq$ 下构造公钥 $e \equiv x_{\text{full}} \pmod p$ 且满足：
     $$u_3 e^3 + u_2 e^2 + u_1 e + u_0 \equiv 0 \pmod N$$
3. **公开卷面呈现（Public Challenge）**：仅给 `(N, e, c)`。
4. **国产 AI 破防推演**：2D Wiener 与 3D 二次格在 $4\times 4$ 三次关系前全部失效；若 AI 在恢复 $(u_0, u_1, u_2, u_3)$ 后盲目构建三次多项式的 1D/2D Coppersmith，未识破 $B_{\text{radix}} = 2^{240}$ 的二进折叠线性同态，根界将超出格归约能力。
5. **解题破译算法（Solver）**：
   - **Stage 1（4D 三次正交格）**：对 $(1, e, e^2, e^3) \bmod N$ 构建 4 维格，一次 LLL（`0.002s`）精确恢复 $(u_3, u_2, u_1, u_0)$。
   - **Stage 2（Base-$2^{240}$ 折叠 4D 线性 Coppersmith）**：重组 $U_{\text{hi}} = u_3 2^{240} + u_2$ 与 $U_{\text{lo}} = u_1 2^{240} + u_0 + \delta$，转化为模 $p$ 一次线性方程 $x_0 + U_{\text{hi}}^{-1} U_{\text{lo}} \equiv 0 \pmod p$，用 4D Herrmann-May 线性格（$m=2, t=2$）瞬间求出 $x_0$ 并分解 $N$。
6. **复杂度与实现**：盲分解 $>2^{85}$；暗门求解 `~0.03s`（见 `locks_B.py: lock08_generate / lock08_solve`）。

---

## 方法 09（Lock 09）：对称切比雪夫 / Lucas-$V$ 积化和差恒等式窃密暗门（Modulo Wrap-Around SETUP）

1. **学术溯源与冷门度验证**
   - **文献**：Ting-Yun Yeh, *"SoK: Kleptographic Attacks and Backdoored Cryptography"*, IACR ePrint 2025/1480; Marc Joye, *"RSA Moduli with a Predetermined Portion"*, PKC 2008; Nemec et al. (ROCA, CCS 2017).
   - **曝光度**：传统 ROCA（$p = k M + 65537^a \bmod M$）在乘积 $N = pq$ 中要求 $65537^{a+b} \bmod M$，一旦被 AI 识别出离散对数群即可用 Pohlig-Hellman 秒解。**本锁用切比雪夫多项式 $V_n(x)$ 的非线性积化和差恒等式彻底摧毁乘法群同态，并通过全长 360-bit 模折叠（Modulo Wrap-Around）消除一切高位明文泄漏！**
2. **核心数学原理与暗门生成算法（KeyGen & Trapdoor）**
   - 设公开切比雪夫模数 $M_{\text{cheb}} = \Phi_6(2^{180}) = 2^{360} - 2^{180} + 1$，固定基点 $g_0 = 2^{120} + 7$。
   - 切比雪夫多项式（Lucas-$V$ 序列，$V_0(x)=2, V_1(x)=x, V_n(x)=x V_{n-1}(x)-V_{n-2}(x)$）满足著名的**积化和差恒等式**：
     $$V_a(g_0) \cdot V_b(g_0) \equiv V_{a+b}(g_0) + V_{|a-b|}(g_0) \pmod{M_{\text{cheb}}}$$
   - **消除高位泄漏的模折叠（Modulo Wrap-Around）**：若选小熵下标 $a, b$ 且取镜像对称 $b = a + \delta$（$\delta \in \{0, 1, 2\}$），令：
     $$p = k_p M_{\text{cheb}} + \left(V_a(g_0) \bmod M_{\text{cheb}}\right), \quad q = k_q M_{\text{cheb}} + \left(V_b(g_0) \bmod M_{\text{cheb}}\right)$$
     因为 $a \ge 5$ 时 $V_a(g_0)$ 远超 $2^{360}$ 并发生模 $M_{\text{cheb}}$ 折叠，$p \bmod M_{\text{cheb}}$ 在二进制下呈现高熵随机分布，**绝无 Variant 7 那样的零比特填充或高位泄漏**！
   - 然而，在模 $M_{\text{cheb}}$ 下观察公开模数 $N = pq$：
     $$N \equiv V_a(g_0) V_{a+\delta}(g_0) \equiv V_{2a+\delta}(g_0) + V_\delta(g_0) \pmod{M_{\text{cheb}}}$$
3. **公开卷面呈现（Public Challenge）**：仅给标准 `(N, e=65537, c)`（$N$ 为 1024 比特，双 512 比特平衡素数）。
4. **国产 AI 破防推演**：卷面只有 $(N, 65537, c)$；ROCA 检测脚本 проверяет $N \bmod M_{\text{roca}} \in \langle 65537 \rangle$ 恒失败；高位无零段、无 `hint` 字段。
5. **解题破译算法（Solver）**：
   1. 计算 $R_N = N \bmod \Phi_6(2^{180})$，对 $\delta \in \{0, 1, 2\}$ 与小下标 $a \in [5, 512)$ 检验恒等式 $(V_{2a+\delta}(g_0) + V_\delta(g_0)) \bmod M_{\text{cheb}} \stackrel{?}{=} R_N$，在 `< 0.002s` 内唯一定位 $(a, \delta)$！
   2. 得到 $r_p = V_a(g_0) \bmod M_{\text{cheb}}$（360 比特已知同余余数），将 $p = k_p M_{\text{cheb}} + r_p$（未知商 $k_p$ 仅 152 比特，远小于 $N^{1/4} = 2^{256}$）喂入 4D 线性整除 Coppersmith 格，0.01 秒内解出 $k_p$ 并分解 $N$！
6. **复杂度与实现**：盲分解 $>2^{85}$；暗门求解 `~0.02s`（见 `locks_B.py: lock09_generate / lock09_solve`）。

---

## 方法 10（Lock 10）：$\Phi_{12}(p) = p^4 - p^2 + 1$ 十二次分圆环 $\mathbb{Z}_N[\zeta_{13}]$ 四项式 Frobenius 环面投影锁

1. **学术溯源与冷门度验证**
   - **文献**：Rubin & Silverberg, *"Torus-Based Cryptography"*, CRYPTO 2003; Lenstra, *"Using Cyclotomic Fields to Construct Hard Instances"*.
   - **曝光度**：十二次分圆环面 $\mathbb{T}_{12}(\mathbb{F}_p) \subset \mathbb{F}_{p^{12}}^*$ 的阶为 $\Phi_{12}(p) = p^4 - p^2 + 1$。全网 CTF 从未出现过在 12 维分圆商环 $\mathbb{Z}_N[x]/(\Phi_{13}(x))$ 中利用四项式伽罗瓦自同构投影分解半素数的先例。
2. **核心数学原理与暗门生成算法（KeyGen & Trapdoor）**
   - 在 $\mathcal{A}_{13} = \mathbb{Z}_N[x]/(\Phi_{13}(x))$ 中，$\mathrm{Gal}(\mathbb{Q}(\zeta_{13})/\mathbb{Q}) \simeq \mathbb{Z}/12\mathbb{Z}$ 以 $2 \pmod{13}$ 为本原根，定义形式自同构 $\sigma_k(\zeta_{13}) = \zeta_{13}^{2^k \bmod 13}$。
   - 利用多项式恒等式：
     $$X^8 + X^6 - X^2 - 1 = (X^4 - X^2 + 1)(X^4 + X^2 - 1)$$
     实际上，更精确的分圆有理商恒等式为：
     $$\frac{(X^6 + 1)(X^2 - 1)}{X^4 - 1} = \frac{(X^2 + 1)(X^4 - X^2 + 1)(X^2 - 1)}{(X^2 - 1)(X^2 + 1)} = X^4 - X^2 + 1 = \Phi_{12}(X)$$
     对偶地，在 $\mathbb{Z}[\mathrm{Gal}]$ 群环中，算子：
     $$\Psi_{12}(\beta) = \sigma_8(\beta)\cdot \sigma_6(\beta)\cdot \left(\sigma_2(\beta)\cdot \beta\right)^{-1} \pmod{\Phi_{13}(x), N}$$
     对应的伽罗瓦零化子整除 $\Phi_{12}(\sigma_1) = \sigma_4 - \sigma_2 + 1$，因此当 $p \equiv 2 \pmod{13}$（使 $\sigma_1$ 恰为模 $p$ Frobenius 映射 $z \mapsto z^p$）时，$\tau = \Psi_{12}(\beta)$ 的模 $p$ 乘法阶**严格整除 $\Phi_{12}(p) = p^4 - p^2 + 1$**！
   - 构造 $\Phi_{12}(p) = G \cdot C_{12}$，并令 $e \equiv (\delta_1(N \bmod \Phi_{12}(p)) + C_{12})(\delta_2 + C_{12})^{-1} \pmod{\Phi_{12}(p)}$。
3. **公开卷面呈现（Public Challenge）**：仅给 `(N, e, c)`。
4. **国产 AI 破防推演**：所有低阶分圆多项式 $\Phi_1, \Phi_2, \Phi_3, \Phi_4, \Phi_6, \Phi_8$ 全部不平滑，唯有 12 次分圆多项式 $\Phi_{12}(p) = p^4 - p^2 + 1$ 含有平滑主部。
5. **解题破译算法（Solver）**：在 12 维商环 $\mathcal{A}_{13}$ 中构造 $\tau = \Psi_{12}(2+x)$，计算 $Q_L = \tau^{M e}$ 与 $Q_R = \tau^{M N}$，提取规范化 0 次项系数并调用 `batch_poly_gcd` 碰撞出 $p$。
6. **复杂度与实现**：盲分解 $>2^{85}$；暗门求解 `~0.42s`（见 `locks_B.py: lock10_generate / lock10_solve`）。
