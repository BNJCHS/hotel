from django import template, forms as djforms

register = template.Library()


@register.filter
def is_wide_field(bound_field):
    """
    Devuelve True si el campo debería ocupar el ancho completo.
    Actualmente considera Textarea y conjuntos de checkboxes múltiples.
    """
    try:
        widget = getattr(bound_field.field, 'widget', None)
        return isinstance(widget, (djforms.Textarea, djforms.CheckboxSelectMultiple))
    except Exception:
        return False


@register.filter
def dict_get(d, key):
    """Obtiene una clave de un diccionario en templates."""
    try:
        return d.get(key)
    except Exception:
        return None


@register.filter
def list_contains(lst, item):
    """Verifica si una lista contiene un elemento en templates."""
    try:
        return item in lst if lst is not None else False
    except Exception:
        return False
