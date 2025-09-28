"""Create multiple windows from the selected borders of a wall and a window

When selecting two edge borders within a single mesh, of which one is a wall
and the other is a window placed inside it, this main function of this file can
be used to evenly space out several windows specified by a given height and
width.

It should be noted that creating and bridging many windows will cause Maya to 
slow down somewhat in order to connect all the windows so be aware when 
creating many windows.

When using the main function, it is intended that the height matches the y-axis.

create_multiple_windows is the main function to use.
"""
import maya.cmds as cmds
import auto_bridge as ab


def create_multiple_windows(height: int, width: int, 
                            bridge_windows: bool = True) -> None:
    """Create multiple windows from the selected borders of a wall and a window

    Args:
        height: Number of windows height-wise
        width: Number of windows width-wise
        bridge_windows: Bool if windows should be bridged together. 
            Defaults to True.

    Raises:
        RuntimeError: If selection contains no edges
    """
    selection = cmds.ls(sl=True, fl=True)
    num_edges = cmds.polyEvaluate(selection, ec=True)

    if not selection or not num_edges:
        raise RuntimeError("Select two edge borders that represent a window and a wall.")

    obj_name = selection[0].split(".")[0]

    (window_border, window_bbox), (wall_border, wall_bbox) = get_borders_and_bboxs(obj_name, selection)

    check_if_windows_can_fit(height, width, window_bbox, wall_bbox)

    # Create the window pivot based on the centre of the edge border's bounding box
    window_pivot = []
    for i in range(3):
        window_pivot.append((window_bbox[i+3] + window_bbox[i]) / 2)

    window_faces = get_shell_faces_from_border(window_border)

    cmds.waitCursor(st=True)
    windows_border = create_windows(height, width, obj_name, window_faces, 
                                    window_pivot, wall_bbox, bridge_windows)

    if bridge_windows:
        cmds.select(wall_border + windows_border)
        ab.auto_bridge()
    
    cmds.waitCursor(st=False)

    cmds.select(obj_name, r=True)


def get_borders_and_bboxs(obj_name, selection) -> tuple[tuple[list[str], list[float]], 
                                                        tuple[list[str], list[float]]]:
    """Get the border edges and bbox of the window and wall

    Args:
        obj_name: Name of the object 
        selection: Current selection

    Returns:
        Two tuples consisting of the window_border, window_bbox and the 
        wall_border, wall_bbox. The borders are a list of edges and the bboxs
        are a set of flaots describing the bounding box of each border
    """
    edge_borders = ab.check_edge_borders(obj_name, selection)

    window_border = get_window_border(obj_name, edge_borders)
    window_bbox = cmds.exactWorldBoundingBox(window_border)

    wall_border = list(set(selection) - set(window_border))
    wall_bbox = cmds.exactWorldBoundingBox(wall_border)

    return (window_border, window_bbox), (wall_border, wall_bbox)

def get_window_border(obj_name: str, 
                      edge_borders: tuple[list[str], list[str]]) -> list[str]:
    """Get the edges of the window border

    Compares the two edge borders to see the difference in size between the two
    before returning the smaller border, which should be the window's border

    Args:
        obj_name: Name of the object
        edge_borders: Tuple of two list of edges that form a border for either 
            the window or the wall

    Returns:
        List of edges of the window border
    """
    smaller_area: list = [[], 0.0] # [list[str], float]
    
    for i in range(2):
        faces_list_old = (cmds.ls(f"{obj_name}.f[*]",fl=True))

        cmds.polyCloseBorder(edge_borders[i])

        faces_list_new = (cmds.ls(f"{obj_name}.f[*]",fl=True))
        new_face = list(set(faces_list_new) - set(faces_list_old))

        area = cmds.polyEvaluate(new_face, fa=True)[0]

        if area < smaller_area[1] or smaller_area[1] == 0:
            smaller_area = [edge_borders[i], area]

        cmds.delete(new_face)

    return smaller_area[0]


def check_if_windows_can_fit(height: int, width: int, window_bbox: list[float], 
                             wall_bbox: list[float]) -> None:
    """Check if the windows can fit inside the wall

    Args:
        height: Number of windows height-wise
        width: Number of windows width-wise
        window_bbox: Bounding box of the window
        wall_bbox: Bounding box of wall

    Raises:
        ValueError: Number of windows won't fit the given wall
    """
    windows_dims = []
    windows_dims.append((window_bbox[3]- window_bbox[0]) * width)
    windows_dims.append((window_bbox[4]- window_bbox[1]) * height)
    windows_dims.append((window_bbox[5]- window_bbox[2]) * width)

    wall_dims = []
    for i in range(3):
        wall_dims.append(wall_bbox[i+3] - wall_bbox[i])

    for i in range(3):
        if windows_dims[i] > wall_dims[i]:
            raise ValueError("Number of windows won't fit the given wall.")


