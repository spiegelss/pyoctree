
import vtk
import numpy as np
import matplotlib.pyplot as plt
import octree

# Read in stl file
reader = vtk.vtkSTLReader()
reader.SetFileName('knot.stl')
reader.MergingOn()
stl = reader.GetOutput()
stl.Update()

#writer = vtk.vtkSTLWriter()
#writer.SetFileName('knot_out.stl')
#writer.SetInput(stl)
#writer.Write()

# Get array of point coordinates
numPoints   = stl.GetNumberOfPoints()
pointCoords = np.zeros((numPoints,3),dtype=float)
for i in xrange(numPoints):
    pointCoords[i,:] = stl.GetPoint(i)
    
# Get polygon connectivity
numPolys     = stl.GetNumberOfCells()
connectivity = np.zeros((numPolys,3),dtype=np.int32)
for i in xrange(numPolys):
    tri = stl.GetCell(i)
    ids = tri.GetPointIds()
    for j in range(3):
        connectivity[i,j] = ids.GetId(j)

# Create octree structure for stl poly mesh
tree = octree.PyOctree(pointCoords,connectivity)

# Visualise octree using Paraview
def getOctreeRep(octnode):
    global connect, numVerts, pc
    if not octnode.isLeaf:
        for branch in octnode.branches:
            pos  = branch.position
            size = branch.size
            halfSize = size/2.0
            n1 = pos + np.array([-halfSize,-halfSize,-halfSize])
            n2 = pos + np.array([+halfSize,-halfSize,-halfSize])  
            n3 = pos + np.array([+halfSize,+halfSize,-halfSize])  
            n4 = pos + np.array([-halfSize,+halfSize,-halfSize])  
            n5 = pos + np.array([-halfSize,-halfSize,+halfSize])
            n6 = pos + np.array([+halfSize,-halfSize,+halfSize])  
            n7 = pos + np.array([+halfSize,+halfSize,+halfSize])  
            n8 = pos + np.array([-halfSize,+halfSize,+halfSize])  
            verts = [n1,n2,n3,n4,n5,n6,n7,n8]
            connect.append(range(numVerts,numVerts+8))  
            numVerts += len(verts)
            for v in verts:
                pc.InsertNextTuple(tuple(v)) 
            getOctreeRep(branch)
    
connect = []
pc = vtk.vtkFloatArray()
pc.SetNumberOfComponents(3)
numVerts = 0    
getOctreeRep(tree.root)

pnts = vtk.vtkPoints()
pnts.SetData(pc)

uGrid = vtk.vtkUnstructuredGrid()
uGrid.SetPoints(pnts)
numElems = len(connect)
for i in range(numElems):
    hexelem = vtk.vtkHexahedron()
    c = connect[i]
    for j in range(8):
        hexelem.GetPointIds().SetId(j,c[j])    
    uGrid.InsertNextCell(hexelem.GetCellType(), hexelem.GetPointIds())  

writer = vtk.vtkXMLUnstructuredGridWriter()
writer.SetFileName('octree.vtu')
writer.SetInput(uGrid)
writer.SetDataModeToAscii()
writer.Write()

# Perform shadowing
from skimage import filter
width,height = 200,200
xr = np.linspace(-0.0526,3.06,width)
yr = np.linspace(5.77,8.88,height)
rayPointList = []
for x in xr:
    for y in yr:
        rayPointList.append([[x,y,6.0],[x,y,0.0]])
rayPointList = np.array(rayPointList,dtype=np.float32)

proj  = tree.rayIntersections(rayPointList)
proj  = proj.reshape((width,height))
proj  = proj.astype(float)
proj  = proj[::-1,:]
edges = filter.canny(proj,sigma=1.0)

fig, (ax1, ax2) = plt.subplots(nrows=1, ncols=2, figsize=(10, 4));
ax1.imshow(proj, cmap=plt.cm.gray)
ax1.axis('off')
ax1.set_title('Projected object', fontsize=16)
ax2.imshow(edges, cmap=plt.cm.gray)
ax2.axis('off')
ax2.set_title('Edge detection (Canny filter)', fontsize=16);
fig.subplots_adjust(wspace=0.1, hspace=0.02, top=0.95, bottom=0.02, left=0.02, right=0.98)
plt.show()

