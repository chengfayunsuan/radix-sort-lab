"""
右侧信息栏
==========

从上到下三块：轮次徽章、过程统计、运行日志。

轮次徽章
--------
"现在第几轮"是整个演示最需要被看见的信息——观众一旦搞不清当前在哪一轮，
后面所有动作都看不懂。所以它不跟其他文字挤在一起，而是单独一张卡片，
用 19 号大字配一排进度点，坐在右栏最顶上。

统计里的"比较次数"是刻意做大的——因为基数排序全过程的比较次数**恒为 0**，
把 0 放大显示在屏幕上，比任何文字解释都更能说明"它和其他排序不是一类东西"。
"""

import tkinter as tk
from tkinter import ttk

from core.radix_engine import digit_name

from .theme import COLORS

PANEL_W = 300


class SidePanel(tk.Frame):
    def __init__(self, parent, fonts):
        super().__init__(parent, bg=COLORS["bg"], width=PANEL_W)
        self.fonts = fonts
        self.pack_propagate(False)

        self._build_round_badge()
        self._build_stats()
        self._build_log()

    # ------------------------------------------------------------------
    # 卡片容器：标题 + 带边框的白底区域，返回内部可放控件的 Frame
    # ------------------------------------------------------------------
    def _card(self, title, expand=False):
        outer = tk.Frame(self, bg=COLORS["bg"])
        outer.pack(fill="both" if expand else "x", expand=expand, pady=(0, 10))

        tk.Label(
            outer, text=title, font=self.fonts["small"],
            fg=COLORS["text_dim"], bg=COLORS["bg"], anchor="w",
        ).pack(fill="x", pady=(0, 4))

        box = tk.Frame(
            outer, bg=COLORS["card"],
            highlightbackground=COLORS["border"],
            highlightthickness=1,
        )
        box.pack(fill="both" if expand else "x", expand=expand)

        inner = tk.Frame(box, bg=COLORS["card"])
        inner.pack(fill="both", expand=True, padx=14, pady=12)
        return inner

    # ------------------------------------------------------------------
    # 轮次徽章
    # ------------------------------------------------------------------
    def _build_round_badge(self):
        outer = tk.Frame(self, bg=COLORS["bg"])
        outer.pack(fill="x", pady=(0, 10))

        tk.Label(
            outer, text="当前第几轮", font=self.fonts["small"],
            fg=COLORS["text_dim"], bg=COLORS["bg"], anchor="w",
        ).pack(fill="x", pady=(0, 4))

        box = tk.Frame(
            outer, bg=COLORS["badge_bg"],
            highlightbackground=COLORS["border_dark"],
            highlightthickness=1,
        )
        box.pack(fill="x")

        # 左侧强调竖条，把这张卡和下面几张区分开
        tk.Frame(box, bg=COLORS["primary"], width=4).pack(side="left", fill="y")

        inner = tk.Frame(box, bg=COLORS["badge_bg"])
        inner.pack(side="left", fill="both", expand=True, padx=13, pady=(8, 10))

        row = tk.Frame(inner, bg=COLORS["badge_bg"])
        row.pack(fill="x")

        self.round_big = tk.Label(
            row, text="准备", font=self.fonts["round"],
            fg=COLORS["primary"], bg=COLORS["badge_bg"], anchor="w",
        )
        self.round_big.pack(side="left")

        self.round_total = tk.Label(
            row, text="", font=self.fonts["small"],
            fg=COLORS["text_dim"], bg=COLORS["badge_bg"], anchor="e",
        )
        self.round_total.pack(side="right", pady=(8, 0))

        # 进度点：已完成 / 当前 / 未开始
        self.dots = tk.Canvas(
            inner, height=10, bg=COLORS["badge_bg"],
            highlightthickness=0, bd=0,
        )
        self.dots.pack(fill="x", pady=(7, 3))

        self.digit_label = tk.Label(
            inner, text="", font=self.fonts["body"],
            fg=COLORS["text_sub"], bg=COLORS["badge_bg"], anchor="w",
        )
        self.digit_label.pack(fill="x")

        self.phase_label = tk.Label(
            inner, text="", font=self.fonts["body"],
            fg=COLORS["primary"], bg=COLORS["badge_bg"], anchor="w",
        )
        self.phase_label.pack(fill="x")

    def _draw_dots(self, done, current, total):
        """画一排进度点：done 表示已完成的轮数，current 是当前轮（从 1 开始）。"""
        self.dots.delete("all")
        x = 1
        for i in range(total):
            if i + 1 == current:
                color = COLORS["active_line"]
                r = 5
            elif i + 1 <= done:
                color = COLORS["primary"]
                r = 4
            else:
                color = COLORS["border_dark"]
                r = 4
            cy = 5
            self.dots.create_oval(x, cy - r, x + r * 2, cy + r, fill=color, outline="")
            x += r * 2 + 7

    # ------------------------------------------------------------------
    def _build_stats(self):
        box = self._card("过程统计")

        grid = tk.Frame(box, bg=COLORS["card"])
        grid.pack(fill="x")

        self.cmp_value = self._stat(grid, "比较次数", "0", 0, 0,
                                    COLORS["active_line"], big=True)
        self.move_value = self._stat(grid, "元素移动", "0", 0, 1,
                                     COLORS["item_text"])
        self.step_value = self._stat(grid, "当前步数", "0 / 0", 1, 0,
                                     COLORS["text"])
        self.round_value = self._stat(grid, "总轮数", "0", 1, 1,
                                      COLORS["text"])

        tk.Label(
            box,
            text="基数排序不做大小比较，比较次数恒为 0。",
            font=self.fonts["small"], fg=COLORS["text_dim"],
            bg=COLORS["card"], anchor="w", justify="left", wraplength=240,
        ).pack(fill="x", pady=(6, 0))

    def _stat(self, parent, label_text, value_text, row, col, color, big=False):
        cell = tk.Frame(parent, bg=COLORS["card"])
        cell.grid(row=row, column=col, sticky="w", padx=(0, 10), pady=(0, 6))
        parent.grid_columnconfigure(col, weight=1)

        tk.Label(
            cell, text=label_text, font=self.fonts["small"],
            fg=COLORS["text_dim"], bg=COLORS["card"], anchor="w",
        ).pack(fill="x")

        value = tk.Label(
            cell, text=value_text,
            font=self.fonts["num"] if big else self.fonts["num_sm"],
            fg=color, bg=COLORS["card"], anchor="w",
        )
        value.pack(fill="x")
        return value

    # ------------------------------------------------------------------
    def _build_log(self):
        box = self._card("运行日志", expand=True)

        wrap = tk.Frame(box, bg=COLORS["card"])
        wrap.pack(fill="both", expand=True)

        self.log_text = tk.Text(
            wrap, font=self.fonts["mono"],
            bg=COLORS["card"], fg=COLORS["text_sub"],
            relief="flat", bd=0, wrap="word",
            height=8, width=10,
            spacing1=2, spacing3=2,
        )
        self.log_text.pack(side="left", fill="both", expand=True)

        bar = ttk.Scrollbar(wrap, command=self.log_text.yview)
        bar.pack(side="right", fill="y")
        self.log_text.configure(yscrollcommand=bar.set)

        self.log_text.tag_config("normal", foreground=COLORS["text_sub"])
        self.log_text.tag_config("phase", foreground=COLORS["primary"])
        self.log_text.tag_config("done", foreground=COLORS["active_text"])
        self.log_text.configure(state="disabled")

    # ------------------------------------------------------------------
    def update_status(self, snap, engine):
        total = engine.rounds

        if snap.phase == "init":
            self.round_big.config(text="准备", fg=COLORS["primary"])
            self.round_total.config(text=f"共 {total} 轮")
            self.digit_label.config(text="每轮处理一个数位")
            self.phase_label.config(text="从个位开始", fg=COLORS["primary"])
            self._draw_dots(0, 0, total)
        elif snap.phase == "done":
            self.round_big.config(text="完成", fg=COLORS["primary"])
            self.round_total.config(text=f"共 {total} 轮")
            self.digit_label.config(text="全部数位处理完毕")
            self.phase_label.config(text="排序结束", fg=COLORS["active_text"])
            self._draw_dots(total, 0, total)
        else:
            self.round_big.config(text=f"第 {snap.round_no} 轮", fg=COLORS["primary"])
            self.round_total.config(text=f"共 {total} 轮")
            self.digit_label.config(text=f"正在看：{digit_name(snap.digit_pos)}")

            if snap.phase == "round_end":
                phase_cn = "本轮结束"
            elif snap.phase == "distribute":
                phase_cn = "分配（进桶）"
            else:
                phase_cn = "收集（出桶）"
            self.phase_label.config(text=phase_cn, fg=COLORS["primary"])

            done = snap.round_no - 1 + (1 if snap.phase == "round_end" else 0)
            self._draw_dots(done, snap.round_no, total)

        self.step_value.config(text=f"{snap.step_no} / {engine.stats.total_steps - 1}")
        self.move_value.config(text=str(engine.stats.moves))
        self.round_value.config(text=str(engine.rounds))

    # ------------------------------------------------------------------
    def clear_log(self):
        self.log_text.configure(state="normal")
        self.log_text.delete("1.0", "end")
        self.log_text.configure(state="disabled")

    def append_log(self, message, tag="normal"):
        self.log_text.configure(state="normal")
        self.log_text.insert("end", message + "\n", tag)
        self.log_text.see("end")
        self.log_text.configure(state="disabled")
