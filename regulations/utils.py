from .models import Regulation

def get_regulation_value(name):
    try:
        regulation = Regulation.objects.get(name=name)
        return regulation.value
    except Regulation.DoesNotExist:
        return None
