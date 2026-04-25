# main.py
import math
import pygame

# ==================================
# Math
# ==================================
class Vector3:
    __slots__ = ("x", "y", "z")

    def __init__(self, x=0.0, y=0.0, z=0.0):
        self.x = float(x)
        self.y = float(y)
        self.z = float(z)


class Mat4:
    __slots__ = ("m",)

    def __init__(self, m=None):
        self.m = m if m else [
            [1.0, 0.0, 0.0, 0.0],
            [0.0, 1.0, 0.0, 0.0],
            [0.0, 0.0, 1.0, 0.0],
            [0.0, 0.0, 0.0, 1.0],
        ]

    @staticmethod
    def rotation_x(a):
        c, s = math.cos(a), math.sin(a)
        return Mat4([
            [1.0, 0.0, 0.0, 0.0],
            [0.0, c, -s, 0.0],
            [0.0, s, c, 0.0],
            [0.0, 0.0, 0.0, 1.0],
        ])

    @staticmethod
    def rotation_y(a):
        c, s = math.cos(a), math.sin(a)
        return Mat4([
            [c, 0.0, s, 0.0],
            [0.0, 1.0, 0.0, 0.0],
            [-s, 0.0, c, 0.0],
            [0.0, 0.0, 0.0, 1.0],
        ])

    @staticmethod
    def translation(v):
        return Mat4([
            [1.0, 0.0, 0.0, v.x],
            [0.0, 1.0, 0.0, v.y],
            [0.0, 0.0, 1.0, v.z],
            [0.0, 0.0, 0.0, 1.0],
        ])

    def __matmul__(self, other):
        a = self.m
        b = other.m
        return Mat4([
            [
                a[0][0] * b[0][0] + a[0][1] * b[1][0] + a[0][2] * b[2][0] + a[0][3] * b[3][0],
                a[0][0] * b[0][1] + a[0][1] * b[1][1] + a[0][2] * b[2][1] + a[0][3] * b[3][1],
                a[0][0] * b[0][2] + a[0][1] * b[1][2] + a[0][2] * b[2][2] + a[0][3] * b[3][2],
                a[0][0] * b[0][3] + a[0][1] * b[1][3] + a[0][2] * b[2][3] + a[0][3] * b[3][3],
            ],
            [
                a[1][0] * b[0][0] + a[1][1] * b[1][0] + a[1][2] * b[2][0] + a[1][3] * b[3][0],
                a[1][0] * b[0][1] + a[1][1] * b[1][1] + a[1][2] * b[2][1] + a[1][3] * b[3][1],
                a[1][0] * b[0][2] + a[1][1] * b[1][2] + a[1][2] * b[2][2] + a[1][3] * b[3][2],
                a[1][0] * b[0][3] + a[1][1] * b[1][3] + a[1][2] * b[2][3] + a[1][3] * b[3][3],
            ],
            [
                a[2][0] * b[0][0] + a[2][1] * b[1][0] + a[2][2] * b[2][0] + a[2][3] * b[3][0],
                a[2][0] * b[0][1] + a[2][1] * b[1][1] + a[2][2] * b[2][1] + a[2][3] * b[3][1],
                a[2][0] * b[0][2] + a[2][1] * b[1][2] + a[2][2] * b[2][2] + a[2][3] * b[3][2],
                a[2][0] * b[0][3] + a[2][1] * b[1][3] + a[2][2] * b[2][3] + a[2][3] * b[3][3],
            ],
            [
                a[3][0] * b[0][0] + a[3][1] * b[1][0] + a[3][2] * b[2][0] + a[3][3] * b[3][0],
                a[3][0] * b[0][1] + a[3][1] * b[1][1] + a[3][2] * b[2][1] + a[3][3] * b[3][1],
                a[3][0] * b[0][2] + a[3][1] * b[1][2] + a[3][2] * b[2][2] + a[3][3] * b[3][2],
                a[3][0] * b[0][3] + a[3][1] * b[1][3] + a[3][2] * b[2][3] + a[3][3] * b[3][3],
            ],
        ])


# ==================================
# Camera and projection
# ==================================
class Camera:
    __slots__ = ("pos", "yaw", "pitch")

    def __init__(self):
        self.pos = Vector3(0.0, 1.0, -8.0)
        self.yaw = 0.0
        self.pitch = 0.0

    def view_matrix(self):
        rot = Mat4.rotation_x(-self.pitch) @ Mat4.rotation_y(-self.yaw)
        tr = Mat4.translation(Vector3(-self.pos.x, -self.pos.y, -self.pos.z))
        return rot @ tr


def build_projection(internal_w, internal_h, fov_deg):
    f = 1.0 / math.tan(math.radians(fov_deg) * 0.5)
    aspect = internal_w / internal_h
    return {
        "sx": internal_w * 0.5 * (f / aspect),
        "sy": internal_h * 0.5 * f,
        "cx": internal_w * 0.5,
        "cy": internal_h * 0.5,
    }


