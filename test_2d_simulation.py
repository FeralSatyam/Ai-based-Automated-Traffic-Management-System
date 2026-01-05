import random
import time
import threading
import pygame
import sys
import os

# -------------------------------
# Default signal times
# -------------------------------
defaultRed = 150
defaultYellow = 5
defaultGreen = 20
defaultMinimum = 10
defaultMaximum = 60

signals = []
noOfSignals = 4
simTime = 300
timeElapsed = 0

currentGreen = 0
currentYellow = 0

speeds = {'car':1, 'bus':1, 'truck':1, 'rickshaw':1, 'bike':1}

# Spawn points just off-screen
spawn_points = {
    'right': [(-60,348),(-60,370),(-60,398)],        # left edge
    'down': [(755,-60),(727,-60),(697,-60)],         # top edge
    'left': [(1460,498),(1460,466),(1460,436)],      # right edge
    'up': [(602,860),(627,860),(657,860)]            # bottom edge
}

stopLines = {'right': 590, 'down': 330, 'left': 800, 'up': 535}

vehicles = {d: {0:[], 1:[], 2:[], 'crossed':0} for d in ['right','down','left','up']}
vehicleTypes = {0:'car', 1:'bus', 2:'truck', 3:'rickshaw', 4:'bike'}
directionNumbers = {0:'right', 1:'down', 2:'left', 3:'up'}

signalCoods = [(530,230),(810,230),(810,570),(530,570)]
signalTimerCoods = [(530,210),(810,210),(810,550),(530,550)]
vehicleCountCoods = [(480,210),(880,210),(880,550),(480,550)]

queue_gap = 40   # gap between queued vehicles
move_gap = 15    # minimal gap while moving

priority_list = []
priority_idx = 0

pygame.init()
simulation = pygame.sprite.Group()

# -------------------------------
# Classes
# -------------------------------
class TrafficSignal:
    def __init__(self, red, yellow, green, minimum, maximum):
        self.red = red
        self.yellow = yellow
        self.green = green
        self.minimum = minimum
        self.maximum = maximum
        self.signalText = "---"
        self.totalGreenTime = 0

class Vehicle(pygame.sprite.Sprite):
    def __init__(self, lane, vehicleClass, direction_number, direction, will_turn):
        pygame.sprite.Sprite.__init__(self)
        self.lane = lane
        self.vehicleClass = vehicleClass
        self.speed = speeds[vehicleClass]
        self.direction_number = direction_number
        self.direction = direction
        self.crossed = 0
        self.willTurn = will_turn
        self.originalImage = pygame.image.load(f"images/{direction}/{vehicleClass}.png")
        self.currentImage = self.originalImage.copy()

        lane_vehicles = vehicles[direction][lane]
        if len(lane_vehicles) == 0:
            self.x, self.y = spawn_points[direction][lane]
        else:
            last = lane_vehicles[-1]
            if direction == 'right':
                self.x = last.x - self.currentImage.get_rect().width - queue_gap
                self.y = spawn_points[direction][lane][1]
            elif direction == 'down':
                self.x = spawn_points[direction][lane][0]
                self.y = last.y - self.currentImage.get_rect().height - queue_gap
            elif direction == 'left':
                self.x = last.x + self.currentImage.get_rect().width + queue_gap
                self.y = spawn_points[direction][lane][1]
            elif direction == 'up':
                self.x = spawn_points[direction][lane][0]
                self.y = last.y + self.currentImage.get_rect().height + queue_gap

        vehicles[direction][lane].append(self)
        simulation.add(self)

    def move(self):
        width = self.currentImage.get_rect().width
        height = self.currentImage.get_rect().height
        if self.direction == 'right': front = self.x + width
        elif self.direction == 'down': front = self.y + height
        elif self.direction == 'left': front = self.x
        else: front = self.y

        stop = stopLines[self.direction]

        prev = None
        lane_list = vehicles[self.direction][self.lane]
        idx = lane_list.index(self)
        if idx > 0: prev = lane_list[idx-1]

        def prev_front(v):
            if v is None: return None
            w = v.currentImage.get_rect().width
            h = v.currentImage.get_rect().height
            if self.direction == 'right': return v.x + w
            elif self.direction == 'down': return v.y + h
            elif self.direction == 'left': return v.x
            else: return v.y

        if self.crossed == 0:
            if (self.direction in ['right','down'] and front >= stop) or \
               (self.direction in ['left','up'] and front <= stop):
                self.crossed = 1
                vehicles[self.direction]['crossed'] += 1

        if self.crossed == 0:
            can_advance = True
            pf = prev_front(prev)
            if pf is not None:
                if self.direction in ['right','down']:
                    can_advance = (front + self.speed) <= (pf - move_gap)
                else:
                    can_advance = (front - self.speed) >= (pf + move_gap)
            if can_advance:
                if self.direction == 'right' and front < stop: self.x += self.speed
                elif self.direction == 'down' and front < stop: self.y += self.speed
                elif self.direction == 'left' and front > stop: self.x -= self.speed
                elif self.direction == 'up' and front > stop: self.y -= self.speed

        elif currentGreen == self.direction_number and currentYellow == 0:
            if self.direction == 'right': self.x += self.speed
            elif self.direction == 'down': self.y += self.speed
            elif self.direction == 'left': self.x -= self.speed
            elif self.direction == 'up': self.y -= self.speed

# -------------------------------
# Priority logic
# -------------------------------
def get_lane_counts():
    counts = {}
    for i in range(noOfSignals):
        direction = directionNumbers[i]
        waiting = sum(1 for lane in range(3) for v in vehicles[direction][lane] if v.crossed == 0)
        counts[direction] = waiting
    return counts

