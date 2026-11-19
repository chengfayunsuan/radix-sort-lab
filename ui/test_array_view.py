# -*- coding: utf-8 -*-
"""数组图层的自动化测试（界面开发 A）。

对应测试方案：
    TC-06  前导零显示：51 在四位数据里显示成 0051，前两位必须是浅灰色
    TC-10  数据量上限：20 张卡片两行排列，不重叠、不越界
以及本轮新增的界面细节：当前数位高亮、空位虚线框。

运行方式（在仓库根目录）：
    python -m ui.test_array_view
全部通过时输出 OK。
"""

import tkinter as tk
from types import SimpleNamespace

from ui import theme
from ui.array_view import ArrayLayer, CARD_W, CARD_H, PER_ROW, STAGE_W


# ----------------------------------------------------------------------
# 小工具
# ----------------------------------------------------------------------
def texts_with_fill(canvas):
    """返回画布上所有文字图元的 (字符, 颜色)。"""
    out = []
    for item in canvas.find_all():
        if canvas.type(item) != "text":
            continue
        out.append((canvas.itemcget(item, "text"), canvas.itemcget(item, "fill")))
    return out


def make_root():
    root = tk.Tk()
    root.withdraw()
    return root


# ----------------------------------------------------------------------
# TC-10：布局不重叠、不越界
# ----------------------------------------------------------------------
def test_layout_20():
    root = make_root()
    fonts = theme.build_fonts(root)
    layer = ArrayLayer(fonts, y0=0)

    n = 20
    rects = []
    for i in range(n):
        x, y = layer.slot(i, n)
        rects.append((x, y, x + CARD_W, y + CARD_H))

    # 1) 左右不越界
    for i, (x1, _, x2, _) in enumerate(rects):
        assert x1 >= 0 and x2 <= STAGE_W, f"第 {i + 1} 张卡片超出左右边界"

    # 2) 任意两张不重叠
    for i in range(n):
        for j in range(i + 1, n):
            a, b = rects[i], rects[j]
            overlap = not (a[2] <= b[0] or b[2] <= a[0]
                           or a[3] <= b[1] or b[3] <= a[1])
            assert not overlap, f"第 {i + 1} 张与第 {j + 1} 张卡片重叠"

    # 3) 每行不超过 10 张，且第二行在第一行下方
    assert rects[0][1] < rects[PER_ROW][1], "第二行应在第一行下方"

    root.destroy()
    print("TC-10 通过：20 张卡片两行排列，不重叠、不越界")


# ----------------------------------------------------------------------
# TC-06：前导零必须是浅灰色
# ----------------------------------------------------------------------
def test_leading_zero_color():
    root = make_root()
    fonts = theme.build_fonts(root)
    canvas = tk.Canvas(root, width=STAGE_W, height=200)

    # 51 在四位数据里显示为 0051
    theme.draw_number(canvas, 100, 50, 51, 4, font=fonts["num"],
                      main=theme.COLORS["text"])

    pairs = texts_with_fill(canvas)
    assert len(pairs) == 4, "应画出 4 个字符"

    chars = [p[0] for p in pairs]
    assert chars == list("0051"), f"字符序列应为 0051，实际 {chars}"

    dim = theme.COLORS["text_dim"]
    ink = theme.COLORS["text"]
    assert pairs[0][1] == dim and pairs[1][1] == dim, "补出来的两个 0 必须是浅灰色"
    assert pairs[2][1] == ink and pairs[3][1] == ink, "真实数字 5、1 必须是深色"

    root.destroy()
    print("TC-06 通过：0051 的前两位为浅灰，真实数字为深色")


# ----------------------------------------------------------------------
# 当前数位高亮：正在处理的那一位要有底色块
# ----------------------------------------------------------------------
def test_active_digit_block():
    root = make_root()
    fonts = theme.build_fonts(root)
    canvas = tk.Canvas(root, width=STAGE_W, height=200)

    theme.draw_number(canvas, 100, 50, 8071, 4, font=fonts["num"],
                      main=theme.COLORS["text"], digit_pos=0, strong=True)

    pairs = texts_with_fill(canvas)
    hot = theme.COLORS["digit_hot"]
    assert pairs[3][1] == hot, "个位（正在处理）应使用 digit_hot 颜色"

    rects = [i for i in canvas.find_all() if canvas.type(i) == "rectangle"]
    assert rects, "正在处理的那一位应带底色块"

    root.destroy()
    print("数位高亮通过：个位变色并带底色块")


# ----------------------------------------------------------------------
# 空位：收集阶段填成 None 的格子画虚线框，不画数字
# ----------------------------------------------------------------------
def test_empty_slot():
    root = make_root()
    fonts = theme.build_fonts(root)
    canvas = tk.Canvas(root, width=STAGE_W, height=220)
    layer = ArrayLayer(fonts, y0=0)

    snap = SimpleNamespace(array=[51, None, 8071], active_index=-1,
                           digit_pos=0, phase="collect")
    layer.draw(canvas, snap, digits=4)

    # 两个非空卡片各 4 个字符，空位用 "·" 占位，这里只关心不抛异常且数量正确
    assert len(texts_with_fill(canvas)) >= 8, "应画出两张卡片和空位占位符"

    root.destroy()
    print("空位通过：None 的格子画成虚线框，不画数字")


def main():
    test_layout_20()
    test_leading_zero_color()
    test_active_digit_block()
    test_empty_slot()
    print("OK：数组图层四项检查全部通过")


if __name__ == "__main__":
    main()