def project_to_screen(x, y, z, proj, near):
    if z <= near:
        return None
    inv_z = 1.0 / z
    sx = int(proj["cx"] + x * proj["sx"] * inv_z)
    sy = int(proj["cy"] - y * proj["sy"] * inv_z)
    return sx, sy, z


# ==================================
# Software triangle rasterizer
# ==================================
def edge(ax, ay, bx, by, px, py):
    return (px - ax) * (by - ay) - (py - ay) * (bx - ax)


def fog_mix(base_rgb, depth, fog_near, fog_far, fog_rgb):
    if fog_far <= fog_near:
        return fog_rgb
    t = (depth - fog_near) / (fog_far - fog_near)
    if t < 0.0:
        t = 0.0
    elif t > 1.0:
        t = 1.0
    return (
        int(base_rgb[0] * (1.0 - t) + fog_rgb[0] * t),
        int(base_rgb[1] * (1.0 - t) + fog_rgb[1] * t),
        int(base_rgb[2] * (1.0 - t) + fog_rgb[2] * t),
    )


def rasterize_triangle(px, zbuf, width, height, p0, p1, p2, color32):
    x0, y0, z0 = p0
    x1, y1, z1 = p1
    x2, y2, z2 = p2

    min_x = max(0, min(x0, x1, x2))
    max_x = min(width - 1, max(x0, x1, x2))
    min_y = max(0, min(y0, y1, y2))
    max_y = min(height - 1, max(y0, y1, y2))
    if min_x > max_x or min_y > max_y:
        return

    area = edge(x0, y0, x1, y1, x2, y2)
    if area == 0:
        return

    if area < 0:
        x1, y1, z1, x2, y2, z2 = x2, y2, z2, x1, y1, z1
        area = -area

    inv_area = 1.0 / area
    z0n = z0 * inv_area
    z1n = z1 * inv_area
    z2n = z2 * inv_area

    # Incremental edge stepping is faster than calling edge() per pixel.
    e0_dx = y2 - y1
    e0_dy = -(x2 - x1)
    e1_dx = y0 - y2
    e1_dy = -(x0 - x2)
    e2_dx = y1 - y0
    e2_dy = -(x1 - x0)

    w0_row = edge(x1, y1, x2, y2, min_x, min_y)
    w1_row = edge(x2, y2, x0, y0, min_x, min_y)
    w2_row = edge(x0, y0, x1, y1, min_x, min_y)

    for py_i in range(min_y, max_y + 1):
        w0 = w0_row
        w1 = w1_row
        w2 = w2_row
        idx = py_i * width + min_x

        for px_i in range(min_x, max_x + 1):
            if w0 >= 0 and w1 >= 0 and w2 >= 0:
                z = w0 * z0n + w1 * z1n + w2 * z2n
                if z < zbuf[idx]:
                    zbuf[idx] = z
                    px[px_i, py_i] = color32

            w0 += e0_dx
            w1 += e1_dx
            w2 += e2_dx
            idx += 1

        w0_row += e0_dy
        w1_row += e1_dy
        w2_row += e2_dy


# ==================================
# Clipping
# ==================================
def lerp_v(a, b, t):
    return (
        a[0] + (b[0] - a[0]) * t,
        a[1] + (b[1] - a[1]) * t,
        a[2] + (b[2] - a[2]) * t,
    )


def clip_triangle_near(v0, v1, v2, near):
    # Sutherland-Hodgman clipping against plane z = near.
    poly = [v0, v1, v2]
    out = []

    prev = poly[-1]
    prev_in = prev[2] > near

    for cur in poly:
        cur_in = cur[2] > near

        if cur_in != prev_in:
            denom = cur[2] - prev[2]
            if denom != 0.0:
                t = (near - prev[2]) / denom
                out.append(lerp_v(prev, cur, t))

        if cur_in:
            out.append(cur)

        prev = cur
        prev_in = cur_in

    if len(out) < 3:
        return []

    if len(out) == 3:
        return [(out[0], out[1], out[2])]

    # Convex quad from clipping -> 2 triangles.
    return [
        (out[0], out[1], out[2]),
        (out[0], out[2], out[3]),
    ]


# ==================================
# Mesh data and level
# ==================================
BOX_VERTS = [
    (-1.0, -1.0, -1.0), (1.0, -1.0, -1.0), (1.0, 1.0, -1.0), (-1.0, 1.0, -1.0),
    (-1.0, -1.0, 1.0), (1.0, -1.0, 1.0), (1.0, 1.0, 1.0), (-1.0, 1.0, 1.0),
]

