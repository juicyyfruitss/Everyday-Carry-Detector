import logging 
import json
from pathlib import Path
from datetime import datetime
from typing import Optional, Sequence
from kivy.app import App 
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.textinput import TextInput
from kivy.clock import Clock
import database
from kivy.uix.scrollview import ScrollView

LevelLabels = {
        "DEBUG": "Info",
        "INFO": "Info",
        "WARNING": "Warning",
        "ERROR": "Error",
        "CRITICAL": "Critical",
    }

# class KivyLogHandler(logging.Handler):
#      def __init__(self, widget, FilterKeyword =None):
#           super().__init__()
#           self.widget = widget
#           self.FilterKeyword = FilterKeyword

#      def emit(self, record):
#       message = self.format(record)
#       # Filters by KeyWords. That way we can still get the reading that its leaving the house but won't print that in the users log screen
#       if self.FilterKeyword and self.FilterKeyword.lower() not in message.lower():
#           return
#       self.widget.text += message + '\n'
        
class DBHandler(logging.Handler):
    def __init__(self, db):
        super().__init__()
        self.db = db


    def emit(self, record):
        when = datetime.fromtimestamp(record.created).strftime("%Y-%m-%d %H:%M:%S")
        label = LevelLabels.get(record.levelname, record.levelname.title())
        message = record.getMessage()
        self.db.LogEvent(label, message, when)

# class JsonFormatter(logging.Formatter):
#     def format(self, record: logging.LogRecord) -> str:
#         data = {
#             "ts": record.created,
#             "time": datetime.fromtimestamp(record.created).isoformat(timespec="seconds"),
#             "name": record.name,
#             "level": record.levelname,
#             "message": record.getMessage(),
#         }
#         return json.dump(data, ensure_ascii=False)
    
class UserFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        # Example: 2026-02-03 22:45:03 : Warning : Bedroom window was left open
        when = datetime.fromtimestamp(record.created).strftime("%Y-%m-%d %H:%M:%S")
        label = LevelLabels.get(record.levelname, record.levelname.title())
        message = record.getMessage()
        return f"{when} : {label} : {message}"

class KivyLogHandler(logging.Handler):

    def __init__(
        self,
        widget: TextInput,
        formatter: Optional[logging.Formatter] = None,
        IncludeKeywords: Optional[Sequence[str]] = None,
        ExcludeKeywords: Optional[Sequence[str]] = None,
        MaxLines: int = 2000,
    ):
        super().__init__()
        self.widget = widget
        if formatter:
            self.setFormatter(formatter)
        self.IncludeKeywords = [k.lower() for k in IncludeKeywords or []]
        self.ExcludeKeywords = [k.lower() for k in ExcludeKeywords or []]
        self.MaxLines = MaxLines

    def FilterChecker(self, MessageLower: str) -> bool:
        if self.IncludeKeywords:
            if not any(k in MessageLower for k in self.IncludeKeywords):
                return False
        if self.ExcludeKeywords:
            if any(k in MessageLower for k in self.ExcludeKeywords):
                return False
        return True

    def emit(self, record: logging.LogRecord):
        try:
            rendered = self.format(record)
            RawMessage = record.getMessage().lower()

            if not self.FilterChecker(RawMessage):
                return

            def AddsText(_dt):
                # Append and cap to last N lines to avoid unbounded growth
                current = self.widget.text
                if current:
                    Text = current + "\n" + rendered
                else:
                    Text = rendered
                # Cap lines
                lines = Text.splitlines()
                if len(lines) > self.MaxLines:
                    lines = lines[-self.MaxLines :]
                self.widget.text = "\n".join(lines)
                # Ensure cursor goes to bottom
                self.widget.cursor = (0, len(self.widget.text))
            # Schedule on main thread
            Clock.schedule_once(AddsText, 0)
    

        except Exception:
            self.handleError(record)

    
# ---------- Utilities for loading & filtering saved logs ----------

def LogFiles(LogDir: Path, base: str = "app.log") -> list[Path]:
    """
    Return current + rotated logs, sorted newest-last.
    Files look like:
      logs/app.log
      logs/app.log.2026-02-01
      logs/app.log.2026-02-02
      ...
    """
    files = []
    current = LogDir / base
    if current.exists():
        files.append(current)
    # Rotated: app.log.YYYY-MM-DD
    for p in sorted(LogDir.glob(f"{base}.*")):
        files.append(p)
    return files


def JsonDictConverter(line: str) -> Optional[dict]:
    try:
        return json.loads(line)
    except Exception:
        return None


def Userline(item: dict) -> str:
    """
    Convert a saved JSON log dict to the same friendly UI format.
    """
    level = item.get("level", "INFO")
    message = item.get("message", "")
    ts = item.get("ts", datetime.now().timestamp())
    when = datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S")


    LabelMap = {
        "DEBUG": "Info",
        "INFO": "Info",
        "WARNING": "Warning",
        "ERROR": "Error",
        "CRITICAL": "Critical",
    }
    label = LabelMap.get(level, level.title())

    return f"{when} : {label} : {message}"


def keyword_match(message: str, include: Sequence[str], exclude: Sequence[str]) -> bool:
    m = message.lower()
    if include:
        if not any(k in m for k in include):
            return False
    if exclude:
        if any(k in m for k in exclude):
            return False
    return True


# ---------- The Kivy Screen ----------

# class LogScreen(BoxLayout):
#     def __init__(self, **kwargs):
#         super().__init__(**kwargs)
#         self.orientation = "vertical"

#         self.LogDisplay = TextInput(readonly=True, size_hint=(1, 1))
#         self.add_widget(self.LogDisplay)

#         # Logger
#         self.logger = logging.getLogger("home-monitor")
#         self.logger.setLevel(logging.INFO)

#         # Ensure logs/ directory exists
#         self.LogDir = Path(__file__).resolve().parent / "logs"
#         self.LogDir.mkdir(parents=True, exist_ok=True)

#         # UI handler: friendly text
#         UIHandler = KivyLogHandler(
#             widget = self.LogDisplay,
#             formatter = UserFormatter(),
#             IncludeKeywords = self.IncludeKeywords,
#             ExcludeKeywords = self.ExcludeKeywords,
#             MaxLines = 2000,
#         )

#         # DB handler: logs to database
#         DB = database.DB()

#         # Avoid duplicate handlers on reload
#         self.logger.handlers.clear()
#         self.logger.addHandler(UIHandler)
#         self.logger.addHandler(DBHandler(DB))

#         # pull everything from db
#         events = DB.GetEvents()
#         lenEvents = len(events)
#         for index, row in enumerate(events):
#             level, event, timestamp = row
#             message = f"{timestamp} : {level} : {event}"
#             if keyword_match(message, self.IncludeKeywords, self.ExcludeKeywords):
#                 self.LogDisplay.text += message
#                 if index <= lenEvents - 2:
#                     self.LogDisplay.text += "\n"
            

#         # Example logs (you can remove these in production)
#         self.logger.info("Bedroom: motion detected")
#         self.logger.info("Kitchen: temperature normal")
#         self.logger.warning("Garage: Phone is leaving house")

# ---------- App ----------

# class LogApp(App):
#     def build(self):
#         self.title = "Home Logs"
#         return LogScreen()


# if __name__ == "__main__":
#     LogApp().run()

# worrk on making it stay for 14 days rather than  on launch 
#remember to commit everything to github

# | level | room   | event    | timestamp |
# | Info  | Bedroom| movement | asdfasdf  |