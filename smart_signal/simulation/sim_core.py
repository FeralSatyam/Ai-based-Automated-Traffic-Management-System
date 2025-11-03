# smart_signal/simulation/sim_core.py
import pygame
import random

WIDTH, HEIGHT = 800, 800
LANE_WIDTH = 40
CENTER = (WIDTH // 2, HEIGHT // 2)

class Vehicle:
    def __init__(self, x, y, direction, approach_id, speed=2.0, color=(0, 220, 0), vehicle_type="car"):
        self.x, self.y = x, y
        self.direction = direction  # "N","S","E","W"
        self.approach_id = approach_id
        self.speed = speed
        self.color = color
        self.vehicle_type = vehicle_type
        self.w, self.h = (20, 36) if direction in ("N", "S") else (36, 20)

    def _near_stop_line(self):
        x1, y1, x2, y2 = CENTER[0] - 60, CENTER[1] - 60, CENTER[0] + 60, CENTER[1] + 60
        if self.direction == "N": return self.y <= y2 + 10
        if self.direction == "S": return self.y + self.h >= y1 - 10
        if self.direction == "E": return self.x + self.w >= x1 - 10
        if self.direction == "W": return self.x <= x2 + 10
        return False

    def move_step(self):
        if self.direction == "N": self.y -= self.speed
        elif self.direction == "S": self.y += self.speed
        elif self.direction == "E": self.x += self.speed
        elif self.direction == "W": self.x -= self.speed

    def draw(self, surf):
        pygame.draw.rect(surf, self.color, (int(self.x), int(self.y), self.w, self.h))
        if self.vehicle_type != "car":
            font = pygame.font.SysFont(None, 16)
            label = font.render("EMG", True, (255, 255, 255))
            surf.blit(label, (int(self.x), int(self.y) - 12))


class SimWorld:
    def __init__(self, width=WIDTH, height=HEIGHT):
        pygame.init()
        self.width, self.height = width, height
        self.screen = pygame.display.set_mode((width, height))
        pygame.display.set_caption("2D Traffic Sim")
        self.clock = pygame.time.Clock()
        self.conflict_box = pygame.Rect(CENTER[0] - 40, CENTER[1] - 40, 80, 80)

        # Lane spawn anchors
        self.lanes = {
            "N": [(self.width // 2 - 30, self.height - 60), (self.width // 2 + 10, self.height - 60)],
            "S": [(self.width // 2 - 30, 20), (self.width // 2 + 10, 20)],
            "E": [(20, self.height // 2 - 30), (20, self.height // 2 + 10)],
            "W": [(self.width - 60, self.height // 2 - 30), (self.width - 60, self.height // 2 + 10)]
        }

        self.stop_lines = {
            "N": self.height // 2 + 60,
            "S": self.height // 2 - 100,
            "E": self.width // 2 - 100,
            "W": self.width // 2 + 60
        }

        self.vehicles = []
        self.lights = {"N": "GREEN", "S": "GREEN", "E": "RED", "W": "RED"}
        self.light_timers = {"N": 12, "S": 12, "E": 0, "W": 0}
        self.cycle_pair = ("N", "S")
        self.fps = 30
        self.running = True

    def spawn_random(self, p=0.02, p_emergency=0.005):
        # Normal vehicles
        lane_choice = {
            "N": 0,  # Northbound uses lane 0
            "S": 1,  # Southbound uses lane 1
            "E": 0,  # Eastbound uses lane 0
            "W": 1   # Westbound uses lane 1
            }

        for approach in ("N", "S", "E", "W"):
            lane_idx = lane_choice[approach]
            lx, ly = self.lanes[approach][lane_idx]
            if random.random() < p:
                self.vehicles.append(Vehicle(
                    lx, ly,
                    direction=approach,
                    approach_id=approach,
                    speed=2.0,
                    color=(0, 220, 0),
                    vehicle_type="car"
                ))

            if random.random() < p:
                self.vehicles.append(Vehicle(
                    lx, ly,
                    direction=approach,
                    approach_id=approach,
                    speed=2.0,
                    color=(0, 220, 0),
                    vehicle_type="car"
                ))


        # Emergency vehicle example: from N lane 0
        if random.random() < p_emergency:
            lx, ly = self.lanes["N"][0]  # still lane 0
            self.vehicles.append(Vehicle(
                lx, ly,
                direction="N",
                approach_id="N",
                speed=3.5,
                color=(255, 0, 0),
                vehicle_type="ambulance"
            ))

    def _update_lights(self):
        # decrement timers for active greens
        for k in self.cycle_pair:
            self.light_timers[k] = max(0, self.light_timers[k] - 1.0 / self.fps)

        # switch when both greens expire
        if all(self.light_timers[k] <= 0 for k in self.cycle_pair):
            self.cycle_pair = ("E", "W") if self.cycle_pair == ("N", "S") else ("N", "S")
            for k in ("N", "S", "E", "W"):
                self.lights[k] = "GREEN" if k in self.cycle_pair else "RED"
                self.light_timers[k] = 12 if self.lights[k] == "GREEN" else 0

    def _move_with_gaps(self):
        headway = 28
        groups = {"N": [], "S": [], "E": [], "W": []}
        for v in self.vehicles:
            groups[v.approach_id].append(v)

        def sort_key(app):
            if app == "N": return lambda v: v.y
            if app == "S": return lambda v: -v.y
            if app == "E": return lambda v: -v.x
            if app == "W": return lambda v: v.x

        for app, vs in groups.items():
            vs.sort(key=sort_key(app))
            for i, v in enumerate(vs):
                leader = None
                for j in range(i):
                    u = vs[j]
                    if app in ("N", "S") and abs(u.x - v.x) < 12:
                        leader = u
                        break
                    if app in ("E", "W") and abs(u.y - v.y) < 12:
                        leader = u
                        break

                red_ahead = (self.lights.get(v.approach_id, "RED") == "RED") and v._near_stop_line()
                too_close = False
                if leader:
                    if app == "N":
                        too_close = (v.y + v.h) > (leader.y - headway)
                    elif app == "S":
                        too_close = (v.y) < (leader.y + leader.h + headway)
                    elif app == "E":
                        too_close = (v.x) < (leader.x + leader.w + headway)
                    elif app == "W":
                        too_close = (v.x + v.w) > (leader.x - headway)

                if not red_ahead and not too_close:
                    if self._box_occupied_by_opposite(v.approach_id):
                        continue  # wait until box is clear
                    if not red_ahead and not too_close and not self._box_occupied_by_opposite(v.approach_id):
                        v.move_step()


    def draw_intersection(self):
        self.screen.fill((28, 28, 28))
        road_color = (70, 70, 70)
        pygame.draw.rect(self.screen, road_color, (CENTER[0] - 3 * LANE_WIDTH, 0, 6 * LANE_WIDTH, self.height))
        pygame.draw.rect(self.screen, road_color, (0, CENTER[1] - 3 * LANE_WIDTH, self.width, 6 * LANE_WIDTH))
        pygame.draw.rect(self.screen, (200, 200, 200), (CENTER[0] - 60, CENTER[1] - 60, 120, 120), 2)

        font = pygame.font.SysFont(None, 24)
        positions = {"N": (CENTER[0] - 10, CENTER[1] - 120),
                     "S": (CENTER[0] - 10, CENTER[1] + 90),
                     "E": (CENTER[0] + 90, CENTER[1] - 10),
                     "W": (CENTER[0] - 120, CENTER[1] - 10)}
        for k, pos in positions.items():
            col = (50, 220, 50) if self.lights[k] == "GREEN" else (230, 60, 60)
            pygame.draw.circle(self.screen, col, pos, 12)
            t = int(self.light_timers[k]) if self.lights[k] == "GREEN" else 0
            timer_text = font.render(str(t), True, (255, 255, 255))
            self.screen.blit(timer_text, (pos[0] - 8, pos[1] + 16))

    def _box_occupied_by_opposite(self, approach):
    # Map each approach to its opposite
        opposite = {"N": "S", "S": "N", "E": "W", "W": "E"}
        opp = opposite[approach]
        for v in self.vehicles:
            if v.approach_id == opp:
                veh_rect = pygame.Rect(v.x, v.y, v.w, v.h)
                if veh_rect.colliderect(self.conflict_box):
                    return True
        return False

    def step(self, spawns=True, spawn_p=0.02):
        # Handle quit events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

        # Spawn vehicles
        if spawns:
            self.spawn_random(spawn_p)

        # Update lights and move vehicles with gap logic
        self._update_lights()
        self._move_with_gaps()

        # Remove vehicles that have left the visible area
        self.vehicles = [
            v for v in self.vehicles
            if -100 <= v.x <= self.width + 100 and -100 <= v.y <= self.height + 100
        ]

    def render(self, fps=30):
        self.draw_intersection()
        for v in self.vehicles:
            v.draw(self.screen)
        pygame.display.flip()
        self.clock.tick(fps)

    def shutdown(self):
        pygame.quit()


if __name__ == "__main__":
    world = SimWorld()
    while world.running:
        world.step(spawns=True, spawn_p=0.03)
        world.render(fps=60)
    world.shutdown()