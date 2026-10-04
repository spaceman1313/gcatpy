"""Internal: the local data root where gcatpy stores files on the user's machine.

Covers locating the root, describing its layout, and the file operations that
keep the download cache consistent. Nothing here is public; user-facing entry
points are re-exported from the top-level `gcatpy` package.
"""
