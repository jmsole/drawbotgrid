import drawBot as db
from .grid import ColumnGrid
import math

# ----------------------------------------

_textbox_funct = db.textBox


def set_text_overflow_test_mode(bool_):
    global _textbox_funct
    if bool_ == False:
        _textbox_funct = db.textBox
    else:
        _textbox_funct = db.textOverflow


textOverflowTestMode = set_text_overflow_test_mode

# ----------------------------------------


def baseline_grid_textBox(
    txt,
    box,
    baseline_grid,
    align_first_line_only=False,
    align="left",
    vertical_align="top",
    direction="ltr",
):

    assert vertical_align in ("top", "bottom", "center")

    # Set default text alignment based on direction
    if direction == "rtl" and align == "left":
        align = "right"

    with db.savedState():
        box = correct_box_direction(box)

        x, y, w, h = box

        if not align_first_line_only:
            actual_line_height = db.fontLineHeight()
            target_line_height = (
                math.ceil(actual_line_height / baseline_grid.line_height)
                * baseline_grid.line_height
            )
            set_metric_baseline_height(target_line_height)

        absolute_cap_height = db.fontCapHeight()

        if vertical_align == "top":
            first_line_y = db.textBoxBaselines(txt, box)[0][1]
            current_cap_y = first_line_y + absolute_cap_height
            cap_distance_from_top = y + h - current_cap_y

            highest_possible_first_line = first_line_y + cap_distance_from_top
            target_line = baseline_grid.closest_line_below_coordinate(
                highest_possible_first_line
            )

            shift = target_line - first_line_y

        elif vertical_align == "bottom":
            last_line_y = db.textBoxBaselines(txt, box)[-1][1]
            target_line = baseline_grid.closest_line_above_coordinate(y)
            shift = target_line - last_line_y

        elif vertical_align == "center":
            # maybe there is more refined solution here
            lines = db.textBoxBaselines(txt, box)
            mid_line_index = int(len(lines) / 2)
            mid_line_y = lines[mid_line_index][1]
            target_line = baseline_grid.closest_line_below_coordinate(
                y + h / 2 - absolute_cap_height / 2
            )
            shift = target_line - mid_line_y

        overflow = _textbox_funct(txt, (x, y + shift, w, h), align=align)
        return overflow


baselineGridTextBox = baseline_grid_textBox

# ----------------------------------------


def column_textBox(
    txt, box, subdivisions=2, gutter=10, align="left", draw_grid=False, direction="ltr"
):
    return _column_textBox_base(
        txt,
        box,
        baseline_grid=None,
        align_first_line_only=False,
        subdivisions=subdivisions,
        gutter=gutter,
        align=align,
        draw_grid=draw_grid,
        direction=direction,
    )


columnTextBox = column_textBox


def column_baseline_grid_textBox(
    txt,
    box,
    baseline_grid,
    align_first_line_only=False,
    subdivisions=2,
    gutter=10,
    align="left",
    draw_grid=False,
    direction="ltr",
):
    return _column_textBox_base(
        txt,
        box,
        baseline_grid,
        align_first_line_only=align_first_line_only,
        subdivisions=subdivisions,
        gutter=gutter,
        align=align,
        draw_grid=draw_grid,
        direction=direction,
    )


columnBaselineGridTextBox = column_baseline_grid_textBox


def _column_textBox_base(
    txt,
    box,
    baseline_grid=None,
    align_first_line_only=False,
    subdivisions=2,
    gutter=10,
    align="left",
    draw_grid=False,
    direction="ltr",
):

    columns = ColumnGrid(
        box, subdivisions=subdivisions, gutter=gutter, direction=direction
    )
    overflow = txt

    # Set default text alignment based on direction
    # If align wasn't explicitly set to something other than "left",
    # use "right" alignment for RTL direction
    if direction == "rtl" and align == "left":
        align = "right"

    # Get column indices based on direction
    if direction == "rtl":
        # For RTL, we want to fill columns from right to left (0, 1, 2, ...)
        # but the visual order is right to left
        column_indices = range(subdivisions)
    else:
        # For LTR, normal left to right order
        column_indices = range(subdivisions)

    for col_index in column_indices:
        if len(overflow) > 0:
            # In RTL mode, we need to adjust the x position
            # columns[col_index] already gives the right edge of the column in RTL mode
            # (see grid.py AbstractGutterGrid.__getitem__)
            if direction == "rtl":
                # For RTL, columns[col_index] returns the right edge
                # We need to position the textbox so its right edge aligns with column's right edge
                # So we need to subtract the column width to get the left edge of the text box
                col_right_edge = columns[col_index]
                col_x = col_right_edge - columns.column_width
                sub_box = (col_x, columns.bottom, columns.column_width, columns.height)
            else:
                # For LTR, columns[col_index] returns the left edge, so use as-is
                col = columns[col_index]
                sub_box = (col, columns.bottom, columns.column_width, columns.height)

            if baseline_grid:
                overflow = baseline_grid_textBox(
                    overflow, sub_box, baseline_grid, align=align, direction=direction
                )
            else:
                overflow = _textbox_funct(overflow, sub_box, align=align)

    if draw_grid:
        grid_color = (0.5, 0, 0.8, 1)
        with db.savedState():
            db.strokeWidth(0.5)

            # Draw the overall box
            db.fill(None)
            db.stroke(*grid_color)
            db.rect(*box)

            # Draw column separators - properly handle RTL and LTR
            for i in range(subdivisions):
                if direction == "rtl":
                    # In RTL mode, columns[i] gives the right edge
                    col_right = columns[i]
                    col_left = col_right - columns.column_width

                    # Draw the column boundaries
                    db.fill(None)
                    db.stroke(*grid_color)
                    db.line(
                        (col_left, columns.bottom), (col_left, columns.top)
                    )  # Left edge
                    db.line(
                        (col_right, columns.bottom), (col_right, columns.top)
                    )  # Right edge
                else:
                    # In LTR mode, columns[i] gives the left edge
                    col_left = columns[i]
                    col_right = col_left + columns.column_width

                    # Draw the column boundaries
                    db.fill(None)
                    db.stroke(*grid_color)
                    db.line(
                        (col_left, columns.bottom), (col_left, columns.top)
                    )  # Left edge
                    db.line(
                        (col_right, columns.bottom), (col_right, columns.top)
                    )  # Right edge

    return overflow