def build_priority_list_once():
    global priority_list, priority_idx
    counts = get_lane_counts()
    priority_list = sorted(counts.keys(), key=lambda d: counts[d], reverse=True)
    priority_idx = 0

# -------------------------------
# Signal cycle
# -------------------------------
def cycle_signals():
    global currentGreen, currentYellow, priority_list, priority_idx
    while True:
        if not priority_list:
            build_priority_list_once()
        direction = priority_list[priority_idx]
        currentGreen = list(directionNumbers.values()).index(direction)
        waiting = get_lane_counts()[direction]
        greenTime = max(defaultMinimum, min(defaultMaximum, waiting * 2))
        signals[currentGreen].green = greenTime
        signals[currentGreen].yellow = defaultYellow
        signals[currentGreen].red = defaultRed

        while signals[currentGreen].green > 0:
            signals[currentGreen].signalText = str(signals[currentGreen].green)
            updateValues()
            time.sleep(1)

        currentYellow = 1
        while signals[currentGreen].yellow > 0:
            signals[currentGreen].signalText = str(signals[currentGreen].yellow)
            updateValues()
            time.sleep(1)
        currentYellow = 0

        signals[currentGreen].signalText = "---"
        signals[currentGreen].green = defaultGreen
        signals[currentGreen].yellow = defaultYellow
        signals[currentGreen].red = defaultRed

        priority_idx += 1
        if priority_idx >= len(priority_list):
            priority_list = []
            priority_idx = 0

def updateValues():
    for i in range(noOfSignals):
        if i == currentGreen:
            if currentYellow == 0:
                signals[i].green -= 1
                signals[i].totalGreenTime += 1
            else:
                signals[i].yellow -= 1
        else:
            signals[i].red -= 1

# -------------------------------
# Vehicle generation
# -------------------------------
def generateVehicles():
    while True:
        direction_number = random.randint(0,3)
        lane_number = random.randint(0,2)
        vehicle_type = random.randint(0,4)
        will_turn = 0
        Vehicle(lane_number, vehicleTypes[vehicle_type],
                direction_number, directionNumbers[direction_number], will_turn)
        time.sleep(1.0)  # one vehicle per second

# -------------------------------
# Simulation time
# -------------------------------
def simulationTime():
    global timeElapsed
    while True:
        timeElapsed += 1
        time.sleep(1)
        if timeElapsed == simTime:
#a
            totalVehicles = sum(vehicles[d]['crossed'] for d in directionNumbers.values())
            print("Total vehicles passed:", totalVehicles)
            os._exit(0)

# -------------------------------
# Main
# -------------------------------
def main():
    # Initialize signals
    for i in range(noOfSignals):
        signals.append(TrafficSignal(defaultRed, defaultYellow,
                                     defaultGreen, defaultMinimum, defaultMaximum))

    # Start threads
    threading.Thread(target=cycle_signals, daemon=True).start()
    threading.Thread(target=generateVehicles, daemon=True).start()
    threading.Thread(target=simulationTime, daemon=True).start()

    # Pygame setup
    black = (0,0,0)
    white = (255,255,255)
    screenWidth, screenHeight = 1400, 800
    screen = pygame.display.set_mode((screenWidth, screenHeight))
    pygame.display.set_caption("Priority-based 2D Traffic Simulation")

    # Assets
    background = pygame.image.load('images/mod_int.png')
    redSignal = pygame.image.load('images/signals/red.png')
    yellowSignal = pygame.image.load('images/signals/yellow.png')
    greenSignal = pygame.image.load('images/signals/green.png')
    font = pygame.font.Font(None, 30)

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sys.exit()

        screen.blit(background,(0,0))

        # Draw signals and timers
        for i in range(noOfSignals):
            if i == currentGreen:
                if currentYellow == 1:
                    screen.blit(yellowSignal, signalCoods[i])
                else:
                    screen.blit(greenSignal, signalCoods[i])
            else:
                screen.blit(redSignal, signalCoods[i])

            # Timer text
            timer_text = font.render(str(signals[i].signalText), True, white, black)
            screen.blit(timer_text, signalTimerCoods[i])

            # Waiting count
            counts = get_lane_counts()
            count_text = font.render(str(counts[directionNumbers[i]]), True, black, white)
            screen.blit(count_text, vehicleCountCoods[i])

        # Time elapsed
        time_text = font.render("Time Elapsed: " + str(timeElapsed), True, black, white)
        screen.blit(time_text, (1100, 50))

        # Live lane counts
        lane_counts = get_lane_counts()
        y_offset = 100
        screen.blit(font.render("Live Vehicle Counts:", True, black, white), (1100, y_offset))
        for i, direction in enumerate(directionNumbers.values()):
            ct = f"{direction.upper()}: {lane_counts[direction]}"
            screen.blit(font.render(ct, True, black, white), (1100, y_offset + 25 * (i+1)))

        # Priority list
        screen.blit(font.render("Priority Order:", True, black, white), (1100, y_offset + 140))
        if priority_list:
            for i, direction in enumerate(priority_list):
                prefix = "→ " if i == priority_idx else "   "
                screen.blit(font.render(f"{prefix}{i+1}. {direction.upper()}", True, black, white),
                            (1100, y_offset + 165 + 25 * i))
        else:
            screen.blit(font.render("Rebuilding next cycle...", True, black, white),
                        (1100, y_offset + 165))

        # Vehicles
        for vehicle in simulation:
            screen.blit(vehicle.currentImage, [vehicle.x, vehicle.y])
            vehicle.move()

        pygame.display.update()

# -------------------------------
# Run
# -------------------------------
if __name__ == "__main__":
    main()
