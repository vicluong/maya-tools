"""Duplicate a selected object a around a point so that they all touch

When selecting two vertices that are on the opposite ends of a mesh but along
the same axis, the main function of this file can duplicate the mesh of the 
vertices a given number of times in way so that they are just touching each
other. You can optionally connect these duplicates together to form one object.

duplicate_around_point is the main function to use.
"""
import math

import maya.cmds as cmds

def duplicate_around_point(amount: int, axis: str, centre_dir: str, 
                           merge: bool) -> None:
    """Duplicate a selected object a around a point so that they all touch

    Args:
        amount: Amount of times the selected_obj needs to be duplicated around 
            the pivot
        axis: Axis to be rotated around
        centre_dir: What direction the pivot should move towards
        merge_thres: Merge threshold for merging the duplicated objects into 
            one object
    """
    obj_name, vert1, vert2 = verify_selection(amount, axis, centre_dir, merge)
    
    set_new_pivot(obj_name, vert1, vert2, amount, axis, centre_dir)
    
    selected_objs = duplicate_and_rotate_object(obj_name, amount, axis)
    
    # Connect and merge the objects together given the merge threshold
    if merge:
        combined_obj = cmds.polyUnite(selected_objs, cp=True)[0]
        cmds.polyMergeVertex(combined_obj, d=0.01)
        cmds.delete(combined_obj, ch=True)
        new_name = cmds.rename(combined_obj, f"{obj_name}_around")
        cmds.select(new_name, r=True)
    else:
        cmds.select(selected_objs, r=True)


def verify_selection(amount: int, axis: str, centre_dir: str, 
                     merge: bool) ->  tuple[str, str, str]:
    """Verify given inputs are correct

    Args:
        amount: Amount of times the selected_obj needs to be duplicated around 
            the pivot
        axis: Axis to be rotated around
        centre_dir: What direction the pivot should move towards
        merge_thres: Merge threshold for merging the duplicated objects into 
            one object

    Raises:
        RuntimeError: Two vertices need to be selected
        RuntimeError: Selected vertices must be from one object
        ValueError: Amount must be an integer of 3 or larger
        ValueError: Incorrect axis provided
        ValueError: Incorrect centre position direction provided
        ValueError: Merge must be a bool value

    Returns:
        Tuple containing the selected object, then the two selected vertices as 
        separate items
    """
    # Filters selections to vertices
    selected_verts = cmds.filterExpand(sm=31)

    if not selected_verts or len(selected_verts) != 2:
        raise RuntimeError("Two vertices must be selected.")
    
    selected_obj1 = selected_verts[0].split(".vtx")[0]
    selected_obj2 = selected_verts[1].split(".vtx")[0]

    if selected_obj1 != selected_obj2:
        raise RuntimeError("Selected vertices must be from one object.")
    else:
        selection = (selected_obj1, selected_verts[0], selected_verts[1])

    if not isinstance(amount, int) or amount < 3:
        raise ValueError("Amount must be an integer of 3 or larger.")
    elif axis not in ("x", "y", "z"):
        raise ValueError("Incorrect axis provided.")
    elif (len(centre_dir) != 2 or not centre_dir[0] in ("+", "-") or
          not centre_dir[1] in ("x", "y", "z")):
        raise ValueError("Incorrect centre position direction provided.")
    elif not isinstance(merge, bool):
        raise ValueError("Merge must be a bool value.")

    return selection


def set_new_pivot(obj_name: str, vert1: str, vert2: str, amount: int, axis: str, 
                  centre_direction: str) -> None:
    """Set a new pivot that is optimal for duplicating the selected object around a point

    Args:
        obj_name: Name of the object where the verts are selected
        vert1: Name of first vertex selected
        vert2: Name of second vertex selected
        amount: Amount of times the selected object needs to be duplicated 
            around the pivot
        axis: Axis to be rotated around
        centre_direction: What direction the pivot should move towards
    """
    bbox_verts = cmds.xform([vert1, vert2], q=True, t=True) # type: ignore
    obj_length = 0

    if "x" not in axis and "x" not in centre_direction:
        obj_length = abs(bbox_verts[3] - bbox_verts[0])
    elif "y" not in axis and "y" not in centre_direction:
        obj_length = abs(bbox_verts[4] - bbox_verts[1])
    elif "z" not in axis and "z" not in centre_direction:
        obj_length = abs(bbox_verts[5] - bbox_verts[2])

    centre_pivot(obj_name, vert1, vert2, axis, centre_direction)
    
    pivot_distance = calculate_pivot_distance(amount, obj_length)
    
    move_pivot(obj_name, pivot_distance, centre_direction)


