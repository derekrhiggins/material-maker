## preview.gd — Preview image capture command handlers for Material Maker MCP
##
## Handles commands: get_preview_image, get_3d_preview
##
## Written for Godot 4.x / Material Maker 1.4+.

extends RefCounted

const Validation = preload("res://addons/material_maker_mcp/commands/validation.gd")

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

## Minimum allowed preview size in pixels.
const MIN_SIZE: int = 16

## Maximum allowed preview size in pixels.
const MAX_SIZE: int = 2048

# ---------------------------------------------------------------------------
# State
# ---------------------------------------------------------------------------

## Reference to Material Maker's MainWindow Control. Set via init().
var _main_window = null

# ---------------------------------------------------------------------------
# Initialisation
# ---------------------------------------------------------------------------

## Called by addon.gd after construction to inject the MM main window reference.
func init(main_window) -> void:
	_main_window = main_window

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

## Return the currently active MMGraphEdit from the main window.
func _get_graph_edit():
	if _main_window == null:
		return null
	return _main_window.get_current_graph_edit()


## Clamp a size value to the allowed range.
func _clamp_size(size: int) -> int:
	return clampi(size, MIN_SIZE, MAX_SIZE)


## Construct a standardised error dictionary.
func _error(msg: String) -> Dictionary:
	return { "error": true, "message": msg }


# ---------------------------------------------------------------------------
# Command: get_preview_image
# ---------------------------------------------------------------------------

## Render a node's output to a PNG image and return it as base64.
##
## Params:
##   node_id      : String (required) — the generator's name in the graph
##   output_index : int    (optional, default 0) — which output port to render
##   size         : int    (optional, default 512) — render resolution in pixels
##
## Returns: { image: base64_string, format: "png", size: int, node_id: String }
func get_preview_image(params: Dictionary):
	var node_id: String = params.get("node_id", "")
	var id_err: String = Validation.validate_node_id(node_id)
	if not id_err.is_empty():
		return _error(id_err)

	var output_index: int = int(params.get("output_index", 0))
	var size: int = _clamp_size(int(params.get("size", 512)))

	var graph_edit = _get_graph_edit()
	if graph_edit == null:
		return _error("No active graph. Is a project open in Material Maker?")

	var graph = graph_edit.top_generator
	if graph == null:
		return _error("No top-level generator found in the current graph.")

	# Find the node by its name among the graph's children.
	var generator = graph.get_node_or_null(NodePath(node_id))
	if generator == null:
		return _error("Node '%s' not found in the current graph." % node_id)

	# Render the output to a texture (async).
	var mm_texture = await generator.render_output_to_texture(output_index, Vector2i(size, size))
	if mm_texture == null:
		return _error("render_output_to_texture returned null for node '%s' output %d." % [node_id, output_index])

	# Get the Texture2D from the MMTexture (async).
	var texture_2d: Texture2D = await mm_texture.get_texture()
	if texture_2d == null:
		return _error("Failed to get Texture2D from rendered output for node '%s'." % node_id)

	var image: Image = texture_2d.get_image()
	if image == null:
		return _error("Failed to get Image from rendered texture for node '%s'." % node_id)

	# Convert to RGBA8 for consistent PNG output.
	if image.get_format() != Image.FORMAT_RGBA8:
		image.convert(Image.FORMAT_RGBA8)

	# Encode as PNG and convert to base64.
	var png_bytes: PackedByteArray = image.save_png_to_buffer()
	if png_bytes.is_empty():
		return _error("Failed to encode image as PNG for node '%s'." % node_id)

	var base64_string: String = Marshalls.raw_to_base64(png_bytes)

	return {
		"image": base64_string,
		"format": "png",
		"size": size,
		"node_id": node_id,
	}


# ---------------------------------------------------------------------------
# Command: get_3d_preview
# ---------------------------------------------------------------------------

## Capture the 3D preview viewport and return it as a base64 PNG.
##
## Params:
##   size : int (optional, default 512) — output image size in pixels
##
## Returns: { image: base64_string, format: "png", size: int }
func get_3d_preview(params: Dictionary):
	var size: int = _clamp_size(int(params.get("size", 512)))

	if _main_window == null:
		return _error("Main window reference not set.")

	# Access the 3D preview panel. MainWindow stores it as preview_3d.
	var preview_3d = _main_window.preview_3d
	if preview_3d == null:
		return _error("3D preview panel not found.")

	# The preview_3d panel is a SubViewportContainer with a SubViewport child
	# named "MaterialPreview".
	var viewport: SubViewport = preview_3d.get_node_or_null("MaterialPreview")
	if viewport == null:
		return _error("MaterialPreview SubViewport not found in the 3D preview panel.")

	# Capture the viewport's current texture as an Image.
	var viewport_texture: ViewportTexture = viewport.get_texture()
	if viewport_texture == null:
		return _error("Failed to get texture from 3D preview viewport.")

	var image: Image = viewport_texture.get_image()
	if image == null:
		return _error("Failed to get image from 3D preview viewport texture.")

	# Resize to the requested size if it differs from the viewport size.
	if image.get_width() != size or image.get_height() != size:
		image.resize(size, size)

	# Convert to RGBA8 for consistent PNG output.
	if image.get_format() != Image.FORMAT_RGBA8:
		image.convert(Image.FORMAT_RGBA8)

	# Encode as PNG and convert to base64.
	var png_bytes: PackedByteArray = image.save_png_to_buffer()
	if png_bytes.is_empty():
		return _error("Failed to encode 3D preview image as PNG.")

	var base64_string: String = Marshalls.raw_to_base64(png_bytes)

	return {
		"image": base64_string,
		"format": "png",
		"size": size,
	}
