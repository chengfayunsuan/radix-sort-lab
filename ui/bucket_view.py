"""
桶图层
======

负责画屏幕下半部分那 10 个桶（0 号到 9 号）。

桶用 U 形绘制（左边、右边、底边三条线，不封顶），比画矩形更直观，
观众一眼就能看出"数是从上面落进去的"。

三个视觉细节是刻意设计的：
  1. 正在被操作的桶，桶壁变成琥珀色；
  2. 刚落进桶里的那个数，卡片变成琥珀色；
  3. 桶内卡片同样逐位绘制，当前处理的数位会标橙——这样数组里的数字
     飞进桶里之后，你还能看出它是靠哪一位进的这个桶。

本模块不持有 Canvas，坐标都相对本层顶部，由 stage_view 传入偏移。
"""

from .theme import COLORS, round_rect, draw_number

STAGE_W = 924

LAYER_H = 470

BUCKET_COUNT = 10
BUCKET_W = 84
GAP = 6
TOP = 34
BOTTOM = 430
LABEL_Y = 451

ITEM_W = 72
ITEM_H = 30
ITEM_GAP = 2
ITEM_TOP = TOP + 10
MAX_ITEMS = 12          # 桶内最多画 12 个卡片，超出时折叠成 "+N"

TITLE_Y = 8


class BucketLayer:
    """下方桶区的绘制器。"""

    HEIGHT = LAYER_H

    def __init__(self, fonts, y0=0):
        self.fonts = fonts
        self.y0 = y0

    # ------------------------------------------------------------------
    # 坐标
    # ------------------------------------------------------------------
    def bucket_x0(self, b):
        total_w = BUCKET_COUNT * BUCKET_W + (BUCKET_COUNT - 1) * GAP
        origin = (STAGE_W - total_w) / 2
        return origin + b * (BUCKET_W + GAP)

    def bucket_cx(self, b):
        return self.bucket_x0(b) + BUCKET_W / 2

    def slot(self, b, k):
        """第 b 个桶里第 k 张卡片的左上角坐标。"""
        return self.bucket_cx(b) - ITEM_W / 2, self.y0 + ITEM_TOP + k * (ITEM_H + ITEM_GAP)

    def center(self, b, k):
        """第 b 个桶里第 k 张卡片的中心坐标，动画的起点/终点用它。"""
        x, y = self.slot(b, k)
        return x + ITEM_W / 2, y + ITEM_H / 2

    # ------------------------------------------------------------------
    # 绘制
    # ------------------------------------------------------------------
    def draw(self, canvas, snap, digits, hide=()):
        """hide 是 [(桶号, 第几张), ...]，动画时把这些卡片藏起来让出位置。"""
        canvas.create_text(
            2, self.y0 + TITLE_Y, text="② 十个桶（按当前数位的数字落桶）",
            anchor="nw", font=self.fonts["small"], fill=COLORS["text_dim"],
        )

        for b in range(BUCKET_COUNT):
            hidden = {k for (bb, k) in hide if bb == b}
            self._draw_bucket(canvas, b, snap, digits, hidden)

    # ------------------------------------------------------------------
    def _draw_bucket(self, canvas, index, snap, digits, hidden):
        x = self.bucket_x0(index)
        y_top = self.y0 + TOP
        y_bottom = self.y0 + BOTTOM

        is_active = (index == snap.active_bucket)
        wall_color = COLORS["active_line"] if is_active else COLORS["bucket_line"]
        wall_width = 2 if is_active else 1

        # 先铺一层极浅的底色，让桶看起来是个实体容器，而不是几根悬空的线
        canvas.create_rectangle(
            x, y_top, x + BUCKET_W, y_bottom,
            fill=COLORS["bucket_bg"], outline="",
        )
        # 桶口的一条短横线，暗示"数是从这里落进去的"
        canvas.create_line(
            x - 3, y_top, x + BUCKET_W + 3, y_top,
            fill=wall_color, width=wall_width,
        )

        # U 形桶壁
        canvas.create_line(x, y_top, x, y_bottom, fill=wall_color, width=wall_width)
        canvas.create_line(x + BUCKET_W, y_top, x + BUCKET_W, y_bottom,
                           fill=wall_color, width=wall_width)
        canvas.create_line(x, y_bottom, x + BUCKET_W, y_bottom,
                           fill=wall_color, width=wall_width)

        # 桶号
        ly = self.y0 + LABEL_Y
        cx = x + BUCKET_W / 2
        canvas.create_oval(
            cx - 11, ly - 11, cx + 11, ly + 11,
            fill=COLORS["active_bg"] if is_active else COLORS["bg"],
            outline=COLORS["active_line"] if is_active else COLORS["border_dark"],
            width=1,
        )
        canvas.create_text(
            cx, ly, text=str(index), font=self.fonts["bucket"],
            fill=COLORS["active_text"] if is_active else COLORS["text_sub"],
        )

        items = snap.buckets[index]
        if not items:
            return

        # 超出上限时折叠显示，避免画到桶外面
        show = items
        extra = 0
        if len(items) > MAX_ITEMS:
            show = items[:MAX_ITEMS - 1]
            extra = len(items) - len(show)

        for k, value in enumerate(show):
            if k in hidden:
                continue
            _, y = self.slot(index, k)
            # 分配阶段刚落进桶里的那一个，高亮显示
            is_new = (
                snap.phase == "distribute"
                and is_active
                and k == len(show) - 1
                and extra == 0
            )
            self._draw_item(canvas, index, k, value, digits, is_new, snap.digit_pos)

        if extra > 0:
            _, y = self.slot(index, len(show))
            canvas.create_text(
                self.bucket_cx(index), y + ITEM_H / 2,
                text=f"+{extra}", font=self.fonts["num_xs"], fill=COLORS["text_sub"],
            )

    # ------------------------------------------------------------------
    def _draw_item(self, canvas, b, k, value, digits, highlight, digit_pos):
        x, y = self.slot(b, k)

        if highlight:
            round_rect(
                canvas, x, y, x + ITEM_W, y + ITEM_H, r=5,
                fill=COLORS["active_bg"], outline=COLORS["active_line"], width=2,
            )
        else:
            round_rect(
                canvas, x, y, x + ITEM_W, y + ITEM_H, r=5,
                fill=COLORS["item_bg"], outline=COLORS["item_line"], width=1,
            )

        draw_number(
            canvas, x + ITEM_W / 2, y + ITEM_H / 2, value, digits,
            font=self.fonts["num_xs"],
            main=COLORS["active_text"] if highlight else COLORS["item_text"],
            digit_pos=digit_pos if digit_pos is not None and digit_pos >= 0 else None,
            strong=highlight,
        )
