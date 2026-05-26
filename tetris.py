#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
俄罗斯方块 — 基于 pygame。
操作：← → 移动，↑ 旋转，↓ 加速下落，空格硬降，R 重新开始，Esc 退出。
"""

from __future__ import annotations

import random
import sys

import pygame

# —— 窗口与网格 ——
CELL = 32
COLS, ROWS = 10, 20
SIDE_PANEL = 200
HUD_LINES = 5
TOP_MARGIN = HUD_LINES * CELL

WIDTH = COLS * CELL + SIDE_PANEL
HEIGHT = ROWS * CELL + TOP_MARGIN

FPS = 60
INITIAL_FALL_MS = 800
FAST_FALL_MS = 50
LOCK_DELAY_MS = 500

BLACK = (15, 15, 20)
GRID_COLOR = (40, 40, 55)
BORDER_COLOR = (80, 80, 100)
TEXT_COLOR = (220, 220, 230)
ACCENT = (100, 180, 255)

# 七种方块：每种为多个旋转形态，5x5 点阵字符串，'#' 为方块
SHAPES_STR = [
    [  # I
        [
            "..#..",
            "..#..",
            "..#..",
            "..#..",
            ".....",
        ],
        [
            ".....",
            ".....",
            "####.",
            ".....",
            ".....",
        ],
    ],
    [  # O
        [
            ".....",
            ".....",
            ".##..",
            ".##..",
            ".....",
        ],
    ],
    [  # T
        [
            ".....",
            ".....",
            ".#...",
            "###..",
            ".....",
        ],
        [
            ".....",
            ".....",
            ".#...",
            ".##..",
            ".#...",
        ],
        [
            ".....",
            ".....",
            ".....",
            "###..",
            ".#...",
        ],
        [
            ".....",
            ".....",
            ".#...",
            "##...",
            ".#...",
        ],
    ],
    [  # S
        [
            ".....",
            ".....",
            ".##..",
            "##...",
            ".....",
        ],
        [
            ".....",
            ".#...",
            ".##..",
            "..#..",
            ".....",
        ],
    ],
    [  # Z
        [
            ".....",
            ".....",
            "##...",
            ".##..",
            ".....",
        ],
        [
            ".....",
            "..#..",
            ".##..",
            ".#...",
            ".....",
        ],
    ],
    [  # J
        [
            ".....",
            ".#...",
            ".#...",
            "##...",
            ".....",
        ],
        [
            ".....",
            ".....",
            ".#...",
            "###..",
            ".....",
        ],
        [
            ".....",
            ".....",
            ".##..",
            "..#..",
            "..#..",
            ".....",
        ],
        [
            ".....",
            ".....",
            ".....",
            "###..",
            "..#..",
            ".....",
        ],
    ],
    [  # L
        [
            ".....",
            "..#..",
            "..#..",
            ".##..",
            ".....",
        ],
        [
            ".....",
            ".....",
            "###..",
            "#....",
            ".....",
        ],
        [
            ".....",
            "##...",
            ".#...",
            ".#...",
            ".....",
        ],
        [
            ".....",
            ".....",
            "..#..",
            "###..",
            ".....",
        ],
    ],
]


def parse_shape(strings: list[str]) -> list[tuple[int, int]]:
    cells: list[tuple[int, int]] = []
    for r, row in enumerate(strings):
        for c, ch in enumerate(row):
            if ch == "#":
                cells.append((c, r))
    return cells


SHAPES: list[list[list[tuple[int, int]]]] = [
    [parse_shape(rot) for rot in piece] for piece in SHAPES_STR
]

COLORS = [
    (0, 240, 240),  # I 青
    (240, 240, 0),  # O 黄
    (160, 0, 240),  # T 紫
    (0, 240, 0),  # S 绿
    (240, 0, 0),  # Z 红
    (0, 0, 240),  # J 蓝
    (240, 160, 0),  # L 橙
]


def empty_grid() -> list[list[int | None]]:
    return [[None for _ in range(COLS)] for _ in range(ROWS)]


class Piece:
    __slots__ = ("kind", "rot", "x", "y")

    def __init__(self, kind: int) -> None:
        self.kind = kind
        self.rot = 0
        self.x = COLS // 2 - 2
        self.y = 0

    def cells(self) -> list[tuple[int, int]]:
        rots = SHAPES[self.kind]
        base = rots[self.rot % len(rots)]
        return [(self.x + cx, self.y + cy) for cx, cy in base]


def valid(piece: Piece, grid: list[list[int | None]], dx: int = 0, dy: int = 0, drot: int = 0) -> bool:
    rots = SHAPES[piece.kind]
    new_rot = (piece.rot + drot) % len(rots)
    base = rots[new_rot]
    nx, ny = piece.x + dx, piece.y + dy
    for cx, cy in base:
        gx, gy = nx + cx, ny + cy
        if gx < 0 or gx >= COLS or gy >= ROWS:
            return False
        if gy >= 0 and grid[gy][gx] is not None:
            return False
    return True


def merge(piece: Piece, grid: list[list[int | None]]) -> None:
    for gx, gy in piece.cells():
        if gy >= 0:
            grid[gy][gx] = piece.kind


def clear_lines(grid: list[list[int | None]]) -> int:
    new_rows: list[list[int | None]] = [row for row in grid if any(c is None for c in row)]
    cleared = ROWS - len(new_rows)
    while len(new_rows) < ROWS:
        new_rows.insert(0, [None for _ in range(COLS)])
    grid[:] = new_rows
    return cleared


def draw_cell(
    surf: pygame.Surface,
    gx: int,
    gy: int,
    color: tuple[int, int, int],
    offset_y: int = 0,
) -> None:
    px = gx * CELL
    py = gy * CELL + offset_y
    inner = pygame.Rect(px + 2, py + 2, CELL - 4, CELL - 4)
    pygame.draw.rect(surf, color, inner, border_radius=3)
    lighter = tuple(min(255, c + 40) for c in color)
    darker = tuple(max(0, c - 40) for c in color)
    pygame.draw.line(surf, lighter, inner.topleft, (inner.right - 1, inner.top), 2)
    pygame.draw.line(surf, lighter, inner.topleft, (inner.left, inner.bottom - 1), 2)
    pygame.draw.line(surf, darker, (inner.left + 1, inner.bottom - 1), (inner.right - 1, inner.bottom - 1), 2)
    pygame.draw.line(surf, darker, (inner.right - 1, inner.top + 1), (inner.right - 1, inner.bottom - 1), 2)


def ghost_y(piece: Piece, grid: list[list[int | None]]) -> int:
    y = piece.y
    while valid(piece, grid, dy=y - piece.y + 1):
        y += 1
    return y


def run() -> None:
    pygame.init()
    pygame.display.set_caption("俄罗斯方块 Tetris")
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("pingfang sc", 22)
    font_small = pygame.font.SysFont("pingfang sc", 16)

    grid = empty_grid()
    current = Piece(random.randrange(len(SHAPES)))
    next_kind = random.randrange(len(SHAPES))
    score = 0
    level = 1
    lines_total = 0
    game_over = False

    fall_ms = INITIAL_FALL_MS
    fall_acc = 0
    lock_timer = 0
    soft_drop = False

    def new_piece() -> None:
        nonlocal current, next_kind, game_over
        current = Piece(next_kind)
        next_kind = random.randrange(len(SHAPES))
        if not valid(current, grid):
            game_over = True

    def update_level() -> None:
        nonlocal level, fall_ms
        level = lines_total // 10 + 1
        fall_ms = max(100, INITIAL_FALL_MS - (level - 1) * 70)

    while True:
        dt = clock.tick(FPS)
        now_soft = soft_drop

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit(0)
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit(0)
                if game_over and event.key == pygame.K_r:
                    grid = empty_grid()
                    current = Piece(random.randrange(len(SHAPES)))
                    next_kind = random.randrange(len(SHAPES))
                    score = 0
                    level = 1
                    lines_total = 0
                    game_over = False
                    fall_ms = INITIAL_FALL_MS
                    fall_acc = 0
                    lock_timer = 0
                    continue
                if game_over:
                    continue
                if event.key == pygame.K_LEFT and valid(current, grid, dx=-1):
                    current.x -= 1
                    lock_timer = 0
                elif event.key == pygame.K_RIGHT and valid(current, grid, dx=1):
                    current.x += 1
                    lock_timer = 0
                elif event.key == pygame.K_UP:
                    if valid(current, grid, drot=1):
                        current.rot = (current.rot + 1) % len(SHAPES[current.kind])
                        lock_timer = 0
                elif event.key == pygame.K_DOWN:
                    soft_drop = True
                elif event.key == pygame.K_SPACE and not game_over:
                    gy = ghost_y(current, grid)
                    drop = gy - current.y
                    current.y = gy
                    score += drop * 2
                    merge(current, grid)
                    n = clear_lines(grid)
                    if n:
                        score += [0, 100, 300, 500, 800][min(n, 4)] * level
                        lines_total += n
                        update_level()
                    new_piece()
                    fall_acc = 0
                    lock_timer = 0
            if event.type == pygame.KEYUP and event.key == pygame.K_DOWN:
                soft_drop = False

        screen.fill(BLACK)

        # 主游戏区边框
        board_rect = pygame.Rect(0, TOP_MARGIN, COLS * CELL, ROWS * CELL)
        pygame.draw.rect(screen, BORDER_COLOR, board_rect, 2)

        # 网格线
        for c in range(1, COLS):
            x = c * CELL
            pygame.draw.line(screen, GRID_COLOR, (x, TOP_MARGIN), (x, HEIGHT))
        for r in range(1, ROWS):
            y = r * CELL + TOP_MARGIN
            pygame.draw.line(screen, GRID_COLOR, (0, y), (COLS * CELL, y))

        # 已锁定方块
        for gy in range(ROWS):
            for gx in range(COLS):
                k = grid[gy][gx]
                if k is not None:
                    draw_cell(screen, gx, gy, COLORS[k], TOP_MARGIN)

        if not game_over:
            gy = ghost_y(current, grid)
            rots = SHAPES[current.kind]
            base = rots[current.rot % len(rots)]
            ghost_cells = [(current.x + cx, gy + cy) for cx, cy in base]
            for gx, gy2 in ghost_cells:
                if gy2 >= 0:
                    px = gx * CELL + CELL // 4
                    py = gy2 * CELL + TOP_MARGIN + CELL // 4
                    s = pygame.Surface((CELL // 2, CELL // 2), pygame.SRCALPHA)
                    s.fill((*COLORS[current.kind], 60))
                    screen.blit(s, (px, py))

            for gx, gy2 in current.cells():
                if gy2 >= 0:
                    draw_cell(screen, gx, gy2, COLORS[current.kind], TOP_MARGIN)

        # 右侧信息
        sx = COLS * CELL + 16
        sy = 16
        for i, line in enumerate(
            [
                f"分数: {score}",
                f"等级: {level}",
                f"消行: {lines_total}",
                "",
                "下一块:",
            ]
        ):
            screen.blit(font.render(line, True, TEXT_COLOR), (sx, sy + i * 28))

        # 预览下一块
        preview_base = SHAPES[next_kind][0]
        mini = CELL // 2
        ox = sx + 20
        oy = sy + 28 * HUD_LINES + 8
        for cx, cy in preview_base:
            rect = pygame.Rect(ox + cx * mini, oy + cy * mini, mini - 2, mini - 2)
            pygame.draw.rect(screen, COLORS[next_kind], rect, border_radius=2)

        help_y = HEIGHT - 120
        for i, h in enumerate(
            [
                "← → 移动  ↑ 旋转",
                "↓ 软降  空格硬降",
                "R 重来  Esc 退出",
            ]
        ):
            screen.blit(font_small.render(h, True, ACCENT), (sx, help_y + i * 22))

        if game_over:
            overlay = pygame.Surface((COLS * CELL, ROWS * CELL), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180))
            screen.blit(overlay, (0, TOP_MARGIN))
            go = font.render("游戏结束 — 按 R 重来", True, ACCENT)
            screen.blit(go, go.get_rect(center=(COLS * CELL // 2, TOP_MARGIN + ROWS * CELL // 2)))
        else:
            grounded = not valid(current, grid, dy=1)
            if grounded:
                lock_timer += dt
            else:
                lock_timer = 0

            if grounded and lock_timer >= LOCK_DELAY_MS:
                merge(current, grid)
                n = clear_lines(grid)
                if n:
                    score += [0, 100, 300, 500, 800][min(n, 4)] * level
                    lines_total += n
                    update_level()
                new_piece()
                lock_timer = 0
                fall_acc = 0
            else:
                fall_interval = FAST_FALL_MS if now_soft else fall_ms
                fall_acc += dt
                if fall_acc >= fall_interval:
                    fall_acc = 0
                    if valid(current, grid, dy=1):
                        current.y += 1
                        lock_timer = 0
                        if now_soft:
                            score += 1

        pygame.display.flip()


if __name__ == "__main__":
    run()
