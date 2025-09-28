"""Fills in the empty space between two edge borders with tris and quads

Intended to be used when one edge border has a different number of edges
to the other edge border, which would normally give an error.

auto_bridge is the main function to use.

check_edge_borders can also be used to verify that a selection consists of
only two edge borders.
"""
import math

import maya.cmds as cmds


def auto_bridge(isQuad:bool=True) -> None:
    """Fills in the empty space between two edge borders with tris and quads

    Args:
        isQuad: If True, the auto_bridge function utilises quadrangulate. 
            Else, it connects each vertex to its closest counterpart.
            Defaults to True.

    Raises:
        RuntimeError: If no selections have been made
    """
    selected_edges = cmds.ls(sl=True, fl=True)
    if not selected_edges:
        raise RuntimeError("No selections have been made.")

    obj_name = selected_edges[0].split(".")[0]

    edge_borders = check_edge_borders(obj_name, selected_edges)

    orig_mesh = cmds.ls(f'{obj_name}.f[*]', fl=True)
    closest_edge_pair = bridge_closest_edges(edge_borders[0], edge_borders[1])
    
    fill_hole(edge_borders, closest_edge_pair)
    filled_mesh = cmds.ls(f'{obj_name}.f[*]', fl=True)
    filled_face = list(set(filled_mesh) - set(orig_mesh))

    if isQuad:
        cmds.polyTriangulate(filled_face)
        cmds.polyQuad()
    else:
        create_closest_edges(edge_borders[0], edge_borders[1], closest_edge_pair)


def check_edge_borders(obj_name: str, selected_edges: list[str]
                      ) -> tuple[list[str], list[str]]:
    """Check that a selection of edges contains two separate edge borders

    Args:
        obj_name: Name of object that has its edges selected
        selected_edges: List of all the edges selected

    Returns:
        A tuple with two lists of each edge in each edge border

    Raises:
        RuntimeError: If anything other than edges are selected
        RuntimeError: If selected edges aren't on the same mesh
        RuntimeError: If first edge is not on a border
        RuntimeError: If selected edges don't match the edge border of the 
            first edge
        RuntimeError: If there is only one edge border selected
        RuntimeError: If edges borders found don't match initial list
        RuntimeError: If second edge is not on a border
        RuntimeError: If selected edges don't match the edge border of the 
            second edge
        RuntimeError: If more edges need to be selected
        RuntimeError: If there are too many edges selected
    """
    num_edges = cmds.polyEvaluate(selected_edges, ec=True)
    if not num_edges:
        raise RuntimeError("Only edge borders should be selected.")

    selected_edges_indices = []
    for edge in selected_edges:
        edge_index = int(edge.split(".e[")[1].split("]")[0])
        selected_edges_indices.append(edge_index)

    if not all(edge.startswith(obj_name) for edge in selected_edges):
        raise RuntimeError("Selected edges must be on the same mesh.")
    
    # Get index of the first item in selected_edges
    first_edge_index = int(selected_edges[0].split(".e[")[1].split("]")[0])

    # Checks if the first_edge is part of a selected border
    eb_first_indices = cmds.polySelect(q=True, eb=first_edge_index)
    if not eb_first_indices:
        raise RuntimeError("Two edge borders must be selected.")
    if not set(eb_first_indices).issubset(set(selected_edges_indices)):
        raise RuntimeError("Two edge borders must be selected.")

    eb_first = [f"{obj_name}.e[{i}]" for i in eb_first_indices[:-1]]

    # Checks if there is another set of edges
    other_edges = list(set(selected_edges) - set(eb_first))
    if not other_edges:
        raise RuntimeError("Another edge border must be selected.")

    # Get index of the first item in other_edges
    second_edge_index = int(other_edges[0].split(".e[")[1].split("]")[0])

    # Checks if the second_edge is part of a border
    eb_second_indices = cmds.polySelect(q=True, eb=second_edge_index)
    if not eb_second_indices:
        raise RuntimeError("Two edge borders must be selected.")
    if not set(eb_second_indices).issubset(set(selected_edges_indices)):
        raise RuntimeError("Two edge borders must be selected.")

    eb_second = [f"{obj_name}.e[{i}]" for i in eb_second_indices[:-1]]

    # Checks if too many or too little edges have been selected
    if len(other_edges) < len(eb_second):
        raise RuntimeError("More edges must be selected for the edge borders.")
    elif (len(eb_first) + len(eb_second)) > len(selected_edges):
        raise RuntimeError("More edges must be selected for the edge borders.")
    elif (len(eb_first) + len(eb_second)) < len(selected_edges):
        raise RuntimeError("Too many edges have been selected.")
    elif len(eb_second) > len(other_edges):
        raise RuntimeError("Too many edges have been selected.")

    return (eb_first, eb_second)


def bridge_closest_edges(edges_main: list[str], edges_secondary: list[str]
                        ) -> list[str]:
    """Bridge the closest edges from two lists of edges that form edge borders

    Args:
        edges_main: List of edges in an edge border
        edges_secondary: List of edges in an edge border

    Returns:
        List of two strings containing the edges bridged
    """
    closest_edge_pair: list[str] = []
    closest_distance = 0.0

    for edge_main in edges_main:
        for edge_secondary in edges_secondary:
            edges_distance = calculate_edges_distance(edge_main, edge_secondary)
            if not closest_edge_pair:
                closest_edge_pair = [edge_main, edge_secondary]
                closest_distance = edges_distance
            elif edges_distance < closest_distance:
                closest_edge_pair = [edge_main, edge_secondary]
                closest_distance = edges_distance

    cmds.polyBridgeEdge(closest_edge_pair[0], closest_edge_pair[1], dv=0)

    return closest_edge_pair


