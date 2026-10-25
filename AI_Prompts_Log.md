# AI 辅助编程记录（AI Prompts Log）

> 本文档记录本项目开发过程中，成员使用大语言模型辅助编码的**三次代表性交互**。
>
> 每次记录包含三部分：**提示词原文** → **AI 的原始输出** → **人工介入的判断与修改**。
>
> 我们的原则是：AI 负责写第一版，人负责判断它对不对。**凡是 AI 写得顺、我们看得也顺的地方，往往最容易埋坑**，所以下面三次记录的重点都在"我们发现了什么"。

---

## 交互一：生成"足够杂乱"的随机数据

### 提示词

```
你是一个资深 Python 开发者。请帮我写一个函数，为排序算法演示程序生成随机数据。

具体需求：
1. 生成 n 个 1 到 9999 之间的整数；
2. 数据要"足够杂乱"，不能是已经排好序的；
3. 数据不能有重复。

约束条件：
- 只用 Python 标准库；
- 代码要有详细中文注释；
- 函数签名固定为 generate(n: int) -> list[int]。
```

### AI 的原始输出（摘要）

AI 给出的方案是循环生成加集合去重：

```python
def generate(n):
    result = []
    seen = set()
    while len(result) < n:
        v = random.randint(1, 9999)
        if v not in seen:
            seen.add(v)
            result.append(v)
    return result
```

思路没问题，能跑，生成的数据看起来也确实很乱。

### 我们发现的三个问题

**问题一：不能保证"不有序"。** 虽然 n 个数恰好递增的概率极低，但不是零。演示时如果真碰上，整个程序的演示价值就没了。概率低不等于可以不管。

**问题二：不能保证"每一位都分散"。** 这一条是大问题，而且不测根本发现不了。假设抽到的 12 个数千位全是 1 到 3，那么第四轮分配时所有数都会挤进 1、2、3 号桶，其余七个桶全程空着——**观众会以为程序卡住了**。更极端的情况是某一位上所有数字完全相同，那一轮分配阶段画面毫无变化。

**问题三：`while` 循环没有重试上限。** 如果参数被改成 `n=20000`（超过 1 到 9999 的范围），这个循环会永久卡死，界面直接无响应。

### 人工介入修改

我们重写了数据生成逻辑，核心改动有三处：

1. 用 `random.sample(range(lo, hi + 1), n)` 一次性取不重复的数，比"循环 + 去重"更直接，也不会死循环；
2. 增加两道校验：`is_sorted()` 检查是否已有序，`digit_spread_ok()` 检查每一位是否至少出现两种不同数字，任一不通过就重新生成；
3. 给重试次数设上限（800 次），耗尽后降级为"只保证不有序"，确保函数一定会返回。

```python
for _ in range(MAX_RETRY):
    data = random.sample(range(lo, hi + 1), n)
    random.shuffle(data)
    digits = max_digits(data)
    if is_sorted(data):
        continue
    if not digit_spread_ok(data, digits):
        continue
    return data
```

其中 `digit_spread_ok` 是我们自己补的：

```python
def digit_spread_ok(data, digits):
    for pos in range(digits):
        distinct = {(v // (10 ** pos)) % 10 for v in data}
        if len(distinct) < 2:
            return False
    return True
```

**这次介入的收获**：AI 理解"随机"就是"看起来乱"，但程序需要的是"可验证地不乱"。凡是描述性的要求（"要足够杂乱"），都必须翻译成可执行的判断条件，否则 AI 只能按字面意思猜。

---

## 交互二：左右分栏布局（这次踩了个大坑）

### 提示词

```
你是一个资深的 Python Tkinter GUI 开发者。请帮我搭一个窗口骨架。

具体需求：
1. 窗口 1280x800，左边一块宽 924 放两个 Canvas（上 186 高，下 418 高），
   右边一块宽 300 放信息面板；
2. 左栏宽度必须固定，不能被右栏挤压；
3. 窗口整体不随内容变化。

约束条件：
- 用 pack 布局管理器；
- 代码要有详细中文注释。
```

### AI 的原始输出（摘要）

AI 给出的方案是 pack 左右分栏，并用 `pack_propagate(False)` 锁住左栏尺寸：

```python
left = tk.Frame(body, bg=BG, width=924)
left.pack(side="left", fill="both", expand=True)
left.pack_propagate(False)          # 锁住尺寸，不让子控件改变它
```

