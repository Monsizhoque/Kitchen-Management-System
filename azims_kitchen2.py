import pygame
import os
from abc import ABC, abstractmethod
from copy import deepcopy
from itertools import count
from datetime import datetime




BG = (25, 20, 17)
PANEL = (43, 34, 28)
PANEL2 = (58, 45, 36)
WHITE = (248, 241, 226)
MUTED = (181, 165, 145)
ORANGE = (225, 125, 55)
GOLD = (235, 190, 75)
GREEN = (75, 180, 105)
RED = (210, 75, 65)
BLUE = (75, 145, 210)
PURPLE = (145, 100, 190)

CATEGORY_COLORS = {
    "Rice Dish": ORANGE, "Curry Dish": RED,
    "Grill Dish": GREEN, "Beverage": BLUE,
    "Dessert": GOLD
}



class KitchenError(Exception):
    pass


class InvalidOrderError(KitchenError):
    pass


class MenuItemNotFoundError(KitchenError):
    pass


class StaffUnavailableError(KitchenError):
    pass




class Staff(ABC):
    def __init__(self, sid, name, exp, specialization="Any"):
        self.staff_id = sid
        self.name = name
        self.experience = exp
        self.specialization = specialization
        self.available = True

    @abstractmethod
    def work_description(self):
        pass

    @abstractmethod
    def can_handle(self, item):
        pass

    def __str__(self):
        return f"{self.name} - {self.role} - " \
               f"{'Available' if self.available else 'Busy'}"


class Chef(Staff):
    def work_description(self):
        return "Prepares and cooks food."

    def can_handle(self, item):
        return self.available and (
            self.specialization == "Any" or
            self.specialization == item.skill
        )


class HeadChef(Chef):
    def __init__(self, sid, name, exp):
        super().__init__(sid, name, exp, "Any")
        self.role = "Head Chef"

    def work_description(self):
        return "Supervises the entire kitchen."


class SousChef(Chef):
    def __init__(self, sid, name, exp, spec):
        super().__init__(sid, name, exp, spec)
        self.role = "Sous Chef"

    def work_description(self):
        return f"Specialist in {self.specialization} dishes."


class Cook(Chef):
    def __init__(self, sid, name, exp, spec):
        super().__init__(sid, name, exp, spec)
        self.role = "Cook"

    def work_description(self):
        return f"Prepares {self.specialization} items."


class Waiter(Staff):
    def __init__(self, sid, name, exp, section):
        super().__init__(sid, name, exp, section)
        self.role = "Waiter"
        self.section = section

    def work_description(self):
        return f"Serves customers in section {self.section}."

    def can_handle(self, item):
        return self.available




class FoodItem(ABC):
    def __init__(self, iid, name, price, time, difficulty, skill, desc=""):
        self.item_id = iid
        self.name = name
        self.price = price
        self.cooking_time = time
        self.difficulty = difficulty
        self.skill = skill
        self.description = desc

    @abstractmethod
    def category(self):
        pass

    def __str__(self):
        return f"{self.item_id} - {self.name} - Tk {self.price}"


class RiceItems(FoodItem):
    def category(self):
        return "Rice Dish"


class CurryItems(FoodItem):
    def category(self):
        return "Curry Dish"


class GrilledItems(FoodItem):
    def category(self):
        return "Grill Dish"


class Beverage(FoodItem):
    def category(self):
        return "Beverage"


class Dessert(FoodItem):
    def category(self):
        return "Dessert"




class OrderItem:
    def __init__(self, food, quantity=1):
        self.food = food
        self.quantity = quantity

    @property
    def subtotal(self):
        return self.food.price * self.quantity

    def increase(self):
        self.quantity += 1

    def decrease(self):
        if self.quantity > 1:
            self.quantity -= 1


class Order:
    counter = count(1001)

    def __init__(self, items):
        if not items:
            raise InvalidOrderError("Order cannot be empty.")

        self.order_id = next(Order.counter)
        self.items = items
        self.status = "Pending"
        self.chef = None
        self.waiter = None
        self.created_at = datetime.now()
        self.started_at = None
        self.completed_at = None
        self.total = self.calculate_total()
        self.discount = 0
        self.final_total = self.total
        self.cooking_duration = 0

    def calculate_total(self):
        return sum(x.subtotal for x in self.items)

    def calculate_discount(self):
        rate = 0.15 if self.total >= 3000 else \
               0.10 if self.total >= 2000 else \
               0.05 if self.total >= 1000 else 0

        self.discount = self.total * rate
        self.final_total = self.total - self.discount

    def start(self):
        self.status = "Cooking"
        self.started_at = datetime.now()
        self.cooking_duration = max(
            x.food.cooking_time for x in self.items
        )

    def complete(self):
        self.status = "Ready"
        self.completed_at = datetime.now()

    def cancel(self):
        self.status = "Cancelled"
        self.completed_at = datetime.now()

    def __len__(self):
        return len(self.items)

    def __add__(self, other):
        if isinstance(other, Order):
            return Order(deepcopy(self.items + other.items))
        return NotImplemented

    def __lt__(self, other):
        return self.final_total < other.final_total

    def __gt__(self, other):
        return self.final_total > other.final_total

    def __str__(self):
        return f"Order #{self.order_id} - {self.status}"