def calculate_edges_distance(edge_one: str, edge_two: str) -> float:
    """Returns the average Euclidean distance between the vertices of two edges.

    Gets the distance between from a vertex from one edge and compares it to its
    closest vertex from the other edge and repeats that with the other vertices.
    It then averages these distances and returns value.

    Args:
        edge_one: Edge to be used for calculations
        edge_two: Edge to be used for calculations

    Returns:
        The Euclidean distance between two edges
    """

    verts_one = cmds.polyListComponentConversion(edge_one, fe=True, tv=True)
    verts_one = cmds.ls(verts_one, fl=True)

    verts_two = cmds.polyListComponentConversion(edge_two, fe=True, tv=True)
    verts_two = cmds.ls(verts_two, fl=True)

    # Get the shortest distance from one vertex to the other two vertices
    min_dist_one0 = calculate_vertices_distance(verts_one[0], verts_two[0])
    min_dist_one1 = calculate_vertices_distance(verts_one[0], verts_two[1])
    min_dist_one = min(min_dist_one0, min_dist_one1)

    # Get the shortest distance from the other vertex to the other two vertices
    min_dist_two0 = calculate_vertices_distance(verts_one[1], verts_two[0])
    min_dist_two1 = calculate_vertices_distance(verts_one[1], verts_two[1])
    min_dist_two = min(min_dist_two0, min_dist_two1)

    avg_dist = (min_dist_one + min_dist_two) / 2

    return avg_dist


def fill_hole(edge_borders: tuple[list[str], list[str]], 
              closest_edge_pair: list[str]) -> None:
    """Fill a hole from two edge borders that are now bridged

    Args:
        edge_borders: Two lists of edges for two edge borders that are now bridged
        closest_edge_pair: List containing two edges that were used to bridge
            between the two edge borders
    """
    # Get a set of edges that has removed the old merged edges
    hole_edges = edge_borders[0] + edge_borders[1]
    hole_edges = list(set(hole_edges) - set(closest_edge_pair))

    edge_index = int(hole_edges[0].split(".e[")[1].split("]")[0])
    cmds.polySelect(eb=edge_index)
    cmds.polyCloseBorder()


def create_closest_edges(edges_first: list[str], edges_second: list[str], 
                         bridged_edge_pair: list[str])-> None:
    """Create edges with minimal distance to one another given a filled hole

    Given two already bridged edges and the two initial edge borders from where
    they originally came from, connect all unconnected vertices of the edge 
    border with most vertices to their closest vertex in the other edge border.

    Args:
        edges_first: Initial string of edges within one edge border
        edges_second: Initial string of edges within another edge border
        closest_edge_pair: Two strings representing the edges bridged

    Raises:
        RuntimeError: If bridged_edge_pair contains edges that aren't within
            the list of edges in the two edge borders
    """
    if len(edges_first) > len(edges_second):
        edges_main = edges_first
        edges_secondary = edges_second
    else:
        edges_main = edges_second
        edges_secondary = edges_first

    verts_main = cmds.polyListComponentConversion(edges_main, fe=True, tv=True)
    verts_main = cmds.ls(verts_main, fl=True)

    verts_secondary = cmds.polyListComponentConversion(edges_secondary, 
                                                       fe=True, tv=True)
    verts_secondary = cmds.ls(verts_secondary, fl=True)

    # Remove already bridged vertices
    if bridged_edge_pair[0] in edges_main:
        verts_to_remove = cmds.polyListComponentConversion(bridged_edge_pair[0], 
                                                           fe=True, tv=True)
    elif bridged_edge_pair[1] in edges_main:
        verts_to_remove = cmds.polyListComponentConversion(bridged_edge_pair[1], 
                                                           fe=True, tv=True)
    else:
        raise RuntimeError("Given bridged edges don't exist in initial edge borders.")

    verts_main = list(set(verts_main) - set(verts_to_remove))

    for vert in verts_main:
        connect_closest_vertex(vert, verts_secondary)


def connect_closest_vertex(connecting_vert: str, vert_list: list[str]) -> None:
    """Connect a vertex to its closest vertex given a list of vertices

    Args:
        connecting_vert: Vertex to be connected
        vert_list: List of verts that could connect to connecting_vert

    """
    shortest_distance: list = ["", 0]

    for vert in vert_list:
        distance = calculate_vertices_distance(connecting_vert, vert)
        if not shortest_distance[1]:
            shortest_distance = [vert, distance]
        elif distance < shortest_distance[1]:
            shortest_distance = [vert, distance]

    cmds.polyConnectComponents(connecting_vert, shortest_distance[0]) 


def calculate_vertices_distance(vert_one: str, vert_two: str) -> float:
    """Returns the Euclidean distance between two vertices

    Args:
        vert_one: Vert to be used for calculations
        vert_two: Vert to be used for calculations

    Returns:
        The Euclidean distance between two vertices
    """
    coords_one = cmds.xform(vert_one, q=True, t=True, ws=True) # type: ignore
    coords_two = cmds.xform(vert_two, q=True, t=True, ws=True) # type: ignore

    distance = math.dist(coords_one, coords_two)

    return distance
