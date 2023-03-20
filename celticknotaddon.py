bl_info = {
    "name": "Celtic Knot",
    "blender": (2, 80, 0),
    "category": "Object",
}
import bpy
import math
from mathutils import Vector

# when vectors drawn from center point C to points A and B are projected onto the plane
# defined by normal vector n, what is the angle between them, going counterclockwise?
# output is in the range of 0 to 2*pi radians
# we have the option to skip the projection step if everything is coplanar
def angle(n, A, B, C, fProject):
    AC = A-C
    BC = B-C
    projectedAC = (AC - AC.project(n)) if fProject else AC
    projectedBC = (BC - BC.project(n)) if fProject else BC
    angle = math.atan2( -n.dot((projectedAC).cross(projectedBC)), -(projectedAC).dot(projectedBC) ) + math.pi
    return angle

def makeBezier(spline, vertList, vectors, hscale):
    # determine the number of points that will constitute this looping curve
    numPoints = len(vertList) - 1
    spline.bezier_points.add(numPoints)
    # flatten the vertex data into a new array and press it onto the curve
    flatList = []
    for vert in vertList:
        flatList.extend(vert)
    spline.bezier_points.foreach_set("co", flatList)
    spline.use_cyclic_u = True
    # modulate the handle scaling
    for index, point in enumerate(spline.bezier_points):
        point.handle_left = point.co + vectors[index]*hscale
        point.handle_right = point.co - vectors[index]*hscale
        
class Celtic_Knot(bpy.types.Operator):
    """Celtic Knot"""
    bl_idname = "object.celtic_knot"
    bl_label = "Celtic Knot"
    bl_options = {'REGISTER', 'UNDO'}
    
    zOffset: bpy.props.FloatProperty(name="Offset", default=.5)
    handleScale: bpy.props.FloatProperty(name="Handle Scale", default=.5)
    bDepth: bpy.props.FloatProperty(name="Bevel Depth", default=0.08, min=0)
    bRes: bpy.props.IntProperty(name="Bevel Resolution",default=2,min=0,max=4)
    fUseNormals: bpy.props.BoolProperty(name="Use Vertex Normals", description="Disable for flat base meshes on the XY plane", default=True)
    
    def execute(self, context):      
        trigConstant = 2 ** (-1/2) # sqrt(2)/2 = sin(45) = cos(45)

        if(bpy.context.view_layer.objects.active==None):
            self.report({"WARNING"}, "No object selected")
            return {'FINISHED'}
        if(bpy.context.view_layer.objects.active.type != 'MESH'):
            self.report({"WARNING"}, "Selected object is not a mesh")
            return {'FINISHED'}
        mesh = bpy.context.view_layer.objects.active.data
        bpy.ops.object.transform_apply(location = True, scale = True, rotation = True)
        bpy.ops.view3d.snap_cursor_to_selected()

        # when an edge has been crossed going from left to right, it updates the value at its index from 0 to 1
        edgeHandledTracker = [0] *len(mesh.edges)

        while True: # one turn of this loop creates one curve
            startedge = None
            # find the first unprocessed edge
            for e in mesh.edges:
                if edgeHandledTracker[e.index]<1:
                    startedge = e
                    break
            if not startedge:
                break
            hubVertIndex = 0 # used to track which of the two verts of the edge we're working with
            vertList = []
            vectors = []
            right = True
            while (not edgeHandledTracker[startedge.index] or not right):  # one turn of this loop adds one spline point
                hubIndex = startedge.vertices[hubVertIndex] # global index of the vertex
                endIndex = startedge.vertices[1-hubVertIndex]
                hubVert = mesh.vertices[hubIndex] # actual vertex object
                endVert = mesh.vertices[endIndex]
                hub = hubVert.co # vertex coords
                end = endVert.co
                # create a spline point located above the edge's midpoint and rotated by 45 degrees relative to the edge
                midpoint = (hub + end)/2
                edgeVec = end-hub
                avgNorm = ((hubVert.normal + endVert.normal)/2).normalized()
                sineOfAngle = trigConstant if right else -trigConstant
                norm = (avgNorm if self.fUseNormals else Vector((0.0, 0.0, 1.0)))
                # minimal form of Rodrigues' rotation formula
                edgeVecRotated = (edgeVec*trigConstant + sineOfAngle*(edgeVec.cross(norm))).normalized()
                vectors.append(edgeVecRotated)
                midpoint += (norm *  self.zOffset * (1 if right else -1))
                vertList.append(midpoint)
                if right: # log that we crossed this edge going from left to right
                    edgeHandledTracker[startedge.index] += 1
                # now we identify which edge to handle next, and which of its two vertices will be the new hub
                neighbors = []
                for e in mesh.edges:
                    if hubIndex in e.vertices and e != startedge:
                        neighbors.append(e)
                if not neighbors:
                    # this is a dead end; we're going to loop back on this same edge
                    hubVertIndex = 1-hubVertIndex
                elif len(neighbors) == 1:
                    # we don't need to search for the best neighbor, as there's only one
                    startedge = neighbors[0]
                    hubVertIndex = int(startedge.vertices[0] == hubIndex) # new hub is whichever vertex isn't shared; this gives us 0 or 1
                else:
                    # use vector math to find the nearest edge going clockwise around the normal axis
                    normal = (hubVert.normal if self.fUseNormals else Vector((0.0, 0.0, 1.0)))
                    if right:
                        normal = -normal
                    nextedge = neighbors[0]
                    nonsharedvertindex = int(nextedge.vertices[0] == hubIndex)
                    bestKnownAngle = angle(normal, end, mesh.vertices[nextedge.vertices[nonsharedvertindex]].co, hub, self.fUseNormals)
                    for e in neighbors[1:]:
                        candidatevertindex = int(e.vertices[0] == hubIndex)
                        candidateAngle = angle(normal, end, mesh.vertices[e.vertices[candidatevertindex]].co, hub, self.fUseNormals)
                        if( candidateAngle > bestKnownAngle):
                            bestKnownAngle = candidateAngle
                            nextedge = e
                    startedge = nextedge
                    hubVertIndex = int(startedge.vertices[0] == hubIndex)
                right = not right
            crv = bpy.data.curves.new("KnotBezier", type = "CURVE")
            crv.dimensions = '3D'
            crv.splines.new(type = 'BEZIER')
            crv.fill_mode = 'FULL'
            crv.bevel_depth = self.bDepth
            crv.bevel_resolution = self.bRes
            makeBezier(crv.splines[0], vertList, vectors, self.handleScale)
            curveObj = bpy.data.objects.new('KnotBezier', crv)
            bpy.context.view_layer.active_layer_collection.collection.objects.link(curveObj)
        return {'FINISHED'}

def menu_func(self, context):
    self.layout.operator(Celtic_Knot.bl_idname) 
    
def register():
    bpy.utils.register_class(Celtic_Knot)
    bpy.types.VIEW3D_MT_object.append(menu_func)

def unregister():
    bpy.utils.unregister_class(Celtic_Knot)
    bpy.types.VIEW3D_MT_object.remove(menu_func)

if __name__ == "__main__":
    register()