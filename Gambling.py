import turtle
import random
import time

# --- GAME STATE ---
balance = 1000
house_remortgages = 0
MIN_REMORTGAGE_AMOUNT = 500
spin_history = []

mode = "game"
current_machine_id = "classic"
max_balance = balance
is_spinning = False

# Boosts
luck_spins = 0
payout_spins = 0
discount_spins = 0

# --- MACHINES WITH THEMES ---
MACHINE_ORDER = ["classic", "gold", "diamond", "cosmic"]

MACHINES = {
    "classic": {
        "name": "Classic",
        "unlock": 0,
        "base_cost": 20,
        "cost_scale": 0.02,
        "max_cost": 2000,
        "symbols": ["🍒", "🍋", "🍊", "🍇", "🔔", "💎"],
        "multipliers": [6, 8, 12, 18, 35, 250],
        "pair_factor": 0.75,
        "weights": [35, 23, 21, 15, 4.5, 1.5],
        "theme": {"bg": "#f4f7f0", "frame": "#5d4037", "accent": "#4caf50", "reel_bg": "#ffffff", "text": "#2e7d32"}
    },
    "gold": {
        "name": "Gold",
        "unlock": 10000,
        "base_cost": 50,
        "cost_scale": 0.02,
        "max_cost": 10000,
        "symbols": ["💰", "💵", "💍", "👑", "🏆", "💎"],
        "multipliers": [8, 12, 18, 25, 45, 350],
        "pair_factor": 0.80,
        "weights": [35, 23, 21, 15, 4.5, 1.5],
        "theme": {"bg": "#fff8e1", "frame": "#b71c1c", "accent": "#ffd700", "reel_bg": "#fffde7", "text": "#f57f17"}
    },
    "diamond": {
        "name": "Diamond",
        "unlock": 100000,
        "base_cost": 250,
        "cost_scale": 0.02,
        "max_cost": 50000,
        "symbols": ["🔹", "🔷", "💠", "💍", "🌌", "💎"],
        "multipliers": [12, 18, 28, 40, 65, 500],
        "pair_factor": 0.85,
        "weights": [35, 23, 21, 15, 4.5, 1.5],
        "theme": {"bg": "#e3f2fd", "frame": "#0d47a1", "accent": "#00e5ff", "reel_bg": "#ffffff", "text": "#01579b"}
    },
    "cosmic": {
        "name": "Cosmic",
        "unlock": 1000000,
        "base_cost": 1000,
        "cost_scale": 0.02,
        "max_cost": 250000,
        "symbols": ["🚀", "🌟", "🌙", "🌞", "🌌", "👽"],
        "multipliers": [18, 28, 45, 65, 100, 750],
        "pair_factor": 0.90,
        "weights": [35, 23, 21, 15, 4.5, 1.5],
        "theme": {"bg": "#1a0033", "frame": "#4a148c", "accent": "#d500f9", "reel_bg": "#311b92", "text": "#ea80fc"}
    }
}

# --- SHOP ITEMS ---
SHOP_ITEMS = {
    "1": {"name": "Lucky Boost", "cost": 1000, "desc": "Adds 25 luck-boosted spins"},
    "2": {"name": "Payout Boost", "cost": 2500, "desc": "Adds 20 spins with 1.5x wins"},
    "3": {"name": "Discount Card", "cost": 4000, "desc": "Adds 30 spins with 25% cheaper cost"}
}

# --- BUTTON AREAS ---
BUTTONS = {
    "spin": {"x": -255, "y": 300, "w": 110, "h": 40},
    "prev": {"x": -140, "y": 300, "w": 70, "h": 40},
    "next": {"x": 140, "y": 300, "w": 70, "h": 40},
    "shop": {"x": 255, "y": 300, "w": 110, "h": 40}
}

# --- WINDOW SETUP ---
screen = turtle.Screen()
screen.title("Slot Machine Tycoon")
screen.setup(width=700, height=800)
screen.tracer(0)

# --- TURTLE OBJECTS ---
text_painter = turtle.Turtle()
text_painter.hideturtle()
text_painter.speed(0)

design_painter = turtle.Turtle()
design_painter.hideturtle()
design_painter.speed(0)

