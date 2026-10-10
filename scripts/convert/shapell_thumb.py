import bpy, mathutils
sc=bpy.context.scene
arm=[o for o in bpy.data.objects if o.type=='ARMATURE'][0]
head=arm.matrix_world @ arm.data.bones['Head'].head_local
cam=bpy.data.cameras.new('c'); co=bpy.data.objects.new('c',cam); sc.collection.objects.link(co); sc.camera=co
cam.lens=85
co.location=(head.x, head.y-1.6, head.z+0.02)
co.rotation_euler=(1.5708,0,0)
sc.render.engine='CYCLES'; sc.cycles.samples=24; sc.cycles.device='CPU'
sc.render.resolution_x=sc.render.resolution_y=512
sc.render.film_transparent=True

w=sc.world or bpy.data.worlds.new('w'); sc.world=w; w.use_nodes=True
w.node_tree.nodes['Background'].inputs[1].default_value=1.2
sun=bpy.data.lights.new('s','SUN'); so=bpy.data.objects.new('s',sun); sc.collection.objects.link(so); so.rotation_euler=(0.9,0,0.3); sun.energy=2.5
sc.render.filepath='/tmp/thumb_raw.png'
bpy.ops.render.render(write_still=True)
print('HEAD',tuple(head))
