import math
import random
import pygame

WIDTH, HEIGHT = 800, 800
FPS = 60

# Colors
SIDEWALK = (80, 80, 80)
ROAD = (30, 30, 30)
WHITE = (255, 255, 255)
YELLOW = (255, 255, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
AMBER = (255, 200, 0)

pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
clock = pygame.time.Clock()

# intersection geometry constants
road_w = WIDTH // 3
road_h = HEIGHT // 3
mid_x = WIDTH // 2
mid_y = HEIGHT // 2
offset_v = road_w // 4
offset_h = road_h // 4
stop_gap = 10
cw_w = 36
top = mid_y - road_h // 2
bottom = mid_y + road_h // 2
left = mid_x - road_w // 2
right = mid_x + road_w // 2
stop_n = top - stop_gap
stop_s = bottom + stop_gap
stop_w = left - stop_gap
stop_e = right + stop_gap

# ---------- drawing primitives ----------

def draw_dashed_line(surf, color, start, end, width=2, dash=10, gap=10):
    x1, y1 = start
    x2, y2 = end
    dx = x2 - x1
    dy = y2 - y1
    length = math.hypot(dx, dy)
    if length <= 0:
        return
    dx /= length
    dy /= length
    dist = 0
    while dist < length:
        sp = (x1 + dx * dist, y1 + dy * dist)
        ep = (x1 + dx * min(dist + dash, length), y1 + dy * min(dist + dash, length))
        pygame.draw.line(surf, color, sp, ep, width)
        dist += dash + gap

def draw_double_yellow(surf, x1, y1, x2, y2, orientation, gap=4, width=2):
    if orientation == 'h':
        pygame.draw.line(surf, YELLOW, (x1, y1 - gap), (x2, y2 - gap), width)
        pygame.draw.line(surf, YELLOW, (x1, y1 + gap), (x2, y2 + gap), width)
    else:
        pygame.draw.line(surf, YELLOW, (x1 - gap, y1), (x2 - gap, y2), width)
        pygame.draw.line(surf, YELLOW, (x1 + gap, y1), (x2 + gap, y2), width)

def draw_crosswalk(surf, rect, stripe_w=6, stripe_gap=6, orientation='h'):
    x, y, w, h = rect
    if orientation == 'h':
        n = int(w // (stripe_w + stripe_gap)) + 1
        for i in range(n):
            left = x + i * (stripe_w + stripe_gap)
            pygame.draw.rect(surf, WHITE, (left, y, stripe_w, h))
    else:
        n = int(h // (stripe_w + stripe_gap)) + 1
        for i in range(n):
            top = y + i * (stripe_w + stripe_gap)
            pygame.draw.rect(surf, WHITE, (x, top, w, stripe_w))

def draw_stop_line(surf, start, end, width=6):
    pygame.draw.line(surf, WHITE, start, end, width)

def draw_arrow_straight(surf, pos, angle, length=28, head=8, width=4):
    x, y = pos
    ex = x + length * math.cos(angle)
    ey = y + length * math.sin(angle)
    pygame.draw.line(surf, WHITE, (x, y), (ex, ey), width)
    left = (ex - head * math.cos(angle - math.pi/6),
            ey - head * math.sin(angle - math.pi/6))
    right = (ex - head * math.cos(angle + math.pi/6),
             ey - head * math.sin(angle + math.pi/6))
    pygame.draw.polygon(surf, WHITE, [left, (ex, ey), right])

def draw_arrow_short(surf, pos, angle, length=16, head=6, width=3):
    draw_arrow_straight(surf, pos, angle, length, head, width)

def draw_vehicle_signal(x, y, phase_color, orientation='h'):
    radius = 8
    spacing = 20
    dark = (60, 60, 60)
    cols = {'R': RED, 'Y': AMBER, 'G': GREEN}
    active = cols.get(phase_color, dark)
    if orientation == 'h':
        pts = [(x - spacing, y), (x, y), (x + spacing, y)]
    else:
        pts = [(x, y - spacing), (x, y), (x, y + spacing)]
    order_cols = [RED, AMBER, GREEN]
    for c, pos in zip(order_cols, pts):
        col = active if c == cols.get(phase_color, dark) else dark
        pygame.draw.circle(screen, col, pos, radius)

def draw_ped_signal(x, y, go):
    size = 12
    col = GREEN if go else RED
    pygame.draw.rect(screen, col, (x - size//2, y - size//2, size, size))


class Car:
    def __init__(self, direction, lane, turn):
        self.direction = direction  # 'N','S','E','W'
        self.lane = lane            # 1 or 2
        self.turn = turn            # 'straight','left','right'
        self.speed = 100  # pixels per second
        self.passed_stop = False
        self.turned = False
        self.waiting = False
        if direction == 'N':
            x = mid_x - offset_v if lane == 1 else mid_x + offset_v
            self.x, self.y = x, -40
        elif direction == 'S':
            x = mid_x + offset_v if lane == 2 else mid_x - offset_v
            self.x, self.y = x, HEIGHT + 40
        elif direction == 'W':
            y = mid_y + offset_h if lane == 2 else mid_y - offset_h
            self.x, self.y = -40, y
        else:  # 'E'
            y = mid_y - offset_h if lane == 1 else mid_y + offset_h
            self.x, self.y = WIDTH + 40, y

    def update(self, dt, ns_green, ew_green):
        speed = self.speed * dt / 1000.0
        if self.direction == 'N':
            stop = stop_n
            if not self.passed_stop:
                if self.y + speed >= stop and not ns_green:
                    self.y = stop - 1
                    self.waiting = True
                    return
                self.y += speed
                if self.y >= stop:
                    self.passed_stop = True
            else:
                self.y += speed
                if not self.turned and self.turn == 'left' and self.y >= mid_y:
                    self.direction = 'E'
                    self.x = mid_x
                    self.turned = True
                elif not self.turned and self.turn == 'right' and self.y >= mid_y:
                    self.direction = 'W'
                    self.x = mid_x
                    self.turned = True
        elif self.direction == 'S':
            stop = stop_s
            if not self.passed_stop:
                if self.y - speed <= stop and not ns_green:
                    self.y = stop + 1
                    self.waiting = True
                    return
                self.y -= speed
                if self.y <= stop:
                    self.passed_stop = True
            else:
                self.y -= speed
                if not self.turned and self.turn == 'left' and self.y <= mid_y:
                    self.direction = 'W'
                    self.x = mid_x
                    self.turned = True
                elif not self.turned and self.turn == 'right' and self.y <= mid_y:
                    self.direction = 'E'
                    self.x = mid_x
                    self.turned = True
        elif self.direction == 'W':
            stop = stop_w
            if not self.passed_stop:
                if self.x + speed >= stop and not ew_green:
                    self.x = stop - 1
                    self.waiting = True
                    return
                self.x += speed
                if self.x >= stop:
                    self.passed_stop = True
            else:
                self.x += speed
                if not self.turned and self.turn == 'left' and self.x >= mid_x:
                    self.direction = 'S'
                    self.y = mid_y
                    self.turned = True
                elif not self.turned and self.turn == 'right' and self.x >= mid_x:
                    self.direction = 'N'
                    self.y = mid_y
                    self.turned = True
        else:  # direction == 'E'
            stop = stop_e
            if not self.passed_stop:
                if self.x - speed <= stop and not ew_green:
                    self.x = stop + 1
                    self.waiting = True
                    return
                self.x -= speed
                if self.x <= stop:
                    self.passed_stop = True
            else:
                self.x -= speed
                if not self.turned and self.turn == 'left' and self.x <= mid_x:
                    self.direction = 'N'
                    self.y = mid_y
                    self.turned = True
                elif not self.turned and self.turn == 'right' and self.x <= mid_x:
                    self.direction = 'S'
                    self.y = mid_y
                    self.turned = True

    def draw(self):
        rect = pygame.Rect(0, 0, 14, 28)
        rect.center = (self.x, self.y)
        pygame.draw.rect(screen, GREEN, rect)

    def is_offscreen(self):
        return self.x < -50 or self.x > WIDTH + 50 or self.y < -50 or self.y > HEIGHT + 50


class Pedestrian:
    def __init__(self, orientation):
        self.orientation = orientation  # 'NS' or 'EW'
        self.speed = 50  # px/s
        if orientation == 'NS':
            # cross north-south road horizontally
            start_side = random.choice(['W', 'E'])
            self.y = stop_n - cw_w//2 if start_side == 'W' else stop_s + cw_w//2
            if start_side == 'W':
                self.x = left - 10
                self.end_x = right + 10
            else:
                self.x = right + 10
                self.end_x = left - 10
        else:  # 'EW'
            start_side = random.choice(['N', 'S'])
            self.x = stop_w - cw_w//2 if start_side == 'N' else stop_e + cw_w//2
            if start_side == 'N':
                self.y = top - 10
                self.end_y = bottom + 10
            else:
                self.y = bottom + 10
                self.end_y = top - 10

    def update(self, dt, go):
        if not go:
            return
        dist = self.speed * dt / 1000.0
        if self.orientation == 'NS':
            if self.x < self.end_x:
                self.x += dist
            else:
                self.x -= dist
        else:
            if self.y < self.end_y:
                self.y += dist
            else:
                self.y -= dist

    def draw(self):
        pygame.draw.circle(screen, (0, 200, 200), (int(self.x), int(self.y)), 6)

    def is_done(self):
        if self.orientation == 'NS':
            return (self.x >= self.end_x and self.end_x > 0) or (self.x <= self.end_x and self.end_x < 0)
        return (self.y >= self.end_y and self.end_y > 0) or (self.y <= self.end_y and self.end_y < 0)

running = True
phase = 0  # 0=NS green, 1=EW green
phase_timer = 0
MIN_GREEN = 3000

cars = []
peds = []
spawn_car_timer = 0
spawn_ped_timer = 0

while running:
    dt = clock.tick(FPS)
    phase_timer += dt
    spawn_car_timer += dt
    spawn_ped_timer += dt

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # spawn cars periodically
    if spawn_car_timer >= 800:
        spawn_car_timer = 0
        direction = random.choice(['N', 'S', 'E', 'W'])
        lane = random.choice([1, 2])
        if lane == 1:
            turn = random.choice(['straight', 'left'])
        else:
            turn = random.choice(['straight', 'right'])
        cars.append(Car(direction, lane, turn))

    # spawn pedestrians periodically
    if spawn_ped_timer >= 4000:
        spawn_ped_timer = 0
        orientation = random.choice(['NS', 'EW'])
        peds.append(Pedestrian(orientation))

    # compute waiting cars
    ns_wait = sum(1 for c in cars if c.waiting and c.direction in ('N', 'S'))
    ew_wait = sum(1 for c in cars if c.waiting and c.direction in ('E', 'W'))

    ns_green = phase == 0
    ew_green = phase == 1
    ped_ns_go = ew_green
    ped_ew_go = ns_green
    if phase_timer >= MIN_GREEN:
        if phase == 0 and ew_wait > ns_wait:
            phase = 1
            phase_timer = 0
        elif phase == 1 and ns_wait > ew_wait:
            phase = 0
            phase_timer = 0

    screen.fill(SIDEWALK)

    road_w = WIDTH // 3
    road_h = HEIGHT // 3
    mid_x = WIDTH // 2
    mid_y = HEIGHT // 2

    top = mid_y - road_h // 2
    bottom = mid_y + road_h // 2
    left = mid_x - road_w // 2
    right = mid_x + road_w // 2

    stop_gap = 10
    cw_w = 36
    merge_len = 70
    dash_len = 15
    dash_gap = 15

    pygame.draw.rect(screen, ROAD, (mid_x - road_w // 2, 0, road_w, HEIGHT))
    pygame.draw.rect(screen, ROAD, (0, mid_y - road_h // 2, WIDTH, road_h))
    # visual sidewalk-road boundaries
    pygame.draw.rect(screen, WHITE, (mid_x - road_w // 2, 0, road_w, HEIGHT), 2)
    pygame.draw.rect(screen, WHITE, (0, mid_y - road_h // 2, WIDTH, road_h), 2)

    stop_n = top - stop_gap
    stop_s = bottom + stop_gap
    stop_w = left - stop_gap
    stop_e = right + stop_gap

    cw_rect_n = (left, stop_n - cw_w, road_w, cw_w)
    cw_rect_s = (left, stop_s, road_w, cw_w)
    cw_rect_w = (stop_w - cw_w, top, cw_w, road_h)
    cw_rect_e = (stop_e, top, cw_w, road_h)

    draw_double_yellow(screen, mid_x, 0, mid_x, stop_n - cw_w, 'v')
    draw_double_yellow(screen, mid_x, stop_s + cw_w, mid_x, HEIGHT, 'v')
    draw_double_yellow(screen, 0, mid_y, stop_w - cw_w, mid_y, 'h')
    draw_double_yellow(screen, stop_e + cw_w, mid_y, WIDTH, mid_y, 'h')

    offset_v = road_w // 4
    offset_h = road_h // 4

    for x in (mid_x - offset_v, mid_x + offset_v):
        draw_dashed_line(screen, WHITE, (x, 0), (x, stop_n - merge_len), 2, dash_len, dash_gap)
        pygame.draw.line(screen, WHITE, (x, stop_n - merge_len), (x, stop_n), 2)
        draw_dashed_line(screen, WHITE, (x, stop_s + merge_len), (x, HEIGHT), 2, dash_len, dash_gap)
        pygame.draw.line(screen, WHITE, (x, stop_s), (x, stop_s + merge_len), 2)

    for y in (mid_y - offset_h, mid_y + offset_h):
        draw_dashed_line(screen, WHITE, (0, y), (stop_w - merge_len, y), 2, dash_len, dash_gap)
        pygame.draw.line(screen, WHITE, (stop_w - merge_len, y), (stop_w, y), 2)
        draw_dashed_line(screen, WHITE, (stop_e + merge_len, y), (WIDTH, y), 2, dash_len, dash_gap)
        pygame.draw.line(screen, WHITE, (stop_e, y), (stop_e + merge_len, y), 2)

    draw_stop_line(screen, (left, stop_n), (right, stop_n))
    draw_stop_line(screen, (left, stop_s), (right, stop_s))
    draw_stop_line(screen, (stop_w, top), (stop_w, bottom))
    draw_stop_line(screen, (stop_e, top), (stop_e, bottom))

    draw_crosswalk(screen, cw_rect_n, orientation='h')
    draw_crosswalk(screen, cw_rect_s, orientation='h')
    draw_crosswalk(screen, cw_rect_w, orientation='v')
    draw_crosswalk(screen, cw_rect_e, orientation='v')

    arrow_back = 40
    lane1x = mid_x - offset_v
    lane2x = mid_x + offset_v
    draw_arrow_straight(screen, (lane1x, stop_n - arrow_back), math.pi / 2)
    draw_arrow_short(screen, (lane1x - 12, stop_n - arrow_back), math.pi)
    draw_arrow_straight(screen, (lane2x, stop_n - arrow_back), math.pi / 2)
    draw_arrow_short(screen, (lane2x + 12, stop_n - arrow_back), -math.pi / 2)

    draw_arrow_straight(screen, (lane2x, stop_s + arrow_back), -math.pi / 2)
    draw_arrow_short(screen, (lane2x + 12, stop_s + arrow_back), 0)
    draw_arrow_straight(screen, (lane1x, stop_s + arrow_back), -math.pi / 2)
    draw_arrow_short(screen, (lane1x - 12, stop_s + arrow_back), math.pi)

    lane1y = mid_y - offset_h
    lane2y = mid_y + offset_h
    draw_arrow_straight(screen, (stop_w - arrow_back, lane1y), 0)
    draw_arrow_short(screen, (stop_w - arrow_back, lane1y - 12), -math.pi / 2)
    draw_arrow_straight(screen, (stop_w - arrow_back, lane2y), 0)
    draw_arrow_short(screen, (stop_w - arrow_back, lane2y + 12), math.pi / 2)

    draw_arrow_straight(screen, (stop_e + arrow_back, lane1y), math.pi)
    draw_arrow_short(screen,    (stop_e + arrow_back, lane1y + 12), math.pi / 2)
    draw_arrow_straight(screen, (stop_e + arrow_back, lane2y), math.pi)
    draw_arrow_short(screen,    (stop_e + arrow_back, lane2y - 12), -math.pi / 2)

    # update cars and pedestrians
    for car in list(cars):
        car.update(dt, ns_green, ew_green)
        car.draw()
        if car.is_offscreen():
            cars.remove(car)

    for ped in list(peds):
        ped.update(dt, ped_ns_go if ped.orientation == 'NS' else ped_ew_go)
        ped.draw()
        if ped.is_done():
            peds.remove(ped)

    ns_go = ns_green
    ew_go = ew_green

    draw_vehicle_signal(mid_x, stop_s + cw_w + 25, 'G' if ns_go else 'R', 'h')
    draw_vehicle_signal(mid_x, stop_n - cw_w - 25, 'G' if ns_go else 'R', 'h')
    draw_vehicle_signal(stop_e + cw_w + 25, mid_y, 'G' if ew_go else 'R', 'h')
    draw_vehicle_signal(stop_w - cw_w - 25, mid_y, 'G' if ew_go else 'R', 'h')

    draw_vehicle_signal(left - 20, stop_n, 'G' if ns_go else 'R', 'v')
    draw_vehicle_signal(right + 20, stop_s, 'G' if ns_go else 'R', 'v')
    draw_vehicle_signal(stop_w, top - 20, 'G' if ew_go else 'R', 'v')
    draw_vehicle_signal(stop_e, bottom + 20, 'G' if ew_go else 'R', 'v')

    draw_ped_signal(left - 8, stop_n - cw_w // 2, ped_ns_go)
    draw_ped_signal(right + 8, stop_n - cw_w // 2, ped_ns_go)
    draw_ped_signal(left - 8, stop_s + cw_w // 2, ped_ns_go)
    draw_ped_signal(right + 8, stop_s + cw_w // 2, ped_ns_go)

    draw_ped_signal(stop_w - cw_w // 2, top - 8, ped_ew_go)
    draw_ped_signal(stop_w - cw_w // 2, bottom + 8, ped_ew_go)
    draw_ped_signal(stop_e + cw_w // 2, top - 8, ped_ew_go)
    draw_ped_signal(stop_e + cw_w // 2, bottom + 8, ped_ew_go)

    pygame.display.flip()

pygame.quit()
