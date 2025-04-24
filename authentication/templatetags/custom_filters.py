from django import template

register = template.Library()

@register.filter(name='get_item')
def get_item(dictionary, key):
    """
    Gets an item from a dictionary using a variable key.
    Usage: {{ dictionary|get_item:key }}
    """
    return dictionary.get(key, None)

@register.filter(name='get_color')
def get_color(counter, index=0):
    """
    Returns a color from a predefined list based on the counter value.
    Usage: {{ forloop.counter|get_color }} or {{ forloop.counter|get_color:1 }}
    """
    colors = ["#4361ee", "#4cc9f0", "#f72585", "#3f37c9", "#e63946"]
    return colors[(counter - 1 + index) % len(colors)]

@register.filter(name='get_rgba')
def get_rgba(counter, index=0):
    """
    Returns an RGBA color string based on the counter value.
    Usage: {{ forloop.counter|get_rgba }} or {{ forloop.counter|get_rgba:1 }}
    """
    rgba_colors = [
        "rgba(67, 97, 238, 0.1)",  # #4361ee
        "rgba(76, 201, 240, 0.1)",  # #4cc9f0
        "rgba(247, 37, 133, 0.1)",  # #f72585
        "rgba(63, 55, 201, 0.1)",   # #3f37c9
        "rgba(230, 57, 70, 0.1)"    # #e63946
    ]
    return rgba_colors[(counter - 1 + index) % len(rgba_colors)]