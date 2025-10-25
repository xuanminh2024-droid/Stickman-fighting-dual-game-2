class Physics:
    def __init__(self):
        self.gravity = 0.5
        self.friction = 0.1

    def apply_gravity(self, entity):
        if not entity.on_ground:
            entity.velocity_y += self.gravity
        else:
            entity.velocity_y = 0

    def check_collision(self, entity1, entity2):
        if (entity1.rect.colliderect(entity2.rect)):
            self.resolve_collision(entity1, entity2)

    def resolve_collision(self, entity1, entity2):
        # Simple collision resolution logic
        if entity1.rect.bottom > entity2.rect.top:
            entity1.rect.bottom = entity2.rect.top
            entity1.on_ground = True
        elif entity1.rect.top < entity2.rect.bottom:
            entity1.rect.top = entity2.rect.bottom
            entity1.velocity_y = 0
        elif entity1.rect.right > entity2.rect.left:
            entity1.rect.right = entity2.rect.left
        elif entity1.rect.left < entity2.rect.right:
            entity1.rect.left = entity2.rect.right