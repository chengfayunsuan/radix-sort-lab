"""
主窗口
======

把各个模块拼起来，并处理所有按钮事件。

界面只做三件事：
  1. 根据当前快照下标，把快照交给舞台视图去画；
  2. 把用户的点击翻译成"下标 +1 / -1 / 跳到下一轮"；
  3. 自动播放时用 after() 定时推进，绝不能用 time.sleep()——否则界面会假死。

关于动画
--------
每一步动作都伴随一张卡片在画布上移动：分配时从数组飞进桶，收集时从桶飞回数组。

关键在于"起点画面"的选取。如果直接在上一帧上叠一个飞行卡片，源位置会凭空多出
一张卡（看起来像复制了一份）。所以飞行期间要画一个**混合画面**：

    分配：数组用上一帧、并藏起那个数；桶用这一帧、并藏起目标槽位
    收集：数组用这一帧、并藏起目标格子；桶用上一帧、并藏起即将取出的那张

两端都空着，飞行卡片正好补上这个空缺，视觉上就是"拿起来、放过去"。

所有排序逻辑都在 core/radix_engine.py 里，这里一行算法都没有。
"""

import tkinter as tk
from dataclasses import replace

from core.data_gen import generate, max_digits
from core.radix_engine import RadixEngine

from .side_panel import SidePanel
from .stage_view import StageView
from .theme import COLORS, build_fonts

WIN_W = 1280
WIN_H = 800

DEFAULT_N = 20
MIN_N, MAX_N = 10, 20


class RadixApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("基数排序可视化 · Radix Sort Lab")
        self.root.configure(bg=COLORS["bg"])
        self.root.geometry(self._center_geometry())
        self.root.resizable(False, False)

        self.fonts = build_fonts(root)

        self.engine: RadixEngine | None = None
        self.index = 0
        self.digits = 4
        self.playing = False
        self.animating = False
        self.logged: set[int] = set()
        self._tick_job = None

        self._build_ui()
        self._bind_keys()
        self.new_data()

    # ------------------------------------------------------------------
    def _center_geometry(self) -> str:
        """把窗口放到屏幕中央偏上一点，投影时不会被任务栏挡住。"""
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        x = max(0, (sw - WIN_W) // 2)
        y = max(0, (sh - WIN_H) // 2 - 30)
        return f"{WIN_W}x{WIN_H}+{x}+{y}"

    # ------------------------------------------------------------------
    # 界面搭建
    # ------------------------------------------------------------------
    def _build_ui(self):
        self._build_header()

        body = tk.Frame(self.root, bg=COLORS["bg"])
        body.pack(fill="both", expand=True, padx=20, pady=(4, 0))
        # 用 grid 而不是 pack，是为了把左区宽度钉死在画布宽度、右区钉死在 300，
        # 否则 pack 会让左侧把右侧挤窄，卡片位置随之全部偏移。
        body.grid_columnconfigure(0, weight=1)
        body.grid_rowconfigure(0, weight=1)

        # 数组和桶合并成一张画布（见 stage_view 的说明），这样卡片才能在两区之间飞
        self.stage = StageView(body, self.fonts)
        self.stage.grid(row=0, column=0, sticky="nw")

        self.side = SidePanel(body, self.fonts)
        self.side.grid(row=0, column=1, sticky="ns", padx=(16, 0))

        self._build_status_bar()

    def _build_header(self):
        header = tk.Frame(self.root, bg=COLORS["header"], height=68)
        header.pack(fill="x")
        header.pack_propagate(False)

        tk.Frame(self.root, bg=COLORS["border"], height=1).pack(fill="x")

        left = tk.Frame(header, bg=COLORS["header"])
        left.pack(side="left", padx=(22, 0), pady=14)

        tk.Label(
            left, text="基数排序可视化", font=self.fonts["title"],
            fg=COLORS["text"], bg=COLORS["header"], anchor="w",
        ).pack(anchor="w")
        tk.Label(
            left, text="LSD Radix Sort · 从个位到高位，每一轮分配后收集",
            font=self.fonts["small"], fg=COLORS["text_dim"],
            bg=COLORS["header"], anchor="w",
        ).pack(anchor="w")

        right = tk.Frame(header, bg=COLORS["header"])
        right.pack(side="right", padx=(0, 22), pady=16)

        # ---- 数据量输入 ----
        tk.Label(
            right, text="数据个数", font=self.fonts["small"],
            fg=COLORS["text_sub"], bg=COLORS["header"],
        ).pack(side="left", padx=(0, 6))

        self.n_entry = tk.Entry(
            right, width=3, font=self.fonts["body"], justify="center",
            relief="solid", bd=1, bg=COLORS["card"], fg=COLORS["text"],
        )
        self.n_entry.insert(0, str(DEFAULT_N))
        self.n_entry.pack(side="left", padx=(0, 8), ipady=3)
        self.n_entry.bind("<Return>", lambda e: self.new_data())

        self._button(right, "生成数据", self.new_data, primary=True).pack(side="left", padx=(0, 12))

        # ---- 播放控制 ----
        self.btn_reset = self._button(right, "重置", self.reset)
        self.btn_reset.pack(side="left", padx=2)

        self.btn_prev = self._button(right, "上一步", self.step_back)
        self.btn_prev.pack(side="left", padx=2)

        self.btn_next = self._button(right, "单步", self.step_forward, primary=True)
        self.btn_next.pack(side="left", padx=2)

        self.btn_play = self._button(right, "自动播放", self.toggle_play)
        self.btn_play.pack(side="left", padx=2)

        self.btn_round = self._button(right, "下一轮", self.jump_next_round)
        self.btn_round.pack(side="left", padx=(2, 10))

        # ---- 速度 ----
        tk.Label(
            right, text="速度", font=self.fonts["small"],
            fg=COLORS["text_sub"], bg=COLORS["header"],
        ).pack(side="left", padx=(0, 5))

        # 滑块外面套一层带描边的 Frame：Scale 自己的 highlight 只在获得焦点时显示，
        # 平时是看不见的，加一圈边框才能让它在白底顶栏上有个明确的边界。
        speed_box = tk.Frame(
            right, bg=COLORS["card"],
            highlightbackground=COLORS["border_dark"], highlightthickness=1, bd=0,
        )
        speed_box.pack(side="left")

        self.speed = tk.Scale(
            speed_box, from_=1, to=10, orient="horizontal", length=68,
            showvalue=False, bg=COLORS["card"], highlightthickness=0,
            troughcolor=COLORS["border"], sliderrelief="flat", bd=0,
            activebackground=COLORS["primary"], sliderlength=15, width=9,
            borderwidth=0,
        )
        self.speed.set(6)
        self.speed.pack(padx=3, pady=2)

    def _button(self, parent, text, command, primary=False):
        """统一样式的扁平按钮。primary 为真时用实心主色。"""
        if primary:
            bg, fg, active_bg = COLORS["primary"], "#FFFFFF", COLORS["primary_dk"]
            disabled_fg = "#9CC3E8"          # 深蓝底上的浅色，保证禁用时仍可读
        else:
            bg, fg, active_bg = COLORS["card"], COLORS["text"], COLORS["bucket_bg"]
            disabled_fg = COLORS["text_dim"]

        return tk.Button(
            parent, text=text, command=command,
            font=self.fonts["body"],
            bg=bg, fg=fg, activebackground=active_bg,
            activeforeground=fg,
            disabledforeground=disabled_fg,
            relief="flat", bd=0, padx=9, pady=5,
            cursor="hand2",
            highlightthickness=1,
            highlightbackground=COLORS["border"] if not primary else bg,
            highlightcolor=COLORS["border"] if not primary else bg,
        )

    def _build_status_bar(self):
        bar = tk.Frame(self.root, bg=COLORS["card"], height=36)
        bar.pack(fill="x", side="bottom")
        bar.pack_propagate(False)

        tk.Frame(bar, bg=COLORS["border"], height=1).pack(fill="x", side="top")

        self.status_label = tk.Label(
            bar, text="", font=self.fonts["body"],
            fg=COLORS["text_sub"], bg=COLORS["card"], anchor="w",
        )
        self.status_label.pack(side="left", padx=20, pady=6)

        tk.Label(
            bar, text="← → 单步　空格 播放/暂停", font=self.fonts["small"],
            fg=COLORS["text_dim"], bg=COLORS["card"], anchor="e",
        ).pack(side="right", padx=20)

    def _bind_keys(self):
        self.root.bind("<Right>", lambda e: self.step_forward())
        self.root.bind("<Left>", lambda e: self.step_back())
        self.root.bind("<space>", lambda e: self.toggle_play())

    # ------------------------------------------------------------------
    # 数据与播放控制
    # ------------------------------------------------------------------
    def new_data(self):
        """重新生成一组随机数据，并从第一步开始。"""
        self._cancel_all()

        try:
            n = int(self.n_entry.get())
        except ValueError:
            n = DEFAULT_N

        n = max(MIN_N, min(MAX_N, n))
        self.n_entry.delete(0, "end")
        self.n_entry.insert(0, str(n))

        data = generate(n)
        self.digits = max_digits(data)
        self.engine = RadixEngine(data)
        self.index = 0
        self.logged.clear()

        self.btn_play.config(text="自动播放")
        self.side.clear_log()
        self.side.append_log("生成 %d 个数据，最大 %d 位" % (n, self.digits), "phase")
        self.render()

    def reset(self):
        """回到第一步，不清空数据。"""
        if not self.engine:
            return
        self._cancel_all()
        self.index = 0
        self.logged.clear()
        self.side.clear_log()
        self.side.append_log("已重置到起点", "phase")
        self.render()

    def step_forward(self):
        if not self.engine or self.animating:
            return
        last = self.engine.stats.total_steps - 1
        if self.index >= last:
            self._stop_play()
            return
        self._advance(self.index + 1)

    def step_back(self):
        if not self.engine:
            return
        self._stop_play()
        self.stage.cancel_fly()
        self.animating = False
        if self.index > 0:
            self.index -= 1
            self.render()

    def jump_next_round(self):
        """直接跳到下一轮的结束帧，方便答辩时快速过场。"""
        if not self.engine:
            return
        self._stop_play()
        self.stage.cancel_fly()
        self.animating = False
        for end_idx in self.engine.round_end_indices():
            if end_idx > self.index:
                self.index = end_idx
                self.render()
                return
        self.index = self.engine.stats.total_steps - 1
        self.render()

    def toggle_play(self):
        if not self.engine:
            return
        if self.playing:
            self._stop_play()
        else:
            if self.index >= self.engine.stats.total_steps - 1:
                self.index = 0
                self.render()
            self.playing = True
            self.btn_play.config(text="暂停")
            self._tick()

    def _stop_play(self):
        self.playing = False
        if self._tick_job is not None:
            self.root.after_cancel(self._tick_job)
            self._tick_job = None
        if hasattr(self, "btn_play"):
            self.btn_play.config(text="自动播放")

    def _cancel_all(self):
        """停播 + 打断动画，重置数据和换数据前都要先做这一步。"""
        self._stop_play()
        self.stage.cancel_fly()
        self.animating = False

    # ---- 速度换算 ----------------------------------------------------
    def _interval_ms(self) -> int:
        """速度滑块 1~10 映射到 900ms ~ 90ms 的单步间隔。"""
        v = int(self.speed.get())
        return int(900 - (v - 1) * 90)

    def _anim_ms(self) -> int:
        """单次飞行动画的时长：慢速 250ms，最快 106ms。"""
        v = int(self.speed.get())
        return int(250 - (v - 1) * 16)

    # ---- 推进 --------------------------------------------------------
    def _tick(self):
        self._tick_job = None
        if not self.playing:
            return
        if self.index >= self.engine.stats.total_steps - 1:
            self._stop_play()
            return
        self._advance(self.index + 1, on_done=self._schedule_next)

    def _schedule_next(self):
        if not self.playing:
            return
        # 动画已经占掉一部分时间，间隔要相应扣掉，否则高速时会明显变卡
        gap = max(30, self._interval_ms() - self._anim_ms())
        self._tick_job = self.root.after(gap, self._tick)

    # ------------------------------------------------------------------
    # 带动画的一步
    # ------------------------------------------------------------------
    def _advance(self, target, on_done=None):
        if self.engine is None:
            return

        plan = self._fly_plan(target)
        if plan is None:
            self.index = target
            self.render()
            if on_done:
                on_done()
            return

        arr_snap, bkt_snap, hide_arr, hide_bkt, p0, p1 = plan

        self.stage.render(
            self.engine.get(target), self.digits,
            arr_snap=arr_snap, bkt_snap=bkt_snap,
            hide_array=hide_arr, hide_bucket=hide_bkt,
        )

        self.animating = True
        nxt = self.engine.get(target)
        self.stage.fly(
            p0, p1, nxt.active_value, self.digits,
            self._anim_ms(), nxt.digit_pos,
            on_done=lambda: self._land(target, on_done),
        )

    def _fly_plan(self, target):
        """
        决定这一步能不能做飞行动画，以及飞行的起终点。

        返回 (数组用哪一帧, 桶用哪一帧, 数组要藏的下标, 桶要藏的槽位, 起点, 终点)
        返回 None 表示这一步不动画（初始化、换轮、结束这些帧）。
        """
        prev = self.engine.get(target - 1) if target > 0 else None
        nxt = self.engine.get(target)
        if prev is None or nxt.active_value is None:
            return None

        n = len(nxt.array)

        if nxt.phase == "distribute" and nxt.active_index >= 0:
            b = nxt.active_bucket
            k = len(nxt.buckets[b]) - 1
            if k < 0:
                return None
            # 数组沿用上一帧（那个数还在原位），桶用这一帧但把目标槽位留空。
            # 必须把上一帧的 active_index 清掉——否则数组里亮着的还是上一步那个数，
            # 观众会以为正在移动的是它，而不是飞在半路上的这一张。
            arr_show = replace(prev, active_index=-1, active_bucket=-1,
                               phase="distribute", digit_pos=nxt.digit_pos)
            p0 = self.stage.array.center(nxt.active_index, n)
            p1 = self.stage.bucket.center(b, min(k, 11))    # 超长桶会折叠，落点取最后一个可见槽位
            return arr_show, nxt, {nxt.active_index}, [(b, k)], p0, p1

        if nxt.phase == "collect" and nxt.active_index >= 0:
            b = nxt.active_bucket
            if not prev.buckets[b]:
                return None
            # 数组用这一帧（目标格子留空），桶用上一帧但把即将取出的那张留空。
            # 桶的高亮要跟着这一帧走，否则亮的是上一步那个桶。
            bkt_show = replace(prev, phase="collect", active_index=-1,
                               active_bucket=b, digit_pos=nxt.digit_pos)
            p0 = self.stage.bucket.center(b, 0)
            p1 = self.stage.array.center(nxt.active_index, n)
            return nxt, bkt_show, {nxt.active_index}, [(b, 0)], p0, p1

        return None

    def _land(self, target, on_done):
        self.animating = False
        self.index = target
        self.render()
        if on_done:
            on_done()

    # ------------------------------------------------------------------
    # 渲染
    # ------------------------------------------------------------------
    def render(self):
        snap = self.engine.get(self.index)

        self.stage.render(snap, self.digits)
        self.side.update_status(snap, self.engine)

        self.status_label.config(text=snap.message)

        if snap.step_no not in self.logged:
            self.logged.add(snap.step_no)
            if snap.phase in ("init", "round_end", "done"):
                tag = "done" if snap.phase == "done" else "phase"
            else:
                tag = "normal"
            self.side.append_log(f"[{snap.step_no:03d}] {snap.message}", tag)

        last = self.engine.stats.total_steps - 1
        self.btn_prev.config(state="normal" if self.index > 0 else "disabled")
        self.btn_next.config(state="normal" if self.index < last else "disabled")