BOX_TRIS = [
    (0, 1, 2), (0, 2, 3),
    (1, 5, 6), (1, 6, 2),
    (5, 4, 7), (5, 7, 6),
    (4, 0, 3), (4, 3, 7),
    (3, 2, 6), (3, 6, 7),
    (4, 5, 1), (4, 1, 0),
]

TRI_BASE_COLORS = [
    (126, 126, 146), (126, 126, 146),
    (112, 112, 132), (112, 112, 132),
    (98, 98, 118), (98, 98, 118),
    (90, 90, 108), (90, 90, 108),
    (78, 78, 95), (78, 78, 95),
    (66, 66, 82), (66, 66, 82),
]


def make_level():
    # (x, y, z, sx, sy, sz, tint)
    raw = [
        (0.0, -2.0, 10.0, 16.0, 0.6, 30.0, 1.00),
        (-16.0, 2.0, 10.0, 0.8, 4.6, 30.0, 0.95),
        (16.0, 2.0, 10.0, 0.8, 4.6, 30.0, 0.95),
        (0.0, 2.0, -20.0, 16.0, 4.6, 0.8, 0.92),
        (0.0, 2.0, 40.0, 16.0, 4.6, 0.8, 0.92),
        (0.0, -0.2, 4.0, 8.0, 0.3, 4.0, 0.85),
        (-10.0, -0.2, 20.0, 5.0, 0.3, 5.0, 0.85),
        (11.0, -0.2, 24.0, 4.0, 0.3, 6.0, 0.85),
        (-6.0, -1.1, 6.0, 1.5, 0.9, 1.5, 1.10),
        (5.0, -1.1, 11.0, 1.5, 0.9, 1.5, 1.10),
        (-3.0, -1.1, 18.0, 1.5, 0.9, 1.5, 1.10),
        (8.0, -1.1, 28.0, 1.8, 0.9, 1.8, 1.10),
        (-11.0, -1.1, 30.0, 1.8, 0.9, 1.8, 1.10),
    ]
    level = []
    for x, y, z, sx, sy, sz, tint in raw:
        radius = math.sqrt(sx * sx + sy * sy + sz * sz)
        level.append((Vector3(x, y, z), Vector3(sx, sy, sz), tint, radius))
    return level


def draw_box(
    surface,
    px,
    zbuf,
    view_m,
    box_pos,
    box_scale,
    tint,
    proj,
    near,
    fog_near,
    fog_far,
    fog_rgb,
    jitter_phase
):
    m = view_m.m
    m00, m01, m02, m03 = m[0]
    m10, m11, m12, m13 = m[1]
    m20, m21, m22, m23 = m[2]

    bx, by, bz = box_pos.x, box_pos.y, box_pos.z
    sx, sy, sz = box_scale.x, box_scale.y, box_scale.z

    # Transform local vertices directly by cached view matrix rows.
    cv = []
    for vx, vy, vz in BOX_VERTS:
        wx = bx + vx * sx
        wy = by + vy * sy
        wz = bz + vz * sz
        cv.append((
            wx * m00 + wy * m01 + wz * m02 + m03,
            wx * m10 + wy * m11 + wz * m12 + m13,
            wx * m20 + wy * m21 + wz * m22 + m23,
        ))

    width, height = surface.get_size()
    map_rgb = surface.map_rgb

    for tri_idx, (a, b, c) in enumerate(BOX_TRIS):
        ax, ay, az = cv[a]
        bxv, byv, bzv = cv[b]
        cx, cy, cz = cv[c]

        # Backface culling in camera space.
        abx, aby, abz = bxv - ax, byv - ay, bzv - az
        acx, acy, acz = cx - ax, cy - ay, cz - az
        nx = aby * acz - abz * acy
        ny = abz * acx - abx * acz
        nz = abx * acy - aby * acx
        if nx * ax + ny * ay + nz * az >= 0.0:
            continue

        clipped = clip_triangle_near((ax, ay, az), (bxv, byv, bzv), (cx, cy, cz), near)
        if not clipped:
            continue

        for ta, tb, tc in clipped:
            pa = project_to_screen(ta[0], ta[1], ta[2], proj, near)
            pb = project_to_screen(tb[0], tb[1], tb[2], proj, near)
            pc = project_to_screen(tc[0], tc[1], tc[2], proj, near)
            if not pa or not pb or not pc:
                continue

            # PS1-style integer-ish jitter in screen space.
            jx = ((tri_idx + jitter_phase) % 3) - 1
            jy = ((tri_idx * 2 + jitter_phase) % 3) - 1
            pa = (pa[0] + jx, pa[1] + jy, pa[2])
            pb = (pb[0] - jy, pb[1] + jx, pb[2])
            pc = (pc[0] + jy, pc[1] - jx, pc[2])

            tri_depth = (ta[2] + tb[2] + tc[2]) * (1.0 / 3.0)
            base = TRI_BASE_COLORS[tri_idx]
            color = fog_mix(
                (int(base[0] * tint), int(base[1] * tint), int(base[2] * tint)),
                tri_depth,
                fog_near,
                fog_far,
                fog_rgb,
            )
            color32 = map_rgb(color)

            rasterize_triangle(px, zbuf, width, height, pa, pb, pc, color32)


