# Celtic Knot Addon
This script generates a Bezier curve Celtic knot based on the selected mesh.

## Installation
Download the .py file. In Blender, go to **File->User Preferences->Install From File...** and choose the .py file. It will then appear as a button at the top of the Objects dropdown, and will be searachable in the spacebar menu (listed under "Celtic Knot").

## Options
- The Offset slider allows you to change the displacement between every pair of Bezier points woven under/over each other.
- The Handle Scale slider allows you to change how much each point in the curve exerts itself.
- The Bevel Depth slider changes how thick the 3D curve is.
- The Bevel Resolution slider can increase or decrease the subdivision of the 3D curve.
- The Use Vertex Normals option allows you to choose whether to use each vertex's individual normal or the z-axis normal in calculating the traversal of the object and the direction of the offset. In general, this box should be checked when the input mesh is 3D, and unchecked for flat meshes lying in the XY plane.

### Special Thanks
[The best guide available to methodically and nonarbitrarily generating Celtic Knots from 2-dimensional arrangements of vertices and edges](http://www.entrelacs.net/-Celtic-Knotwork-The-ultimate-)

[Blender Artists user elbrujodelatribu, for an excellent example of Bezier curve generation](http://blenderartists.org/forum/archive/index.php/t-325717.html)
