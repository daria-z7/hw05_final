import datetime


def year(request):
    """Добавляет в контекст переменную year с текущим годом."""
    now = datetime.datetime.now()
    return {'year': now.year, }