button_painter = turtle.Turtle()
button_painter.hideturtle()
button_painter.speed(0)

reel_painter = turtle.Turtle()
reel_painter.hideturtle()
reel_painter.speed(0)

# --- HELPERS ---
def money(amount):
    return f"£{int(amount):,}"

def write_text(x, y, text, size=12, style="normal", align="center", color="#222222"):
    text_painter.penup()
    text_painter.goto(x, y)
    text_painter.color(color)
    text_painter.write(text, align=align, font=("Arial", size, style))

def update_max_balance():
    global max_balance
    if balance > max_balance:
        max_balance = balance

def is_unlocked(machine_id):
    return max_balance >= MACHINES[machine_id]["unlock"]

def get_next_unlock_text():
    for machine_id in MACHINE_ORDER:
        if not is_unlocked(machine_id):
            return f"Next unlock: {MACHINES[machine_id]['name']} at {money(MACHINES[machine_id]['unlock'])}"
    return "All machines unlocked!"

def get_base_spin_cost():
    machine = MACHINES[current_machine_id]
    dynamic_cost = int(balance * machine["cost_scale"])
    cost = max(machine["base_cost"], dynamic_cost)
    return max(1, min(machine["max_cost"], cost))

def get_spin_cost():
    cost = get_base_spin_cost()
    if discount_spins > 0:
        cost = int(cost * 0.75)
    return max(1, cost)

