"""Create a clothesline from data of materials and objects to be made

This file allows a clothesline to be made from a collection of file paths with 
their associated material names and a collection of objects that list their 
materials and lengths.

All images maintain their aspect ratio when trying to match their specified
length.

create_clothesline is the main function to use.
"""
try:
    from PySide6 import QtGui
except:
    from PySide2 import QtGui # type: ignore[no-redef]

import random
import math
from typing import TypedDict

import maya.cmds as cmds


class ObjData(TypedDict):
    file_path: str
    mat_name: str
    amount: int
    length: float


def create_clothesline(mat_data: dict[str, str], objs_data: list[ObjData], 
                       length: float, wire_rad: float, curvature: float, 
                       randomise: bool) -> None:
    """Create a clothesline from data of materials and objects to be made

    Creates a group to hold a wire obj, several planes with images as their 
    textures that are evenly separated, all of which can be bent with a 
    specified curvature.

    Args:
        mat_data: Dict containing file paths mapped to their node name
        objs_data: Data related to each object containing their file_path,
            mat_name, amount and length
        length: Length of the clothesline
        wire_rad: Radius of the wire
        curvature: Curvature of clothesline
        randomise: Whether the placement of the objects should be randomised 
            or not
    """
    avg_space = calculate_avg_space_between(objs_data, length)

    clothesline_grp = create_clothesline_group()
    wire = create_wire(length, wire_rad)
    cmds.parent(wire, clothesline_grp)

    shaders = {}

    for file_path, mat_name in mat_data.items():
        shd_grp = create_material(mat_name, file_path)
        shaders[mat_name] = shd_grp

    clothes = create_clothes(objs_data, shaders, clothesline_grp)

    arrange_clothing(clothes, length, avg_space, wire_rad, randomise)

    clothesline = [wire] + [clothing_obj[0] for clothing_obj in clothes]
    bend = bend_clothesline(clothesline, curvature)
    cmds.parent(bend, clothesline_grp)

    cmds.select(clothesline_grp, r=True)


def calculate_avg_space_between(objs_data: list[ObjData], 
                                length: float) -> float:
    """Calculate the average space between each piece of clothing

    Args:
        objs_data: Data related to each object containing their file_path,
            mat_name, amount and length
        length: Length of clothesline

    Raises:
        ValueError: If total length of clothing is larger than the length of
            the clothesline
    """
    clothing_length: float = 0

    total_clothes = sum(key["amount"] for key in objs_data)

    for obj in objs_data:
        clothing_length += obj["length"] * obj["amount"]

    # Add 1 to total_clothes to represent number of gaps to jump
    if length >= clothing_length:
        return (length - clothing_length) / (total_clothes + 1)
    else:
        raise ValueError("Total length of clothing is larger than length of clothesline")


def create_clothesline_group() -> str:
    """Create a clothesline group with a unique name"""
    full_name = get_unique_name("clothesline_grp")
    clothesline_grp = cmds.group(em=True, n=full_name)

    return clothesline_grp


def create_wire(length: float = 5.0, wire_rad: float = 0.02) -> str:
    """Create wire object

    Args:
        length: Length of wire. Defaults to 5.0.
        wire_rad: Radius of Wire. Defaults to 0.02.

    Returns:
        Name of wire object
    """
    full_name = get_unique_name("clothesline_wire")
    subd = math.floor(length * 4)
    wire = cmds.polyCylinder(n=full_name, sh=subd)

    cmds.scale(wire_rad, (length / 2), wire_rad)
    cmds.rotate(0, 0, 90)
    cmds.move(0, 0, 0)

    return wire[0]


def create_material(name: str, file_path: str) -> str:
    """Creates a material from a given image

    Args:
        name: Name of the material
        file_path: Location of the file

    Returns:
        Name of shading group
    """

    shd = cmds.shadingNode("standardSurface", asShader=True, 
                           n=name)
    shd_grp = cmds.sets(n=f"{shd}SG", em=True, r=True, nss=True)
    cmds.connectAttr(f"{shd}.outColor", f"{shd_grp}.surfaceShader")

    connect_values = connect_place2d_to_file(file_path)
    tx = connect_values[0]

    # Connect file outputs to standard_surface inputs
    cmds.connectAttr(f"{tx}.outColor", f"{shd}.baseColor")
    cmds.connectAttr(f"{tx}.outAlpha", f"{shd}.opacityR")
    cmds.connectAttr(f"{tx}.outAlpha", f"{shd}.opacityG")
    cmds.connectAttr(f"{tx}.outAlpha", f"{shd}.opacityB")

    return shd_grp


