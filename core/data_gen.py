"""
数据生成模块
============

负责按项目需求生成演示用的随机数据。看似简单，但有两条硬约束：

1. **不能生成已经有序的数据**。基数排序演示的是"打乱的数据如何一步步变有序"，
   如果一开始就是有序的，整个演示既看不出过程，也没有说服力。

2. **每一个数位上都要有分散的数字**。这是容易被忽略的一条：假设生成的数里，
   十位全都是 0，那么第二轮分配时所有数都会进 0 号桶，画面上什么变化都没有，
   观众会以为程序卡死了。

因此 generate() 采用"生成 - 校验 - 重试"的策略，两道校验都通过才返回。
"""

import random

# 默认数据范围。上限取 9999 而不是 10000，原因见 README：
# 10000 是全范围内唯一的五位数，抽中它会把轮数从 4 变成 5，
# 多出整整一轮毫无意义的空转，演示效果很差。
DEFAULT_MIN = 1
DEFAULT_MAX = 9999

MAX_RETRY = 800


def digit_count(value: int) -> int:
    """返回一个正整数的十进制位数。例如 4821 -> 4，60 -> 2。"""
    if value == 0:
        return 1
    count = 0
    while value > 0:
        value //= 10
        count += 1
    return count


def max_digits(data: list[int]) -> int:
    """返回整组数据中的最大位数，它就是基数排序需要跑的轮数。"""
    if not data:
        return 1
    return max(digit_count(v) for v in data)


def is_sorted(data: list[int]) -> bool:
    """判断数据是否已经按从小到大排好序。"""
    return all(data[i] <= data[i + 1] for i in range(len(data) - 1))


def digit_spread_ok(data: list[int], digits: int) -> bool:
    """
    检查每一位上是否至少出现了 2 种不同的数字。

    digits 是最大位数。例如 digits=4 时，会分别检查个位、十位、百位、千位。
    任何一位只有一种数字，就认为这组数据不合格。
    """
    for pos in range(digits):
        distinct = {(v // (10 ** pos)) % 10 for v in data}
        if len(distinct) < 2:
            return False
    return True


def generate(n: int, lo: int = DEFAULT_MIN, hi: int = DEFAULT_MAX) -> list[int]:
    """
    生成 n 个互不重复、足够杂乱的随机数。

    策略：反复生成，直到同时满足
      - 不是有序的
      - 每一位都有至少 2 种数字
    若重试次数耗尽（理论上极少发生），降级为"只保证不有序"，
    确保函数一定会返回，不会卡死界面。
    """
    if n <= 0:
        return []
    if hi - lo + 1 < n:
        raise ValueError(f"取值范围 [{lo}, {hi}] 容不下 {n} 个不重复的数")

    for _ in range(MAX_RETRY):
        data = random.sample(range(lo, hi + 1), n)
        random.shuffle(data)
        digits = max_digits(data)
        if is_sorted(data):
            continue
        if not digit_spread_ok(data, digits):
            continue
        return data

    # 兜底：只要不是有序的就行
    while True:
        data = random.sample(range(lo, hi + 1), n)
        if not is_sorted(data):
            return data


def pad_to(value: int, digits: int) -> str:
    """
    把数字补零到指定位数，返回字符串。

    补出来的前导零在界面上会用浅灰色绘制，用来提醒观众
    "这些 0 不是数据本身的，是为了让所有数等长而补的"。
    """
    return str(value).zfill(digits)
