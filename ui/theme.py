"""
界面主题与绘图工具
==================

风格：红黑白，但轻。
  * 一律直角硬边，不要圆角
  * 三色是红、墨、纸白：暖白纸底 + 墨黑线字 + 砖红高亮
  * "轻"体现在——不用纯黑撞鲜红：黑是暖墨、红是砖红、高亮用浅红底
  * 构成感靠直角和少量色条，不靠大面积色块

所有配色集中在这里，改风格只动这一个文件。
"""

import tkinter.font as tkfont

# ------------------------------ 配色 ------------------------------
COLORS = {
    # 暖白纸底 + 墨黑线字
    "bg":          "#F6F3ED",   # 窗口底：暖白，不是冷灰
    "paper":       "#FFFCF6",
    "card":        "#FFFCF6",   # 卡片：暖白
    "header":      "#FFFCF6",

    "border":      "#3A3630",   # 暖墨边框（不是纯黑，也不是浅灰）
    "border_dark": "#24211D",

    "text":        "#1F1C18",   # 主文字：暖墨黑
    "text_sub":    "#5C554C",
    "text_dim":    "#A29A8E",

    # 砖红（暗一点，不刺眼）
    "primary":     "#B23A2E",
    "primary_dk":  "#8E2D24",

    # 当前处理元素：浅红底 + 砖红边 + 深红字
    "active_bg":   "#FBEAE5",
    "active_line": "#B23A2E",
    "active_text": "#8E2D24",

    # 正在看的数位：深红 + 淡红底
    "digit_hot":    "#A5301F",
    "digit_hot_bg": "#F7DCD5",
    "digit_warm":   "#B23A2E",
    "badge_bg":     "#F7F1E7",

    "bucket_bg":   "#FFFCF6",
    "bucket_line": "#3A3630",
    "item_bg":     "#F7F1E7",
    "item_line":   "#8A8176",
    "item_text":   "#2A2621",

    "empty":       "#EDE7DC",

    # 暖灰投影：右下挪 3px
    "shadow":      "#D9D3C7",
    "panel_alt":   "#F9F6EF",
    "chip":        "#F7DCD5",
}

FONT_FAMILY_CN = "Microsoft YaHei"
FONT_FAMILY_MONO = "Consolas"


def build_fonts(root):
    return {
        "title":   tkfont.Font(root=root, family=FONT_FAMILY_CN, size=15, weight="bold"),
        "h2":      tkfont.Font(root=root, family=FONT_FAMILY_CN, size=11, weight="bold"),
        "body":    tkfont.Font(root=root, family=FONT_FAMILY_CN, size=10),
        "small":   tkfont.Font(root=root, family=FONT_FAMILY_CN, size=9),
        "round":   tkfont.Font(root=root, family=FONT_FAMILY_MONO, size=19, weight="bold"),
        "num":     tkfont.Font(root=root, family=FONT_FAMILY_MONO, size=19, weight="bold"),
        "num_md":  tkfont.Font(root=root, family=FONT_FAMILY_MONO, size=16, weight="bold"),
        "num_sm":  tkfont.Font(root=root, family=FONT_FAMILY_MONO, size=14, weight="bold"),
        "num_xs":  tkfont.Font(root=root, family=FONT_FAMILY_MONO, size=12, weight="bold"),
        "mono":    tkfont.Font(root=root, family=FONT_FAMILY_MONO, size=10),
        "bucket":  tkfont.Font(root=root, family=FONT_FAMILY_MONO, size=10, weight="bold"),
    }


def round_rect(canvas, x1, y1, x2, y2, r=8, **kwargs):
    """
    一律画直角矩形。保留 r 参数只为兼容旧调用，不生效——风格上不要圆角。
    """
    return canvas.create_rectangle(x1, y1, x2, y2, **kwargs)


def draw_number(canvas, cx, cy, value, digits, font, main,
                digit_pos=None, strong=False, tags=None):
    """
    在 (cx, cy) 处居中画一个补零后的数字，逐字符绘制。

    逐字符画是为了给单独的数位换色：
      strong=True   正在移动的那一个 → 淡红底块 + 深红字
      strong=False  其他卡片         → 砖红字 + 砖红下划线
    前导零：普通卡片用浅灰，高亮卡片用浅红，保证看得见。
    """
    text = str(value).zfill(digits)
    leading = digits - len(str(value))

    widths = [font.measure(ch) for ch in text]
    total_w = sum(widths)
    cur = cx - total_w / 2
    ascent = font.metrics("ascent")
    descent = font.metrics("descent")

    for k, ch in enumerate(text):
        pos_from_right = digits - 1 - k
        mark = (digit_pos is not None and pos_from_right == digit_pos)

        if mark and strong:
            pad = 3
            canvas.create_rectangle(
                cur - pad, cy - ascent + 2,
                cur + widths[k] + pad, cy + descent - 1,
                fill=COLORS["digit_hot_bg"], outline="", tags=tags,
            )
            color = COLORS["digit_hot"]
        elif mark:
            # 以前这里在数字底下补一条横线。7 的字形是"顶横 + 斜竖"，
            # 底下本来没有横，结果被这条线补上一道底横，放大后整个 7
            # 看着就像字母 Z，明明是数字却认不出来。
            # 现在只在当前位换个醒目色，字形一动不动，是几就是几。
            color = COLORS["digit_hot"]
        elif k < leading:
            color = "#D9A99F" if strong else COLORS["text_dim"]
        else:
            color = main

        canvas.create_text(cur, cy, text=ch, anchor="w", font=font, fill=color, tags=tags)
        cur += widths[k]
