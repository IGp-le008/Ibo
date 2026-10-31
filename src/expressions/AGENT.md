# AGENT.md --- CUDO Robot Expression Coding Conventions

This document defines the coding style and implementation rules for
creating CUDO's Pygame facial expressions. Follow it for every new
expression and when modifying an existing one, unless the project
explicitly adopts a newer convention.

The goal is to make expressions **consistent, resolution-independent,
easy to tune, and straightforward to integrate** with face tracking and
the agent's runtime states.

## 1. Core principles

1.  **Use Pygame and Python** for the current expression renderer.
2.  **Prefer proportions over fixed pixel coordinates.** The face should
    scale when the window or display resolution changes.
3.  **Keep tunable design values in named constants** near the top of
    the file. Do not scatter unexplained numeric values throughout
    drawing code.
4.  **Use normalized coordinates for shape geometry**, especially mouth
    polygons and other custom features.
5.  **Separate geometry, drawing, animation calculations, and the main
    event loop** into clearly named functions.
6.  **Keep the expression visually self-contained.** A face expression
    should draw its features; 
7.  **Use descriptive names and comments** that explain intent,
    coordinate reference, or a non-obvious implementation choice.
8.  **Preserve the existing expression's visual design** when
    refactoring. A structural improvement must not silently change the
    face's appearance.

## 2. File and expression organization

Use one clearly named Python module per expression while the project is
small. For example:

-   `expressions/greeting.py`
-   `expressions/listening.py`
-   `expressions/thinking.py`
-   `expressions/sleeping.py`

If expressions later share drawing utilities, move those shared
functions into a common module (for example, `expressions/drawing.py`)
rather than copying and independently editing them in every file.

Each expression module should follow this order:

1.  Imports
2.  Pygame initialization and display configuration (or receive a
    surface from the application, if the project has moved to a shared
    renderer)
3.  Color constants
4.  Proportional-ratio constants
5.  Animation timing and scale constants
6.  Geometry/animation helper functions
7.  Feature drawing functions
8.  `draw_face(...)` or the expression's equivalent render function
9.  `main()` and the `if __name__ == "__main__":` entry point for
    standalone testing

For a standalone prototype, it is acceptable for the module to create
its own Pygame window. In the integrated application, prefer drawing
onto a supplied `surface` so the agent UI can control the display and
expression switching.

## 3. Naming conventions

Use `snake_case` for functions, variables, and module names. Use
`UPPER_SNAKE_CASE` for constants.

### Constants

Constants describe stable design/tuning values:

``` python
FACE_RADIUS_RATIO = 0.36
EYE_WIDTH_RATIO = 0.122
EYE_HEIGHT_RATIO = 0.130
EYE_SPACING_RATIO = 0.163
EYE_Y_OFFSET_RATIO = -0.076

BLINK_INTERVAL_MS = 4000
BLINK_DURATION_MS = 240
SMILE_SIZE = 1.65
```

Name proportional constants with a `_RATIO` suffix. Name animation
durations in `_MS` (milliseconds). Use `_S` for seconds if seconds are
used.

### Variables

Use names that communicate both the value and its role:

-   `face_radius`, `face_diameter`
-   `eye_width`, `base_eye_height`, `current_eye_height`
-   `eye_spacing`, `base_eye_y`, `current_eye_y`
-   `mouth_center`, `mouth_points`
-   `current_time_ms`, `blink_scale`

Use `base_` for the unanimated/base geometry and `current_` for values
after applying animation or tracking. Avoid ambiguous names such as `w`,
`h`, `val`, or `tmp`, except for short local coordinate unpacking
(`x, y = center`).

### Functions

Use action-oriented names:

-   `get_blink_scale(...)` --- calculates animation scale; does not draw
-   `draw_glowing_eye(...)` --- draws one eye
-   `draw_mouth(...)` --- draws the mouth
-   `draw_face(...)` --- composes the complete expression
-   `main()` --- standalone event loop

A function should have one clear responsibility. Add a short docstring
describing what it draws/calculates and any important coordinate
assumptions.

## 4. Responsive geometry: the face is the reference

Use the **face diameter** as the main reference unit for facial-feature
dimensions and offsets. This allows the whole expression to scale as one
design.

For a square window:

``` python
center = (WIDTH // 2, HEIGHT // 2)
face_radius = int(min(WIDTH, HEIGHT) * FACE_RADIUS_RATIO)
face_diameter = face_radius * 2
```

For other layouts, derive the face center and available face size from
the intended face area, not blindly from the full window. Keep the face
within the display bounds.

Convert ratios to pixels at render time:

``` python
eye_width = max(4, int(face_diameter * EYE_WIDTH_RATIO))
eye_spacing = int(face_diameter * EYE_SPACING_RATIO)
eye_y = center[1] + int(face_diameter * EYE_Y_OFFSET_RATIO)
```

Rules:

-   Store design dimensions and offsets as ratios; calculate pixel
    values inside the rendering/geometry code.
-   Use `int(...)` when converting a calculated coordinate or size to
    Pygame's integer pixel geometry.
-   Use a small `max(...)` lower bound where a feature would otherwise
    become zero-sized at small resolutions.
-   Keep signs meaningful: a negative Y offset means above the face
    center; a positive Y offset means below it.
-   Document what each ratio is relative to. Prefer `face_diameter` for
    facial features, and use `min(WIDTH, HEIGHT)` only when defining the
    face's overall size.
-   Do not mix ratios with different reference bases without
    naming/documenting that basis.

## 5. Normalized custom-shape coordinates

For polygons such as mouths, store points as normalized
`(x_ratio, y_ratio)` pairs relative to a documented anchor and reference
dimension.