def get_spins_left():
    cost = get_spin_cost()
    return int(balance // cost) if cost > 0 else 0

def get_symbol_multiplier(machine, symbol):
    return machine["multipliers"][machine["symbols"].index(symbol)]

def get_weighted_symbol(machine):
    weights = machine["weights"][:]
    if luck_spins > 0:
        weights[-1] *= 6
        weights[-2] *= 3
        weights[-3] *= 2
    return random.choices(machine["symbols"], weights=weights, k=1)[0]

def inside_button(x, y, btn):
    return (btn["x"] - btn["w"] / 2 <= x <= btn["x"] + btn["w"] / 2 and
            btn["y"] - btn["h"] / 2 <= y <= btn["y"] + btn["h"] / 2)

def draw_rounded_rect(painter, x, y, w, h, radius, color, border_color=None, border_width=2):
    painter.penup()
    painter.goto(x - w/2 + radius, y - h/2)
    painter.setheading(0)
    painter.pendown()
    painter.fillcolor(color)
    painter.begin_fill()
    
    for _ in range(2):
        painter.forward(w - 2*radius)
        painter.circle(radius, 90)
        painter.forward(h - 2*radius)
        painter.circle(radius, 90)
        
    painter.end_fill()
    
    if border_color:
        painter.pencolor(border_color)
        painter.pensize(border_width)
        painter.penup()
        painter.goto(x - w/2 + radius, y - h/2)
        painter.setheading(0)
        painter.pendown()
        for _ in range(2):
            painter.forward(w - 2*radius)
            painter.circle(radius, 90)
            painter.forward(h - 2*radius)
            painter.circle(radius, 90)
        painter.pencolor("#333333")
        painter.pensize(1)

def draw_button_custom(btn, label, colour, text_colour):
    x, y, w, h = btn["x"], btn["y"], btn["w"], btn["h"]
    draw_rounded_rect(button_painter, x, y, w, h, 8, colour, "#333333", 2)
    button_painter.penup()
    button_painter.goto(x, y - 6)
    button_painter.color(text_colour)
    button_painter.write(label, align="center", font=("Arial", 14, "bold"))

def draw_buttons():
    button_painter.clear()
    theme = MACHINES[current_machine_id]["theme"]
    
    if mode == "game":
        draw_button_custom(BUTTONS["spin"], "SPIN", theme["accent"], "#ffffff")
        draw_button_custom(BUTTONS["prev"], "◀", "#e0e0e0", "#333333")
        draw_button_custom(BUTTONS["next"], "▶", "#e0e0e0", "#333333")
        draw_button_custom(BUTTONS["shop"], "SHOP", "#ff9800", "#ffffff")
    else:
        draw_button_custom(BUTTONS["spin"], "SPIN", "#cccccc", "#888888")
        draw_button_custom(BUTTONS["prev"], "◀", "#cccccc", "#888888")
        draw_button_custom(BUTTONS["next"], "▶", "#cccccc", "#888888")
        draw_button_custom(BUTTONS["shop"], "BACK", theme["accent"], "#ffffff")

def draw_reels_only(reel1, reel2, reel3):
    reel_painter.clear()
    machine = MACHINES[current_machine_id]
    theme = machine["theme"]
    
    reel_positions = [-120, 0, 120]
    reels = [reel1, reel2, reel3]
    for i, x in enumerate(reel_positions):
        draw_rounded_rect(reel_painter, x, 170, 110, 90, 10, theme["reel_bg"], theme["frame"], 3)
        write_text(x + 2, 170 - 5, reels[i], 48, "normal", color="#e0e0e0")
        write_text(x, 170 - 5, reels[i], 48, "normal", color="#222222")
    screen.update()

# --- UI ---
def update_ui(reel1="🍒", reel2="🍒", reel3="🍒", message="Press Spin!"):
    if mode == "shop":
        draw_shop(message)
    else:
        draw_game(reel1, reel2, reel3, message)
    draw_buttons()
    screen.update()

def draw_game(reel1, reel2, reel3, message):
    text_painter.clear()
    design_painter.clear()
    machine = MACHINES[current_machine_id]
    theme = machine["theme"]
    
    screen.bgcolor(theme["bg"])
    
    draw_rounded_rect(design_painter, 0, 350, 300, 50, 10, theme["frame"], theme["accent"], 3)
    write_text(0, 335, f"★ {machine['name']} SLOTS ★", 22, "bold", color="#ffffff")
    
    draw_rounded_rect(design_painter, 0, 170, 420, 120, 15, theme["frame"], theme["accent"], 4)
    
    reel_positions = [-120, 0, 120]
    reels = [reel1, reel2, reel3]
    for i, x in enumerate(reel_positions):
        draw_rounded_rect(design_painter, x, 170, 110, 90, 10, theme["reel_bg"], theme["frame"], 3)
        write_text(x + 2, 170 - 5, reels[i], 48, "normal", color="#e0e0e0")
        write_text(x, 170 - 5, reels[i], 48, "normal", color="#222222")

    msg_color = theme["text"] if "No luck" not in message and "JACKPOT" not in message else ("#d32f2f" if "No luck" in message else "#ff6f00")
    if "JACKPOT" in message:
        msg_color = "#d500f9"
    write_text(0, 80, message, 16, "bold", color=msg_color)
    
    draw_rounded_rect(design_painter, 0, 20, 660, 50, 8, "#ffffff", "#e0e0e0", 2)
    write_text(-310, 5, f"Balance: {money(balance)}", 13, "bold", align="left", color="#2e7d32")
    write_text(0, 5, f"Spins left: {get_spins_left()}", 13, "bold", color="#333333")
    write_text(310, 5, f"Remortgages: {house_remortgages}", 13, "normal", align="right", color="#c62828")

    cost_text = f"Cost: {money(get_spin_cost())}"
    if discount_spins > 0:
        cost_text += f" (Was {money(get_base_spin_cost())})"
    boost_text = f"{cost_text}  |  Luck: {luck_spins}  |  Payout: {payout_spins}  |  Discount: {discount_spins}"
    write_text(0, -20, boost_text, 11, "normal", color="#555555")
    
    write_text(0, -45, "Controls: Space=Spin | ← →=Change | S=Shop | Y=Remortgage", 10, "italic", color="#888888")

    write_text(-310, -75, "RECENT SPINS:", 11, "bold", align="left", color="#333333")
    start_y = -100
    for item in spin_history[-5:]:
        write_text(-310, start_y, item, 11, "normal", align="left", color="#555555")
        start_y -= 22

def draw_shop(message):
    text_painter.clear()
    design_painter.clear()
    screen.bgcolor("#fafafa")
    
    draw_rounded_rect(design_painter, 0, 350, 300, 50, 10, "#333333", "#ff9800", 3)
    write_text(0, 335, "★ BOOST SHOP ★", 22, "bold", color="#ffffff")
    
    draw_rounded_rect(design_painter, 0, 250, 660, 50, 8, "#ffffff", "#e0e0e0", 2)
    write_text(0, 235, f"Balance: {money(balance)}  |  Spins left: {get_spins_left()}", 13, "bold", color="#333333")
    write_text(0, 205, message, 12, "italic", color="#d32f2f")

    y = 160
    for key in ["1", "2", "3"]:
        item = SHOP_ITEMS[key]
        draw_rounded_rect(design_painter, 0, y, 660, 40, 8, "#f5f5f5", "#e0e0e0", 1)
        line = f"[{key}] {item['name']} - {money(item['cost'])}  |  {item['desc']}"
        write_text(0, y - 5, line, 13, "bold", color="#333333")
        y -= 50

    draw_rounded_rect(design_painter, 0, -50, 660, 80, 8, "#e3f2fd", "#90caf9", 2)
    write_text(-310, 10, "ACTIVE BOOSTS:", 11, "bold", align="left", color="#0d47a1")
    write_text(-310, -15, f"Luck: {luck_spins}  |  Payout: {payout_spins}  |  Discount: {discount_spins}", 11, "normal", align="left", color="#1565c0")

    y = -110
    write_text(-310, y+10, "MACHINES:", 11, "bold", align="left", color="#333333")
    for index, machine_id in enumerate(MACHINE_ORDER, 1):
        machine = MACHINES[machine_id]
        status = "✓ UNLOCKED" if is_unlocked(machine_id) else f"🔒 Reach {money(machine['unlock'])}"
        active = " ◀ ACTIVE" if machine_id == current_machine_id else ""
        color = "#2e7d32" if is_unlocked(machine_id) else "#999999"
        if machine_id == current_machine_id:
            color = "#d500f9"
        line = f"[{index}] {machine['name']} | {status}{active}"
        write_text(-310, y, line, 11, "bold", align="left", color=color)
        y -= 25

    write_text(0, -350, "Press S or Back button to return | Press 1-4 to select machine | 1-3 to buy boosts", 11, "italic", color="#888888")

# --- ACTIONS ---
def toggle_shop():
    global mode
    if is_spinning: return
    mode = "shop" if mode == "game" else "game"
    update_ui(message="Welcome to the shop!" if mode == "shop" else "Shop closed. Press Spin!")

def handle_number(number):
    if is_spinning: return
    if mode == "shop":
        if number in ["1", "2", "3"]:
            buy_item(number)
        elif number == "4":
            select_machine("4")
    else:
        select_machine(number)

def select_machine(number):
    global current_machine_id
    if is_spinning: return
    index = int(number) - 1
    if index < 0 or index >= len(MACHINE_ORDER): return
    machine_id = MACHINE_ORDER[index]
    if is_unlocked(machine_id):
        current_machine_id = machine_id
        update_ui(message=f"Switched to {MACHINES[machine_id]['name']} Slots.")
    else:
        update_ui(message=f"{MACHINES[machine_id]['name']} is locked! Reach {money(MACHINES[machine_id]['unlock'])}.")

def cycle_machine(direction=1):
    global current_machine_id
    if is_spinning or mode != "game": return
    unlocked = [m for m in MACHINE_ORDER if is_unlocked(m)]
    if len(unlocked) <= 1:
        update_ui(message="No other machines unlocked yet.")
        return
    if current_machine_id not in unlocked:
        current_machine_id = unlocked[0]
    current_index = unlocked.index(current_machine_id)
    next_index = (current_index + direction) % len(unlocked)
    current_machine_id = unlocked[next_index]
    update_ui(message=f"Switched to {MACHINES[current_machine_id]['name']} Slots.")

def buy_item(number):
    global balance, luck_spins, payout_spins, discount_spins
    if is_spinning or number not in SHOP_ITEMS: return
    item = SHOP_ITEMS[number]
    if balance < item["cost"]:
        update_ui(message=f"Not enough balance for {item['name']}!")
        return
    balance -= item["cost"]
    if number == "1": luck_spins += 25
    elif number == "2": payout_spins += 20
    elif number == "3": discount_spins += 30
    update_ui(message=f"Bought {item['name']}!")

# --- GAME MECHANICS ---
def spin_slots():
    global balance, luck_spins, payout_spins, discount_spins, is_spinning
    if is_spinning or mode != "game": return
    
    spin_cost = get_spin_cost()
    if balance < spin_cost:
        update_ui(message=f"No money! Spin costs {money(spin_cost)}. Remortgage? (Press Y)")
        return

    is_spinning = True
    balance -= spin_cost
    machine = MACHINES[current_machine_id]

    # Animation - only update reels, not entire UI
    for _ in range(10):
        r1, r2, r3 = get_weighted_symbol(machine), get_weighted_symbol(machine), get_weighted_symbol(machine)
        draw_reels_only(r1, r2, r3)
        time.sleep(0.05)

    res1, res2, res3 = get_weighted_symbol(machine), get_weighted_symbol(machine), get_weighted_symbol(machine)
    win_msg, outcome_summary, payout, win_type, side = "No luck. Try again.", f"[{res1} {res2} {res3}] -", 0, "loss", ""

    if res1 == res2 == res3:
        payout = int(get_symbol_multiplier(machine, res1) * get_base_spin_cost())
        win_type = "jackpot"
    elif res1 == res2 or res2 == res3:
        matched_symbol = res1 if res1 == res2 else res2
        side = "left" if res1 == res2 else "right"
        payout = int(get_symbol_multiplier(machine, matched_symbol) * machine["pair_factor"] * get_base_spin_cost())
        win_type = "pair"
    elif random.random() < 0.15:
        payout = max(1, int(get_base_spin_cost() * 0.75))
        win_type = "refund"
    else:
        outcome_summary += " Lost"

    if payout > 0:
        if payout_spins > 0: payout = int(payout * 1.5)
        balance += payout
        if win_type == "jackpot":
            win_msg = f"★ JACKPOT! Won {money(payout)}! ★"
            outcome_summary += f" JACKPOT! +{money(payout)}"
        elif win_type == "pair":
            win_msg = f"Matched 2 ({side})! Won {money(payout)}."
            outcome_summary += f" Pair ({side}) +{money(payout)}"
        else:
            win_msg = f"Small refund! Won {money(payout)}."
            outcome_summary += f" Refund +{money(payout)}"

    if luck_spins > 0: luck_spins -= 1
    if payout_spins > 0: payout_spins -= 1
    if discount_spins > 0: discount_spins -= 1

    update_max_balance()
    spin_history.append(outcome_summary)
    is_spinning = False
    update_ui(res1, res2, res3, message=win_msg)

def process_remortgage():
    global balance, house_remortgages
    if is_spinning: return
    if balance < get_spin_cost():
        amount = max(MIN_REMORTGAGE_AMOUNT, get_base_spin_cost() * 20)
        house_remortgages += 1
        balance += amount
        update_max_balance()
        update_ui(message=f"Remortgaged! Added {money(amount)}.")
    else:
        update_ui(message="You still have money for spins.")

def exit_game():
    screen.bye()

# --- INPUT HANDLING ---
def on_screen_click(x, y):
    if is_spinning: return
    if inside_button(x, y, BUTTONS["spin"]): spin_slots()
    elif inside_button(x, y, BUTTONS["prev"]): cycle_machine(-1)
    elif inside_button(x, y, BUTTONS["next"]): cycle_machine(1)
    elif inside_button(x, y, BUTTONS["shop"]): toggle_shop()

screen.onclick(on_screen_click)
screen.listen()
screen.onkey(spin_slots, "space")
screen.onkey(toggle_shop, "s")
screen.onkey(toggle_shop, "S")
screen.onkey(process_remortgage, "y")
screen.onkey(process_remortgage, "Y")
screen.onkey(exit_game, "n")
screen.onkey(exit_game, "N")
screen.onkey(lambda: handle_number("1"), "1")
screen.onkey(lambda: handle_number("2"), "2")
screen.onkey(lambda: handle_number("3"), "3")
screen.onkey(lambda: handle_number("4"), "4")
screen.onkey(lambda: cycle_machine(-1), "Left")
screen.onkey(lambda: cycle_machine(1), "Right")

# --- START ---
update_ui()
screen.mainloop()