class OrderIterator:
    def __init__(self, orders):
        self.orders = orders
        self.index = 0

    def __iter__(self):
        return self

    def __next__(self):
        if self.index >= len(self.orders):
            raise StopIteration
        order = self.orders[self.index]
        self.index += 1
        return order


def pending_orders(orders):
    for order in orders:
        if order.status in ("Pending", "Cooking"):
            yield order


def available_staff(staff):
    for person in staff:
        if person.available:
            yield person




class KitchenManager:
    def __init__(self):
        self.menu = []
        self.staff = []
        self.active_orders = []
        self.completed_orders = []
        self.cancelled_orders = []
        self.cart = []
        self.revenue = 0
        self.load_menu()
        self.load_staff()

    def load_menu(self):
        self.menu = [
            RiceItems("M01", "Azim's Special Kacchi Biryani", 400, 30,
                      "Easy", "Curry"),
            RiceItems("M02", "Azim's Special OOP Biryani", 380, 30,
                      "Easy", "Curry"),
            RiceItems("M03", "Chicken Biryani", 200, 18,
                      "Medium", "Curry"),
            RiceItems("M04", "Fried Rice", 250, 15,
                      "Easy", "Curry"),
            RiceItems("M05", "Khichuri", 150, 15,
                      "Easy", "Curry"),
            RiceItems("M06", "Beef Biryani", 300, 30,
                      "Easy", "Curry"),
            RiceItems("M07", "White Rice", 100, 10,
                      "Medium", "Curry"),
            RiceItems("M08", "Butter Naan", 100, 10,
                      "Medium", "Curry"),
            GrilledItems("M09", "Beef Steak", 800, 40,
                         "Hard", "Grill"),
            GrilledItems("M10", "Grilled Chicken", 199, 15,
                         "Medium", "Grill"),
            GrilledItems("M11", "Beef Sheekh", 299, 15,
                         "Medium", "Grill"),
            CurryItems("M012", "Butter Chicken", 349, 20,
                       "Medium", "Curry"),
            CurryItems("M013", "Prawn Malai Curry", 549, 20,
                       "Medium", "Curry"),
            CurryItems("M014", "Mezbani Beef", 449, 20,
                       "Medium", "Curry"),
            CurryItems("M015", "Lamb Curry", 650, 20,
                       "Medium", "Curry"),
            Beverage("B01", "Lemonade", 60, 5,
                     "Easy", "Beverage"),
            Beverage("B02", "Cold Coffee", 180, 6,
                     "Easy", "Beverage"),
            Beverage("B03", "Soft Drinks", 70, 2,
                     "Easy", "Beverage"),
            Beverage("B04", "Mineral Water", 20, 2,
                     "Easy", "Beverage"),
            Beverage("B05", "Orange/Malta Juice", 150, 5,
                     "Easy", "Beverage"),
            Dessert("D01", "Chocolate Lava Cake", 250, 5,
                    "Easy", "Dessert"),
            Dessert("D02", "Ice Cream Scoop", 120, 3,
                    "Easy", "Dessert"),
            Dessert("D03", "Falooda", 220, 3,
                    "Easy", "Dessert")
        ]

    def load_staff(self):
        self.staff = [
            HeadChef("C01", "Azim Sir", 12),
            SousChef("C02", "Monsiz", 7, "Grill"),
            SousChef("C03", "Athar", 5, "Curry"),
            Cook("K01", "Hasan", 4, "Dessert"),
            Waiter("W01", "Rifah", 3, "A"),
            Waiter("W02", "Afnan", 2, "B"),
            Waiter("W03", "Fahim", 4, "C")
        ]

    def search_food(self, keyword):
        keyword = keyword.lower().strip()
        return [x for x in self.menu if keyword in x.name.lower()]

    def get_food(self, item_id):
        for x in self.menu:
            if x.item_id == item_id:
                return x
        raise MenuItemNotFoundError("Food item not found.")

    def add_to_cart(self, food):
        for item in self.cart:
            if item.food.item_id == food.item_id:
                item.increase()
                return
        self.cart.append(OrderItem(food))

    def remove_from_cart(self, index):
        if 0 <= index < len(self.cart):
            return self.cart.pop(index)

    def cart_total(self):
        return sum(x.subtotal for x in self.cart)

    def get_discount(self):
        total = self.cart_total()
        rate = 0.15 if total >= 3000 else \
               0.10 if total >= 2000 else \
               0.05 if total >= 1000 else 0
        return total * rate

    def choose_chef(self, items):
        skills = {x.food.skill for x in items}

        for person in self.staff:
            if isinstance(person, Chef) and person.available:
                if person.specialization in skills:
                    return person

        for person in self.staff:
            if isinstance(person, HeadChef) and person.available:
                return person

        raise StaffUnavailableError("No chef is currently available.")

    def choose_waiter(self):
        for person in self.staff:
            if isinstance(person, Waiter) and person.available:
                return person
        raise StaffUnavailableError("No waiter is currently available.")

    def create_order(self):
        if not self.cart:
            raise InvalidOrderError("Cart is empty.")

        items = deepcopy(self.cart)
        order = Order(items)
        order.calculate_discount()

        order.chef = self.choose_chef(items)
        order.waiter = self.choose_waiter()

        order.chef.available = False
        order.waiter.available = False
        order.start()

        self.active_orders.append(order)
        self.cart.clear()
        return order

    def cancel_order(self, order):
        if order not in self.active_orders:
            raise InvalidOrderError("This order is no longer active.")

        order.cancel()

        
        if order.chef:
            order.chef.available = True
        if order.waiter:
            order.waiter.available = True

        self.active_orders.remove(order)
        self.cancelled_orders.append(order)

    def update_orders(self):
        now = datetime.now()

        for order in self.active_orders[:]:
            if order.started_at:
                elapsed = (now - order.started_at).total_seconds()
                required = order.cooking_duration * 2

                if elapsed >= required:
                    order.complete()

                    if order.chef:
                        order.chef.available = True
                    if order.waiter:
                        order.waiter.available = True

                    self.revenue += order.final_total
                    self.completed_orders.append(order)
                    self.active_orders.remove(order)

    def save(self):
        os.makedirs("data", exist_ok=True)

        with open("data/kitchen_report.txt", "w",
                  encoding="utf-8") as file:

            file.write("====================================\n")
            file.write("          AZIM'S KITCHEN\n")
            file.write("====================================\n\n")
            file.write(f"Generated: {datetime.now()}\n\n")
            file.write(f"Completed Orders: "
                       f"{len(self.completed_orders)}\n")
            file.write(f"Cancelled Orders: "
                       f"{len(self.cancelled_orders)}\n")
            file.write(f"Revenue: Tk {self.revenue:.2f}\n\n")

            for order in self.completed_orders:
                file.write(f"Order #{order.order_id}\n")
                file.write(f"Total: Tk {order.final_total:.2f}\n")
                file.write(f"Chef: {order.chef.name}\n")
                file.write("----------------------------\n")

        return "Data saved successfully."


 #UI HELPERS

