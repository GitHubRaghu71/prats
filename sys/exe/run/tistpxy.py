from datetime import datetime, timezone, timedelta
from nftpxy import Day_Change
from clorpxy import BRIGHT_YELLOW, BRIGHT_RED, BRIGHT_GREEN, RESET
# import pytz

def print_current_datetime_in_ist():
    # utc_now = datetime.utcnow()
    # utc_timezone = pytz.timezone('UTC')
    # utc_now = utc_timezone.localize(utc_now)
    #ist_timezone = pytz.timezone('Asia/Kolkata')
    
    # Get the current time in UTC (timezone-aware)
    utc_now = datetime.now(timezone.utc)

    # Define the IST timezone (UTC+5:30)
    ist_timezone = timezone(timedelta(hours=5, minutes=30))

    # Convert UTC time to IST
    ist_now = utc_now.astimezone(ist_timezone)

    # Format the IST datetime for display
    formatted_datetime = (
        f"|🌏{ist_now.strftime('%d')} "  # Bright yellow color and underline
        f"{ist_now.strftime('%B'):9} {ist_now.strftime('%Y')}|"  # Month, year
        f"🕛{ist_now.strftime('%A'):9}|"  # Day
        f"⏰{ist_now.strftime('%I:%M%p')}"  # Time (reset color)
    )

    # Display the formatted datetime with color based on Day_Change
    if Day_Change > 0:
        print(f"{BRIGHT_GREEN}{formatted_datetime}{RESET}")
    elif Day_Change < 0:
        print(f"{BRIGHT_RED}{formatted_datetime}{RESET}")
    else:
        print(f"{BRIGHT_YELLOW}{formatted_datetime}{RESET}")

# Call the function to print current datetime in IST
print_current_datetime_in_ist()
