"""
1回に1つのグリッドセルをランダムに移動する一般的な動作。
"""

import mesa


class RandomWalker(mesa.Agent):
    """
    ランダムウォーカーのメソッドを一般的な方法で実装するクラス。

    単独で使用することを目的とせず、他のエージェントにそのメソッドを継承させるために使われる。
    """

    grid = None
    x = None
    y = None
    moore = True

    def __init__(self, unique_id, pos, model, moore=True):
        """
        grid: エージェントが存在するMultiGridオブジェクト。
        x: エージェントの現在のx座標。
        y: エージェントの現在のy座標。
        moore: Trueの場合、全8方向に移動可能。
               それ以外の場合、上下左右にのみ移動可能。
        """
        super().__init__(unique_id, model)
        self.pos = pos
        self.moore = moore

    def random_move(self, move_steps=1):
        """
        許可された方向のいずれかに指定されたセル数だけ移動する。

        move_steps: 移動するセル数（デフォルトは1）
        """
        for _ in range(move_steps):
            # 隣接するセルから次のセルを選択する。
            next_moves = self.model.grid.get_neighborhood(self.pos, self.moore, True)
            next_move = self.random.choice(next_moves)
            # 移動する:
            self.model.grid.move_agent(self, next_move)