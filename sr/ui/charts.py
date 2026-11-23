"""簡單圖表（Flet 畫布）：分數折線圖、橫條圖。"""
import flet as ft
import flet.canvas as cv

from . import theme as T


def line_chart(values, labels, width=560, height=220, pass_line=None, top=100):
    pl, pr, pt, pb = 36, 14, 14, 26
    w, h = width - pl - pr, height - pt - pb
    n = len(values)
    shapes = []
    for k in range(0, 101, 20):
        y = pt + h - h * k / top
        shapes.append(cv.Line(pl, y, pl + w, y, paint=ft.Paint(color="#E5E9F0", stroke_width=1)))
        shapes.append(cv.Text(pl - 6, y, str(k), style=ft.TextStyle(size=10, color=T.MUTED),
                              alignment=ft.Alignment.CENTER_RIGHT))
    if pass_line is not None:
        y = pt + h - h * pass_line / top
        shapes.append(cv.Line(pl, y, pl + w, y, paint=ft.Paint(color="#F59E0B", stroke_width=1.5,
                                                               stroke_dash_pattern=[6, 4])))
        shapes.append(cv.Text(pl + w, y - 2, "及格 %d" % pass_line, style=ft.TextStyle(size=10, color="#B45309"),
                              alignment=ft.Alignment.BOTTOM_RIGHT))
    pts = []
    for i, v in enumerate(values):
        x = pl + (w * (i + 0.5) / n if n else 0)
        y = pt + h - h * max(0, min(top, v)) / top
        pts.append((x, y))
    if len(pts) > 1:
        el = [cv.Path.MoveTo(*pts[0])] + [cv.Path.LineTo(x, y) for x, y in pts[1:]]
        shapes.append(cv.Path(el, paint=ft.Paint(color=T.ACCENT, stroke_width=2.5, style=ft.PaintingStyle.STROKE)))
    for i, (x, y) in enumerate(pts):
        shapes.append(cv.Circle(x, y, 4.5, paint=ft.Paint(color=T.PRIMARY)))
        shapes.append(cv.Text(x, y - 7, "%g" % values[i], style=ft.TextStyle(size=10, color=T.TEXT,
                                                                           weight=ft.FontWeight.W_600),
                              alignment=ft.Alignment.BOTTOM_CENTER))
        if i < len(labels) and (n <= 12 or i % max(1, n // 10) == 0):
            shapes.append(cv.Text(x, pt + h + 6, labels[i], style=ft.TextStyle(size=10, color=T.MUTED),
                                  alignment=ft.Alignment.TOP_CENTER))
    return cv.Canvas(shapes=shapes, width=width, height=height)


def bars(items, width=300, tone=T.ACCENT, suffix="%"):
    """items=[(名稱, 數值 0～100, 附註)]"""
    return ft.Column([ft.Row([ft.Text(n, size=13, width=120, max_lines=1),
                              ft.Container(ft.Container(bgcolor=tone, width=max(2, width * v / 100), height=10,
                                                        border_radius=5), width=width + 4),
                              ft.Text("%g%s" % (v, suffix), size=13, weight=ft.FontWeight.W_700),
                              T.muted(note, 11)], spacing=8) for n, v, note in items], spacing=8)
