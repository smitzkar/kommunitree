"""
https://gpiozero.readthedocs.io/en/stable/recipes.html#button


mock pins -> deve laptop
https://gpiozero.readthedocs.io/en/stable/api_pins.html#mock-pins

"""

# #MARK: mock
# from gpiozero import Device, LED
# from gpiozero.pins.mock import MockFactory

# Device.pin_factory = MockFactory() # sets pins to fake

# led = LED(3)


# # will run say_hello whenever the button is pressed  -> callback
# from gpiozero import Button
# from signal import pause

# def say_hello():
#     print("Hello!")

# button = Button(2)

# button.when_pressed = say_hello

# pause() # keeps the script running indefinitely (until user stops it with keyboard interrupt or such)


import os
from gpiozero import Device, LED
from gpiozero.pins.mock import MockFactory
from rich.console import Console
from rich.table import Table
from rich.columns import Columns
from rich.panel import Panel
from rich.layout import Layout

Device.pin_factory = MockFactory()

leds = [LED(i) for i in range(4)]
led_names = ['A', 'S', 'D', 'F']
key_map = {'a': 0, 's': 1, 'd': 2, 'f': 3}
# Console output buffer - store messages here
console_output = []
console = Console()

def add_console_message(message):
    """Add a message to the console output (left panel)"""
    console_output.append(message)
    # Keep only last 20 messages to prevent overflow
    if len(console_output) > 20:
        console_output.pop(0)

def render_controls():
    """Render the controls panel (right side)"""
    table = Table(title="Controls", show_header=True, width=30)
    
    # Add button headers
    table.add_column("Key", justify="center", width=6)
    table.add_column("LED", justify="center", width=6)
    
    # Add LED status rows
    for i, name in enumerate(led_names):
        status = "[green]●[/green]" if leds[i].is_lit else "[red]●[/red]"
        table.add_row(f"[cyan]{name}[/cyan]", status)
    
    # Add instructions
    table.add_row("", "")
    table.add_row("[dim]Q[/dim]", "[dim]Quit[/dim]")
    
    return table

def render_console():
    """Render the console output panel (left side)"""
    if not console_output:
        return "[dim]Console output will appear here...[/dim]"
    
    return "\n".join(console_output[-15:])  # Show last 15 messages

def render_layout():
    """Create the main layout with console (left) and controls (right)"""
    layout = Layout()
    layout.split_row(
        Layout(Panel(render_console(), title="Console Output", border_style="green"), name="console", ratio=7),
        Layout(Panel(render_controls(), title="Controls", border_style="blue"), name="controls", ratio=3)
    )
    return layout

# Add some initial messages
add_console_message("System initialized")
add_console_message("GPIO mock pins active")
add_console_message("Ready for input...")

while True:
    os.system("clear")
    console.print(render_layout())
    
    key = input("Press a key (a/s/d/f to toggle LEDs, q to quit): ").lower()
    
    if key == 'q':
        add_console_message("Shutting down...")
        break
    elif key in key_map:
        led_index = key_map[key]
        leds[led_index].toggle()
        state = "ON" if leds[led_index].is_lit else "OFF"
        add_console_message(f"LED {led_names[led_index]} toggled {state}")
    else:
        add_console_message(f"Unknown key: {key}")

print("Goodbye!")


# import os
# from gpiozero import Device, LED
# from gpiozero.pins.mock import MockFactory
# from rich.console import Console
# from rich.table import Table
# from rich.columns import Columns
# from rich.panel import Panel
# from rich.layout import Layout

# Device.pin_factory = MockFactory()

# leds = [LED(i) for i in range(4)]
# led_names = ['A', 'S', 'D', 'F']
# key_map = {'a': 0, 's': 1, 'd': 2, 'f': 3}
# key_history = []

# console = Console()

# def render_led_table():
#     table = Table(title="LED Status", show_header=True)
    
#     # Add button row
#     table.add_column("", justify="center", width=8)
#     for name in led_names:
#         table.add_column(name, justify="center", width=8)
    
#     # Add LED status row
#     led_row = ["LEDs"]
#     for i in range(len(leds)):
#         status = "[green]●[/green]" if leds[i].is_lit else "[red]●[/red]"
#         led_row.append(status)
    
#     table.add_row(*led_row)
#     return table

# def render_history():
#     # Show last 20 key presses as a comma-separated string
#     recent_keys = key_history[-20:] if len(key_history) > 20 else key_history
#     if not recent_keys:
#         history_text = "[dim]No keys pressed yet[/dim]"
#     else:
#         history_text = f"[cyan]{','.join(recent_keys)}[/cyan]"
    
#     return f"Key History: {history_text}"

# while True:
#     os.system("clear")  # Clears the terminal
    
#     # Get actual terminal dimensions and reserve space for input
#     terminal_height = os.get_terminal_size().lines
#     available_height = terminal_height - 3  # Reserve 3 lines for input prompt
    
#     # Create layout with constrained height
#     layout = Layout()
#     layout.split_row(
#         Layout(Panel(render_led_table(), title="Controls", border_style="blue"), name="controls", ratio=3),
#         Layout(Panel(render_history(), title="History", border_style="green"), name="info", ratio=7)
#     )
    
#     # Print with height constraint
#     with console.capture() as capture:
#         console.print(layout)
    
#     output = capture.get()
#     lines = output.split('\n')
    
#     # Only print the lines that fit in available space
#     for line in lines[:available_height]:
#         print(line)
    
#     key = input("Type a, s, d, or f to toggle LEDs, q to exit; execute with enter: ").lower()
#     if key == 'q':
#         break
#     if key in key_map:
#         key_history.append(key)
#         leds[key_map[key]].toggle()
