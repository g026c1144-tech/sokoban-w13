import json  # ★機能2：記録をファイルに保存するため

RECORD_FILE = "best_records.json"  # ★機能2：ベスト記録の保存先

LEVELS = [
    [
        "#########",
        "#       #",
        "#  .    #",
        "#  $    #",
        "#  @    #",
        "#       #",
        "#########",
    ],
    [
        "##########",
        "#        #",
        "#  ..    #",
        "#  $$    #",
        "#   @    #",
        "#        #",
        "##########",
    ],
    [
        "###########",
        "#         #",
        "#         #",
        "#    #    #",
        "#    #    #",
        "#  . # $  #",
        "#      @  #",
        "###########",
    ],
]

DIRECTIONS = {"w": (0, -1), "s": (0, 1), "a": (-1, 0), "d": (1, 0)}


def load_level(rows):
    walls, goals, boxes = set(), set(), set()
    player = None
    width = len(rows[0])
    if not rows or any(len(row) != width for row in rows):
        raise ValueError("マップの行の長さをそろえてください")
    for y, row in enumerate(rows):
        for x, ch in enumerate(row):
            pos = (x, y)
            if ch == "#":
                walls.add(pos)
            elif ch in ".+*":
                goals.add(pos)
            if ch in "$*":
                boxes.add(pos)
            if ch in "@+":
                if player is not None:
                    raise ValueError("プレイヤーは1人にしてください")
                player = pos
    if player is None or not boxes or len(boxes) != len(goals):
        raise ValueError("プレイヤー1人、箱とゴールは同じ数が必要です")
    return {"walls": walls, "goals": goals, "boxes": boxes, "player": player,
            "width": width, "height": len(rows), "moves": 0, "history": [],
            "pushes": 0}  # ★機能2：箱を押した回数


def draw_game(game):
    print("\n" * 2 + "=== SOKOBAN ===")
    print("# 壁   . ゴール   $ 箱   @ プレイヤー   * ゴール上の箱")
    for y in range(game["height"]):
        line = ""
        for x in range(game["width"]):
            pos = (x, y)
            if pos == game["player"]:
                line += "+" if pos in game["goals"] else "@"
            elif pos in game["boxes"]:
                line += "*" if pos in game["goals"] else "$"
            elif pos in game["walls"]:
                line += "#"
            elif pos in game["goals"]:
                line += "."
            else:
                line += " "
        print(line)
    # ★機能2：押した回数も表示
    print(f"移動回数: {game['moves']} | 押した回数: {game['pushes']}")
    # ★機能3：M キーの説明を追加
    print("WASD: 移動 / U: 一手戻す / R: リスタート / M: ステージ選択 / Q: 終了")


def inside(game, pos):
    return 0 <= pos[0] < game["width"] and 0 <= pos[1] < game["height"]


def move_player(game, key):
    if key not in DIRECTIONS:
        return False
    dx, dy = DIRECTIONS[key]
    x, y = game["player"]
    target = (x + dx, y + dy)
    if not inside(game, target) or target in game["walls"]:
        return False
    pushed_to = None
    if target in game["boxes"]:
        pushed_to = (target[0] + dx, target[1] + dy)
        if (not inside(game, pushed_to) or pushed_to in game["walls"]
                or pushed_to in game["boxes"]):
            return False
    # ★機能2：Undoで戻せるよう、押した回数も履歴に保存
    game["history"].append((game["player"], game["boxes"].copy(), game["pushes"]))
    if pushed_to is not None:
        game["boxes"].remove(target)
        game["boxes"].add(pushed_to)
        game["pushes"] += 1  # ★機能2
    game["player"] = target
    game["moves"] += 1
    return True


def undo(game):
    if game["history"]:
        # ★機能2：押した回数も元に戻す
        game["player"], game["boxes"], game["pushes"] = game["history"].pop()
        game["moves"] -= 1


def is_cleared(game):
    return game["boxes"] == game["goals"]


# ★機能1：デッドロック検出
def is_deadlocked(game):
    """角に詰まった箱（ゴール以外）があればTrueを返す。"""
    for (x, y) in game["boxes"]:
        if (x, y) in game["goals"]:
            continue  # ゴール上の箱は問題なし
        up = (x, y - 1) in game["walls"]
        down = (x, y + 1) in game["walls"]
        left = (x - 1, y) in game["walls"]
        right = (x + 1, y) in game["walls"]
        if (up or down) and (left or right):
            return True
    return False


# ★機能2：ベスト記録の読み込み
def load_records():
    """ファイルからベスト記録を読む。ファイルがなければ空の辞書を返す。"""
    try:
        with open(RECORD_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


# ★機能2：ベスト記録の保存
def save_records(records):
    """ベスト記録をファイルに書き込む。"""
    with open(RECORD_FILE, "w", encoding="utf-8") as f:
        json.dump(records, f)


# ★機能3：ステージ選択メニュー
def select_level(records):
    """ステージ一覧とベスト記録を表示し、選ばれたステージ番号(0始まり)を返す。
    Q が入力されたら None を返す（ゲーム終了）。"""
    print("\n=== ステージ選択 ===")
    for i in range(len(LEVELS)):
        print(f"{i + 1}: ステージ{i + 1}  (ベスト記録: {records.get(str(i), 'なし')})")
    print("Q: 終了")
    while True:
        choice = input(f"ステージ番号を入力 (1-{len(LEVELS)}) > ").strip().lower()
        if choice == "q":
            return None
        if choice.isdigit() and 1 <= int(choice) <= len(LEVELS):
            return int(choice) - 1
        print("正しい番号を入力してください。")


def main():
    records = load_records()  # ★機能2
    level_index = select_level(records)  # ★機能3：最初にステージを選ぶ
    if level_index is None:
        return
    game = load_level(LEVELS[level_index])
    while True:
        draw_game(game)
        # ★機能2：このステージのベスト記録を表示
        print(f"ベスト記録: {records.get(str(level_index), 'なし')}")
        if is_cleared(game):
            print("クリア！")
            # ★機能2：記録を更新したら保存
            best = records.get(str(level_index))
            if best is None or game["moves"] < best:
                records[str(level_index)] = game["moves"]
                save_records(records)
                print(f"★ 新記録！ {game['moves']} 手")
            # ★機能3：クリア後はステージ選択メニューに戻る
            input("Enterを押してステージ選択へ...")
            level_index = select_level(records)
            if level_index is None:
                break
            game = load_level(LEVELS[level_index])
            continue
        # ★機能1：箱が角に詰まったら警告
        if is_deadlocked(game):
            print("⚠ 箱が角に詰まりました！ U で戻すか R でリスタートしてください。")
        key = input("操作 > ").strip().lower()[:1]
        if key == "q":
            break
        if key == "r":
            game = load_level(LEVELS[level_index])
        elif key == "m":  # ★機能3：メニューに戻る
            level_index = select_level(records)
            if level_index is None:
                break
            game = load_level(LEVELS[level_index])
        elif key == "u":
            undo(game)
        else:
            move_player(game, key)
    print("ゲームを終了します。")


if __name__ == "__main__":
    main()