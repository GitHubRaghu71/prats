import time
from rich.console import Console

console = Console()

def progress_bar(duration, mktpxy):
    for i in range(int(duration)):
        time.sleep(1)
        if mktpxy == 'Buy':
            console.print('[green]..PRATS®[/]👆', end='')  # Up arrow + handshake
        elif mktpxy == 'Sell':
            console.print('[red]..PRATS®[/]👇', end='')  # Down arrow + handshake
        elif mktpxy == 'Bull':
            console.print('[green]..PRATS®[/]🟢', end='')  # Right arrow + handshake
        elif mktpxy == 'Bear':
            console.print('[red]..PRATS®[/]🔴', end='')  # Left arrow + handshake
        else:
            console.print('[yellow]..PRATS®[/]🤝', end='')  # Neutral with handshake
        
        if (i + 1) % 5 == 0:
            console.print()  # Move to the next line after every 5 cycles

    console.print()  # Ensure final newline after the loop ends
