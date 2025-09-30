# maya-tools

## Auto Fill

### Description

![Auto Fill](assets/auto_fill.gif)

### Usage

```python
import auto_fill as af

af.auto_fill()
```

## Create Clothesline

### Description

![Create Clothesline](assets/create_clothesline.gif)

### Usage

```python
from create_clothesline import clothesline_ui as clu

clu.ClotheslineDialog.show_dialog()
```

## Create Windows

### Description

This script allows for the user to fill the space between selected two sets of edge borders with tris and quads, no matter the difference in the number of edges they have. Additionally, instead of the optimised positioning of tris and quads this script provides, it also provides the user with the option to directly connect all of the vertices of one edge border to their closest counterparts.

![Create Windows](assets/create_windows.gif)

### Usage

```python
from create_multiple_windows import create_multiple_windows_ui as cmwu

cmwu.MultipleWindowsDialog.show_dialog()
```

## Duplicate Around

### Description

![Duplicate Around](assets/duplicate_around.gif)

### Usage

```python
from duplicate_around_point import duplicate_around_ui as dau

dau.DuplicateAroundDialog.show_dialog()
```

## Reload Scripts

### Description

### Usage

```python
import reload_files as rf

rf.reload_modules()
```
