import mesa
from kyon.random_walk import RandomWalker

class Kyon(RandomWalker):
    """
    草原を歩き回り、繁殖し（無性繁殖）、捕食されるキョン。
    初期化メソッドはRandomWalkerと同じです。
    """
    
    def __init__(self, unique_id, pos, model, moore, kyon_reproduce_count=False, after_birth=0):
        super().__init__(unique_id, pos, model, moore=moore)
        self.kyon_reproduce_count = kyon_reproduce_count  # 繁殖フラグの初期化
        self.after_birth = after_birth
        self.in_food_area = False
        self.steps_in_food_area = 0  # 食物資源エリア内にいるターン数
        self.avoiding_trap = False  # 罠を避けるフラグ
        self.avoid_trap_steps = 0   # 罠を避ける期間のカウント
        self.avoiding_food_area = False  # 食物資源エリアを避けるフラグ
        self.avoid_food_area_steps = 0   # 食物資源エリアを避けるカウント

    def step(self):
        """
        キョンの1ステップ。移動、罠のチェック、食物資源エリアの確認、繁殖、死亡を行う。
        """
        self.kyon_reproduce_count = False  # ステップごとに繁殖フラグをリセット
        self.after_birth += 1

        # 罠を避ける期間中かどうかを確認
        if self.avoiding_trap:
            # 罠を避けている期間中は罠に近づかない
            self.random_move()  # ランダムに移動して罠から離れる
            self.avoid_trap_steps += 1
            if self.avoid_trap_steps >= 7:  # 罠を避ける期間が終了したらリセット
                self.avoiding_trap = False
                self.avoid_trap_steps = 0
            
            return  # 他の処理は行わない

        # 食物資源エリアを避けている期間かどうかを確認
        if self.avoiding_food_area:
            # 食物資源エリアを避ける期間中は近づかない
            self.random_move()  # ランダムに移動してエリアを避ける
            self.avoid_food_area_steps += 1
            if self.avoid_food_area_steps >= 5:  # 5ステップ避けたらリセット
                self.avoiding_food_area = False
                self.avoid_food_area_steps = 0
            return  # 他の処理は行わない

        # 現在のセル情報を取得
        current_cell = self.model.grid.get_cell_list_contents([self.pos])

        # キョンが罠に引き寄せられる特性
        nearest_trap = self.find_nearest_trap()
        # 罠が近くにある場合、通常は近づくが、罠を避けている場合はランダムに移動
        if nearest_trap and self.model.get_distance(self.pos, nearest_trap.pos) <= 5:
            if not self.avoiding_trap:  # 罠を避けていない場合のみ近づく
                if self.random.random() < 0.7:  # 70%の確率で罠に近づく
                    self.move_towards(nearest_trap.pos)
                else:
                    self.random_move()

                # 罠に入った場合、捕獲をチェック
                if self.check_for_trap():
                    return  # 捕獲された場合は終了


        # キョンが食物資源エリア内にいるかを確認
        in_food_area = any(isinstance(obj, FoodResourceArea) for obj in current_cell)

        # 食物資源エリア内にいる場合の動き
        if in_food_area:
            self.steps_in_food_area += 1
            if self.steps_in_food_area < 3:   # 食物資源エリアに3ターン以内で滞在
                self.random_move()
            else:
                # エリアから出て、5ステップ避けるフラグを立てる
                self.avoiding_food_area = True
                self.steps_in_food_area = 0
                self.random_move()
        else:
            # 食物資源エリア外にいる場合
            self.steps_in_food_area = 0
            nearest_food_area = self.find_nearest_food_area()
            if nearest_food_area:
                distance_to_food_area = self.model.get_distance(self.pos, nearest_food_area.pos)
                if distance_to_food_area <= 5:
                    if self.random.random() < 0.7:  # 70%の確率で食物資源エリアに向かう
                        self.move_towards(nearest_food_area.pos)
                    else:
                        self.random_move()
                else:
                    if self.random.random() < 0.2:  # 20%の確率で遠くから食物資源エリアに向かう
                        self.move_towards(nearest_food_area.pos)
                    else:
                        self.random_move()
            else:
                self.random_move()


        # 死亡処理
        if self.random.random() < (1 / 1000) * (self.after_birth / 540):
            self.model.grid.remove_agent(self)
            self.model.schedule.remove(self)
            return  # 死亡した場合は以降の処理を行わない

        # 繁殖処理
        if self.after_birth >= 150 and self.random.random() < (1/2) * (1/210):
            lamb = Kyon(
                self.model.next_id(), self.pos, self.model, self.moore, kyon_reproduce_count=True, after_birth=0
            )
            self.model.grid.place_agent(lamb, self.pos)
            self.model.schedule.add(lamb)
            self.kyon_reproduce_count = True

    def check_for_trap(self):
        """
        現在の位置に罠があるかどうかを確認し、捕獲が成功するか判定。
        捕獲されなかった場合、罠を避けるように設定する。
        """
        current_cell = self.model.grid.get_cell_list_contents([self.pos])
        trap_in_cell = [obj for obj in current_cell if isinstance(obj, Trap)]

        if trap_in_cell:
            for trap in trap_in_cell:
                if trap.recovery_timer == 0:  # 罠が稼働中かどうか
                    success_rate = trap.calculate_trap_success_rate(self.pos)
                    if self.random.random() < success_rate:
                        # 捕獲成功
                        self.model.grid.remove_agent(self)
                        self.model.schedule.remove(self)
                        trap.is_hunt = True
                        trap.recovery_timer = trap.trap_recovery_turns
                        return True  # 捕獲成功
                    else:
                        # 捕獲失敗（罠を避けるフラグを立てる）
                        self.avoiding_trap = True
                        self.avoid_trap_steps = 0
                        return False
        return False

    def find_nearest_food_area(self):
        """
        最も近い食物資源エリアを見つけ、その位置を返す。
        """
        min_distance = float("inf")
        nearest_food_area = None
        for food_area in [agent for agent in self.model.schedule.agents if isinstance(agent, FoodResourceArea)]:
            distance = self.model.get_distance(self.pos, food_area.pos)
            if distance < min_distance:
                min_distance = distance
                nearest_food_area = food_area
        return nearest_food_area

    def find_nearest_trap(self):
        """
        最も近い罠を見つけ、その位置を返す
        """
        min_distance = float("inf")
        nearest_trap = None
        for trap in [agent for agent in self.model.schedule.agents if isinstance(agent, Trap)]:
            distance = self.model.get_distance(self.pos, trap.pos)
            if distance < min_distance:
                min_distance = distance
                nearest_trap = trap
        return nearest_trap    
       