# ==================================
# Main loop
# ==================================
def main():
    pygame.init()

    INTERNAL_W, INTERNAL_H = 256, 192
    WINDOW_W, WINDOW_H = 1280, 720

    FOG_RGB = (10, 10, 14)
    FOG_NEAR = 8.0
    FOG_FAR = 42.0
    NEAR = 0.1

    screen = pygame.display.set_mode((WINDOW_W, WINDOW_H))
    pygame.display.set_caption("PS1 Software 3D Prototype")
    lowres = pygame.Surface((INTERNAL_W, INTERNAL_H)).convert()
    upscaled = pygame.Surface((WINDOW_W, WINDOW_H)).convert()

    pygame.mouse.set_visible(False)
    pygame.event.set_grab(True)
    pygame.event.set_allowed([pygame.QUIT, pygame.KEYDOWN, pygame.MOUSEMOTION])

    clock = pygame.time.Clock()
    camera = Camera()
    proj = build_projection(INTERNAL_W, INTERNAL_H, 72.0)
    running = True
    jitter_phase = 0

    level = make_level()
    max_visible_boxes = 18

    zbuf_size = INTERNAL_W * INTERNAL_H
    inf = float("inf")
    zbuf = [inf] * zbuf_size
    zclear = [inf] * zbuf_size

    while running:
        dt = clock.tick(45) / 1000.0
        jitter_phase = (jitter_phase + 1) % 60

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                running = False
            elif event.type == pygame.MOUSEMOTION:
                mx, my = event.rel
                camera.yaw += mx * 0.0032
                camera.pitch += my * 0.0032
                if camera.pitch > 1.35:
                    camera.pitch = 1.35
                elif camera.pitch < -1.35:
                    camera.pitch = -1.35

        keys = pygame.key.get_pressed()
        speed = 5.2 * dt
        sin_y = math.sin(camera.yaw)
        cos_y = math.cos(camera.yaw)
        fx, fz = sin_y, cos_y
        rx, rz = cos_y, -sin_y

        if keys[pygame.K_w]:
            camera.pos.x += fx * speed
            camera.pos.z += fz * speed
        if keys[pygame.K_s]:
            camera.pos.x -= fx * speed
            camera.pos.z -= fz * speed
        if keys[pygame.K_a]:
            camera.pos.x -= rx * speed
            camera.pos.z -= rz * speed
        if keys[pygame.K_d]:
            camera.pos.x += rx * speed
            camera.pos.z += rz * speed
        if keys[pygame.K_SPACE]:
            camera.pos.y += speed
        if keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]:
            camera.pos.y -= speed

        lowres.fill(FOG_RGB)
        zbuf[:] = zclear
        px = pygame.PixelArray(lowres)
        view = camera.view_matrix()

        # Fast object culling first, then render nearest set.
        vm = view.m
        visible = []
        for box_pos, box_scale, tint, radius in level:
            cx = box_pos.x * vm[0][0] + box_pos.y * vm[0][1] + box_pos.z * vm[0][2] + vm[0][3]
            cy = box_pos.x * vm[1][0] + box_pos.y * vm[1][1] + box_pos.z * vm[1][2] + vm[1][3]
            cz = box_pos.x * vm[2][0] + box_pos.y * vm[2][1] + box_pos.z * vm[2][2] + vm[2][3]

            if cz + radius <= NEAR:
                continue
            if cz - radius > FOG_FAR + 18.0:
                continue

            zref = max(cz, NEAR)
            if abs(cx) > zref * 2.1 + radius + 8.0:
                continue
            if abs(cy) > zref * 1.7 + radius + 8.0:
                continue

            visible.append((cz, box_pos, box_scale, tint))

        visible.sort(key=lambda item: item[0])

        rendered = 0
        for _, box_pos, box_scale, tint in visible:
            draw_box(
                lowres,
                px,
                zbuf,
                view,
                box_pos,
                box_scale,
                tint,
                proj,
                NEAR,
                FOG_NEAR,
                FOG_FAR,
                FOG_RGB,
                jitter_phase,
            )
            rendered += 1
            if rendered >= max_visible_boxes:
                break

        del px

        pygame.transform.scale(lowres, (WINDOW_W, WINDOW_H), upscaled)
        screen.blit(upscaled, (0, 0))
        pygame.display.set_caption(f"PS1 Software 3D Prototype | FPS: {int(clock.get_fps())}")
        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()