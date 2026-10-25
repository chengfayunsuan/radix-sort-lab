"""
基数排序引擎（LSD，Least Significant Digit first，最低位优先）
=============================================================

核心设计：**快照序列**
----------------------
本模块不直接操作界面，而是在初始化时把整个排序过程"一口气算完"，
每一步生成一张完整的画面快照（Snapshot），存进一个列表。

界面层只需要按索引取快照来绘制即可。这样做的好处：

1. 单步 / 上一步 / 自动播放 / 跳转到某一轮，全部退化成"改一个下标"；
2. 逻辑与界面彻底解耦，两个人可以同时改不同的文件而互不影响；
3. 可以脱离界面单独测试——引擎跑对了，画面就一定是对的。

算法原理（为什么这样能排好序）
------------------------------
每一轮只处理一个数位，从最低位（个位）开始，依次向高位推进。
每一轮做两件事：

  分配：按当前位的数字，把每个数丢进 0~9 号桶
  收集：从 0 号桶到 9 号桶，依次把数倒回数组

关键点在于**收集时必须保持桶内的原有顺序**，这叫作"稳定性"。
正因为稳定，上一轮排好的低位顺序才不会被打乱，高位排序时它被完整保留下来。
如果收集时不保持顺序（比如在桶里再排一次序），整个算法立刻失效。
"""

from dataclasses import dataclass, field

from .data_gen import max_digits


# 位的中文名称，用于界面提示与日志
DIGIT_NAMES = ["个位", "十位", "百位", "千位", "万位"]


def digit_name(pos: int) -> str:
    """返回第 pos 位的名称。pos=0 是个位。"""
    if 0 <= pos < len(DIGIT_NAMES):
        return DIGIT_NAMES[pos]
    return f"第 {pos + 1} 位"


def get_digit(value: int, pos: int) -> int:
    """取出一个整数第 pos 位上的数字。pos=0 表示个位。"""
    return (value // (10 ** pos)) % 10


@dataclass
class Snapshot:
    """一帧画面。界面拿到它就能把整个屏幕画出来。"""

    step_no: int                     # 第几步，从 0 开始
    array: list                      # 当前数组顺序，收集过程中可能含 None（还没填的格子）
    buckets: list                    # 10 个桶，每个桶是一个整数列表，按先进先出排列
    active_value: int | None         # 当前正在处理的数，None 表示没有
    active_index: int                # 该数在数组中的下标，-1 表示无
    active_bucket: int               # 正在操作的桶号，-1 表示无
    round_no: int                    # 第几轮（从 1 开始），0 表示尚未开始
    digit_pos: int                   # 当前处理的是哪一位，0 = 个位
    phase: str                       # init / distribute / collect / done
    message: str                     # 这一句话会显示在状态栏，也会写进日志


@dataclass
class Stats:
    """排序过程产生的统计数据，用于和比较类排序做对比。"""

    total_numbers: int = 0
    digits: int = 0                  # 位数，也就是轮数
    total_steps: int = 0
    moves: int = 0                   # 元素移动总次数（分配一次 + 收集一次）
    compares: int = 0                # 比较次数，基数排序恒为 0


class RadixEngine:
    """把一组数据展开成一条完整的快照序列。"""

    def __init__(self, data: list[int]):
        self.data = list(data)
        self.rounds = max_digits(self.data)      # 轮数 = 最大位数
        self.snapshots: list[Snapshot] = []
        self.stats = Stats(
            total_numbers=len(self.data),
            digits=self.rounds,
            # 每轮：分配 n 次 + 收集 n 次
            moves=2 * len(self.data) * self.rounds,
            compares=0,
        )
        self._build()
        self.stats.total_steps = len(self.snapshots)

    # ------------------------------------------------------------------
    # 内部：追加一张快照
    # ------------------------------------------------------------------
    def _snap(self, array, buckets, phase, message,
              round_no=0, digit_pos=0,
              active_value=None, active_index=-1, active_bucket=-1):
        self.snapshots.append(Snapshot(
            step_no=len(self.snapshots),
            array=list(array),                       # 必须复制，否则后续修改会污染历史快照
            buckets=[list(b) for b in buckets],
            active_value=active_value,
            active_index=active_index,
            active_bucket=active_bucket,
            round_no=round_no,
            digit_pos=digit_pos,
            phase=phase,
            message=message,
        ))

    # ------------------------------------------------------------------
    # 主流程
    # ------------------------------------------------------------------
    def _build(self):
        n = len(self.data)
        arr = list(self.data)
        empty_buckets = [[] for _ in range(10)]

        self._snap(
            arr, empty_buckets, "init",
            f"共 {n} 个数据，最大 {self.rounds} 位，因此要跑 {self.rounds} 轮。"
            f"每轮分「分配」和「收集」两个阶段。",
        )

        for r in range(self.rounds):
            pos = r
            buckets = [[] for _ in range(10)]

            # ---------------- 分配阶段 ----------------
            for i, value in enumerate(arr):
                d = get_digit(value, pos)
                buckets[d].append(value)
                self._snap(
                    arr, buckets, "distribute",
                    f"第 {r + 1} 轮 · 分配：{value} 的{digit_name(pos)}是 {d}，进入 {d} 号桶",
                    round_no=r + 1, digit_pos=pos,
                    active_value=value, active_index=i, active_bucket=d,
                )

            # ---------------- 收集阶段 ----------------
            remain = [list(b) for b in buckets]   # 收集过程中桶会逐个变空
            recv = [None] * n                     # 结果数组，格子逐个填满
            j = 0
            for b in range(10):
                while remain[b]:
                    value = remain[b].pop(0)      # 严格先进先出，这就是稳定性的实现
                    recv[j] = value
                    j += 1
                    self._snap(
                        recv, remain, "collect",
                        f"第 {r + 1} 轮 · 收集：从 {b} 号桶取出 {value}，放到第 {j} 个位置",
                        round_no=r + 1, digit_pos=pos,
                        active_value=value, active_index=j - 1, active_bucket=b,
                    )
            arr = recv

            self._snap(
                arr, [[] for _ in range(10)], "round_end",
                f"第 {r + 1} 轮结束。现在这组数按「{digit_name(pos)}及更低位」已经有序了。",
                round_no=r + 1, digit_pos=pos,
            )

        self._snap(
            arr, [[] for _ in range(10)], "done",
            f"全部 {self.rounds} 轮完成，排序结束。"
            f"全过程移动 {self.stats.moves} 次，比较 0 次。",
            round_no=self.rounds, digit_pos=self.rounds - 1,
        )

    # ------------------------------------------------------------------
    # 供界面调用的便捷方法
    # ------------------------------------------------------------------
    def get(self, index: int) -> Snapshot:
        """取第 index 张快照，越界时自动夹紧到有效范围。"""
        if not self.snapshots:
            raise RuntimeError("快照序列为空，说明数据有问题")
        index = max(0, min(index, len(self.snapshots) - 1))
        return self.snapshots[index]

    def round_end_indices(self) -> list[int]:
        """返回每一轮结束那一帧的下标，用于"跳到下一轮"。"""
        return [s.step_no for s in self.snapshots if s.phase == "round_end"]

    def bucket_usage(self) -> dict[int, int]:
        """
        统计每个桶一共收进过多少个数，用于侧栏的桶使用情况小图。
        （只统计分配阶段，不重复统计收集阶段）
        """
        usage = {i: 0 for i in range(10)}
        for s in self.snapshots:
            if s.phase == "distribute":
                usage[s.active_bucket] += 1
        return usage