#    def move_towards(self, target_pos):
#        """
#        指定された位置に向かって移動する
#        """
#        possible_steps = self.model.grid.get_neighborhood(self.pos, moore=True, include_center=False)
#        next_step = min(possible_steps, key=lambda x: self.model.get_distance(x, target_pos))
#        self.model.grid.move_agent(self, next_step)




class Trap(mesa.Agent):
    """
    トラップエージェント（罠）。植生の密度に応じて捕獲確率が異なる。
    """
    def __init__(self, unique_id, pos, model, is_hunt=False, trap_recovery_turns=0):
        super().__init__(unique_id, model)
        self.is_hunt = False
        self.trap_recovery_turns = trap_recovery_turns
        self.recovery_timer = 0

    def step(self):
        """
        罠のステップ。再稼働までのカウントダウンを行う。
        """
        if self.recovery_timer > 0:
            self.recovery_timer -= 1
        if self.recovery_timer == 0:
            self.is_hunt = False

            # 現在のマスにキョンがいるかどうかを確認して捕獲を試みる
            current_cell = self.model.grid.get_cell_list_contents([self.pos])
            kyon_in_cell = [obj for obj in current_cell if isinstance(obj, Kyon)]

            if kyon_in_cell:
                for kyon in kyon_in_cell:
                    success_rate = self.calculate_trap_success_rate(self.pos)
                    if self.random.random() < success_rate:
                        self.model.grid.remove_agent(kyon)
                        self.model.schedule.remove(kyon)
                        self.is_hunt = True
                        self.recovery_timer = self.trap_recovery_turns
                        return

    def calculate_trap_success_rate(self, position):
        """
        現在のマスに基づいて、罠の捕獲成功率を計算する。
        """
        current_cell = self.model.grid.get_cell_list_contents([position])
        vegetation_density = [obj for obj in current_cell if isinstance(obj, VegetationDensity)][0]
        
        if vegetation_density.density == "dense":
            success_rate = self.model.base_success_rate * self.model.dense_vegetation_modifier
        elif vegetation_density.density == "normal":
            success_rate = self.model.base_success_rate * self.model.normal_vegetation_modifier
        else:
            success_rate = self.model.base_success_rate * self.model.sparse_vegetation_modifier

        # 食物資源エリアでの成功率を調整
        in_food_area = any(isinstance(obj, FoodResourceArea) for obj in current_cell)
        if in_food_area:
            success_rate *= 1.5

        return success_rate


class VegetationDensity(mesa.Agent):
    """
    各セルに植生密度を設定するエージェント。密度は "dense"（濃い）、"normal"（普通）、"sparse"（薄い）のいずれか。
    """
    def __init__(self, unique_id, pos, model, density):
        super().__init__(unique_id, model)
        self.pos = pos
        self.density = density

    def step(self):
        pass


class FoodResourceArea(mesa.Agent):
    """
    フィールド上の食物資源エリアを表すエージェント。エリア内ではキョンの動きに影響を与える。
    """
    def __init__(self, unique_id, pos, model):
        super().__init__(unique_id, model)
        self.pos = pos

    def step(self):
        pass
