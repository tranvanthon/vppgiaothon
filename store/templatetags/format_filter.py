from django import template
register = template.Library()

@register.filter
def dot_thousands(value):
    try:
        value = float(value)
        return f"{value:,.0f}".replace(',', '.')
    except (TypeError, ValueError):
        return value
    