def centre_pivot(obj_name: str, vert1: str, vert2: str, axis: str, centre_direction: str) -> None:
    """Centre the pivot along the length of the selected object

    To ensure that the pivot is placed towards the centre of the intended new 
    selected_obj, the pivot first needs to be centred along the axis of its length.

    Args:
        obj_name: Name of the object where the verts are selected
        vert1: Name of first vertex selected
        vert2: Name of second vertex selected
        axis: Axis to be rotated around
        centre_direction: What direction the pivot should move towards
    """

    # Use the axis not specified by the user to centre the pivot along
    if "x" not in axis and "x" not in centre_direction:
        centre_pivot_on_axis(obj_name, vert1, vert2, 0)
    elif "y" not in axis and "y" not in centre_direction:
        centre_pivot_on_axis(obj_name, vert1, vert2, 1)
    elif "z" not in axis and "z" not in centre_direction:
        centre_pivot_on_axis(obj_name, vert1, vert2, 2)


def centre_pivot_on_axis(obj_name: str, vert1: str, vert2: str, axis_num: int) -> None:
    """Centre the pivot along a specific axis given

    Args:
        obj_name: Name of the object where the verts are selected
        vert1: Name of first vertex selected
        vert2: Name of second vertex selected
        axis_num: Int describing what axis to centre along with x=0, y=1, z=2 
            based on the array the bounding box provides
    """
    bbox_verts = cmds.xform([vert1, vert2], q=True, t=True, ws=True) # type: ignore

    centre = (bbox_verts[axis_num + 3] + bbox_verts[axis_num]) / 2

    vert_axis_pos = [bbox_verts[0], bbox_verts[1], bbox_verts[2]]
    vert_axis_pos[axis_num] = centre

    cmds.xform(obj_name, ws=True, rp=vert_axis_pos)
    cmds.xform(obj_name, ws=True, sp=vert_axis_pos)


def calculate_pivot_distance(amount: int, obj_length: float) -> float:
    """Calculate distance to place pivot away from object

    Args:
        amount: Amount of times the selected object needs to be duplicated 
            around the pivot
        obj_length: Length of object along non-specified axis

    Returns:
        Distance to place pivot away from object
    """
    interior_angle = (((amount - 2) * (180)) / amount) / 2
    angle_radian = math.radians(interior_angle)
    tan_value = math.tan(angle_radian)
    pivot_distance = (tan_value * (obj_length / 2))

    return pivot_distance


def move_pivot(obj_name: str, pivot_distance: float, centre_direction: str) -> None:
    """Move the pivot to duplicate objects around it

    Args:
        obj_name: Name of the object where the verts are selected
        pivot_distance: Distance for pivot to move
        centre_direction: What direction the pivot should move towards
    """
    x = y = z = 0.0
    
    if centre_direction == "+x":
        x = pivot_distance
    elif centre_direction =="-x":
        x = -pivot_distance
    elif centre_direction =="+y":
        y = pivot_distance
    elif centre_direction =="-y":
        y = -pivot_distance
    elif centre_direction =="+z":
        z = pivot_distance
    elif centre_direction =="-z":
        z = -pivot_distance

    cmds.move(x, y, z, f"{obj_name}.scalePivot", 
              f"{obj_name}.rotatePivot", r=True)


def duplicate_and_rotate_object(obj_name: str, amount: int, 
                                axis: str) -> list[str]:
    """Duplicate and rotate objects around an axis a given amount of times

    Args:
        obj_name: Name of the object where the verts are selected
        amount: Amount of times the selected_obj needs to be duplicated around 
            the pivot
        axis: Axis to be rotated around

    Returns:
        List of original and duplicated objects as strings
    """
    selected_objs = [obj_name]
    dup = obj_name
    rotate_num = 360 / amount

    for _ in range(amount - 1):
        dup = cmds.duplicate(dup)
        if axis == "x":
            cmds.rotate(rotate_num, 0, 0, dup, r=True)
        elif axis =="y":
            cmds.rotate(0, rotate_num, 0, dup, r=True)
        elif axis =="z":
            cmds.rotate(0, 0, rotate_num, dup, r=True)

        selected_objs.append(dup[0])

    return selected_objs