Example:

``` python
# Points are normalized to face diameter and relative to mouth center.
MOUTH_POINTS_RATIOS = [
    (-0.0587, -0.0174),
    ( 0.0587, -0.0174),
    ( 0.0522,  0.0022),
    ( 0.0370,  0.0196),
    ( 0.0174,  0.0283),
    ( 0.0000,  0.0304),
    (-0.0174,  0.0283),
    (-0.0370,  0.0196),
    (-0.0522,  0.0022),
]
```

Convert normalized points into pixel coordinates when drawing:

``` python
points = [
    (
        int(anchor_x + x_ratio * face_diameter * shape_scale),
        int(anchor_y + y_ratio * face_diameter * shape_scale),
    )
    for x_ratio, y_ratio in SHAPE_POINTS_RATIOS
]
```

Rules:

-   Name normalized point lists with a `_POINTS_RATIOS` suffix.
-   State whether the anchor is the face center, feature center, or
    another point.
-   Keep the shape's position in a separate offset constant; don't bake
    the position into every point unless the geometry intentionally
    requires it.
-   Use a dedicated scale multiplier (for example, `SMILE_SIZE`) when a
    feature should be independently resized.
-   Avoid hard-coded pixel vertices in scalable facial features.

## 6. Animation values and timing

Keep animation parameters in named constants, such as:

``` python
BLINK_INTERVAL_MS = 4000
BLINK_DURATION_MS = 240
```

Use Pygame's elapsed-time clock (`pygame.time.get_ticks()`) or delta
time rather than frame counts. The animation should look approximately
the same at different frame rates.

Animation helpers should calculate a value (for example, eye openness)
and return it. Drawing functions then use that value to render the
feature.

Use names that distinguish the baseline from the animated result:

``` python
base_eye_height = ...
blink_scale = get_blink_scale(current_time_ms)
current_eye_height = max(2, int(base_eye_height * blink_scale))
```

For anchored animation (such as an eyelid closing), document the
anchor/baseline and calculate the moving edge from it. Do not let a
feature drift unintentionally while it animates.

When adding face tracking later, treat gaze offset as an input to
geometry. Keep the tracking calculation outside the expression drawing
functions where practical.

## 7. Drawing-function conventions

Feature functions should receive the values they need explicitly. Follow
the existing style:

``` python
def draw_glowing_eye(surface, center, width, height, face_diameter):
    """Draw one cyan eye; dimensions are already scaled to the face."""
```

-   Pass the target Pygame `surface` explicitly.
-   Pass feature center, dimensions, and relevant reference size
    explicitly.
-   Keep color, glow strength, and geometry tuning in named constants
    when they are design choices.
-   Use separate layers/surfaces for transparency and glow where needed.
-   Avoid relying on hidden global state inside reusable drawing
    functions.

**Performance note:** a transparent glow surface the size of the entire
window is simple and valid for a prototype, but can be wasteful when
many features are drawn every frame. If profiling shows a cost, use a
small glow surface sized to the feature's bounding box, or cache static
glow layers. Keep the appearance consistent when optimizing.

## 8. Rendering and main-loop conventions

A standalone expression should:

1.  Process quit and keyboard events.
2.  Read the current elapsed time.
3.  Calculate animation values.
4.  Draw the background and face/features in a consistent order.
5.  Present the completed frame (`pygame.display.flip()` or
    `pygame.display.update()`).
6.  Limit frame rate with `clock.tick(...)`.

Use `pygame.QUIT` and provide a convenient exit key such as Escape
during development.

Keep drawing order explicit. For example:

1.  Background
2.  Face base
3.  Glow layers
4.  Eye shells/cores
5.  Mouth and other facial features
6.  Optional overlays

Do not call `pygame.display.flip()` inside each individual feature
function; present the frame once after the whole face has been drawn.

## 9. Display-size and integration requirements

-   Do not assume the final Raspberry Pi display has the laptop's
    resolution.
-   Keep geometry derived from the active display/face area.
-   Make the expression drawable at different sizes, including small
    test sizes.
-   For a circular physical display, account for its visible circular
    region and avoid placing features outside it.
-   In the integrated bot, expression state
    (greeting/listening/thinking/etc.), agent status text, and
    camera-derived gaze should be inputs to the UI---not tightly coupled
    to the RAG/LLM implementation.
-   The face renderer should remain responsive while the LLM or tools
    are working. Do not block its event/render loop on a model request.

## 10. New-expression checklist

Before considering an expression complete, verify:

-   [ ] All design/tuning constants are grouped near the top.
-   [ ] Proportional dimensions and offsets use clearly documented
    ratios.
-   [ ] Custom polygon geometry uses normalized points.
-   [ ] The face and its features scale correctly at more than one
    resolution.
-   [ ] Animation uses elapsed time, not assumed frame counts.
-   [ ] Base and animated geometry are named distinctly.
-   [ ] Drawing functions have clear responsibilities and explicit
    parameters.
-   [ ] The expression runs standalone for visual testing.
-   [ ] The expression can later be called by a shared renderer without
    depending on the LLM.
-   [ ] No accidental visual change was introduced while refactoring.

## 11. Preserve the established style

When asked to create another CUDO expression, use the same overall
structure and approach as the approved greeting expression:

-   grouped uppercase constants;
-   ratio-based face and feature sizing;
-   normalized custom-shape points;
-   clearly named timing and scale multipliers;
-   small drawing and calculation functions;
-   a `draw_face(current_time_ms, ...)`-style composition function;
-   a standalone Pygame loop for development.

Do not replace this approach with a fixed-pixel mockup, a static image,
or a different framework unless the user explicitly requests that
change.
