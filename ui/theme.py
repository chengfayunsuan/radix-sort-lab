"""
界面主题与通用绘图工具
======================

把所有颜色、字体、圆角矩形等绘制细节集中在这里，好处是：

1. 改配色只需要动这一个文件，不用满项目找颜色值；
2. 负责界面的同学和负责逻辑的同学不会因为样式代码打架；
3. 答辩时如果老师问"你们的界面规范怎么定的"，可以直接指到这里。
"""

import tkinter.font as tkfont

# ------------------------------ 配色 ------------------------------
# 整体走浅色系：投影到教室屏幕上比深色更容易看清。
COLORS = {
    "bg":          "#F5F7FA",   # 窗口底色
    "card":        "#FFFFFF",   # 卡片底色
    "border":      "#E3E8EF",   # 普通边框
    "border_dark": "#CBD3DF",   # 强调边框
    "text":        "#1A1F29",   # 主文字
    "text_sub":    "#6B7684",   # 次要文字
    "text_dim":    "#A8B0BD",   # 前导零、占位符
    "header":      "#FFFFFF",   # 顶栏底色

    "active_bg":   "#FDF1E0",   # 当前处理元素：底
    "active_line": "#BA7517",   # 当前处理元素：边
    "active_text": "#8A5209",   # 当前处理元素：字

    # 正在处理的那一位数字：用比琥珀色更重的橙红，和卡片高亮区分开
    "digit_hot":   "#C2410C",   # 当前位：字
    "digit_hot_bg": "#FFE3CE",  # 当前位：底色块
    "digit_warm":  "#B45309",   # 其他卡片上同一数位的提示色
    "badge_bg":    "#F1F6FC",   # 轮次徽章底色

    "bucket_bg":   "#FBFCFE",   # 桶内部
    "bucket_line": "#CBD3DF",   # 桶壁
    "item_bg":     "#E6F1FB",   # 桶内数字卡片
    "item_line":   "#85B7EB",
    "item_text":   "#185FA5",

    "primary":     "#185FA5",   # 主按钮
    "primary_dk":  "#134A80",
    "empty":       "#F0F3F8",   # 空位
}

# ------------------------------ 字体 ------------------------------
# 数字统一用等宽字体 Consolas，保证 4 位数在格子里宽度一致、纵向对齐。
FONT_FAMILY_CN = "Microsoft YaHei"
FONT_FAMILY_MONO = "Consolas"


def build_fonts(root):
    """
    创建字体对象。

    为什么必须传 root：tkinter.font.Font 需要绑定一个已存在的 Tk 实例。
    返回字典而不是全局变量，是为了让测试时可以重新构建。
    """
    return {
        "title":   tkfont.Font(root=root, family=FONT_FAMILY_CN, size=15, weight="bold"),
        "h2":      tkfont.Font(root=root, family=FONT_FAMILY_CN, size=11, weight="bold"),
        "body":    tkfont.Font(root=root, family=FONT_FAMILY_CN, size=10),
        "small":   tkfont.Font(root=root, family=FONT_FAMILY_CN, size=9),
        "round":   tkfont.Font(root=root, family=FONT_FAMILY_CN, size=19, weight="bold"),
        "num":     tkfont.Font(root=root, family=FONT_FAMILY_MONO, size=19, weight="bold"),
        "num_md":  tkfont.Font(root=root, family=FONT_FAMILY_MONO, size=16, weight="bold"),
        "num_sm":  tkfont.Font(root=root, family=FONT_FAMILY_MONO, size=14, weight="bold"),
        "num_xs":  tkfont.Font(root=root, family=FONT_FAMILY_MONO, size=12, weight="bold"),
        "mono":    tkfont.Font(root=root, family=FONT_FAMILY_MONO, size=10),
        "bucket":  tkfont.Font(root=root, family=FONT_FAMILY_MONO, size=10, weight="bold"),
    }


def round_rect(canvas, x1, y1, x2, y2, r=8, **kwargs):
    """
    在 Canvas 上画一个圆角矩形。

    Tkinter 没有现成的圆角矩形，这里用 create_polygon 加 smooth=True 近似。
    这是社区里最常用的写法，顶点顺序必须首尾相接。
    """
    points = [
        x1 + r, y1,
        x2 - r, y1,
        x2, y1,
        x2, y1 + r,
        x2, y2 - r,
        x2, y2,
        x2 - r, y2,
        x1 + r, y2,
        x1, y2,
        x1, y2 - r,
        x1, y1 + r,
        x1, y1,
    ]
    return canvas.create_polygon(points, smooth=True, **kwargs)


def draw_number(canvas, cx, cy, value, digits, font, main,
                digit_pos=None, strong=False, tags=None):
    """
    在 (cx, cy) 处居中画一个补零后的数字，逐字符绘制。

    逐字符画而不是整体画，是为了能单独给某一位换颜色：
      digit_pos 不为 None 时，把对应数位标色
        strong=True   正在移动的那一个 → 橙红字 + 橙色底块
        strong=False  其他卡片        → 浅橙字，提示"这一轮看的就是这一位"

    前导零始终用浅灰，和标色互不影响。
    tags 用于飞行卡片：动画结束时按 tag 一次性删掉，不用逐个记 id。
    """
    text = str(value).zfill(digits)
    leading = digits - len(str(value))

    widths = [font.measure(ch) for ch in text]
    total_w = sum(widths)
    cur = cx - total_w / 2

    ascent = font.metrics("ascent")
    descent = font.metrics("descent")

    for k, ch in enumerate(text):
        pos_from_right = digits - 1 - k          # 该字符对应的数位，0 表示个位
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
            # 其他卡片的同一位：用橙色标出来，但不要底块，避免满屏色块。
            # 只换颜色不加下划线——下划线会让数字看起来像"被划了一道"，很脏。
            color = COLORS["digit_warm"]
        elif k < leading:
            color = COLORS["text_dim"]
        else:
            color = main

        canvas.create_text(cur, cy, text=ch, anchor="w", font=font, fill=color, tags=tags)
        cur += widths[k]
