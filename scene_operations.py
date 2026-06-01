from __future__ import annotations

from typing import Any


SAVE_OPERATION_WARNINGS = {
    "save_png": "save_png is handled by the API response contract and the render job.",
    "save_pse": "save_pse is handled by export_session and the render job.",
    "save_pml": "save_pml is handled by export_script and the render job.",
}


def apply_scene_operations(
    cmd: Any,
    operations: list[dict[str, Any]] | None,
    *,
    object_name: str = "structure",
) -> list[str]:
    warnings: list[str] = []
    for operation in operations or []:
        warnings.extend(_apply_scene_operation(cmd, operation, object_name=object_name))
    return warnings


def scene_operation_lines(
    operations: list[dict[str, Any]] | None,
    *,
    object_name: str = "structure",
) -> tuple[list[str], list[str]]:
    lines: list[str] = []
    warnings: list[str] = []
    for operation in operations or []:
        op_lines, op_warnings = _scene_operation_lines(operation, object_name=object_name)
        lines.extend(op_lines)
        warnings.extend(op_warnings)
    return lines, warnings


def _apply_scene_operation(cmd: Any, operation: dict[str, Any], *, object_name: str) -> list[str]:
    action = str(operation.get("action") or "").strip()
    warnings: list[str] = []
    selection = str(operation.get("selection") or "all")
    target = str(operation.get("target") or "")
    representation = str(operation.get("representation") or "")
    color = str(operation.get("color") or "")
    text = str(operation.get("text") or "")
    buffer_value = float(operation.get("buffer") or 4.0)
    value = float(operation.get("value") or 0.0)

    if action == "show" and representation:
        cmd.show(representation, selection)
    elif action == "hide":
        cmd.hide(target or "everything", selection)
    elif action == "color" and color:
        color_name = _apply_color(cmd, color)
        cmd.color(color_name, selection)
    elif action == "remove":
        cmd.remove(selection)
    elif action == "select":
        name = str(operation.get("name") or "selection")
        cmd.select(name, selection)
    elif action == "label":
        cmd.label(selection, _label_expression(text))
    elif action == "zoom":
        cmd.zoom(selection, buffer=buffer_value)
    elif action == "orient":
        cmd.orient(selection)
    elif action == "center":
        cmd.center(selection)
    elif action == "set_representation" and representation:
        cmd.show(representation, selection)
    elif action == "set_background" and color:
        cmd.bg_color(_apply_color(cmd, color))
    elif action == "set_transparency":
        if selection and selection != "all":
            cmd.set("transparency", value, selection)
        else:
            cmd.set("transparency", value)
    elif action in SAVE_OPERATION_WARNINGS:
        warnings.append(SAVE_OPERATION_WARNINGS[action])
    else:
        raise ValueError(f"Unsupported scene operation: {action}")
    return warnings


def _scene_operation_lines(operation: dict[str, Any], *, object_name: str) -> tuple[list[str], list[str]]:
    action = str(operation.get("action") or "").strip()
    warnings: list[str] = []
    selection = str(operation.get("selection") or "all")
    target = str(operation.get("target") or "")
    representation = str(operation.get("representation") or "")
    color = str(operation.get("color") or "")
    text = str(operation.get("text") or "")
    buffer_value = float(operation.get("buffer") or 4.0)
    value = float(operation.get("value") or 0.0)

    if action == "show" and representation:
        return [f"show {representation}, {selection}"], warnings
    if action == "hide":
        return [f"hide {target or 'everything'}, {selection}"], warnings
    if action == "color" and color:
        lines = _color_lines(color, selection)
        return lines, warnings
    if action == "remove":
        return [f"remove {selection}"], warnings
    if action == "select":
        name = str(operation.get("name") or "selection")
        return [f"select {name}, {selection}"], warnings
    if action == "label":
        return [f"label {selection}, {_label_expression(text)}"], warnings
    if action == "zoom":
        return [f"zoom {selection}, {buffer_value:g}"], warnings
    if action == "orient":
        return [f"orient {selection}"], warnings
    if action == "center":
        return [f"center {selection}"], warnings
    if action == "set_representation" and representation:
        return [f"show {representation}, {selection}"], warnings
    if action == "set_background" and color:
        text = color.strip()
        if text.startswith("#") and len(text) == 7:
            name = _color_reference(text)
            red = int(text[1:3], 16) / 255
            green = int(text[3:5], 16) / 255
            blue = int(text[5:7], 16) / 255
            return [f"set_color {name}, [{red:.3f}, {green:.3f}, {blue:.3f}]", f"bg_color {name}"], warnings
        return [f"bg_color {text}"], warnings
    if action == "set_transparency":
        if selection and selection != "all":
            return [f"set transparency, {value:.3f}, {selection}"], warnings
        return [f"set transparency, {value:.3f}"], warnings
    if action in SAVE_OPERATION_WARNINGS:
        warnings.append(SAVE_OPERATION_WARNINGS[action])
        return [f"# {SAVE_OPERATION_WARNINGS[action]}"], warnings
    raise ValueError(f"Unsupported scene operation: {action}")


def _label_expression(text: str) -> str:
    if _looks_like_pymol_label_expression(text):
        return text
    return repr(text)


def _apply_color(cmd: Any, color: str) -> str:
    text = color.strip()
    if text.startswith("#") and len(text) == 7:
        name = f"api_color_{text[1:].lower()}"
        red = int(text[1:3], 16) / 255
        green = int(text[3:5], 16) / 255
        blue = int(text[5:7], 16) / 255
        cmd.set_color(name, [red, green, blue])
        return name
    return text


def _color_reference(color: str) -> str:
    text = color.strip()
    if text.startswith("#") and len(text) == 7:
        return f"api_color_{text[1:].lower()}"
    return text


def _color_lines(color: str, selection: str) -> list[str]:
    text = color.strip()
    if text.startswith("#") and len(text) == 7:
        name = _color_reference(text)
        red = int(text[1:3], 16) / 255
        green = int(text[3:5], 16) / 255
        blue = int(text[5:7], 16) / 255
        return [f"set_color {name}, [{red:.3f}, {green:.3f}, {blue:.3f}]", f"color {name}, {selection}"]
    return [f"color {text}, {selection}"]


def _looks_like_pymol_label_expression(value: str) -> bool:
    allowed = {"name", "resn", "resi", "chain", "segi", "elem", "oneletter"}
    tokens = {
        token.strip()
        for token in value.replace("+", " ").replace("'", " ").replace('"', " ").split()
        if token.strip()
    }
    return bool(tokens) and tokens.issubset(allowed)
