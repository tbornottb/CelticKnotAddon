bl_info = {
	"name": "Celtic Knot",
	"category": "Object",
}
import bpy
import math
from bpy_extras.object_utils import object_data_add
import mathutils

class Celtic_Knot(bpy.types.Operator):
	"""Celtic Knotter"""
	bl_idname = "object.celtic_knot"
	bl_label = "Celtic Knot"
	bl_options = {'REGISTER', 'UNDO'}

	zoffset = bpy.props.FloatProperty(name="Offset", default=.5)
	handleScale = bpy.props.FloatProperty(name="Handle Scale", default=.5)
	bDepth = bpy.props.FloatProperty(name="Bevel Depth", default=0.08, min=0)
	bRes = bpy.props.IntProperty(name="Bevel Resolution",default=2,min=0,max=4)
	zBool = bpy.props.BoolProperty(name="Use Vertex Normals", default=False)

	def execute(self, context):
		scene = context.scene
		obj = scene.objects.active
		mesh = obj.data
		bpy.ops.object.transform_apply(location = False, scale = True, rotation = True)
		bpy.ops.view3d.snap_cursor_to_selected()
		R = [0] *len(mesh.edges) # listed by edges' personal index
		
		while True: # 1 turn of this loop creates one curve
			startedge = None
			for e in mesh.edges:
				if R[e.index] < 1 :
					startedge = e
					break
			if not startedge:
				break
			hubpoint = 0
			vertList = []
			vectors = []
			right = True
			while (R[startedge.index]!=1 or not right): # 1 turn of this loop adds one spline point
				h = startedge.vertices[hubpoint] # index
				ba = startedge.vertices[1-hubpoint]
				hub = mesh.vertices[h] # actual point
				back = mesh.vertices[ba]
				a = mathutils.Vector(hub.co)
				b = mathutils.Vector(back.co)
				midpoint = (a + b)/2
				v = mathutils.Vector(b-a)
				anorm = mathutils.Vector(hub.normal)
				bnorm = mathutils.Vector(back.normal)
				avnorm = ((anorm + bnorm)/2).normalized()
				sff = math.sin((math.pi/4 if right else -math.pi/4))
				cff = math.cos((math.pi/4 if right else -math.pi/4))
				norm = (avnorm if self.zBool else mathutils.Vector((0.0, 0.0, 1.0)))
				vrot = (v*cff + sff*(v.cross(norm))+(v.dot(norm))*(1-cff)*v).normalized()
				vectors.append(vrot)
				midpoint += (norm *  self.zoffset * (1 if right else -1))
				vertList.append(midpoint[0])
				vertList.append(midpoint[1])
				vertList.append(midpoint[2])
				if right:
					R[startedge.index] += 1
				neighbors = []
				for e in mesh.edges:
					if h in e.vertices and ba not in e.vertices:
						neighbors.append(e)	
				if not neighbors:
					hubpoint = 1-hubpoint
				elif len(neighbors) == 1:
					startedge = neighbors[0]
					hubpoint = (1 if (startedge.vertices[0] == h) else 0)
				else: 
					n = (norm if right else -norm)
					nextedge = None
					for e in neighbors: # test for any CCW
						vertB = (1 if (e.vertices[0] == h) else 0)
						if CCW(n, b, mathutils.Vector(mesh.vertices[e.vertices[vertB]].co), a):
							nextedge = e
							break
					if nextedge is None: # no CCW
						nextedge = neighbors[0]
						for e in neighbors:
							if e == nextedge:
								continue
							vertA = (1 if (nextedge.vertices[0] == h) else 0)
							vertB = (1 if (e.vertices[0] == h) else 0)
							if CW(n, mathutils.Vector(mesh.vertices[nextedge.vertices[vertA]].co), mathutils.Vector(mesh.vertices[e.vertices[vertB]].co), a):
								nextedge = e
					else:
						for e in neighbors:
							if e == nextedge:
								continue 
							vertA = (1 if (nextedge.vertices[0] == h) else 0)
							vertB = (1 if (e.vertices[0] == h) else 0)
							if CW(n, mathutils.Vector(mesh.vertices[nextedge.vertices[vertA]].co), mathutils.Vector(mesh.vertices[e.vertices[vertB]].co), a) and CCW(n, b, mathutils.Vector(mesh.vertices[e.vertices[vertB]].co), a):
								nextedge = e
					hubpoint = (1 if (nextedge.vertices[0] == h) else 0)
					startedge = nextedge
				right = not right
			crv = bpy.data.curves.new("CelticKnot", type = "CURVE")
			crv.dimensions = '3D'
			crv.splines.new(type = 'BEZIER')
			crv.fill_mode = 'FULL'
			crv.bevel_depth = self.bDepth
			crv.bevel_resolution = self.bRes
			spline = crv.splines[0]
			makeBezier(spline, vertList, vectors, self.handleScale)
			new_obj = object_data_add(bpy.context, crv)
		
		return {'FINISHED'}
		
def CW(n, A, B, C):
	return True if (n.dot((A-C).cross(B-C)) <= 0) else False
		
def CCW(n, A, B, C):
	return True if (n.dot((A-C).cross(B-C)) >= 0) else False
		
def makeBezier(spline, vertList, vectors, hscale):
	numPoints = (len(vertList) / 3) - 1
	spline.bezier_points.add(numPoints)
	spline.bezier_points.foreach_set("co", vertList)
	spline.use_cyclic_u = True
	counter = 0
	for point in spline.bezier_points:
		point.handle_left = point.co + vectors[counter]*hscale
		point.handle_right = point.co - vectors[counter]*hscale
		counter += 1 
		
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