程序能启动，窗口也正常打开了，**没有任何报错**。

### 我们发现的问题

界面打开后，左栏一片空白——两个 Canvas 都不见了。但代码里明明创建了它们，也 `pack()` 了。

排查过程：

1. 先在代码里打印 `len(canvas.find_all())`，结果是 **36 和 74**，说明图形元素确实画出来了；
2. 再打印 `canvas.winfo_rootx()`，结果全是 `0 0 1 1`——位置和尺寸都是 1 像素；
3. 最后打印父容器尺寸：`left frame: 924 x 1`。

问题就在这里：**左栏高度是 1 像素**。

原因是 `pack_propagate(False)` 关闭了"子控件决定父容器尺寸"的传播，于是父容器完全依赖 `width` 和 `height` 参数。但 AI 只给了 `width=924`，没给 `height`，Tkinter 就把高度当成默认的最小值。子控件因此被压进 1 像素的高度里，全部不可见。

### 人工介入修改

我们的改法是**换掉整个布局方式**，而不是补一个 `height`：

```python
body.grid_columnconfigure(0, weight=1)
body.grid_rowconfigure(0, weight=1)

left = tk.Frame(body, bg=BG)                    # 不关闭 propagate
left.grid(row=0, column=0, sticky="nw")         # 宽高都由内容自然决定

side = SidePanel(body, fonts)
side.grid(row=0, column=1, sticky="ns", padx=(16, 0))
```

为什么不在 `pack` 里补 `height`？因为补了之后，只要以后调整了某个子控件的高度，父容器就会和内容不匹配，还得同步改数字。**让容器由内容撑开，才是这个场景下的正解**。宽度则通过 Canvas 自身的固定宽度自然确定，不需要显式指定。

**这次介入的收获**：AI 写的代码"能跑、不报错"，和"显示正确"是两件完全不同的事。`pack_propagate(False)` 这种调用，AI 用得很自然，因为它看起来像是"把尺寸锁住"的意思，但少了 `height` 就会**静默塌缩**——不抛异常、不打日志，只是东西不见了。这类错误只能靠实际观察界面和打印控件尺寸才能发现。

---

## 交互三：数字卡片上的前导零

### 提示词

```
你是一个资深 Tkinter 开发者。请帮我写一个函数，在 Canvas 上绘制一排数字卡片。

具体需求：
1. 每个数画在一张 80x58 的圆角卡片里，数字居中；
2. 数据一共 4 位（例如 51 要显示成 0051）；
3. 数字用等宽字体 Consolas，19 号加粗。

约束条件：
- 只写绘制部分，不要处理布局；
- 代码要有详细中文注释。
```

### AI 的原始输出（摘要）

```python
text = str(value).zfill(digits)
canvas.create_text(x + CARD_W / 2, y + CARD_H / 2, text=text, font=font)
```

补零是对的（用了 `zfill`），居中也是对的。单体看没有任何毛病。

### 我们发现的问题

问题出在"看得见"这一层，而不是"对不对"这一层：

1. **补出来的零和真实数字长得一模一样**。`0051` 里的两个 0 和真实数据位没有任何视觉区别，观众会以为这个数本来就是 0051。
2. **观众会因此误解算法**。当被问到"为什么 51 要进 1 号桶而不是 5 号桶"时，如果画面上 `0051` 四个数字一视同仁，这个疑问就无法当场解释清楚。

### 人工介入修改

我们把它拆成两段绘制，用不同颜色区分"补出来的位"和"真实的位"：

```python
leading = digits - len(str(value))          # 补出来的前导零个数
font = self.fonts["num"]
total_w = font.measure(text)                # 先量出整串宽度
x_start = x + (CARD_W - total_w) / 2        # 整体居中

if leading > 0:
    # 浅灰色画前导零
    canvas.create_text(x_start, cy, text=text[:leading],
                       anchor="w", font=font, fill=COLORS["text_dim"])
    # 深色画真实数字，起点接在灰字后面
    canvas.create_text(x_start + font.measure(text[:leading]), cy,
                       text=text[leading:], anchor="w", font=font,
                       fill=main_color)
```

关键是 `font.measure()`：要拼接两段不同颜色的文字并整体居中，必须知道第一段的像素宽度，否则接缝会错位。这个方法是查 Tkinter 文档找到的，AI 给的版本里没有涉及。

