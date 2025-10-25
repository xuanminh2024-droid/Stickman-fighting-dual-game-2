def load_image(file_path):
    """Load an image from the specified file path."""
    try:
        image = pygame.image.load(file_path)
        return image.convert_alpha()  # Use convert_alpha for transparency
    except pygame.error as e:
        print(f"Unable to load image at {file_path}: {e}")
        return None

def clamp(value, min_value, max_value):
    """Clamp a value between a minimum and maximum value."""
    return max(min(value, max_value), min_value)

def distance(point1, point2):
    """Calculate the distance between two points."""
    return ((point1[0] - point2[0]) ** 2 + (point1[1] - point2[1]) ** 2) ** 0.5

def draw_text(surface, text, position, font, color):
    """Draw text on the given surface at the specified position."""
    text_surface = font.render(text, True, color)
    surface.blit(text_surface, position)