# ----------------------------------------


def _get_text_flow_path(xy1, xy2):
    x_1, y_1 = xy1
    x_2, y_2 = xy2
    off_curve_length = 100
    text_flow_path = db.BezierPath()
    text_flow_path.moveTo((x_1, y_1))
    text_flow_path.curveTo(
        (x_1 + off_curve_length, y_1), (x_2 - off_curve_length, y_2), (x_2, y_2)
    )
    return text_flow_path


def _draw_point(xy, radius=2):
    x, y = xy
    db.oval(x - radius, y - radius, radius * 2, radius * 2)


# ----------------------------------------


def vertical_align_textBox(txt, box, align=None, vertical_align="top", direction="ltr"):

    assert vertical_align in ("top", "bottom", "center")

    # Set default text alignment based on direction
    if direction == "rtl" and (align is None or align == "left"):
        align = "right"

    x, y, w, h = correct_box_direction(box)

    absolute_cap_height = db.fontCapHeight()

    if vertical_align == "top":
        first_line_y = db.textBoxBaselines(txt, box)[0][1]
        current_cap_y = first_line_y + absolute_cap_height
        cap_distance_from_top = y + h - current_cap_y
        highest_possible_first_line = first_line_y + cap_distance_from_top
        target_line = y + h - absolute_cap_height
        shift = target_line - first_line_y

    elif vertical_align == "bottom":
        last_line_y = db.textBoxBaselines(txt, box)[-1][1]
        target_line = y
        shift = target_line - last_line_y

    elif vertical_align == "center":
        # maybe there is more refined solution here
        lines = db.textBoxBaselines(txt, box)

        top = lines[0][1] + absolute_cap_height
        bottom = lines[-1][1]
        text_h = top - bottom
        margin = (h - text_h) / 2
        shift = y + margin - bottom

    box = (x, y + shift, w, h)
    overflow = _textbox_funct(txt, box, align=align)
    return overflow


verticalAlignTextBox = vertical_align_textBox


# ----------------------------------------


def set_metric_baseline_height(baseline_height):
    # this seems to be necessary only for fonts with unusual vertical metrics
    line_height = _get_line_height_from_desired_baseline_height(baseline_height)
    db.lineHeight(line_height)
    return line_height


baselineHeight = set_metric_baseline_height


def _get_line_height_from_desired_baseline_height(baseline_height):
    with db.savedState():
        txt = "H\nH"
        db.lineHeight(baseline_height)
        # should calculate appropriate size here
        lines = db.textBoxBaselines(txt, (0, 0, 10000, 10000))
        line_dist = lines[0][1] - lines[1][1]
        target_line_dist = baseline_height
        required_line_dist = target_line_dist - line_dist + target_line_dist
    return required_line_dist


# ----------------------------------------


def correct_box_direction(box):
    x, y, w, h = box
    if h < 0:
        y = y + h
        h = h * -1
    return (x, y, w, h)


# ----------------------------------------

# def image_at_size(path, box, preserve_proprotions=True):
#     """
#     this could do a lot more.
#     Things like cropping the image,
#     aligning it somewhere esle that bottom, left...
#     """
#     x, y, w, h = box
#     actual_w, actual_h = db.imageSize(path)
#     if not w:
#         scale_ratio_w = h / actual_h
#         scale_ratio_h = h / actual_h
#     elif not h:
#         scale_ratio_w = w / actual_w
#         scale_ratio_h = w / actual_w
#     else:
#         scale_ratio_w = w / actual_w
#         scale_ratio_h = h / actual_h

#         if preserve_proprotions:
#             scale_ratio = min(scale_ratio_w, scale_ratio_h)
#             scale_ratio_w = scale_ratio
#             scale_ratio_h = scale_ratio

#     with db.savedState():
#         db.translate(x, y)
#         db.scale(scale_ratio_w, scale_ratio_h)
#         db.image(path, (0, 0))
