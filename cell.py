import random


#NOT CALIBRATED CLINICAL RATES
MUTATION_EFFECTS = {
    "BRAF": 0.30,
    "Faster Growth": 0.05,
    "Immune Evasion": 0.00,
    "Drug Resistance": 0.00,
}

ACQUIRED_MUTATIONS = [
    "Faster Growth",
    "Immune Evasion",
    "Drug Resistance",
]


class Cell:
    _next_cell_id = 1

    @classmethod
    def reset_counter(cls):
        cls._next_cell_id = 1

    def __init__(
        self,
        cancerous=False,
        parent_id=None,
        clone_id=None,
        mutations=None,
        x=None,
        y=None,
        normal_type="keratinocyte",
        displaced_cell_type=None,
    ):
        self.cell_id = Cell._next_cell_id
        Cell._next_cell_id += 1

        self.cancerous = cancerous
        self.parent_id = parent_id
        self.clone_id = clone_id
        self.mutations = list(mutations) if mutations else []

        self.x = x
        self.y = y
        self.normal_type = normal_type
        self.displaced_cell_type = displaced_cell_type
        self.age = 0

    @property
    def growth_rate(self):
        if not self.cancerous:
            return 0.0

        rate = sum(
            MUTATION_EFFECTS[mutation]
            for mutation in self.mutations
        )

        return min(max(rate, 0.0), 0.95)

    def grow(self):
        self.age += 1

    def divide(
        self,
        mutation_chance=0.005,
        x=None,
        y=None,
    ):
        if not self.cancerous:
            return None, None

        daughter_mutations = self.mutations.copy()
        new_mutation = None

        available_mutations = [
            mutation
            for mutation in ACQUIRED_MUTATIONS
            if mutation not in daughter_mutations
        ]

        if (
            available_mutations
            and random.random() < mutation_chance
        ):
            new_mutation = random.choice(available_mutations)
            daughter_mutations.append(new_mutation)

        daughter = Cell(
            cancerous=True,
            parent_id=self.cell_id,
            clone_id=self.clone_id,
            mutations=daughter_mutations,
            x=x,
            y=y,
            normal_type="melanocyte",
        )

        return daughter, new_mutation
