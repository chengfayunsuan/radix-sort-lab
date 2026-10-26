"""
数组图层
========

负责画屏幕上半部分那一排数字卡片。这是整个界面里"补零"最容易出错的地方，
因为前导零必须用浅灰色单独绘制，才能让观众看出哪些 0 是补出来的。

本模块现在不直接持有 Canvas，而是提供 draw()/center() 两个方法，
由 stage_view 统一调用。这样数组和桶共用同一块画布，卡片才能"飞过去"。

逐位绘制
--------
以前的实现把整个数字当成一个字符串画，没法单独给某一位换颜色。
现在改为逐字符绘制，好处有两个：

  1. 正在处理的那一位（个位 / 十位 / …）可以单独标色，一眼看出本轮在看哪一位；
  2. 前导零照样是灰色，和标色互不影响。

绘制思路：
  1. 先算出补零后的完整字符串，例如 525 -> "0525"
  2. 用 font.measure() 逐字量宽，得到每个字符的精确起点
  3. 逐字画，前导零用浅灰，当前位加橙色底色块
"""

from .theme import COLORS, round_rect, draw_number

STAGE_W = 924

LAYER_H = 190             # 本层占用的高度
TITLE_Y = 8               # 小标题基线
TOP_PAD = 34              # 第一行卡片的顶部

PER_ROW = 10              # 每行最多放 10 个卡片
CARD_W = 80
CARD_H = 58
GAP = 8
ROW_GAP = 14


class ArrayLayer:
    """上方数组区的绘制器。"""

    HEIGHT = LAYER_H

    def __init__(self, fonts, y0=0):
        self.fonts = fonts
        self.y0 = y0

    # ------------------------------------------------------------------
    # 坐标
    # ------------------------------------------------------------------
    def slot(self, i, n):
        """第 i 个格子的左上角坐标。n 是总数，用于让每行居中。"""
        row, col = divmod(i, PER_ROW)
        in_row = min(PER_ROW, n - row * PER_ROW)
        row_w = in_row * CARD_W + (in_row - 1) * GAP
        x = (STAGE_W - row_w) / 2 + col * (CARD_W + GAP)
        y = self.y0 + TOP_PAD + row * (CARD_H + ROW_GAP)
        return x, y

    def center(self, i, n):
        """第 i 个格子的中心坐标，动画的起点/终点用它。"""
        x, y = self.slot(i, n)
        return x + CARD_W / 2, y + CARD_H / 2

    # ------------------------------------------------------------------
    # 绘制
    # ------------------------------------------------------------------
    def draw(self, canvas, snap, digits, hide=()):
        """把整个数组区画到 canvas 上。hide 里的下标不画（动画时让出位置）。"""
        canvas.create_text(
            2, self.y0 + TITLE_Y, text="① 当前数组（灰色高位为补出来的前导零）",
            anchor="nw", font=self.fonts["small"], fill=COLORS["text_dim"],
        )

        arr = snap.array
        n = len(arr)
        if n == 0:
            return

        for i, value in enumerate(arr):
            x0, y0 = self.slot(i, n)
            is_active = (i == snap.active_index and snap.active_index >= 0)

            if i in hide:
                # 动画时这个格子让给飞行卡片，画成空位框，避免出现"两个数"
                self._draw_card(canvas, x0, y0, None, digits, False, snap.digit_pos, False)
                canvas.create_text(
                    x0 + CARD_W / 2, y0 + CARD_H + 9,
                    text=str(i + 1), font=self.fonts["small"], fill=COLORS["text_dim"],
                )
                continue

            self._draw_card(canvas, x0, y0, value, digits, is_active, snap.digit_pos,
                            show_digit=snap.phase in ("distribute", "collect"))

            canvas.create_text(
                x0 + CARD_W / 2, y0 + CARD_H + 9,
                text=str(i + 1), font=self.fonts["small"], fill=COLORS["text_dim"],
            )

    # ------------------------------------------------------------------
    def _draw_card(self, canvas, x, y, value, digits, active, digit_pos, show_digit):
        """画一张数字卡片。value 为 None 时表示收集阶段尚未填入的空位。"""
        if value is None:
            round_rect(
                canvas, x, y, x + CARD_W, y + CARD_H, r=8,
                fill=COLORS["empty"], outline=COLORS["border_dark"],
                width=1, dash=(4, 4),
            )
            canvas.create_text(
                x + CARD_W / 2, y + CARD_H / 2,
                text="·", font=self.fonts["num"], fill=COLORS["text_dim"],
            )
            return

        if active:
            round_rect(
                canvas, x, y, x + CARD_W, y + CARD_H, r=8,
                fill=COLORS["active_bg"], outline=COLORS["active_line"], width=2,
            )
        else:
            round_rect(
                canvas, x, y, x + CARD_W, y + CARD_H, r=8,
                fill=COLORS["card"], outline=COLORS["border"], width=1,
            )

        draw_number(
            canvas, x + CARD_W / 2, y + CARD_H / 2, value, digits,
            font=self.fonts["num"],
            main=COLORS["active_text"] if active else COLORS["text"],
            digit_pos=digit_pos if show_digit else None,
            strong=active,
        )
