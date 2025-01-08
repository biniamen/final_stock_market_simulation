# utils.py
from django.utils.timezone import localtime
from regulations.models import WorkingHours  # Import from the regulations app

def is_within_working_hours(current_time):
    """
    Checks if the current time is within the platform's working hours.
    """
    current_day = current_time.strftime('%A')  # e.g., 'Monday'
    current_hour = current_time.time()

    try:
        working_hours = WorkingHours.objects.get(day_of_week=current_day)
        return working_hours.start_time <= current_hour <= working_hours.end_time
    except WorkingHours.DoesNotExist:
        return False  # If working hours are not defined for the day, consider it as outside working hours
