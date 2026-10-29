import colorsys

import pygame

from simulation import Simulation


TOP_CELL_SIZE = 8
INFO_PANEL_WIDTH = 280
SECTION_PANEL_WIDTH = 400
SECTION_CELL_SIZE = 11
SLICE_RADIUS = 10

BACKGROUND_COLOR = (20, 22, 28)
INFO_BACKGROUND = (27, 29, 36)
SECTION_BACKGROUND = (31, 33, 40)
PANEL_BORDER = (70, 74, 88)
TEXT_COLOR = (235, 235, 235)
SECONDARY_TEXT_COLOR = (170, 175, 185)
GRID_COLOR = (92, 77, 68)
HIGHLIGHT_COLOR = (255, 230, 90)

SURFACE_COLORS = {
    "keratinocyte": (229, 205, 183),
    "melanocyte": (104, 71, 48),
    "langerhans": (92, 180, 216),
    "merkel": (232, 102, 174),
}

SECTION_LAYER_COLORS = {
    "stratum_corneum": (242, 224, 193),
    "epidermis": (227, 199, 176),
    "basal": (191, 154, 127),
    "dermis": (232, 178, 172),
    "hypodermis": (243, 218, 132),
    "melanocyte": (104, 71, 48),
    "langerhans": (92, 180, 216),
    "merkel": (232, 102, 174),
    "vessel": (172, 31, 43),
    "vessel_core": (235, 84, 91),
}

CLONES_PER_PAGE = 8


