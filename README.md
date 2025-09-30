# maya-tools

aaaaaaaaaaaaaaaaaa

## Auto Fill

### Description

This script allows for the user to fill the space between selected two sets of edge borders with tris and quads, no matter the difference in the number of edges they have.

![Auto Fill](assets/auto_fill.gif)

### Usage

To use this script as an item on a shelf, paste the code below in either the command line or script editor, highlight it and middle mouse drag it onto a shelf. Make sure that, when prompted, the language of the shelf object is in Python.

```python
import auto_fill as af

af.auto_fill()
```

This tool requires that two edge borders of a single object with one edge border residing in the empty space of the other edge border.

By default, the script utilises Maya's Quadrangulate tool but if the user so chooses to, by writing False as an argument for auto_fill, they can have all the vertices ine one edge border connect to their closest counterparts in the other edge border.

## Create Clothesline

### Description

This tool allows the user to create a clothesline from a set of textures.
![Create Clothesline](assets/create_clothesline.gif)

### Usage

To use this script as an item on a shelf, paste the code below in either the command line or script editor, highlight it and middle mouse drag it onto a shelf. Make sure that, when prompted, the language of the shelf object is in Python.

```python
from create_clothesline import clothesline_ui as clu

clu.ClotheslineDialog.show_dialog()
```

Through the UI, users can utilise images to create materials that serve as clothing on the clothesline. The tool automatically seeks files in the sourceimages folder of the current project but files in other folders can be selected. The name of the material can then be renamed.

From there, users can add these materials as many times as they require, with the order of the clothing added preserved when the clothesline is created. In addition, each individual clothing piece can have its amount and width adjusted or be removed entirely.

Finally, the clothesline itself can be manipulated, where you can change its length, wire radius, curvature and randomisation of clothing order.

## Create Windows

This tool, when selecting the edge borders of a window and an empty wall that are part of one mesh, creates multiples of the window as part of the wall that are all equally spaced.

### Description

![Create Windows](assets/create_windows.gif)

### Usage

To use this script as an item on a shelf, paste the code below in either the command line or script editor, highlight it and middle mouse drag it onto a shelf. Make sure that, when prompted, the language of the shelf object is in Python.

```python
from create_multiple_windows import create_multiple_windows_ui as cmwu

cmwu.MultipleWindowsDialog.show_dialog()
```

This tool requires that two edge borders of a single object with one edge border (the window) residing in the empty space of the other edge border (the wall).

Through the UI, users can specify how many windows they want both height-wise and width-wise. Additionally, they can choose to forgo connecting the windows and wall and just create multiples of the window instead.

It is important to note that the tool assumes that height runs along the y-axis and that users should ensure that their objects follow this convention.

## Duplicate Around

This tool allows for the user to duplicate a mesh around a point a specified number of times and connect them by their edges.

### Description

![Duplicate Around](assets/duplicate_around.gif)

### Usage

To use this script as an item on a shelf, paste the code below in either the command line or script editor, highlight it and middle mouse drag it onto a shelf. Make sure that, when prompted, the language of the shelf object is in Python.

```python
from duplicate_around_point import duplicate_around_ui as dau

dau.DuplicateAroundDialog.show_dialog()
```

This tool requires that users select two vertices along the same axis, which serve as the point of connection for the other duplicated meshes.

After doing so, the UI requires that the user specify in what direction should the object rotate around and where should the centre of all these meshes be located. For example, the duplicated objects above utilised the UI to specify that the object should rotate around the y-axis and that the centre of these meshes should be in the negative x direction.

Additionally, the user can specify the number of meshes that should be created and if the meshes should be connected at all.

## Reload Modules

### Description

This script reloads all modules found in a specified folder, which is by default the location of where the Reload Modules file is.

### Usage

To use this script as an item on a shelf, paste the code below in either the command line or script editor, highlight it and middle mouse drag it onto a shelf. Make sure that, when prompted, the language of the shelf object is in Python.

```python
import reload_modules as rm

rm.reload_modules()
```

By default, all modules found in the directory where the Reload Modules