def get_shell_faces_from_border(border: list[str]) -> list[str]:
    """Get the shell faces from a border

    Args:
        border: List of edges that form a border

    Returns:
        List of faces that form the shell connected to the border
    """
    adj_face = cmds.polyListComponentConversion(border[0], tf=True)[0]
    adj_face_index = int(adj_face.split(".f[")[1].split("]")[0])
    cmds.polySelect(ets=adj_face_index)

    return cmds.ls(sl=True)


def create_windows(height: int, width: int, obj_name: str, window: list[str], 
                   window_pivot: list[float], wall_bbox: list[float], 
                   bridge_windows: bool = True) -> list[str]:
    """Create windows by specified height and width and optionally connect them

    Args:
        height: Number of windows height-wise
        width: Number of windows width-wise
        obj_name: Name of the object
        window: List of faces for the window
        window_pivot: Pivot for the window
        wall_bbox: Bounding box of wall
        bridge_windows: Bool if windows should be bridged together. 
            Defaults to True.

    Returns:
        List of edges that form the border of the connected windows
    """
    movement = move_window_to_start(height, width, window, window_pivot, wall_bbox)

    main_window_border = cmds.ls(cmds.polyListComponentConversion(window, bo=True, te=True), fl=True) #type: ignore
    dup_window_border = []

    for i in range(height):
        for j in range(width):
            if not (i == 0 and j == 0):
                print(f"Creating window: Height-{i+1}/{height} Width-{j+1}/{width}")
                cmds.polyChipOff(window, t=[j * movement[0], i * movement[1], 
                                            j * movement[2]])
                
                if bridge_windows:
                    dup_window_border = cmds.ls(cmds.polyListComponentConversion(bo=True, te=True), fl=True)

                    closest_edge_pair = ab.bridge_closest_edges(main_window_border, 
                                                                dup_window_border)

                    main_window_border = get_bridged_border(main_window_border, 
                                                            dup_window_border, 
                                                            closest_edge_pair, 
                                                            obj_name)

    return main_window_border


def move_window_to_start(height: int, width: int, window: list[str], 
                         window_pivot: list[float], 
                         wall_bbox: list[float]) -> list[float]:
    """Move the window to its starting location before duplication and movement

    Args:
        height: Number of windows height-wise
        width: Number of windows width-wise
        window: List of faces for the window
        window_pivot: Pivot for the window
        wall_bbox: Bounding box of wall

    Returns:
        List of movements for x, y, z for each window to move
    """
    wall_bbox_start = wall_bbox[0:3]

    shift_to_bbox = [x - y for x, y in zip(wall_bbox_start, window_pivot)]

    cmds.move(shift_to_bbox[0], shift_to_bbox[1], shift_to_bbox[2], window, r=True)

    x_move = (wall_bbox[3] - wall_bbox[0]) / width
    y_move = (wall_bbox[4] - wall_bbox[1]) / height
    z_move = (wall_bbox[5] - wall_bbox[2]) / width

    cmds.move(x_move / 2, y_move / 2, z_move / 2, window, r=True)

    return [x_move, y_move, z_move]


def get_bridged_border(main_window_border: list[str], dup_window_border: list[str], 
                       closest_edge_pair: list[str], obj_name: str) -> list[str]:
    """Get border edges from a mesh that bridged itself to a duplicated window

    Args:
        main_window_border: Main collection of window's edges
        dup_window_border: Duplicate window's edges
        closest_edge_pair: Edge pair that was used to be bridged
        obj_name: Name of the object

    Returns:
        List of border edges from the newly bridged mesh
    """
    overlapping_combined_borders = main_window_border + dup_window_border
    combined_borders = list(set(overlapping_combined_borders) - set(closest_edge_pair))

    bridged_edge_index = int(combined_borders[0].split(".e[")[1].split("]")[0])
    bridged_edges_indices = cmds.polySelect(q=True, eb=bridged_edge_index)

    bridged_border = [f"{obj_name}.e[{i}]" for i in bridged_edges_indices]

    return bridged_border
