"""main.py – entry point with correct Bot constructor (expects grid)."""
from __future__ import annotations

import pygame
import random
from typing import List, Tuple, Optional, cast

import config
from cell import Cell
from grid import Grid
from bot import Bot
from item import Item
from ui import UI
from state import SimulationState


def _require_cell(c: Optional[Cell]) -> Cell:
    assert c is not None, "Expected non‑None Cell"
    return cast(Cell, c)


def main() -> None:
    pygame.init()
    state = SimulationState()

    grid_w_px = config.GRID_WIDTH * config.CELL_SPACING
    grid_h_px = config.GRID_HEIGHT * config.CELL_SPACING
    screen = pygame.display.set_mode((grid_w_px + 300, max(grid_h_px, 600)))
    pygame.display.set_caption("Warehouse Simulator")

    grid = Grid()
    bots: List[Bot] = []
    grid.bots = bots  # type: ignore[attr-defined]
    first_cell = _require_cell(grid.get_cell(0, config.INBOUND_CELLS) or grid.get_cell(0, 0))
    colour = config.PATH_COLORS[0 % len(config.PATH_COLORS)]
    bots.append(Bot("a", first_cell, grid, color=colour))

    ui = UI(grid, bots, state)

    clock = pygame.time.Clock()
    pref_timer = 0.0
    auto_in_timer = 0.0
    auto_out_timer = 0.0
    running = True

    while running:
        dt = clock.tick(60) / 1000.0
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                running = False
            ui.handle_event(ev)

        # UI flags → bot list changes
        if state.request_add_bot:
            state.request_add_bot = False
            new_id = "a" if not bots else chr(ord(bots[-1].bot_id) + 1)
            rest_cell = _require_cell(grid.get_cell(0, config.GRID_HEIGHT - 1) or grid.get_cell(0, 0))
            colour = config.PATH_COLORS[len(bots) % len(config.PATH_COLORS)]
            bots.append(Bot(new_id, rest_cell, grid, color=colour))
            ui.bots = bots
        if state.request_remove_bot:
            state.request_remove_bot = False
            if bots:
                bots.pop()
                ui.bots = bots

        # inbound quick‑demo
        if state.awaiting_inbound_input is not None:
            in_c = state.awaiting_inbound_input
            in_c.add_item(Item(f"ITEM{pygame.time.get_ticks() % 1000:03}"))
            state.awaiting_inbound_input = None

        # automatic inbound/outbound generation
        auto_in_timer += dt
        auto_out_timer += dt
        if state.auto_inbound and auto_in_timer >= 1.0:
            auto_in_timer = 0.0
            y_idx = random.randint(0, config.INBOUND_CELLS - 1)
            c = grid.get_cell(0, y_idx)
            if c:
                c.add_item(Item(f"ITEM{random.randint(0,999):03}"))
                state.auto_in_count += 1
        if state.auto_outbound and auto_out_timer >= 1.0:
            auto_out_timer = 0.0
            best_pref, best_code = -1, None
            for col in grid.cells:
                for cell in col:
                    if cell.type in ("storage", "inbound"):
                        for it in cell.items:
                            if it.preference > best_pref:
                                best_pref = it.preference
                                best_code = it.code
            if best_code:
                state.manual_requests.append((best_code, 1))
                state.auto_mode = False
                state.auto_out_count += 1

        # preference update
        pref_timer += dt
        pref_updated = False
        if pref_timer >= config.PREFERENCE_UPDATE_INTERVAL:
            pref_timer = 0.0
            pref_updated = True
            for col in grid.cells:
                for cell in col:
                    for it in cell.items:
                        it.update_preference()

        # queues shorthand
        man_q = state.manual_requests
        auto_q = state.auto_requests

        # auto request generation
        if state.auto_mode and pref_updated:
            best_pref, best_code = -1, None
            for col in grid.cells:
                for cell in col:
                    if cell.type == "storage":
                        for it in cell.items:
                            if it.preference > best_pref:
                                best_pref, best_code = it.preference, it.code
            if best_code:
                auto_q.append(best_code)

        idle = [b for b in bots if b.current_task is None]

        # manual dispatch
        if man_q and idle:
            code, qty = man_q[0]
            src, _ = grid.find_item(code)
            if src:
                bot = idle.pop(0)
                dst = _require_cell(grid.get_cell(grid.width - 1, 0))
                bot.set_task_pickup(src, dst, code)
                qty -= 1
                if qty <= 0:
                    man_q.pop(0)
                else:
                    man_q[0] = (code, qty)

        # inbound put‑away
        for y in range(config.INBOUND_CELLS):
            if not idle:
                break
            c0 = grid.get_cell(0, y)
            if c0 and c0.items:
                bot = idle.pop(0)
                dst = grid.find_empty_storage_cell()
                if dst:
                    bot.set_task_pickup(c0, dst)

        # auto dispatch
        if auto_q and idle:
            code = auto_q.pop(0)
            src, _ = grid.find_item(code)
            if src and idle:
                bot = idle.pop(0)
                dst = _require_cell(grid.get_cell(grid.width - 1, 0))
                bot.set_task_pickup(src, dst, code)

        # resort tasks
        for col in grid.cells:
            for cell in col:
                if not idle:
                    break
                if cell.type == "storage" and cell.needs_resort():
                    bot = idle.pop(0)
                    bot.set_task_resort(cell)

        for b in bots:
            b.update(dt, grid)

        ui.draw(screen)
        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()