def connect_place2d_to_file(file_path: str) -> tuple[str, str]:
    """Connects place2d node to file node

    Args:
        file_path: Location of the file

    Returns:
        Tuple containing name of file node then name of place2d node
    """
    tx = cmds.shadingNode("file", at=True)
    cmds.setAttr(f"{tx}.fileTextureName", file_path, typ="string")
    place2d = cmds.shadingNode("place2dTexture", au=True)

    attributes = (
        ".coverage",
        ".translateFrame",
        ".rotateFrame",
        ".mirrorU",
        ".mirrorV",
        ".stagger",
        ".wrapU",
        ".wrapV",
        ".repeatUV",
        ".offset",
        ".rotateUV",
        ".noiseUV",
        ".vertexUvOne",
        ".vertexUvTwo",
        ".vertexUvThree",
        ".vertexCameraOne",
    )

    for attr in attributes:
        cmds.connectAttr(f"{place2d}{attr}", f"{tx}{attr}", f=True) # type: ignore

    cmds.connectAttr(
        f"{place2d}.outUvFilterSize", f"{tx}.uvFilterSize"
    )
    cmds.connectAttr(f"{place2d}.outUV", f"{tx}.uvCoord")

    return (tx, place2d)


def create_clothes(objs_data: list[ObjData], shaders: dict[str, str], 
                   clothesline_grp: str) -> list[tuple[str, float]]:
    """Create all the clothing for the clothesline

    Given several objects with information about their length and shader, 
    create planes with this information applied to them.

    Args:
        objs_data: Data related to each object containing their file_path,
            mat_name, amount and length
        shaders: Dict of material names mapped to shading group
        clothesline_grp: Name of clothesline group

    Returns:
        List of tuples containing clothing_obj names and their length
    """
    clothes = []
    
    for obj in objs_data:
        for _ in range(obj["amount"]):
            obj_name = "clothing_" + obj["mat_name"]
            shd_grp = shaders[obj["mat_name"]]
            clothing_obj = create_clothing_obj(obj_name, obj["file_path"], shd_grp, 
                                               obj["length"])
            cmds.parent(clothing_obj, clothesline_grp)
            clothes.append((clothing_obj, obj["length"]))

    return clothes


def create_clothing_obj(name: str, file_path: str, shd_grp: str, 
                        length: float) -> str:
    """Create clothing object

    Args:
        name: Name of the clothing_obj
        file_path: File path of the original texture
        shd_grp: Shading group to add clothing_obj to
        length: Length of wire.

    Returns:
        Return clothing_obj name
    """
    # Scale down dimensions of picture by adjusting original height 
    # to its specified length
    pic = QtGui.QImage(file_path)
    pic_width = length
    pic_height = pic.height() / (pic.width() / pic_width)

    full_name = get_unique_name(name)
    clothing_obj = cmds.polyPlane(n=full_name)

    cmds.scale(pic_width, 1, pic_height)
    cmds.rotate(90, 0, 0)
    cmds.move(0, (-pic_height / 2), 0)

    # Apply material to object
    cmds.sets([clothing_obj[0]], fe=shd_grp)

    clothing_obj = cmds.ls(clothing_obj[0])[0]

    return clothing_obj


def arrange_clothing(clothes_list: list[tuple[str, float]], length: float, 
                     avg_space: float, wire_rad: float, 
                     randomise: bool = False) -> None:
    """Arrange all given clothing to form a clothesline

    Args:
        clothes_dict: List of tuples containing clothing name and its length
        length: Length of a clotheslines
        avg_space: Average space between each clothing_obj
        wire_rad: Radius of wire
        randomise: Randomise placement of clothing. Defaults to False.
    """
    dist_moved = avg_space - (length / 2)

    if randomise:
        random.shuffle(clothes_list)

    for clothing, length in clothes_list:
            dist_moved += length / 2
            cmds.move(dist_moved, - wire_rad, 0, clothing, r=True)
            dist_moved += length / 2 + avg_space


def bend_clothesline(clothesline: list[str], curvature: float = 5.0) -> str:
    """Bend all on the objects on the clotheslines given a curvature

    Args:
        clothesline: List of all clothes and the wire
        curvature: Curvature to bend clothesline. Defaults to 5.0.

    Returns:
        Name of bend handle
    """
    full_name = get_unique_name("clothesline_bend")
    bend = cmds.nonLinear(clothesline, type="bend", 
                          curvature=curvature, n=full_name) #type: ignore
    
    cmds.rotate(0, 0, 90)
    cmds.setAttr(bend[1] + ".translateY", 0)

    return bend[1]


def get_unique_name(name: str) -> str:
    """Create a unique name from a name given"""
    unique_name = ""
    suffix = 1

    while not unique_name:
        if f"{name}_{suffix}" not in cmds.ls(f"{name}_*"):
            unique_name = f"{name}_{suffix}"
        else:
            suffix += 1

    return unique_name
