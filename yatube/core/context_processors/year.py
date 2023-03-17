from datetime import datetime


def year(request):
    """Добавляет переменную с текущим годом."""
    this_year = datetime.now()
    return {
        'year': this_year.year,
    }
