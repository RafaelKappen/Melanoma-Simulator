import random
from collections import defaultdict

from cell import Cell


class Simulation:
    def __init__(
        self,
        width=80,
        height=60,
        mutation_chance=0.10,
    ):
        Cell.reset_counter()

        self.width = width
        self.height = height
        self.mutation_chance = mutation_chance
        self.step_number = 0
        self.clone_registry = {}
        self.next_clone_id = 1
        self.next_mutation_event_id = 1
        # Values are display rows, not millimetres.
        self.layer_depths = {
            "stratum_corneum": 2,
            "epidermis": 5,
            "basal": 2,
            "dermis": 12,
            "hypodermis": 7,
        }

        self.total_tissue_depth = sum(self.layer_depths.values())

        self.basal_start_row = (
            self.layer_depths["stratum_corneum"]
            + self.layer_depths["epidermis"]
        )
        self.basal_end_row = (
            self.basal_start_row
            + self.layer_depths["basal"]
        )
        self.dermis_end_row = (
            self.basal_end_row
            + self.layer_depths["dermis"]
        )
        self.vessel_row = self.dermis_end_row - 3
        self.max_tumor_depth = (
            self.total_tissue_depth
            - self.basal_start_row
        )
        self.vessel_contact_depth = (
            self.vessel_row
            - self.basal_start_row
        )

        self.grid = []
        self.tumor_depth_map = [
            [0 for _ in range(width)]
            for _ in range(height)
        ]

        for y in range(height):
            row = []
            for x in range(width):
                row.append(
                    Cell(
                        cancerous=False,
                        x=x,
                        y=y,
                        normal_type=self.choose_surface_cell_type(x, y),
                    )
                )
            self.grid.append(row)

        founder_mutations = ["BRAF"]
        founder_clone = self.create_clone(
            mutations=founder_mutations,
            parent_clone_id=None,
            founding_mutation="BRAF",
            created_step=0,
        )
        center_x = width // 2
        center_y = height // 2

        melanocyte_positions = [
            (x, y)
            for y in range(height)
            for x in range(width)
            if self.grid[y][x].normal_type == "melanocyte"
        ]

        founder_x, founder_y = min(
            melanocyte_positions,
            key=lambda position: (
                (position[0] - center_x) ** 2
                + (position[1] - center_y) ** 2
            ),
        )

        founder_cell = Cell(
            cancerous=True,
            clone_id=founder_clone,
            mutations=founder_mutations,
            x=founder_x,
            y=founder_y,
            normal_type="melanocyte",
            displaced_cell_type="melanocyte",
        )

        self.grid[founder_y][founder_x] = founder_cell
        self.tumor_depth_map[founder_y][founder_x] = 1
        self.clone_registry[founder_clone]["founder_cell_id"] = (
            founder_cell.cell_id
        )

    def choose_surface_cell_type(self, x, y):
    

     value = (x * 37 + y * 61) % 1000

     if value < 90:
        return "melanocyte"       # 9.0%

     if value < 110:
        return "langerhans"       # 2.0%

     if value < 112:
        return "merkel"           # 0.2%

     return "keratinocyte"         # 88.8%

    def create_clone(
        self,
        mutations,
        parent_clone_id,
        founding_mutation,
        created_step=None,
        founder_cell_id=None,
    ):
        """
        Create a true lineage clone.

        Clone identity follows ancestry. Every independent mutation
        event gets a new clone ID and mutation-event ID even when
        another lineage already has the same modeled mutation profile.
        """
        clone_id = self.next_clone_id
        self.next_clone_id += 1

        mutation_event_id = self.next_mutation_event_id
        self.next_mutation_event_id += 1

        if created_step is None:
            created_step = self.step_number

        self.clone_registry[clone_id] = {
            "parent_clone_id": parent_clone_id,
            "founding_mutation": founding_mutation,
            "mutation_event_id": mutation_event_id,
            "mutations": sorted(mutations),
            "created_step": created_step,
            "founder_cell_id": founder_cell_id,
        }

        return clone_id

    def get_neighbors(self, x, y):
        neighbors = []

        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                if dx == 0 and dy == 0:
                    continue

                nx = x + dx
                ny = y + dy

                if (
                    0 <= nx < self.width
                    and 0 <= ny < self.height
                ):
                    neighbors.append((nx, ny))

        return neighbors

    def get_cancer_cells(self):
        return [
            cell
            for row in self.grid
            for cell in row
            if cell.cancerous
        ]

    def deepen_tumor_at(self, x, y, growth_rate):
        current_depth = self.tumor_depth_map[y][x]

        if current_depth <= 0:
            return

        # A deliberately extremely simple invasion rule for now.
        deepening_chance = min(0.08, growth_rate * 0.10)

        if random.random() < deepening_chance:
            self.tumor_depth_map[y][x] = min(
                current_depth + 1,
                self.max_tumor_depth,
            )

    def step(self):
        cancer_cells = self.get_cancer_cells()
        random.shuffle(cancer_cells)

        new_cells = []
        reserved_positions = set()

        for cell in cancer_cells:
            cell.grow()
            self.deepen_tumor_at(
                cell.x,
                cell.y,
                cell.growth_rate,
            )

            if random.random() >= cell.growth_rate:
                continue

            available_neighbors = []

            for nx, ny in self.get_neighbors(cell.x, cell.y):
                target = self.grid[ny][nx]

                if (
                    not target.cancerous
                    and (nx, ny) not in reserved_positions
                ):
                    available_neighbors.append((nx, ny))

            if not available_neighbors:
                continue

            new_x, new_y = random.choice(available_neighbors)
            target = self.grid[new_y][new_x]

            daughter, new_mutation = cell.divide(
                mutation_chance=self.mutation_chance,
                x=new_x,
                y=new_y,
            )

            if daughter is None:
                continue
            daughter.displaced_cell_type = target.normal_type

            if new_mutation is not None:
                new_clone_id = self.create_clone(
                    mutations=daughter.mutations,
                    parent_clone_id=cell.clone_id,
                    founding_mutation=new_mutation,
                    created_step=self.step_number + 1,
                    founder_cell_id=daughter.cell_id,
                )
                daughter.clone_id = new_clone_id
            else:
                daughter.clone_id = cell.clone_id

            parent_depth = self.tumor_depth_map[cell.y][cell.x]
            self.tumor_depth_map[new_y][new_x] = max(
                1,
                parent_depth - 1,
            )

            reserved_positions.add((new_x, new_y))
            new_cells.append(daughter)

        for daughter in new_cells:
            self.grid[daughter.y][daughter.x] = daughter

        self.step_number += 1

    def cancer_count(self):
        return len(self.get_cancer_cells())

    def genotype_count(self):
        """Number of distinct mutation profiles currently present."""
        return len(
            {
                tuple(sorted(cell.mutations))
                for cell in self.get_cancer_cells()
            }
        )

    def clone_summary(self):
        """
        Return current clone populations plus lineage metadata.

        Clone identity is based on ancestry/mutation event, not merely
        on having the same mutation profile.
        """
        clones = {}

        for clone_id, metadata in self.clone_registry.items():
            clones[clone_id] = {
                "count": 0,
                "mutations": list(metadata["mutations"]),
                "parent_clone_id": metadata["parent_clone_id"],
                "founding_mutation": metadata["founding_mutation"],
                "mutation_event_id": metadata["mutation_event_id"],
                "created_step": metadata["created_step"],
                "founder_cell_id": metadata["founder_cell_id"],
            }

        for cell in self.get_cancer_cells():
            clones[cell.clone_id]["count"] += 1
        return {
            clone_id: info
            for clone_id, info in clones.items()
            if info["count"] > 0
        }

    def clone_generation(self, clone_id):
        """Return the lineage generation relative to the founder."""
        generation = 0
        current_id = clone_id

        while current_id is not None:
            metadata = self.clone_registry.get(current_id)
            if metadata is None:
                break

            parent_id = metadata["parent_clone_id"]
            if parent_id is None:
                break

            generation += 1
            current_id = parent_id

        return generation

    def clone_identity(self, clone_id):
        """Return detailed information for a clone identity card."""
        metadata = self.clone_registry.get(clone_id)
        if metadata is None:
            return None

        clone_cells = [
            cell
            for cell in self.get_cancer_cells()
            if cell.clone_id == clone_id
        ]

        population = len(clone_cells)
        if population == 0:
            return None

        total_cancer = self.cancer_count()
        tumor_fraction = (
            100.0 * population / total_cancer
            if total_cancer > 0
            else 0.0
        )

        deepest_invasion = max(
            self.tumor_depth_map[cell.y][cell.x]
            for cell in clone_cells
        )

        x_positions = [cell.x for cell in clone_cells]
        y_positions = [cell.y for cell in clone_cells]

        genotype = tuple(sorted(metadata["mutations"]))
        summary = self.clone_summary()

        same_genotype_clones = [
            other_clone_id
            for other_clone_id, info in summary.items()
            if (
                other_clone_id != clone_id
                and tuple(sorted(info["mutations"])) == genotype
            )
        ]

        children = [
            other_clone_id
            for other_clone_id, other_metadata
            in self.clone_registry.items()
            if other_metadata["parent_clone_id"] == clone_id
        ]

        return {
            "clone_id": clone_id,
            "population": population,
            "tumor_fraction": tumor_fraction,
            "parent_clone_id": metadata["parent_clone_id"],
            "founding_mutation": metadata["founding_mutation"],
            "mutation_event_id": metadata["mutation_event_id"],
            "mutations": list(metadata["mutations"]),
            "created_step": metadata["created_step"],
            "age_steps": self.step_number - metadata["created_step"],
            "generation": self.clone_generation(clone_id),
            "growth_rate": clone_cells[0].growth_rate,
            "deepest_invasion": deepest_invasion,
            "spatial_width": max(x_positions) - min(x_positions) + 1,
            "spatial_height": max(y_positions) - min(y_positions) + 1,
            "same_genotype_clones": sorted(same_genotype_clones),
            "children": sorted(children),
        }

    def local_cancer_density(self, x, y, radius=2):
        cancer = 0
        total = 0

        for dy in range(-radius, radius + 1):
            for dx in range(-radius, radius + 1):
                nx = x + dx
                ny = y + dy

                if (
                    0 <= nx < self.width
                    and 0 <= ny < self.height
                ):
                    total += 1
                    if self.grid[ny][nx].cancerous:
                        cancer += 1

        return cancer / total if total else 0.0

    def deepest_invasion(self):
        return max(max(row) for row in self.tumor_depth_map)

    def vessel_contact(self):
        return (
            self.deepest_invasion()
            >= self.vessel_contact_depth
        )

    def get_cross_section_columns(
        self,
        center_x,
        center_y,
        radius=10,
    ):
        start_x = max(0, center_x - radius)
        end_x = min(self.width - 1, center_x + radius)

        columns = []

        for x in range(start_x, end_x + 1):
            cell = self.grid[center_y][x]
            columns.append(
                {
                    "x": x,
                    "y": center_y,
                    "surface_type": cell.normal_type,
                    "cancerous": cell.cancerous,
                    "clone_id": cell.clone_id,
                    "displaced_cell_type": cell.displaced_cell_type,
                    "tumor_depth": self.tumor_depth_map[center_y][x],
                }
            )

        return columns