class Visualizer:
    def __init__(self, simulation):
        pygame.init()

        self.simulation = simulation
        self.tissue_pixel_width = simulation.width * TOP_CELL_SIZE
        self.tissue_pixel_height = simulation.height * TOP_CELL_SIZE

        self.window_width = (
            self.tissue_pixel_width
            + INFO_PANEL_WIDTH
            + SECTION_PANEL_WIDTH
        )
        self.window_height = max(
            self.tissue_pixel_height,
            820,
        )

        self.screen = pygame.display.set_mode(
            (self.window_width, self.window_height)
        )
        pygame.display.set_caption(
            "Melanoma Spatial Simulator"
        )

        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("Arial", 18)
        self.small_font = pygame.font.SysFont("Arial", 14)
        self.tiny_font = pygame.font.SysFont("Arial", 12)
        self.title_font = pygame.font.SysFont(
            "Arial",
            24,
            bold=True,
        )

        self.paused = False
        self.step_delay = 250
        self.last_step_time = pygame.time.get_ticks()
        self.heatmap_mode = False
        self.magnifier_mode = False
        self.slice_radius = SLICE_RADIUS
        self.hover_cell = None
        self.clone_scroll = 0
        self.selected_clone_id = None
        self.clone_hitboxes = {}

    def clone_color(self, clone_id):
        """Return a deterministic color for a lineage clone."""
        hue = ((clone_id - 1) * 0.61803398875) % 1.0
        saturation = 0.82
        value = 0.95

        red, green, blue = colorsys.hsv_to_rgb(
            hue,
            saturation,
            value,
        )

        return (
            int(red * 255),
            int(green * 255),
            int(blue * 255),
        )

    def heatmap_color(self, density):
        density = max(0.0, min(1.0, density))
        red = 235
        green = int(210 - 175 * density)
        blue = int(190 - 165 * density)
        return (red, green, blue)

    def get_mouse_grid_position(self):
        mouse_x, mouse_y = pygame.mouse.get_pos()

        if (
            0 <= mouse_x < self.tissue_pixel_width
            and 0 <= mouse_y < self.tissue_pixel_height
        ):
            return (
                mouse_x // TOP_CELL_SIZE,
                mouse_y // TOP_CELL_SIZE,
            )

        return None

    def draw_tissue(self):
        for y in range(self.simulation.height):
            for x in range(self.simulation.width):
                cell = self.simulation.grid[y][x]

                if cell.cancerous:
                    if self.heatmap_mode:
                        density = self.simulation.local_cancer_density(
                            x,
                            y,
                            radius=2,
                        )
                        color = self.heatmap_color(density)
                    else:
                        color = self.clone_color(cell.clone_id)
                else:
                    color = SURFACE_COLORS.get(
                        cell.normal_type,
                        SURFACE_COLORS["keratinocyte"],
                    )

                rect = pygame.Rect(
                    x * TOP_CELL_SIZE,
                    y * TOP_CELL_SIZE,
                    TOP_CELL_SIZE,
                    TOP_CELL_SIZE,
                )

                pygame.draw.rect(self.screen, color, rect)
                pygame.draw.rect(
                    self.screen,
                    (40, 40, 40) if cell.cancerous else GRID_COLOR,
                    rect,
                    1,
                )

        if self.magnifier_mode and self.hover_cell is not None:
            hover_x, hover_y = self.hover_cell
            left = max(0, hover_x - self.slice_radius)
            right = min(
                self.simulation.width - 1,
                hover_x + self.slice_radius,
            )

            slice_rect = pygame.Rect(
                left * TOP_CELL_SIZE,
                hover_y * TOP_CELL_SIZE,
                (right - left + 1) * TOP_CELL_SIZE,
                TOP_CELL_SIZE,
            )
            pygame.draw.rect(
                self.screen,
                HIGHLIGHT_COLOR,
                slice_rect,
                2,
            )

            hover_rect = pygame.Rect(
                hover_x * TOP_CELL_SIZE,
                hover_y * TOP_CELL_SIZE,
                TOP_CELL_SIZE,
                TOP_CELL_SIZE,
            )
            pygame.draw.rect(
                self.screen,
                (255, 255, 255),
                hover_rect,
                2,
            )

    def draw_magnifier_cursor(self):
        if not self.magnifier_mode or self.hover_cell is None:
            return

        mouse_x, mouse_y = pygame.mouse.get_pos()
        pygame.draw.circle(
            self.screen,
            HIGHLIGHT_COLOR,
            (mouse_x, mouse_y),
            15,
            2,
        )
        pygame.draw.line(
            self.screen,
            HIGHLIGHT_COLOR,
            (mouse_x + 10, mouse_y + 10),
            (mouse_x + 22, mouse_y + 22),
            3,
        )

    def draw_info_panel(self):
        panel_x = self.tissue_pixel_width

        pygame.draw.rect(
            self.screen,
            INFO_BACKGROUND,
            (
                panel_x,
                0,
                INFO_PANEL_WIDTH,
                self.window_height,
            ),
        )
        pygame.draw.line(
            self.screen,
            PANEL_BORDER,
            (panel_x, 0),
            (panel_x, self.window_height),
            2,
        )

        x = panel_x + 16
        y = 18

        title = self.title_font.render(
            "Melanoma Simulator",
            True,
            TEXT_COLOR,
        )
        self.screen.blit(title, (x, y))
        y += 42

        data = [
            ("Simulation step", self.simulation.step_number),
            ("Cancer cells", self.simulation.cancer_count()),
            ("Lineage clones", len(self.simulation.clone_summary())),
            ("Genotypes", self.simulation.genotype_count()),
            ("Max invasion", f"{self.simulation.deepest_invasion()} units"),
            (
                "Vessel contact",
                "Yes" if self.simulation.vessel_contact() else "No",
            ),
            (
                "View",
                "Heat map" if self.heatmap_mode else "Clone map",
            ),
            (
                "Magnifier",
                "ON" if self.magnifier_mode else "OFF",
            ),
        ]

        for label, value in data:
            text = self.small_font.render(
                f"{label}: {value}",
                True,
                TEXT_COLOR,
            )
            self.screen.blit(text, (x, y))
            y += 22

        y += 10
        heading = self.font.render(
            "Clone populations",
            True,
            TEXT_COLOR,
        )
        self.screen.blit(heading, (x, y))
        y += 27

        clones = self.simulation.clone_summary()
        clone_ids = sorted(clones)
        self.clone_hitboxes = {}

        max_start = max(0, len(clone_ids) - CLONES_PER_PAGE)
        self.clone_scroll = max(
            0,
            min(self.clone_scroll, max_start),
        )

        visible_clone_ids = clone_ids[
            self.clone_scroll:
            self.clone_scroll + CLONES_PER_PAGE
        ]

        if clone_ids:
            range_start = self.clone_scroll + 1
            range_end = self.clone_scroll + len(visible_clone_ids)
            page_text = self.tiny_font.render(
                f"{range_start}-{range_end} of {len(clone_ids)}",
                True,
                SECONDARY_TEXT_COLOR,
            )
            self.screen.blit(page_text, (x + 178, y - 24))

        for index, clone_id in enumerate(visible_clone_ids):
            info = clones[clone_id]
            column = index // 4
            row = index % 4
            clone_x = x + column * 125
            clone_y = y + row * 58

            clone_card_rect = pygame.Rect(
                clone_x - 4,
                clone_y - 4,
                120,
                54,
            )
            self.clone_hitboxes[clone_id] = clone_card_rect

            if clone_id == self.selected_clone_id:
                pygame.draw.rect(
                    self.screen,
                    HIGHLIGHT_COLOR,
                    clone_card_rect,
                    2,
                )

            color = self.clone_color(clone_id)
            pygame.draw.rect(
                self.screen,
                color,
                (clone_x, clone_y + 2, 13, 13),
            )
            pygame.draw.rect(
                self.screen,
                (110, 110, 110),
                (clone_x, clone_y + 2, 13, 13),
                1,
            )

            clone_text = self.tiny_font.render(
                f"Clone {clone_id}: {info['count']}",
                True,
                TEXT_COLOR,
            )
            self.screen.blit(
                clone_text,
                (clone_x + 18, clone_y),
            )

            parent = info["parent_clone_id"]
            event_id = info["mutation_event_id"]

            if parent is None:
                lineage_value = f"E{event_id} • Founder BRAF"
            else:
                lineage_value = (
                    f"E{event_id} • P{parent} +{info['founding_mutation']}"
                )

            if len(lineage_value) > 20:
                lineage_value = lineage_value[:18] + "..."

            lineage_text = self.tiny_font.render(
                lineage_value,
                True,
                SECONDARY_TEXT_COLOR,
            )
            self.screen.blit(
                lineage_text,
                (clone_x, clone_y + 18),
            )

            mutations = ", ".join(info["mutations"])
            if len(mutations) > 20:
                mutations = mutations[:18] + "..."

            mutation_text = self.tiny_font.render(
                mutations,
                True,
                SECONDARY_TEXT_COLOR,
            )
            self.screen.blit(
                mutation_text,
                (clone_x, clone_y + 34),
            )

        if len(clone_ids) > CLONES_PER_PAGE:
            scroll_hint = self.tiny_font.render(
                "Scroll here for more clones",
                True,
                SECONDARY_TEXT_COLOR,
            )
            self.screen.blit(
                scroll_hint,
                (x, y + 4 * 58 + 2),
            )

        visible_rows = min(4, len(visible_clone_ids))
        legend_y = y + max(1, visible_rows) * 58 + 24
        legend_title = self.font.render(
            "Normal skin cells",
            True,
            TEXT_COLOR,
        )
        self.screen.blit(legend_title, (x, legend_y))
        legend_y += 28

        normal_cells = [
            ("Keratinocyte", "keratinocyte"),
            ("Melanocyte", "melanocyte"),
            ("Langerhans", "langerhans"),
            ("Merkel", "merkel"),
        ]

        for label, cell_type in normal_cells:
            pygame.draw.rect(
                self.screen,
                SURFACE_COLORS[cell_type],
                (x, legend_y + 2, 13, 13),
            )
            text = self.small_font.render(
                label,
                True,
                TEXT_COLOR,
            )
            self.screen.blit(text, (x + 20, legend_y))
            legend_y += 22

        controls_y = self.window_height - 120
        heading = self.font.render(
            "Controls",
            True,
            TEXT_COLOR,
        )
        self.screen.blit(heading, (x, controls_y - 26))

        controls = [
            "SPACE  pause / resume",
            "N      single step",
            "H      clone / heat map",
            "M      magnifier / cut view",
            "R      reset",
        ]

        for control in controls:
            text = self.small_font.render(
                control,
                True,
                SECONDARY_TEXT_COLOR,
            )
            self.screen.blit(text, (x, controls_y))
            controls_y += 20

    def get_layer_name(self, depth_row):
        if depth_row < self.simulation.layer_depths["stratum_corneum"]:
            return "stratum_corneum"
        if depth_row < self.simulation.basal_start_row:
            return "epidermis"
        if depth_row < self.simulation.basal_end_row:
            return "basal"
        if depth_row < self.simulation.dermis_end_row:
            return "dermis"
        return "hypodermis"

    def section_base_color(self, depth_row, surface_type):
        layer_name = self.get_layer_name(depth_row)
        color = SECTION_LAYER_COLORS[layer_name]

        if (
            surface_type == "melanocyte"
            and depth_row == self.simulation.basal_start_row
        ):
            return SECTION_LAYER_COLORS["melanocyte"]

        if (
            surface_type == "langerhans"
            and depth_row
            == self.simulation.layer_depths["stratum_corneum"] + 2
        ):
            return SECTION_LAYER_COLORS["langerhans"]

        if (
            surface_type == "merkel"
            and depth_row == self.simulation.basal_start_row
        ):
            return SECTION_LAYER_COLORS["merkel"]

        return color

    def in_vessel(self, column_index, depth_row, column_count):
        center_x = column_count // 2
        radius_x = max(2, column_count // 5)
        center_y = self.simulation.vessel_row
        radius_y = 2

        normalized = (
            ((column_index - center_x) / radius_x) ** 2
            + ((depth_row - center_y) / radius_y) ** 2
        )
        return normalized <= 1.0

    def draw_section_panel(self):
        panel_x = self.tissue_pixel_width + INFO_PANEL_WIDTH

        pygame.draw.rect(
            self.screen,
            SECTION_BACKGROUND,
            (
                panel_x,
                0,
                SECTION_PANEL_WIDTH,
                self.window_height,
            ),
        )
        pygame.draw.line(
            self.screen,
            PANEL_BORDER,
            (panel_x, 0),
            (panel_x, self.window_height),
            2,
        )

        x = panel_x + 16
        title = self.title_font.render(
            "Magnified cut view",
            True,
            TEXT_COLOR,
        )
        self.screen.blit(title, (x, 18))

        subtitle = self.small_font.render(
            "Press M, then move over the top-view grid.",
            True,
            SECONDARY_TEXT_COLOR,
        )
        self.screen.blit(subtitle, (x, 50))

        if not self.magnifier_mode:
            text = self.font.render(
                "Magnifier OFF — press M",
                True,
                TEXT_COLOR,
            )
            self.screen.blit(text, (x, 95))
            return

        if self.hover_cell is None:
            text = self.font.render(
                "Move the cursor over the skin map.",
                True,
                TEXT_COLOR,
            )
            self.screen.blit(text, (x, 95))
            return

        hover_x, hover_y = self.hover_cell
        columns = self.simulation.get_cross_section_columns(
            hover_x,
            hover_y,
            radius=self.slice_radius,
        )

        location_text = self.small_font.render(
            f"Top-view slice: x={hover_x}, y={hover_y}",
            True,
            TEXT_COLOR,
        )
        self.screen.blit(location_text, (x, 78))

        grid_left = panel_x + 18
        grid_top = 112
        column_count = len(columns)

        for column_index, column in enumerate(columns):
            for depth_row in range(self.simulation.total_tissue_depth):
                color = self.section_base_color(
                    depth_row,
                    column["surface_type"],
                )

                if self.in_vessel(
                    column_index,
                    depth_row,
                    column_count,
                ):
                    color = SECTION_LAYER_COLORS["vessel"]

                if (
                    column["cancerous"]
                    and self.simulation.basal_start_row
                    <= depth_row
                    < self.simulation.basal_start_row
                    + column["tumor_depth"]
                ):
                    color = self.clone_color(column["clone_id"])

                rect = pygame.Rect(
                    grid_left + column_index * SECTION_CELL_SIZE,
                    grid_top + depth_row * SECTION_CELL_SIZE,
                    SECTION_CELL_SIZE,
                    SECTION_CELL_SIZE,
                )
                pygame.draw.rect(self.screen, color, rect)
                pygame.draw.rect(
                    self.screen,
                    (72, 72, 72),
                    rect,
                    1,
                )
        center_x = column_count // 2
        vessel_width = max(5, column_count // 3)
        vessel_rect = pygame.Rect(
            grid_left
            + (center_x - vessel_width // 2) * SECTION_CELL_SIZE,
            grid_top
            + (self.simulation.vessel_row - 1) * SECTION_CELL_SIZE,
            vessel_width * SECTION_CELL_SIZE,
            3 * SECTION_CELL_SIZE,
        )
        pygame.draw.ellipse(
            self.screen,
            SECTION_LAYER_COLORS["vessel_core"],
            vessel_rect,
            2,
        )

        label_x = grid_left + column_count * SECTION_CELL_SIZE + 10
        layer_labels = [
            ("Stratum corneum", 0),
            (
                "Epidermis",
                self.simulation.layer_depths["stratum_corneum"],
            ),
            ("Basal layer", self.simulation.basal_start_row),
            ("Dermis", self.simulation.basal_end_row),
            ("Hypodermis", self.simulation.dermis_end_row),
        ]

        for label, row_start in layer_labels:
            text = self.tiny_font.render(
                label,
                True,
                TEXT_COLOR,
            )
            self.screen.blit(
                text,
                (
                    label_x,
                    grid_top + row_start * SECTION_CELL_SIZE,
                ),
            )

        center_column = columns[len(columns) // 2]
        notes_y = (
            grid_top
            + self.simulation.total_tissue_depth * SECTION_CELL_SIZE
            + 14
        )

        if center_column["cancerous"]:
            displaced = center_column["displaced_cell_type"]
            selected_description = (
                "Melanoma cell"
                if displaced is None
                else f"Melanoma invading {displaced} region"
            )
        else:
            selected_description = center_column["surface_type"]

        notes = [
            f"Selected: {selected_description}",
            f"Tumor depth here: {center_column['tumor_depth']} units",
            (
                "Blood-vessel contact: "
                + ("YES" if self.simulation.vessel_contact() else "NO")
            ),
        ]

        for note in notes:
            text = self.small_font.render(
                note,
                True,
                TEXT_COLOR,
            )
            self.screen.blit(text, (grid_left, notes_y))
            notes_y += 21

    def draw_clone_identity_card(self):
        """Draw details for the lineage clone selected in the middle panel."""
        panel_x = self.tissue_pixel_width + INFO_PANEL_WIDTH
        card_x = panel_x + 18
        card_y = 500
        card_width = SECTION_PANEL_WIDTH - 36
        card_height = 300

        pygame.draw.rect(
            self.screen,
            (38, 41, 49),
            (card_x, card_y, card_width, card_height),
            border_radius=8,
        )
        pygame.draw.rect(
            self.screen,
            PANEL_BORDER,
            (card_x, card_y, card_width, card_height),
            2,
            border_radius=8,
        )

        title = self.font.render(
            "Clone identity card",
            True,
            TEXT_COLOR,
        )
        self.screen.blit(title, (card_x + 14, card_y + 12))

        if self.selected_clone_id is None:
            instruction = self.small_font.render(
                "Click a clone in the middle panel to inspect it.",
                True,
                SECONDARY_TEXT_COLOR,
            )
            self.screen.blit(instruction, (card_x + 14, card_y + 48))
            return

        info = self.simulation.clone_identity(self.selected_clone_id)

        if info is None:
            text = self.small_font.render(
                "This lineage currently has no living cells.",
                True,
                SECONDARY_TEXT_COLOR,
            )
            self.screen.blit(text, (card_x + 14, card_y + 48))
            return

        color = self.clone_color(info["clone_id"])
        pygame.draw.rect(
            self.screen,
            color,
            (card_x + 14, card_y + 46, 18, 18),
        )

        clone_title = self.font.render(
            f"Clone {info['clone_id']}",
            True,
            TEXT_COLOR,
        )
        self.screen.blit(clone_title, (card_x + 42, card_y + 44))

        parent = info["parent_clone_id"]
        parent_text = "Founder" if parent is None else f"Clone {parent}"
        genotype = ", ".join(info["mutations"])

        same_genotype = info["same_genotype_clones"]
        same_text = (
            ", ".join(str(clone_id) for clone_id in same_genotype[:6])
            if same_genotype
            else "None"
        )
        if len(same_genotype) > 6:
            same_text += "..."

        children = info["children"]
        children_text = (
            ", ".join(str(clone_id) for clone_id in children[:6])
            if children
            else "None"
        )
        if len(children) > 6:
            children_text += "..."

        left_lines = [
            ("Population", str(info["population"])),
            ("Tumor share", f"{info['tumor_fraction']:.2f}%"),
            ("Parent", parent_text),
            ("Generation", str(info["generation"])),
            ("Founded at step", str(info["created_step"])),
            ("Lineage age", f"{info['age_steps']} steps"),
        ]

        right_lines = [
            ("Mutation event", f"E{info['mutation_event_id']}"),
            ("Founding change", info["founding_mutation"]),
            ("Growth probability", f"{info['growth_rate']:.2f}"),
            ("Deepest invasion", f"{info['deepest_invasion']} units"),
            (
                "Spatial footprint",
                f"{info['spatial_width']} x {info['spatial_height']}",
            ),
            ("Child clones", children_text),
        ]

        def draw_column(lines, draw_x):
            line_y = card_y + 78
            for label, value in lines:
                label_text = self.tiny_font.render(
                    label,
                    True,
                    SECONDARY_TEXT_COLOR,
                )
                value_text = self.small_font.render(
                    value,
                    True,
                    TEXT_COLOR,
                )
                self.screen.blit(label_text, (draw_x, line_y))
                self.screen.blit(value_text, (draw_x, line_y + 12))
                line_y += 31

        draw_column(left_lines, card_x + 14)
        draw_column(right_lines, card_x + 194)

        genotype_text = self.tiny_font.render(
            f"Genotype: {genotype}",
            True,
            TEXT_COLOR,
        )
        self.screen.blit(genotype_text, (card_x + 14, card_y + 267))

        same_text_surface = self.tiny_font.render(
            f"Same-genotype lineages: {same_text}",
            True,
            SECONDARY_TEXT_COLOR,
        )
        self.screen.blit(
            same_text_surface,
            (card_x + 14, card_y + 283),
        )

    def reset(self):
        old = self.simulation
        self.simulation = Simulation(
            width=old.width,
            height=old.height,
            mutation_chance=old.mutation_chance,
        )
        self.paused = False
        self.hover_cell = None
        self.clone_scroll = 0
        self.selected_clone_id = None
        self.clone_hitboxes = {}
        self.last_step_time = pygame.time.get_ticks()

    def close(self):
        pygame.quit()

    def run(self):
        running = True

        while running:
            self.hover_cell = self.get_mouse_grid_position()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE:
                        self.paused = not self.paused

                    elif event.key == pygame.K_n:
                        if self.paused:
                            self.simulation.step()

                    elif event.key == pygame.K_h:
                        self.heatmap_mode = not self.heatmap_mode

                    elif event.key == pygame.K_m:
                        self.magnifier_mode = not self.magnifier_mode

                    elif event.key == pygame.K_r:
                        self.reset()

                elif (
                    event.type == pygame.MOUSEBUTTONDOWN
                    and event.button == 1
                ):
                    clicked_clone = None

                    for clone_id, hitbox in self.clone_hitboxes.items():
                        if hitbox.collidepoint(event.pos):
                            clicked_clone = clone_id
                            break

                    if clicked_clone is not None:
                        if self.selected_clone_id == clicked_clone:
                            self.selected_clone_id = None
                        else:
                            self.selected_clone_id = clicked_clone

                elif event.type == pygame.MOUSEWHEEL:
                    mouse_x, _ = pygame.mouse.get_pos()
                    info_left = self.tissue_pixel_width
                    info_right = info_left + INFO_PANEL_WIDTH

                    if info_left <= mouse_x < info_right:
                        clone_count = len(
                            self.simulation.clone_summary()
                        )
                        max_start = max(
                            0,
                            clone_count - CLONES_PER_PAGE,
                        )

                        self.clone_scroll -= event.y * 2
                        self.clone_scroll = max(
                            0,
                            min(self.clone_scroll, max_start),
                        )

            current_time = pygame.time.get_ticks()

            if (
                not self.paused
                and current_time - self.last_step_time
                >= self.step_delay
            ):
                self.simulation.step()
                self.last_step_time = current_time

            self.screen.fill(BACKGROUND_COLOR)
            self.draw_tissue()
            self.draw_info_panel()
            self.draw_section_panel()
            self.draw_clone_identity_card()
            self.draw_magnifier_cursor()

            pygame.display.flip()
            self.clock.tick(60)

        self.close()
