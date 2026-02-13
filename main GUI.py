from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.screenmanager import ScreenManager, Screen, FadeTransition
from kivy.core.window import Window
from kivy.graphics import Color, RoundedRectangle, Line
from kivy.metrics import dp
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
import log
import database
import logging
from pathlib import Path
from kivy.uix.scrollview import ScrollView


# --- Theme Settings ---
# Dark mode colors
THEME = {
    "background": (0.1, 0.1, 0.14, 1),        # LIGHTER Background (was 0.05)
    "surface": (0.2, 0.2, 0.23, 1),           # Lighter grey
    "surface_active": (0.25, 0.25, 0.28, 1),  # Even lighter
    "primary": (0.0, 0.48, 1.0, 1),           # Vivid Apple Blue
    "accent": (0.2, 0.8, 0.6, 1),             # Mint/Teal accent
    "text_primary": (1.0, 1.0, 1.0, 1),       # Pure white text
    "text_secondary": (0.7, 0.7, 0.75, 1),    # Brighter grey text
    "danger": (1.0, 0.27, 0.27, 1),           # Red
    "border_color": (1, 1, 1, 0.2)            # Stronger border
}

Window.clearcolor = THEME["background"]

# --- Global List ---
items_list = []

# --- UI  ---


class ProButton(Button):
    """A nice button with rounded corners."""

    def __init__(self, bg_color=THEME["primary"], font_size=dp(16), radius=dp(8), **kwargs):
        super().__init__(**kwargs)
        self.background_normal = ""
        self.background_down = ""
        self.background_color = (0, 0, 0, 0)  # We draw manually
        self.custom_bg_color = bg_color
        self.font_size = font_size
        self.bold = True
        self.color = THEME["text_primary"]
        self.radius = radius
        self.bind(pos=self.update_canvas, size=self.update_canvas,
                  state=self.update_canvas)

    def update_canvas(self, *args):
        self.canvas.before.clear()
        with self.canvas.before:
            # Color change on press
            if self.state == 'down':
                # Darken slightly
                r, g, b, a = self.custom_bg_color
                Color(r*0.8, g*0.8, b*0.8, a)
            else:
                Color(*self.custom_bg_color)

            RoundedRectangle(pos=self.pos, size=self.size,
                             radius=[self.radius])


