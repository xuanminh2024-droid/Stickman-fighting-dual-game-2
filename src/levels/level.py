class Level:
    def __init__(self, level_number, background_image):
        self.level_number = level_number
        self.background_image = background_image
        self.entities = []
        self.is_active = False

    def load_level(self):
        # Load level-specific assets and initialize entities
        self.is_active = True

    def update(self):
        # Update entities and game state for the level
        if self.is_active:
            for entity in self.entities:
                entity.update()

    def draw(self, screen):
        # Draw the level background and entities
        if self.is_active:
            screen.blit(self.background_image, (0, 0))
            for entity in self.entities:
                entity.draw(screen)

    def unload_level(self):
        # Clean up and unload level assets
        self.entities.clear()
        self.is_active = False

    def add_entity(self, entity):
        self.entities.append(entity)