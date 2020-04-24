import bpy

class UndoChanges:
    def __enter__(self):
        bpy.ops.ed.undo_push(message="before")

    def __exit__(self, exc_type, exc_value, traceback):
        bpy.ops.ed.undo_push(message="after")
        bpy.ops.ed.undo()
