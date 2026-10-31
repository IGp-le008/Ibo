import pygame
import sys
import math

# Initialize Pygame
pygame.init()

# Window settings
WIDTH, HEIGHT = 640, 640
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("CUDO Robot - Bored Face (😮💨 -> 😐 -> 🥱)")

# Colors
BACKGROUND = (20, 25, 32)
BLACK = (0, 0, 0)
CYAN = (185, 235, 255)
WHITE = (240, 250, 255)
GLOW_BLUE = (70, 180, 255)
PUFF_COLOR = (150, 220, 255)

# Proportional Ratios (relative to face diameter = face_radius * 2)
FACE_RADIUS_RATIO = 0.36
EYE_WIDTH_RATIO = 0.125
EYE_HEIGHT_RATIO = 0.130
EYE_SPACING_RATIO = 0.165
EYE_Y_OFFSET_RATIO = -0.065

MOUTH_Y_OFFSET_RATIO = 0.075    # Vertical position of mouth relative to center

# Timeline Stage Durations (in milliseconds)
STAGE_1_DURATION = 5000   # 0s - 5s: Sighing face releasing gas/puff (😮💨)
STAGE_2_DURATION = 10000  # 5s - 15s: Looking around left and right 3 cycles (😐)
STAGE_3_DURATION = 4000   # 15s - 19s: Deep yawn animation (🥱)
TOTAL_BORED_DURATION = STAGE_1_DURATION + STAGE_2_DURATION + STAGE_3_DURATION  # 19000 ms

AUTO_TRANSITION_TO_IDEAL = True  # Automatically transition to ideal (sleeping) mode after 19s sequence

clock = pygame.time.Clock()