class ProInput(TextInput):
    """Simple text input field."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.background_normal = ""
        self.background_active = ""
        self.background_color = THEME["surface"]
        self.foreground_color = THEME["text_primary"]
        self.hint_text_color = THEME["text_secondary"]
        self.cursor_color = THEME["primary"]
        self.padding = [dp(16), dp(16), dp(16), dp(16)]  # Comfortable padding
        self.font_size = dp(16)
        self.multiline = False
        self.size_hint_y = None
        self.height = dp(54)
        self.bind(pos=self.update_canvas, size=self.update_canvas,
                  focus=self.update_canvas)
        self.update_canvas()

    def update_canvas(self, *args):
        self.canvas.before.clear()
        with self.canvas.before:
            # Background
            if self.focus:
                Color(*THEME["surface_active"])
            else:
                Color(*THEME["surface"])
            RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(10)])

            # Subtle Border (Highlight on focus)
            if self.focus:
                Color(*THEME["primary"])
            else:
                Color(*THEME["border_color"])
            Line(rounded_rectangle=(self.x, self.y,
                 self.width, self.height, dp(10)), width=1.2)


class ItemCard(BoxLayout):
    """Displays an item with an edit button."""

    def __init__(self, name, desc, index, **kwargs):
        super().__init__(**kwargs)
        self.index = index
        self.orientation = 'horizontal'  # Side by side
        self.size_hint_y = None
        self.height = dp(85)
        self.padding = dp(16)
        self.spacing = dp(15)

        self.bind(pos=self.update_canvas, size=self.update_canvas)

        # Text Container (Vertical: Name + Desc)
        text_content = BoxLayout(orientation='vertical', spacing=dp(2))

        # Name
        text_content.add_widget(Label(
            text=name,
            font_size=dp(18),
            bold=True,
            color=THEME["text_primary"],
            halign='left',
            valign='bottom',  # Align to bottom of its space
            size_hint_y=0.6,
            text_size=(self.width, None)  # Placeholder, updated in canvas
        ))

        # Description
        desc_text = desc if desc else "No description provided"
        text_content.add_widget(Label(
            text=desc_text,
            font_size=dp(14),
            color=THEME["text_secondary"],
            halign='left',
            valign='top',  # Align to top of its space
            size_hint_y=0.4,
            max_lines=1,
            text_size=(self.width, None)  # Placeholder
        ))

        self.add_widget(text_content)

        # Edit Button (Right aligned)
        # We use a smaller version of ProButton
        edit_btn = ProButton(
            text="Edit",
            bg_color=THEME["surface_active"],
            font_size=dp(13),
            radius=dp(6)
        )
        edit_btn.size_hint = (None, None)
        edit_btn.size = (dp(60), dp(34))
        edit_btn.pos_hint = {'center_y': 0.5}
        edit_btn.bind(on_release=self.on_edit)
        self.add_widget(edit_btn)

    def update_canvas(self, *args):
        # Update text alignment for labels inside the text box
        # Children are in reverse order of addition? No, [1] is likely edit_btn or text_content depending on internals.
        text_box = self.children[1]
        # Actually children list order varies by widget type sometimes, but usually index 0 is last added.
        # Safer to iterate.

        # Layout width calculation
        # Width - padding - spacing - button width
        text_area_width = self.width - dp(32) - dp(15) - dp(60)

        for child in self.children:
            if isinstance(child, BoxLayout):  # The text container
                for lbl in child.children:
                    lbl.text_size = (text_area_width, None)

        self.canvas.before.clear()
        with self.canvas.before:
            # Card Background
            Color(*THEME["surface"])
            RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(12)])

            # Subtle Border
            Color(*THEME["border_color"])
            Line(rounded_rectangle=(self.x, self.y,
                 self.width, self.height, dp(12)), width=1)

    def on_edit(self, instance):
        # Find the main screen and trigger edit
        app = App.get_running_app()
        if app and app.root:
            main_screen = app.root.get_screen('main')
            main_screen.open_edit_screen(self.index)


# --- Screens ---

class LoginScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.db = database.DB()
        self.mode = 'login'  # 'login' or 'signup'

        # Login card layout
        card = BoxLayout(orientation='vertical',
                         padding=dp(40), spacing=dp(24))
        card.size_hint = (None, None)
        card.size = (dp(360), dp(520))  # Increased height for feedback/toggle
        card.pos_hint = {'center_x': 0.5, 'center_y': 0.5}

        # Title
        title_box = BoxLayout(orientation='vertical',
                              size_hint_y=None, height=dp(80), spacing=dp(5))
        self.title_lbl = Label(
            text="Everyday Carry",
            font_size=dp(36),
            bold=True,
            color=THEME["text_primary"],
            halign='center'
        )
        self.subtitle_lbl = Label(
            text="Your digital loadout manager.",
            font_size=dp(16),
            color=THEME["text_secondary"],
            halign='center'
        )
        title_box.add_widget(self.title_lbl)
        title_box.add_widget(self.subtitle_lbl)
        card.add_widget(title_box)

        # Inputs
        input_container = BoxLayout(orientation='vertical', spacing=dp(
            15), size_hint_y=None, height=dp(130))
        self.username = ProInput(hint_text="Username")
        self.password = ProInput(hint_text="Password", password=True)
        input_container.add_widget(self.username)
        input_container.add_widget(self.password)
        card.add_widget(input_container)

        # Feedback Label
        self.feedback_lbl = Label(
            text="",
            font_size=dp(14),
            color=THEME["danger"],
            size_hint_y=None,
            height=dp(20),
            halign='center'
        )
        card.add_widget(self.feedback_lbl)

        # Main Action Button (Login/Signup)
        self.action_btn = ProButton(
            text="Sign In", height=dp(54), size_hint_y=None)
        self.action_btn.bind(on_release=self.perform_action)
        card.add_widget(self.action_btn)

        # Toggle Mode Button
        self.toggle_btn = Button(
            text="New here? Create an account",
            font_size=dp(14),
            color=THEME["primary"],
            background_normal="",
            background_down="",
            background_color=(0, 0, 0, 0),
            size_hint_y=None,
            height=dp(30)
        )
        self.toggle_btn.bind(on_release=self.toggle_mode)
        card.add_widget(self.toggle_btn)

        self.add_widget(card)

    def toggle_mode(self, instance):
        if self.mode == 'login':
            self.mode = 'signup'
            self.title_lbl.text = "Create Account"
            self.subtitle_lbl.text = "Join Everyday Carry today."
            self.action_btn.text = "Sign Up"
            self.toggle_btn.text = "Already have an account? Sign In"
            self.feedback_lbl.text = ""
        else:
            self.mode = 'login'
            self.title_lbl.text = "Everyday Carry"
            self.subtitle_lbl.text = "Your digital loadout manager."
            self.action_btn.text = "Sign In"
            self.toggle_btn.text = "New here? Create an account"
            self.feedback_lbl.text = ""

    def perform_action(self, instance):
        user = self.username.text.strip()
        pwd = self.password.text.strip()

        if not user or not pwd:
            self.feedback_lbl.text = "Please enter both username and password."
            self.feedback_lbl.color = THEME["danger"]
            return

        if self.mode == 'login':
            if self.db.verify_user(user, pwd):
                self.feedback_lbl.text = ""
                self.manager.current = 'main'
                self.username.text = ""
                self.password.text = ""
            else:
                self.feedback_lbl.text = "Invalid username or password."
                self.feedback_lbl.color = THEME["danger"]
        else:  # signup
            if self.db.create_user(user, pwd):
                self.feedback_lbl.text = "Account created! Please sign in."
                self.feedback_lbl.color = THEME["accent"]
                # Switch back to login mode
                self.toggle_mode(None)
                self.username.text = user  # Keep username filled
                self.password.text = ""
            else:
                self.feedback_lbl.text = "Username already exists."
                self.feedback_lbl.color = THEME["danger"]


class AddItemScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # Layout with padding
        root = BoxLayout(orientation='vertical', padding=[
                         dp(30), dp(50), dp(30), dp(30)], spacing=dp(20))

        # Header
        root.add_widget(Label(
            text="Add New Item",
            font_size=dp(28),
            bold=True,
            color=THEME["text_primary"],
            size_hint_y=None,
            height=dp(60),
            halign='center'
        ))

        # Form Container
        form = BoxLayout(orientation='vertical', spacing=dp(
            20), size_hint_y=None, height=dp(200))
        self.item_name = ProInput(hint_text="Item Name (e.g. Wallet)")
        self.item_desc = ProInput(
            hint_text="Description (e.g. Leather, brown)")
        form.add_widget(self.item_name)
        form.add_widget(self.item_desc)
        root.add_widget(form)

        # Spacer
        root.add_widget(Label())

        # Actions
        actions = BoxLayout(orientation='horizontal', spacing=dp(
            15), size_hint_y=None, height=dp(60))

        cancel_btn = ProButton(
            text="Cancel",
            bg_color=THEME["surface"],  # Grey implementation for cancel
            font_size=dp(16)
        )
        cancel_btn.color = THEME["text_secondary"]
        cancel_btn.bind(on_release=self.cancel)

        save_btn = ProButton(text="Save Item")
        save_btn.bind(on_release=self.save_item)

        actions.add_widget(cancel_btn)
        actions.add_widget(save_btn)
        root.add_widget(actions)

        self.add_widget(root)

    def cancel(self, instance):
        self.manager.current = 'main'
        self.clear_inputs()

    def save_item(self, instance):
        name = self.item_name.text.strip()
        desc = self.item_desc.text.strip()
        if name:
            items_list.append({
                "name": name,
                "desc": desc
            })
            self.manager.get_screen('main').update_items_list()
            self.cancel(instance)

    def clear_inputs(self):
        self.item_name.text = ""
        self.item_desc.text = ""


class EditItemScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.edit_index = None

        # Consistent Padding
        root = BoxLayout(orientation='vertical', padding=[
                         dp(30), dp(50), dp(30), dp(30)], spacing=dp(20))

        # Header
        root.add_widget(Label(
            text="Edit Item",
            font_size=dp(28),
            bold=True,
            color=THEME["text_primary"],
            size_hint_y=None,
            height=dp(60),
            halign='center'
        ))

        # Form Container
        form = BoxLayout(orientation='vertical', spacing=dp(
            20), size_hint_y=None, height=dp(200))
        self.item_name = ProInput(hint_text="Item Name")
        self.item_desc = ProInput(hint_text="Description")
        form.add_widget(self.item_name)
        form.add_widget(self.item_desc)
        root.add_widget(form)

        # Actions
        actions = BoxLayout(orientation='horizontal', spacing=dp(
            15), size_hint_y=None, height=dp(60))

        # Delete Button (Left side)
        delete_btn = ProButton(
            text="Delete",
            bg_color=THEME["danger"],
            font_size=dp(16)
        )
        delete_btn.bind(on_release=self.delete_item)

        # Cancel Button
        cancel_btn = ProButton(
            text="Cancel",
            bg_color=THEME["surface"],
            font_size=dp(16)
        )
        cancel_btn.color = THEME["text_secondary"]
        cancel_btn.bind(on_release=self.cancel)

        # Save Button
        save_btn = ProButton(text="Save Changes")
        save_btn.bind(on_release=self.save_item)

        actions.add_widget(delete_btn)
        actions.add_widget(cancel_btn)
        actions.add_widget(save_btn)
        root.add_widget(actions)

        # Spacer
        root.add_widget(Label())

        self.add_widget(root)

    def load_item(self, index, item_data):
        self.edit_index = index
        self.item_name.text = item_data['name']
        self.item_desc.text = item_data.get('desc', '')

    def cancel(self, instance):
        self.manager.current = 'main'
        self.edit_index = None

    def save_item(self, instance):
        name = self.item_name.text.strip()
        desc = self.item_desc.text.strip()
        if self.edit_index is not None and name:
            items_list[self.edit_index] = {
                "name": name,
                "desc": desc
            }
            self.manager.get_screen('main').update_items_list()
            self.cancel(instance)

    def delete_item(self, instance):
        if self.edit_index is not None:
            items_list.pop(self.edit_index)
            self.manager.get_screen('main').update_items_list()
            self.cancel(instance)


class LogbookScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        root = BoxLayout(orientation='vertical',
                         padding=dp(30), spacing=dp(20))
        IncludeKeywords: list[str] = []          # e.g., ["bedroom"]
        ExcludeKeywords: list[str] = []  # example of hiding a term
        self.IncludeKeywords = IncludeKeywords
        self.ExcludeKeywords = [k.lower() for k in ExcludeKeywords]

        # Logger
        self.logger = logging.getLogger("home-monitor")
        self.logger.setLevel(logging.INFO)

        # Ensure logs/ directory exists
        self.LogDir = Path(__file__).resolve().parent / "logs"
        self.LogDir.mkdir(parents=True, exist_ok=True)

        # Log Display
        label = Label(text="There is no log data to display.",
                      font_size=dp(24),
                      color=THEME["text_secondary"],
                      size_hint_y=None,
                      halign='left',
                      valign='top')
        label.bind(texture_size=self.update_height)
        label.bind(width=self.update_width)

        # Scroll View for log display
        scroll = ScrollView(size_hint=(1, 1))
        scroll.add_widget(label)

        root.add_widget(scroll)

        DB = database.DB()

        # UI handler: friendly text
        if len(DB.GetEvents()) == 0:
            label.text = "No log events found."
        else:
            label.text = ""

        scroll = ScrollView(size_hint=(1, 1))
        UIHandler = log.KivyLogHandler(
            widget=label,
            formatter=log.UserFormatter(),
            IncludeKeywords=self.IncludeKeywords,
            ExcludeKeywords=self.ExcludeKeywords,
            MaxLines=2000,
        )

        # DB handler: logs to database
        DB = database.DB()

        # Avoid duplicate handlers on reload
        self.logger.handlers.clear()
        self.logger.addHandler(UIHandler)
        self.logger.addHandler(log.DBHandler(DB))

        # pull everything from db
        events = DB.GetEvents()
        lenEvents = len(events)
        for index, row in enumerate(events):
            level, event, timestamp = row
            message = f"{timestamp} : {level} : {event}"
            if log.keyword_match(message, self.IncludeKeywords, self.ExcludeKeywords):
                label.text += message
                if index <= lenEvents - 2:
                    label.text += "\n"

        # Example logs (you can remove these in production)
        self.logger.info("Bedroom: motion detected")
        self.logger.info("Kitchen: temperature normal")
        self.logger.warning("Garage: Phone is leaving house")

        # Header
        root.add_widget(Label(
            text="Logbook",
            font_size=dp(28),
            bold=True,
            color=THEME["text_primary"],
            size_hint_y=None,
            height=dp(60)
        ))

        # Back Button
        back_btn = ProButton(
            text="Back", bg_color=THEME["surface"], size_hint_y=None, height=dp(50))
        back_btn.color = THEME["text_primary"]
        back_btn.bind(on_release=self.go_back)
        root.add_widget(back_btn)

        self.add_widget(root)

    def update_height(self, instance, value):
        instance.height = value[1]

    def update_width(self, instance, width):
        instance.text_size = (width, None)

    def go_back(self, instance):
        self.manager.current = 'main'


class SettingsScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        root = BoxLayout(orientation='vertical',
                         padding=dp(30), spacing=dp(20))

        # Header
        root.add_widget(Label(
            text="Settings",
            font_size=dp(28),
            bold=True,
            color=THEME["text_primary"],
            size_hint_y=None,
            height=dp(60)
        ))

        # Pseudo Settings
        settings = ["Dark Mode", "Notifications"]
        for s in settings:
            row = BoxLayout(orientation='horizontal',
                            size_hint_y=None, height=dp(50))
            row.add_widget(Label(
                text=s, color=THEME["text_primary"], halign='left', text_size=(dp(200), None)))
            # Fake toggle
            row.add_widget(Label(text="ON", color=THEME["primary"], bold=True))
            root.add_widget(row)

        root.add_widget(Label())  # Spacer

        # Back Button
        back_btn = ProButton(
            text="Back", bg_color=THEME["surface"], size_hint_y=None, height=dp(50))
        back_btn.color = THEME["text_primary"]
        back_btn.bind(on_release=self.go_back)
        root.add_widget(back_btn)

        self.add_widget(root)

    def go_back(self, instance):
        self.manager.current = 'main'


class MainScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        root = BoxLayout(orientation="vertical")

        # 1. Header (Clean, minimal)
        header = BoxLayout(
            orientation="horizontal",
            padding=[dp(25), dp(15)],
            size_hint_y=None,
            height=dp(70)
        )

        title = Label(
            text="Dashboard",
            font_size=dp(24),
            bold=True,
            color=THEME["text_primary"],
            halign='left',
            valign='middle'
        )
        title.bind(size=title.setter('text_size'))
        header.add_widget(title)

        # User Name / Status (Right aligned)
        user_lbl = Label(
            text="Admin User",
            font_size=dp(14),
            color=THEME["primary"],
            halign='right',
            valign='middle'
        )
        user_lbl.bind(size=user_lbl.setter('text_size'))
        header.add_widget(user_lbl)

        root.add_widget(header)

        # 2. List of Items
        self.scroll = ScrollView(size_hint=(1, 1), do_scroll_x=False)
        self.items_grid = GridLayout(cols=1, spacing=dp(
            15), size_hint_y=None, padding=[dp(20), dp(10)])
        self.items_grid.bind(minimum_height=self.items_grid.setter('height'))

        self.scroll.add_widget(self.items_grid)
        root.add_widget(self.scroll)

        self.update_items_list()  # Init empty state

        # 3. Bottom Menu
        # We put the buttons inside a container that has padding to simulate "floating"
        dock_container = BoxLayout(
            padding=[dp(20), dp(20), dp(20), dp(30)],
            size_hint_y=None,
            height=dp(100)
        )

        # The visual pill/bar
        dock = BoxLayout(
            orientation="horizontal",
            spacing=dp(15),
            padding=[dp(20), dp(10)]
        )

        # Dock Background
        with dock.canvas.before:
            Color(*THEME["surface"])
            RoundedRectangle(pos=dock.pos, size=dock.size, radius=[dp(20)])
        dock.bind(pos=lambda inst, v: self.update_dock_display(dock),
                  size=lambda inst, v: self.update_dock_display(dock))

        # Actions
        actions = [
            ("Add", self.go_add),
            ("Logbook", self.go_logbook),
            ("Settings", self.go_settings)
        ]

        for text, callback in actions:
            btn = ProButton(text=text, bg_color=(0, 0, 0, 0), font_size=dp(14))
            btn.color = THEME["primary"]
            btn.bind(on_release=callback)
            dock.add_widget(btn)

        # Exit Button (Red accent)
        exit_btn = ProButton(
            text="Exit", bg_color=THEME["danger"], font_size=dp(14), radius=dp(15))
        exit_btn.size_hint_x = None
        exit_btn.width = dp(80)
        exit_btn.bind(on_release=self.logout)
        dock.add_widget(exit_btn)

        dock_container.add_widget(dock)
        root.add_widget(dock_container)

        self.add_widget(root)

    def update_dock_display(self, instance):
        instance.canvas.before.clear()
        with instance.canvas.before:
            Color(*THEME["surface"])
            RoundedRectangle(pos=instance.pos,
                             size=instance.size, radius=[dp(20)])
            # Optional Border
            Color(*THEME["border_color"])
            Line(rounded_rectangle=(instance.x, instance.y,
                 instance.width, instance.height, dp(20)), width=1)

    def update_items_list(self):
        self.items_grid.clear_widgets()
        if not items_list:
            empty_box = BoxLayout(orientation='vertical',
                                  size_hint_y=None, height=dp(200))
            empty_box.add_widget(Label(
                text="No Items Found",
                font_size=dp(20),
                bold=True,
                color=THEME["text_secondary"]
            ))
            empty_box.add_widget(Label(
                text="Tap 'Add' to start your collection",
                font_size=dp(14),
                color=THEME["text_secondary"]
            ))
            self.items_grid.add_widget(empty_box)
            return

        for index, item in enumerate(items_list):
            card = ItemCard(item['name'], item.get('desc', ''), index)
            self.items_grid.add_widget(card)

    def open_edit_screen(self, index):
        self.manager.transition.direction = 'left'
        edit_screen = self.manager.get_screen('edit_item')
        edit_screen.load_item(index, items_list[index])
        self.manager.current = 'edit_item'

    def go_add(self, instance):
        self.manager.transition.direction = 'left'
        self.manager.current = 'add_item'

    def go_logbook(self, instance):
        self.manager.transition.direction = 'left'
        self.manager.current = 'logbook'

    def go_settings(self, instance):
        self.manager.transition.direction = 'left'
        self.manager.current = 'settings'

    def logout(self, instance):
        self.manager.transition.direction = 'right'
        self.manager.current = 'login'


class EverydayCarryApp(App):
    def build(self):
        sm = ScreenManager(transition=FadeTransition(
            duration=0.2))  # Smoother transition
        sm.add_widget(LoginScreen(name='login'))
        sm.add_widget(MainScreen(name='main'))
        sm.add_widget(AddItemScreen(name='add_item'))
        sm.add_widget(EditItemScreen(name='edit_item'))
        sm.add_widget(LogbookScreen(name='logbook'))
        sm.add_widget(SettingsScreen(name='settings'))
        return sm


if __name__ == "__main__":
    EverydayCarryApp().run()
