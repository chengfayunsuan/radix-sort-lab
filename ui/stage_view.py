"""
舞台视图
========

把「数组层」和「桶层」合并画在同一块 Canvas 上。

为什么要合并
------------
最初两块内容各占一个 Canvas，中间还夹着一个小标题。静止时看不出问题，
但一旦要做"数字从数组飞进桶里"的动画，跨 Canvas 是做不到的——
Canvas 里的图元不能越过自己的边界，也没法真的透明。

合并之后，整个左区就是一张大画布，飞行动画只是在这张画布上移动一个图元，
既流畅又不会出现"画到一半被裁掉"的情况。

坐标约定
--------
数组层占 y ∈ [0, 190)，桶层占 y ∈ [190, 660)。
两个图层自己不知道这个偏移，由本类构造时注入，所以它们仍然可以单独测试。
"""

import tkinter as tk

from .array_view import ArrayLayer, STAGE_W
from .bucket_view import BucketLayer
from .theme import COLORS, round_rect, draw_number

STAGE_H = 660

FLY_TAG = "flyer"
FRAME_MS = 16           # 每帧间隔，约 60fps


class StageView(tk.Canvas):
    def __init__(self, parent, fonts):
        super().__init__(
            parent,
            width=STAGE_W,
            height=STAGE_H,
            bg=COLORS["bg"],
            highlightthickness=0,
        )
        self.fonts = fonts
        self.array = ArrayLayer(fonts, y0=0)
        self.bucket = BucketLayer(fonts, y0=ArrayLayer.HEIGHT)

        self._fly_job = None
        self._fly_done = None

    # ------------------------------------------------------------------
    # 静态绘制
    # ------------------------------------------------------------------
    def render(self, snap, digits, arr_snap=None, bkt_snap=None,
               hide_array=(), hide_bucket=()):
        """
        画一帧。默认数组和桶都用 snap；
        动画时可以让数组用上一帧、桶用这一帧（或反过来），详见 app._fly_plan。
        """
        self.delete("all")
        self.array.draw(self, arr_snap or snap, digits, hide=hide_array)
        self.bucket.draw(self, bkt_snap or snap, digits, hide=hide_bucket)

    # ------------------------------------------------------------------
    # 飞行动画
    # ------------------------------------------------------------------
    def fly(self, p0, p1, value, digits, duration_ms, digit_pos, on_done=None):
        """
        让一张卡片从 p0 飞到 p1。

        p0 / p1 是画布坐标（中心点）。duration_ms 是总时长，
        帧数按 FRAME_MS 换算，所以速度快时自动减少帧数。
        """
        self.cancel_fly()

        frames = max(4, int(duration_ms / FRAME_MS))
        shrink = 1 if p0[1] > p1[1] else -1     # 向上飞（收集）时由小变大

        w0, h0 = 78.0, 54.0
        w1, h1 = 72.0, 32.0
        if shrink < 0:
            w0, w1 = w1, w0
            h0, h1 = h1, h0

        self._fly_done = on_done

        def frame(k):
            self._fly_job = None
            t = k / frames
            e = t * t * (3 - 2 * t)             # smoothstep，起步和收尾都缓一点

            cx = p0[0] + (p1[0] - p0[0]) * e
            cy = p0[1] + (p1[1] - p0[1]) * e
            # 轻微弧线：让轨迹不是一条死板的直线
            cy -= 26 * (e - e * e) * shrink

            w = w0 + (w1 - w0) * e
            h = h0 + (h1 - h0) * e
            self._paint_flyer(cx, cy, w, h, value, digits, digit_pos)

            if k < frames:
                self._fly_job = self.after(FRAME_MS, frame, k + 1)
            else:
                self.delete(FLY_TAG)
                done, self._fly_done = self._fly_done, None
                if done:
                    done()

        frame(0)

    def _paint_flyer(self, cx, cy, w, h, value, digits, digit_pos):
        self.delete(FLY_TAG)
        x1, y1 = cx - w / 2, cy - h / 2
        x2, y2 = cx + w / 2, cy + h / 2

        # 阴影：Tk 的 Canvas 不支持半透明，用一层浅灰下移两像素近似
        round_rect(self, x1, y1 + 3, x2, y2 + 3, r=8,
                   fill="#DFE5EE", outline="", tags=FLY_TAG)
        round_rect(self, x1, y1, x2, y2, r=8,
                   fill=COLORS["active_bg"], outline=COLORS["active_line"],
                   width=2, tags=FLY_TAG)
        draw_number(
            self, cx, cy - 1, value, digits,
            font=self.fonts["num_md"],
            main=COLORS["active_text"],
            digit_pos=digit_pos if digit_pos is not None and digit_pos >= 0 else None,
            strong=True,
            tags=FLY_TAG,
        )

    def cancel_fly(self):
        """打断正在进行的动画，并把半路上的卡片清掉。"""
        if self._fly_job is not None:
            try:
                self.after_cancel(self._fly_job)
            except tk.TclError:
                pass
            self._fly_job = None
        self.delete(FLY_TAG)
        self._fly_done = None