**这次介入的收获**：AI 完成的是"功能正确"，我们要的是"教学有效"。这两者之间隔着一层判断——**这个画面能不能让一个没学过基数排序的人看懂**。这种判断 AI 替不了，只能由人来提。

---

## 补充记录：给每一步加飞行动画（不计入三次核心记录）

**我们给的提示词**

> 排序过程数字放到下面的时候加一个动画，是数字移动过去的，回来也加动画。

**AI 的原始输出（大意）**

```python
# 在 ArrayView 里创建一个临时卡片，用 after 逐帧移动
def animate_to_bucket(self, start, end):
    card = self.create_rectangle(*start, fill=COLORS["card"])
    dx = (end[0] - start[0]) / 10
    dy = (end[1] - start[1]) / 10
    def step(n=0):
        if n >= 10:
            return
        self.move(card, dx, dy)
        self.after(16, step, n + 1)
    step()
```

**它错在哪**

跑起来第一眼就发现：卡片根本没动。原因是数组和桶各是一张独立的 Canvas，`move()` 只能在自己那张画布里挪，走到边界就被裁掉了——**Canvas 里的图元不可能跨画布移动，也不能真的透明**。

第二个问题是：就算把两层合并，动画过程中数组里会同时出现两张一样的卡片（原位置一张、飞行中一张），看起来像复制了一份。

**我们的修改**

第一步，把数组和桶合并成一张 924×660 的画布，两个绘制器改成"按传入的纵向偏移画"，不再自己持有 Canvas。

第二步，飞行期间不画"上一帧 + 飞行卡片"，而是画一个**混合画面**：

```python
if nxt.phase == "distribute":
    # 数组用上一帧（那个数还在原位），桶用这一帧但把目标槽位留空
    arr_show = replace(prev, active_index=-1, active_bucket=-1,
                       phase="distribute", digit_pos=nxt.digit_pos)
    return arr_show, nxt, {nxt.active_index}, [(b, k)], p0, p1

if nxt.phase == "collect":
    # 数组用这一帧（目标格子留空），桶用上一帧但把即将取出的那张留空
    bkt_show = replace(prev, phase="collect", active_index=-1,
                       active_bucket=b, digit_pos=nxt.digit_pos)
    return nxt, bkt_show, {nxt.active_index}, [(b, 0)], p0, p1
```

两端都空着，飞行卡片正好补上这个空缺。

第三步是看了截图才发现的：动画进行到一半，数组里亮着的不是正在飞的 2436，而是上一步的 7279。因为起点画面用的是**上一帧**的快照，它的 `active_index` 指向的是上一帧那个数，高亮就留在那儿了。清掉它才对：

```python
arr_show = replace(prev, active_index=-1, ...)
```

**这次介入的收获**：动画的难点从来不是"怎么让它动"，而是**"动的过程中，画面里没动的部分该显示哪一帧的状态"**。AI 给的方案能跑通一条直线，但它没有"画面是一帧一帧被组合出来的"这个概念。这类问题只能靠盯着屏幕看，一看就发现不对——代码本身不会报任何错。

---

## 附：我们总结的"AI 输出常见坑"清单

开发过程中我们整理了一份检查清单，用来在采纳 AI 代码前快速过一遍：

| 坑的类型 | 具体表现 | 我们的检查方式 |
|---|---|---|
| **静默失效** | 代码能跑、不报错，但界面空白或元素不可见 | 打印控件 `winfo_width()`、`winfo_height()` 验证 |
| **边界缺失** | 没处理空输入、超范围、重复值 | 逐条对照测试用例表 |
| **循环无上限** | `while` 没有重试上限，参数异常时死循环 | 检查每个 `while` 是否有退出条件 |
| **描述性要求落空** | 提示词说"要足够杂乱"，代码只保证随机 | 把形容词翻译成可执行判断 |
| **阻塞主线程** | 用 `time.sleep()` 做动画，界面假死 | 全局搜索 `time.sleep`，一律换成 `after()` |
| **过度自信的注释** | 注释写着"保持顺序"，实际用了 `pop()` 而非 `pop(0)` | 注释和代码逐行比对，以代码为准 |

---

**文档说明**：以上三次核心交互与一次补充记录均来自本项目开发过程中的真实调试记录。AI 原始输出部分为便于阅读作了摘要，关键代码片段保持原样。