class Button:
    def __init__(self, rect, text, color, text_color=WHITE):
        self.rect = pygame.Rect(rect)
        self.text = text
        self.color = color
        self.text_color = text_color

    def draw(self, screen, font, mouse):
        color = tuple(min(255, c + 25)
                      for c in self.color) \
                if self.rect.collidepoint(mouse) else self.color

        pygame.draw.rect(screen, color, self.rect, border_radius=10)
        pygame.draw.rect(screen, WHITE, self.rect, 1, border_radius=10)

        surface = font.render(self.text, True, self.text_color)
        screen.blit(surface, surface.get_rect(center=self.rect.center))

    def clicked(self, pos):
        return self.rect.collidepoint(pos)


def txt(screen, font, text, x, y, color=WHITE):
    screen.blit(font.render(str(text), True, color), (x, y))


#APPLICATION =====================

class App:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((1200, 750))
        pygame.display.set_caption("AZIM'S KITCHEN")
        self.clock = pygame.time.Clock()

        self.title = pygame.font.SysFont("arial", 34, bold=True)
        self.big = pygame.font.SysFont("arial", 22, bold=True)
        self.medium = pygame.font.SysFont("arial", 18)
        self.small = pygame.font.SysFont("arial", 15)
        self.tiny = pygame.font.SysFont("arial", 13)
        self.stat = pygame.font.SysFont("arial", 28, bold=True)

        self.manager = KitchenManager()
        self.running = True
        self.page = "welcome"
        self.logged_in = False

        self.username = ""
        self.password = ""
        self.login_field = "username"

        self.user_rect = pygame.Rect(390, 220, 420, 50)
        self.pass_rect = pygame.Rect(390, 290, 420, 50)
        self.login_btn = Button(
            (450, 390, 300, 55), "ENTER KITCHEN", ORANGE
        )

        self.search = ""
        self.search_active = False
        self.category = "All"

        self.order_scroll = 0
        self.menu_scroll = 0
        self.selected_order = None

        self.message = ""
        self.message_time = 0

        self.nav = [
            Button((20, 80, 140, 42), "Dashboard", ORANGE),
            Button((170, 80, 140, 42), "New Order", GREEN),
            Button((320, 80, 140, 42), "Menu", BLUE),
            Button((470, 80, 140, 42), "Staff", GOLD),
            Button((620, 80, 140, 42), "Reports", PURPLE),
            Button((995, 80, 175, 42), "Save Data", GREEN)
        ]

    def message_show(self, text):
        self.message = text
        self.message_time = pygame.time.get_ticks()

    #SCROLL HELPERS =================

    def foods_shown(self):
        foods = self.manager.menu

        if self.category != "All":
            foods = [x for x in foods
                     if x.category() == self.category]

        if self.search:
            foods = [x for x in foods
                     if self.search.lower() in x.name.lower()]

        return foods

    def order_content_height(self):
        rows = (len(self.manager.menu) + 1) // 2      # 2 cards per row
        return rows * 150 + 20

    def order_max_scroll(self):
        return max(0, self.order_content_height() - 460)

    def menu_max_scroll(self):
        rows = (len(self.foods_shown()) + 2) // 3     # 3 cards per row
        return max(0, rows * 150 + 20 - 440)

    #HEADER 

    def header(self):
        pygame.draw.rect(self.screen, PANEL, (0, 0, 1200, 135))
        txt(self.screen, self.title, "AZIM'S KITCHEN",
            20, 15, ORANGE)
        txt(self.screen, self.small,
            "Premium Kitchen Management System",
            22, 52, MUTED)

        for b in self.nav:
            b.draw(self.screen, self.small, pygame.mouse.get_pos())

    # WELCOME 

    def welcome(self):
        self.screen.fill(BG)

        pygame.draw.circle(self.screen, PANEL, (600, 180), 150)
        pygame.draw.circle(self.screen, PANEL2, (600, 180), 110)

        txt(self.screen, self.big, "WELCOME TO", 505, 120, MUTED)
        txt(self.screen, self.title, "AZIM'S KITCHEN",
            430, 160, ORANGE)

        pygame.draw.rect(self.screen, PANEL,
                         (340, 260, 520, 300), border_radius=18)

        pygame.draw.rect(self.screen, PANEL2,
                         self.user_rect, border_radius=8)
        pygame.draw.rect(self.screen, PANEL2,
                         self.pass_rect, border_radius=8)

        txt(self.screen, self.tiny, "Username",
            405, 225, MUTED)
        txt(self.screen, self.medium, self.username,
            405, 240)

        txt(self.screen, self.tiny, "Password",
            405, 295, MUTED)
        txt(self.screen, self.medium,
            "*" * len(self.password), 405, 310)

        self.login_btn.draw(
            self.screen, self.medium, pygame.mouse.get_pos()
        )

        txt(self.screen, self.tiny,
            "Demo login: admin / 1234",
            495, 475, MUTED)

    # DASHBOARD 

    def card(self, x, title, value, color, y=230):
        pygame.draw.rect(self.screen, PANEL,
                         (x, y, 270, 130), border_radius=15)
        pygame.draw.rect(self.screen, color,
                         (x, y, 270, 7), border_radius=4)
        txt(self.screen, self.small, title, x + 20, y + 20, MUTED)
        txt(self.screen, self.stat, value,
            x + 20, y + 55, color)

    def dashboard(self):
        txt(self.screen, self.title,
            "AZIM'S KITCHEN DASHBOARD",
            20, 150, GOLD)

        txt(self.screen, self.small,
            datetime.now().strftime(
                "%A, %d %B %Y • %I:%M %p"
            ), 22, 192, MUTED)

        cards = [
            ("TOTAL ORDERS",
             len(self.manager.completed_orders), ORANGE),
            ("ACTIVE ORDERS",
             len(self.manager.active_orders), GREEN),
            ("AVAILABLE STAFF",
             len(list(available_staff(self.manager.staff))), BLUE),
            ("REVENUE",
             f"Tk {self.manager.revenue:.0f}", GOLD)
        ]

        for x, data in zip((20, 310, 600, 890), cards):
            self.card(x, *data)

        pygame.draw.rect(self.screen, PANEL,
                         (20, 390, 1120, 300),
                         border_radius=15)

        txt(self.screen, self.big,
            "ACTIVE ORDERS", 40, 410, ORANGE)

        if not self.manager.active_orders:
            txt(self.screen, self.medium,
                "No active orders right now.",
                40, 465, MUTED)
            return

        y = 460

        for order in self.manager.active_orders[:5]:
            txt(self.screen, self.medium,
                f"#{order.order_id}", 40, y)
            txt(self.screen, self.small,
                order.status, 130, y, GREEN)
            txt(self.screen, self.small,
                f"Chef: {order.chef.name}", 280, y, MUTED)
            txt(self.screen, self.small,
                f"Tk {order.final_total:.0f}", 600, y, GOLD)

            elapsed = (
                datetime.now() - order.started_at
            ).total_seconds()
            required = order.cooking_duration * 2
            progress = min(1, elapsed / required)

            pygame.draw.rect(
                self.screen, PANEL2,
                (700, y + 4, 300, 10),
                border_radius=5
            )
            pygame.draw.rect(
                self.screen, GREEN,
                (700, y + 4, int(300 * progress), 10),
                border_radius=5
            )

            Button((1020, y - 3, 100, 28),
                   "CANCEL", RED).draw(
                self.screen, self.tiny, pygame.mouse.get_pos()
            )
            y += 45

    #FOOD CARD 

    def food_card(self, food, x, y, add=True):
        color = CATEGORY_COLORS.get(food.category(), ORANGE)

        pygame.draw.rect(self.screen, PANEL,
                         (x, y, 345, 135),
                         border_radius=12)
        pygame.draw.rect(self.screen, color,
                         (x, y, 7, 135),
                         border_radius=4)

        txt(self.screen, self.medium,
            food.name, x + 20, y + 15)
        txt(self.screen, self.tiny,
            food.item_id, x + 20, y + 43, MUTED)
        txt(self.screen, self.tiny,
            food.category(), x + 80, y + 43, color)
        txt(self.screen, self.tiny,
            f"{food.cooking_time} min", x + 210, y + 43, MUTED)
        txt(self.screen, self.big,
            f"Tk {food.price}", x + 20, y + 73, GOLD)

        if add:
            Button((x + 235, y + 85, 90, 35),
                   "ADD +", color).draw(
                self.screen, self.tiny, pygame.mouse.get_pos()
            )

    #CART 

    def cart(self):
        pygame.draw.rect(self.screen, PANEL,
                         (790, 155, 380, 550),
                         border_radius=15)

        txt(self.screen, self.big, "YOUR CART",
            815, 175, ORANGE)

        txt(self.screen, self.tiny,
            f"{len(self.manager.cart)} item type(s)",
            815, 205, MUTED)

        if not self.manager.cart:
            txt(self.screen, self.medium,
                "Your cart is empty.", 815, 280, MUTED)
            txt(self.screen, self.tiny,
                "Select food from the left side.",
                815, 315, MUTED)
            return

        y = 245

        for item in self.manager.cart:
            pygame.draw.rect(
                self.screen, PANEL2,
                (810, y - 5, 340, 70),
                border_radius=8
            )

            txt(self.screen, self.tiny,
                item.food.name[:25],
                825, y + 3)

            txt(self.screen, self.tiny,
                f"Tk {item.subtotal}",
                1035, y + 3, GOLD)

            Button((825, y + 30, 30, 25),
                   "-", RED).draw(
                self.screen, self.tiny, pygame.mouse.get_pos()
            )

            Button((860, y + 30, 30, 25),
                   "+", GREEN).draw(
                self.screen, self.tiny, pygame.mouse.get_pos()
            )

            txt(self.screen, self.tiny,
                f"Qty: {item.quantity}",
                910, y + 34, MUTED)

            Button((1060, y + 30, 80, 25),
                   "REMOVE", RED).draw(
                self.screen, self.tiny, pygame.mouse.get_pos()
            )

            y += 80

        total = self.manager.cart_total()
        discount = self.manager.get_discount()
        final = total - discount

        pygame.draw.line(
            self.screen, PANEL2,
            (815, 555), (1145, 555), 2
        )

        txt(self.screen, self.small,
            f"Subtotal: Tk {total:.0f}",
            815, 570)

        txt(self.screen, self.small,
            f"Discount: Tk {discount:.0f}",
            815, 595, GREEN)

        txt(self.screen, self.big,
            f"TOTAL: Tk {final:.0f}",
            815, 625, GOLD)

        Button((815, 660, 335, 38),
               "CONFIRM ORDER", GREEN).draw(
            self.screen, self.small, pygame.mouse.get_pos()
        )

    # NEW ORDER 

    def new_order(self):
        txt(self.screen, self.title,
            "CREATE NEW ORDER", 20, 150, GREEN)
        txt(self.screen, self.small,
            "Choose your food and add it to the cart.",
            22, 190, MUTED)

        area = pygame.Rect(10, 215, 760, 480)
        self.screen.set_clip(area)

        for i, food in enumerate(self.manager.menu):
            col = i % 2
            row = i // 2
            x = 20 + col * 365
            y = 225 + row * 150 - self.order_scroll
            self.food_card(food, x, y)

        self.screen.set_clip(None)

        content = self.order_content_height()
        max_scroll = self.order_max_scroll()

        if max_scroll:
            pygame.draw.rect(
                self.screen, PANEL2,
                (765, 220, 8, 460),
                border_radius=4
            )
            h = max(50, int(460 * 460 / content))
            by = 220 + int(
                self.order_scroll / max_scroll * (460 - h)
            )
            pygame.draw.rect(
                self.screen, ORANGE,
                (765, by, 8, h),
                border_radius=4
            )

        self.cart()

    # MENU 

    def menu(self):
        txt(self.screen, self.title,
            "OUR MENU", 20, 150, GOLD)

        search_rect = pygame.Rect(300, 145, 300, 42)
        pygame.draw.rect(self.screen, PANEL,
                         search_rect, border_radius=8)

        txt(self.screen, self.small,
            self.search or "Search food...",
            315, 157, WHITE if self.search else MUTED)

        categories = [
            ("All", WHITE), ("Rice Dish", ORANGE),
            ("Curry Dish", RED), ("Grill Dish", GREEN),
            ("Beverage", BLUE), ("Dessert", GOLD)
        ]

        for i, (cat, color) in enumerate(categories):
            Button((20 + i * 128, 205, 120, 35),
                   cat, color).draw(
                self.screen, self.tiny,
                pygame.mouse.get_pos()
            )

        foods = self.foods_shown()

        area = pygame.Rect(10, 250, 1150, 440)
        self.screen.set_clip(area)

        for i, food in enumerate(foods):
            x = 20 + (i % 3) * 375
            y = 260 + (i // 3) * 150 - self.menu_scroll
            self.food_card(food, x, y, False)

        self.screen.set_clip(None)

    # ================= STAFF =================

    def staff_page(self):
        txt(self.screen, self.title,
            "OUR STAFF", 20, 150, BLUE)

        y = 215

        for person in self.manager.staff:
            color = GREEN if person.available else RED

            pygame.draw.rect(
                self.screen, PANEL,
                (20, y, 1120, 58),
                border_radius=10
            )

            pygame.draw.circle(
                self.screen, color,
                (45, y + 29), 8
            )

            txt(self.screen, self.medium,
                person.name, 70, y + 12)
            txt(self.screen, self.small,
                person.role, 250, y + 15, GOLD)
            txt(self.screen, self.small,
                f"Experience: {person.experience} yrs",
                400, y + 15, MUTED)
            txt(self.screen, self.small,
                f"Specialization: {person.specialization}",
                620, y + 15, MUTED)
            txt(self.screen, self.small,
                "AVAILABLE" if person.available else "BUSY",
                1000, y + 15, color)

            y += 70

     #REPORTS

    def reports(self):
        txt(self.screen, self.title,
            "DAILY REPORT", 20, 150, GREEN)

        completed = len(self.manager.completed_orders)
        revenue = self.manager.revenue
        average = revenue / completed if completed else 0

        cards = [
            ("COMPLETED ORDERS", completed, ORANGE),
            ("TOTAL REVENUE", f"Tk {revenue:.0f}", GREEN),
            ("AVERAGE ORDER", f"Tk {average:.0f}", BLUE),
            ("ACTIVE ORDERS",
             len(self.manager.active_orders), GOLD)
        ]

        for x, data in zip((20, 310, 600, 890), cards):
            self.card(x, *data, y=220)

        pygame.draw.rect(
            self.screen, PANEL,
            (20, 390, 1120, 300),
            border_radius=15
        )

        txt(self.screen, self.big,
            "COMPLETED ORDERS",
            45, 415, GOLD)
        txt(self.screen, self.small,
            f"Cancelled orders: {len(self.manager.cancelled_orders)}",
            900, 420, RED)

        if not self.manager.completed_orders:
            txt(self.screen, self.medium,
                "No completed orders yet.",
                45, 470, MUTED)
            return

        y = 465

        for order in self.manager.completed_orders[-5:]:
            txt(self.screen, self.medium,
                f"Order #{order.order_id}",
                45, y)
            txt(self.screen, self.small,
                f"{len(order)} items",
                220, y, MUTED)
            txt(self.screen, self.small,
                f"Chef: {order.chef.name}",
                350, y, MUTED)
            txt(self.screen, self.small,
                f"Tk {order.final_total:.0f}",
                650, y, GREEN)
            txt(self.screen, self.small,
                "READY", 900, y, GREEN)
            y += 40

    #SUCCESS 

    def success(self):
        self.screen.fill(BG)

        pygame.draw.rect(
            self.screen, PANEL,
            (280, 70, 640, 610),
            border_radius=20
        )

        order = self.selected_order

        txt(self.screen, self.title,
            "ORDER CONFIRMED", 450, 105, GREEN)
        txt(self.screen, self.big,
            f"Order #{order.order_id}",
            505, 160, GOLD)

        y = 210

        for item in order.items:
            txt(self.screen, self.small,
                item.food.name, 340, y)
            txt(self.screen, self.small,
                f"x{item.quantity}", 680, y, MUTED)
            txt(self.screen, self.small,
                f"Tk {item.subtotal}",
                760, y, GOLD)
            y += 32

        pygame.draw.line(
            self.screen, PANEL2,
            (340, y + 10), (850, y + 10), 2
        )

        y += 35

        txt(self.screen, self.small,
            f"Subtotal: Tk {order.total:.0f}",
            340, y)

        y += 30

        txt(self.screen, self.small,
            f"Discount: Tk {order.discount:.0f}",
            340, y, GREEN)

        y += 40

        txt(self.screen, self.big,
            f"TOTAL: Tk {order.final_total:.0f}",
            340, y, GOLD)

        y += 55

        txt(self.screen, self.medium,
            f"Chef: {order.chef.name}",
            340, y, BLUE)
        txt(self.screen, self.medium,
            f"Waiter: {order.waiter.name}",
            600, y, BLUE)

        txt(self.screen, self.small,
            "Your order is now being prepared.",
            440, 555, MUTED)

        txt(self.screen, self.tiny,
            "Cooking progress will appear on Dashboard.",
            430, 580, MUTED)

        Button((450, 620, 300, 40),
               "BACK TO DASHBOARD", ORANGE).draw(
            self.screen, self.small, pygame.mouse.get_pos()
        )

    # EVENTS =================

    def handle_event(self, event):

        if event.type == pygame.QUIT:
            self.running = False
            return

        # ---------- LOGIN ----------

        if self.page == "welcome":

            if event.type == pygame.MOUSEBUTTONDOWN:
                pos = event.pos

                if self.user_rect.collidepoint(pos):
                    self.login_field = "username"

                elif self.pass_rect.collidepoint(pos):
                    self.login_field = "password"

                elif self.login_btn.clicked(pos):
                    self.login()

            elif event.type == pygame.KEYDOWN:

                if event.key == pygame.K_BACKSPACE:
                    if self.login_field == "username":
                        self.username = self.username[:-1]
                    else:
                        self.password = self.password[:-1]

                elif event.key == pygame.K_TAB:
                    self.login_field = (
                        "password"
                        if self.login_field == "username"
                        else "username"
                    )

                elif event.key == pygame.K_RETURN:
                    self.login()

                elif event.unicode.isprintable():
                    if self.login_field == "username":
                        if len(self.username) < 20:
                            self.username += event.unicode
                    else:
                        if len(self.password) < 20:
                            self.password += event.unicode

            return

        # SUCCESS ----------

        if self.page == "success":
            if event.type == pygame.MOUSEBUTTONDOWN:
                if pygame.Rect(450, 620, 300, 40).collidepoint(
                        event.pos):
                    self.page = "dashboard"
            return

        # ---------- SCROLLING ----------

        if event.type == pygame.MOUSEWHEEL:
            mx, my = pygame.mouse.get_pos()

            if self.page == "new_order" and 10 <= mx <= 775 \
                    and 215 <= my <= 700:

                self.order_scroll = max(
                    0, min(
                        self.order_scroll - event.y * 40,
                        self.order_max_scroll()
                    )
                )

            elif self.page == "menu":
                self.menu_scroll = max(
                    0, min(
                        self.menu_scroll - event.y * 40,
                        self.menu_max_scroll()
                    )
                )

            return

        # MENU SEARCH TYPING ----------

        if self.page == "menu" and event.type == pygame.KEYDOWN:
            if self.search_active:
                if event.key == pygame.K_BACKSPACE:
                    self.search = self.search[:-1]
                elif event.key == pygame.K_ESCAPE:
                    self.search = ""
                elif event.unicode.isprintable() and len(self.search) < 25:
                    self.search += event.unicode

        if event.type != pygame.MOUSEBUTTONDOWN:
            return

        pos = event.pos

        # ---------- NAVIGATION ----------

        for i, button in enumerate(self.nav):
            if button.clicked(pos):

                pages = [
                    "dashboard", "new_order",
                    "menu", "staff", "reports"
                ]

                if i < 5:
                    self.page = pages[i]

                    if i == 1:
                        self.order_scroll = 0
                    elif i == 2:
                        self.menu_scroll = 0

                else:
                    self.message_show(self.manager.save())

                return

        # ---------- DASHBOARD: CANCEL ORDER ----------

        if self.page == "dashboard":
            y = 460

            for order in self.manager.active_orders[:5]:
                if pygame.Rect(
                    1020, y - 3, 100, 28
                ).collidepoint(pos):
                    try:
                        self.manager.cancel_order(order)
                        self.message_show(
                            f"Order #{order.order_id} cancelled."
                        )
                    except KitchenError as e:
                        self.message_show(str(e))
                    return

                y += 45

        # ---------- NEW ORDER ----------

        if self.page == "new_order":

            for i, food in enumerate(self.manager.menu):
                col = i % 2
                row = i // 2

                x = 20 + col * 365
                y = 225 + row * 150 - self.order_scroll

                if pygame.Rect(
                    x + 235, y + 85, 90, 35
                ).collidepoint(pos):

                    self.manager.add_to_cart(food)
                    self.message_show(f"{food.name} added.")
                    return

            y = 245

            for index, item in enumerate(self.manager.cart):

                if pygame.Rect(
                    825, y + 30, 30, 25
                ).collidepoint(pos):
                    item.decrease()
                    return

                if pygame.Rect(
                    860, y + 30, 30, 25
                ).collidepoint(pos):
                    item.increase()
                    return

                if pygame.Rect(
                    1060, y + 30, 80, 25
                ).collidepoint(pos):
                    removed = self.manager.remove_from_cart(index)
                    self.message_show(f"{removed.food.name} removed.")
                    return

                y += 80

            if pygame.Rect(
                815, 660, 335, 38
            ).collidepoint(pos):

                try:
                    self.selected_order = \
                        self.manager.create_order()
                    self.page = "success"
                    self.message_show(
                        "Order confirmed successfully!"
                    )
                except KitchenError as e:
                    self.message_show(str(e))

                return

        # ---------- MENU ----------

        if self.page == "menu":

            search_rect = pygame.Rect(300, 145, 300, 42)

            if search_rect.collidepoint(pos):
                self.search_active = True
            else:
                self.search_active = False

            categories = [
                "All", "Rice Dish", "Curry Dish",
                "Grill Dish", "Beverage", "Dessert"
            ]

            for i, category in enumerate(categories):
                if pygame.Rect(
                    20 + i * 128, 205, 120, 35
                ).collidepoint(pos):

                    self.category = category
                    self.menu_scroll = 0
                    return

    def login(self):
        if self.username == "admin" and self.password == "1234":
            self.logged_in = True
            self.page = "dashboard"
        else:
            self.message_show(
                "Invalid login! Use admin / 1234"
            )

    def draw(self):
        self.screen.fill(BG)

        if self.page == "welcome":
            self.welcome()

        elif self.page == "success":
            self.success()

        else:
            self.header()

            if self.page == "dashboard":
                self.dashboard()
            elif self.page == "new_order":
                self.new_order()
            elif self.page == "menu":
                self.menu()
            elif self.page == "staff":
                self.staff_page()
            elif self.page == "reports":
                self.reports()

        if self.message:
            if pygame.time.get_ticks() - self.message_time < 3000:
                pygame.draw.rect(
                    self.screen, PANEL2,
                    (350, 700, 500, 38),
                    border_radius=10
                )
                txt(self.screen, self.small,
                    self.message, 370, 711)
            else:
                self.message = ""

        pygame.display.flip()

    def run(self):
        while self.running:

            for event in pygame.event.get():
                self.handle_event(event)

            if self.logged_in:
                self.manager.update_orders()

            self.draw()
            self.clock.tick(60)

        pygame.quit()


# ===================== MAIN =====================

if __name__ == "__main__":
    App().run()
