from django import template

register = template.Library()

@register.filter(name='add_class')
def add_class(field, css_class):
    """
    Ajoute dynamiquement une ou plusieurs classes CSS à un champ de formulaire
    sans supprimer ses attributs existants.
    """
    attrs = field.field.widget.attrs.copy()  # Garde les attributs existants
    existing_class = attrs.get("class", "")
    combined_class = (existing_class + " " + css_class).strip()
    attrs["class"] = combined_class
    return field.as_widget(attrs=attrs)
