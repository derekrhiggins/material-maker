## validation.gd — Shared validation helpers for Material Maker MCP commands
##
## Centralises path and node_id validation to avoid duplication across
## command handler modules.
##
## Written for Godot 4.x.

extends RefCounted


## Validate that a file path is safe for writing/reading.
## Uses an allowlist approach: only permits paths under the user's home
## directory or relative paths (which resolve within the working directory).
## Rejects path traversal sequences in all cases.
static func validate_path(path: String) -> String:
	# Reject path traversal sequences.
	if ".." in path:
		return "Path contains '..' traversal and is not allowed."

	var normalized: String = path.replace("\\", "/")

	# Allow relative paths (no leading slash or drive letter).
	if not normalized.begins_with("/") and not (normalized.length() >= 2 and normalized[1] == ":"):
		return ""

	# Absolute paths: only allow under the user's home directory.
	var home_dir: String = OS.get_environment("HOME")
	if home_dir.is_empty():
		home_dir = OS.get_environment("USERPROFILE")  # Windows fallback
	if home_dir.is_empty():
		return "Cannot determine home directory. Use a relative path instead."

	home_dir = home_dir.replace("\\", "/")
	if not home_dir.ends_with("/"):
		home_dir += "/"

	if not normalized.begins_with(home_dir) and normalized != home_dir.trim_suffix("/"):
		return "Absolute paths must be under the user's home directory (%s)." % home_dir

	return ""


## Validate that a node_id is a plain name with no path separators.
## Prevents NodePath injection (e.g. "../../mm_globals").
static func validate_node_id(node_id: String) -> String:
	if node_id.is_empty():
		return "node_id must not be empty."
	if "/" in node_id or "\\" in node_id or ".." in node_id:
		return "node_id must be a plain name (no '/', '\\', or '..' allowed)."
	return ""