def draw_flat_neutral_eye(surface, center, width, height, gaze_offset_x=0):
    """Draws a half-lidded neutral eye with flat top and curved bottom (😐)."""
    x, y = center
    gx = x + gaze_offset_x

    # Soft outer glow
    glow_surf = pygame.Surface((width * 2 + 20, height * 2 + 20), pygame.SRCALPHA)
    cx, cy = glow_surf.get_width() // 2, glow_surf.get_height() // 2

    for r in range(12, 1, -3):
        alpha = max(5, int(20 * (1.0 - r / 12)))
        pygame.draw.ellipse(glow_surf, (*GLOW_BLUE, alpha), (cx - width // 2 - r, cy - height // 2 - r, width + r * 2, height + r * 2))
    surface.blit(glow_surf, (gx - cx, y - cy))

    # Outer cyan eye with flat upper lid (eyelid droop)
    eye_rect = pygame.Rect(gx - width // 2, y - height // 2, width, height)
    pygame.draw.ellipse(surface, CYAN, eye_rect)
    # Cut off upper half with background to make flat half-open lid
    pygame.draw.rect(surface, BLACK, (eye_rect.left - 4, eye_rect.top - 4, width + 8, height // 2 + 4))
    # Re-draw clean flat upper eyelid line
    pygame.draw.line(surface, CYAN, (eye_rect.left, eye_rect.centery), (eye_rect.right, eye_rect.centery), width=3)
    pygame.draw.line(surface, WHITE, (eye_rect.left, eye_rect.centery), (eye_rect.right, eye_rect.centery), width=1)

    # Lower core dome
    core_inset = max(2, int(width * 0.1))
    core_rect = pygame.Rect(
        eye_rect.left + core_inset,
        eye_rect.top + core_inset,
        max(2, width - core_inset * 2),
        max(2, height - core_inset * 2),
    )
    pygame.draw.ellipse(surface, WHITE, core_rect)
    pygame.draw.rect(surface, BLACK, (core_rect.left - 2, core_rect.top - 2, core_rect.width + 4, core_rect.height // 2 + 2))


def draw_squint_yawn_eye(surface, center, width, height):
    """Draws tightly squeezed shut eyes for the yawn expression (><)."""
    x, y = center
    surf = pygame.Surface((width * 2, height * 2), pygame.SRCALPHA)
    cx, cy = width, height

    # Squished arch / wedge lines
    pts = [(cx - width // 2, cy - height // 3), (cx, cy + height // 4), (cx + width // 2, cy - height // 3)]
    for r in range(8, 1, -2):
        pygame.draw.lines(surf, (*GLOW_BLUE, 40), False, pts, width=r + 2)
    pygame.draw.lines(surf, CYAN, False, pts, width=4)
    pygame.draw.lines(surf, WHITE, False, pts, width=2)

    surface.blit(surf, (x - cx, y - cy))


def draw_sigh_puff_cloud(surface, mouth_center, face_diameter, stage_t):
    """
    Draws animated breath / vapor clouds drifting from the mouth (😮💨).
    stage_t: 0 to 5000 ms.
    """
    mx, my = mouth_center
    num_particles = 4

    for i in range(num_particles):
        # Staggered loop
        p_cycle = (stage_t / 1800.0 + i * 0.28) % 1.0
        # Drift right and slightly upwards
        drift_x = int(p_cycle * (face_diameter * 0.22))
        drift_y = -int(math.sin(p_cycle * math.pi * 0.8) * (face_diameter * 0.06))
        
        px = mx + int(face_diameter * 0.06) + drift_x
        py = my + drift_y
        
        pr = int(face_diameter * (0.02 + 0.045 * p_cycle))
        alpha = int(180 * math.sin(p_cycle * math.pi))

        p_surf = pygame.Surface((pr * 4, pr * 4), pygame.SRCALPHA)
        pc = pr * 2
        pygame.draw.circle(p_surf, (*GLOW_BLUE, int(alpha * 0.4)), (pc, pc), pr + 4)
        pygame.draw.circle(p_surf, (*PUFF_COLOR, int(alpha * 0.7)), (pc, pc), pr)
        pygame.draw.circle(p_surf, (*WHITE, alpha), (pc - pr // 3, pc - pr // 3), max(1, pr // 3))
        surface.blit(p_surf, (px - pc, py - pc))


def draw_yawn_mouth(surface, center, face_diameter, progress):
    """
    Draws a deep open yawning mouth that stretches wide and then closes (🥱).
    progress: 0.0 -> 1.0 across the 4-second yawn.
    """
    cx, cy = center
    
    # Calculate stretch curve with smooth easing: open, hold, close
    if progress < 0.35:
        stretch = 0.5 * (1.0 - math.cos((progress / 0.35) * math.pi))
    elif progress < 0.75:
        stretch = 1.0
    else:
        stretch = 0.5 * (1.0 + math.cos(((progress - 0.75) / 0.25) * math.pi))

    mw = int(face_diameter * (0.08 + 0.06 * stretch))
    mh = max(4, int(face_diameter * (0.02 + 0.13 * stretch)))

    # Outer mouth glow
    glow_surf = pygame.Surface((mw * 2, mh * 2), pygame.SRCALPHA)
    pygame.draw.ellipse(glow_surf, (*GLOW_BLUE, int(70 * stretch)), (mw // 2, mh // 2, mw, mh))
    surface.blit(glow_surf, (cx - mw, cy - mh))

    # Inner open mouth cavity (dark cyan/black with glowing rim)
    yawn_rect = pygame.Rect(cx - mw // 2, cy - mh // 2, mw, mh)
    pygame.draw.ellipse(surface, (15, 25, 35), yawn_rect)
    pygame.draw.ellipse(surface, CYAN, yawn_rect, width=max(2, int(face_diameter * 0.008)))
    
    # Small tongue highlight at the bottom
    if stretch > 0.4:
        tw = int(mw * 0.5)
        th = int(mh * 0.28)
        pygame.draw.ellipse(surface, (120, 205, 255), (cx - tw // 2, yawn_rect.bottom - th - 2, tw, th))


def get_stage_2_gaze(stage_t, face_diameter):
    """
    Computes horizontal gaze offset for Stage 2 (3 cycles of Center -> Left -> Right -> Center).
    10 seconds total duration / 3 cycles = 3333 ms per cycle.
    Uses cosine ease-in-out for smooth, natural-looking transitions.
    """
    cycle_ms = 10000.0 / 3.0
    t_in_cycle = (stage_t % cycle_ms) / cycle_ms  # 0.0 to 1.0
    max_offset = int(face_diameter * 0.035)

    def ease(p):
        """Cosine ease-in-out: smooth start and end."""
        return 0.5 * (1.0 - math.cos(p * math.pi))

    # 4 distinct phases in each cycle:
    # 0.00 - 0.20: Center hold (0)
    # 0.20 - 0.30: Ease to left
    # 0.30 - 0.45: Left hold (-max_offset)
    # 0.45 - 0.55: Ease from left to right
    # 0.55 - 0.70: Right hold (+max_offset)
    # 0.70 - 0.80: Ease back to center
    # 0.80 - 1.00: Center hold (0)
    if t_in_cycle < 0.20:
        return 0
    elif t_in_cycle < 0.30:
        p = ease((t_in_cycle - 0.20) / 0.10)
        return -int(max_offset * p)
    elif t_in_cycle < 0.45:
        return -max_offset
    elif t_in_cycle < 0.55:
        p = ease((t_in_cycle - 0.45) / 0.10)
        return -max_offset + int(2 * max_offset * p)
    elif t_in_cycle < 0.70:
        return max_offset
    elif t_in_cycle < 0.80:
        p = ease((t_in_cycle - 0.70) / 0.10)
        return max_offset - int(max_offset * p)
    else:
        return 0


def draw_face(current_time_ms):
    # If past the 19s sequence and auto-transition is enabled, seamlessly transition to ideal (sleeping)
    if AUTO_TRANSITION_TO_IDEAL and current_time_ms >= TOTAL_BORED_DURATION:
        try:
            from expressions import ideal
            ideal.draw_face(current_time_ms - TOTAL_BORED_DURATION)
            return
        except ImportError:
            pass

    center = (WIDTH // 2, HEIGHT // 2)
    face_radius = int(min(WIDTH, HEIGHT) * FACE_RADIUS_RATIO)
    face_diameter = face_radius * 2

    # Background
    screen.fill(BACKGROUND)

    # Black face circle
    pygame.draw.circle(screen, BLACK, center, face_radius)

    eye_spacing = int(face_diameter * EYE_SPACING_RATIO)
    eye_w = int(face_diameter * EYE_WIDTH_RATIO)
    eye_h = int(face_diameter * EYE_HEIGHT_RATIO)
    eye_y = center[1] + int(face_diameter * EYE_Y_OFFSET_RATIO)
    mouth_y = center[1] + int(face_diameter * MOUTH_Y_OFFSET_RATIO)

    timeline_ms = current_time_ms % TOTAL_BORED_DURATION

    # ==============================================================
    # STAGE 1 (0 to 5s): Sighing Face releasing gas (😮💨)
    # ==============================================================
    if timeline_ms < STAGE_1_DURATION:
        stage_t = timeline_ms

        # Weary half-lidded eyes
        draw_flat_neutral_eye(screen, (center[0] - eye_spacing, eye_y), eye_w, eye_h, gaze_offset_x=0)
        draw_flat_neutral_eye(screen, (center[0] + eye_spacing, eye_y), eye_w, eye_h, gaze_offset_x=0)

        # Small round exhaling mouth (😮)
        mw = int(face_diameter * 0.055)
        mh = int(face_diameter * 0.065)
        mouth_rect = pygame.Rect(center[0] - mw // 2, mouth_y - mh // 2, mw, mh)
        pygame.draw.ellipse(screen, (*GLOW_BLUE, 60), (mouth_rect.left - 4, mouth_rect.top - 4, mw + 8, mh + 8))
        pygame.draw.ellipse(screen, CYAN, mouth_rect, width=2)
        pygame.draw.ellipse(screen, WHITE, (mouth_rect.left + 2, mouth_rect.top + 2, mw - 4, mh - 4))

        # Releasing puff / air cloud (💨)
        draw_sigh_puff_cloud(screen, (center[0], mouth_y), face_diameter, stage_t)

    # ==============================================================
    # STAGE 2 (5s to 15s): Looking Left & Right for 3 Cycles (😐)
    # ==============================================================
    elif timeline_ms < (STAGE_1_DURATION + STAGE_2_DURATION):
        stage_t = timeline_ms - STAGE_1_DURATION
        gaze_x = get_stage_2_gaze(stage_t, face_diameter)

        # Neutral half-lidded eyes with animated gaze shifting
        draw_flat_neutral_eye(screen, (center[0] - eye_spacing, eye_y), eye_w, eye_h, gaze_offset_x=gaze_x)
        draw_flat_neutral_eye(screen, (center[0] + eye_spacing, eye_y), eye_w, eye_h, gaze_offset_x=gaze_x)

        # Flat neutral bar mouth (😐)
        mw = int(face_diameter * 0.09)
        pygame.draw.line(screen, (*GLOW_BLUE, 70), (center[0] - mw // 2, mouth_y), (center[0] + mw // 2, mouth_y), width=6)
        pygame.draw.line(screen, CYAN, (center[0] - mw // 2, mouth_y), (center[0] + mw // 2, mouth_y), width=4)
        pygame.draw.line(screen, WHITE, (center[0] - mw // 2, mouth_y), (center[0] + mw // 2, mouth_y), width=2)

    # ==============================================================
    # STAGE 3 (15s to 19s): Deep Yawn Animation (🥱) -> Transition to ideal
    # ==============================================================
    else:
        stage_t = timeline_ms - (STAGE_1_DURATION + STAGE_2_DURATION)
        progress = stage_t / float(STAGE_3_DURATION)

        # Squeezed shut yawn eyes (><)
        draw_squint_yawn_eye(screen, (center[0] - eye_spacing, eye_y), eye_w, eye_h // 2)
        draw_squint_yawn_eye(screen, (center[0] + eye_spacing, eye_y), eye_w, eye_h // 2)

        # Gaping yawning mouth (🥱)
        draw_yawn_mouth(screen, (center[0], mouth_y + int(face_diameter * 0.02)), face_diameter, progress)

    pygame.display.flip()


def main():
    running = True

    while running:
        current_time_ms = pygame.time.get_ticks()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False

        draw_face(current_time_ms)
        clock.tick(60)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
