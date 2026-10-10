import bpy, os, sys
bpy.ops.preferences.addon_enable(module='VRM_Addon_for_Blender-release')
TEX='/tmp/shtex/'
texmap={'blazer':'shapell_blazer.png','body':'shapell_body.png','clothes':'shapell_clothes.png','faceex01':'shapell_faceex01.png','Hair':'shapell_hair.png'}
for m in bpy.data.materials:
    if m.name not in texmap: continue
    m.use_nodes=True
    nt=m.node_tree; nt.nodes.clear()
    out=nt.nodes.new('ShaderNodeOutputMaterial'); bsdf=nt.nodes.new('ShaderNodeBsdfPrincipled')
    img=nt.nodes.new('ShaderNodeTexImage'); img.image=bpy.data.images.load(TEX+texmap[m.name])
    nt.links.new(img.outputs['Color'],bsdf.inputs['Base Color'])
    bsdf.inputs['Roughness'].default_value=1.0
    bsdf.inputs['Metallic'].default_value=0.0
    if m.name in ('faceex01','Hair'):
        nt.links.new(img.outputs['Alpha'],bsdf.inputs['Alpha'])
        m.blend_method='CLIP' if m.name=='Hair' else 'BLEND'
    nt.links.new(bsdf.outputs['BSDF'],out.inputs['Surface'])

for m in bpy.data.materials:
    if m.name not in texmap: continue
    mt=m.vrm_addon_extension.mtoon1
    mt.enabled=True
    tex=mt.pbr_metallic_roughness.base_color_texture.index
    print('MTOON', m.name, tex.source.name if tex.source else None)
    if not tex.source: tex.source=bpy.data.images.load(TEX+texmap[m.name])
    mt.extensions.vrmc_materials_mtoon.shade_multiply_texture.index.source=tex.source
    mt.extensions.vrmc_materials_mtoon.shade_color_factor=(0.85,0.78,0.82)
    if m.name in ('faceex01','Hair'):
        mt.alpha_mode='MASK' if m.name=='Hair' else 'BLEND'
arm=[o for o in bpy.data.objects if o.type=='ARMATURE'][0]
ext=arm.data.vrm_addon_extension
bpy.context.view_layer.objects.active=arm
bpy.ops.object.mode_set(mode='OBJECT')
ext.spec_version='1.0'
hb=ext.vrm1.humanoid.human_bones
M={'hips':'Hips','spine':'Spine','chest':'Chest','neck':'Neck','head':'Head','left_eye':'LeftEye','right_eye':'RightEye'}
for side,S in (('left','L'),('right','R')):
    M.update({f'{side}_upper_leg':f'UpperLeg.{S}',f'{side}_lower_leg':f'LowerLeg.{S}',f'{side}_foot':f'Foot.{S}',f'{side}_toes':f'Toes.{S}',
      f'{side}_shoulder':f'Shoulder.{S}',f'{side}_upper_arm':f'UpperArm.{S}',f'{side}_lower_arm':f'LowerArm.{S}',f'{side}_hand':f'Hand.{S}',
      f'{side}_thumb_metacarpal':f'Thumb Proximal.{S}',f'{side}_thumb_proximal':f'Thumb Intermediate.{S}',f'{side}_thumb_distal':f'Thumb Distal.{S}'})
    for f in ('index','middle','ring','little'):
        for a,b in (('proximal','Proximal'),('intermediate','Intermediate'),('distal','Distal')):
            M[f'{side}_{f}_{a}']=f'{f.capitalize()} {b}.{S}'
for k,v in M.items():
    getattr(hb,k).node.bone_name=v
print('HB',sum(1 for k in M if getattr(hb,k).node.bone_name))
P=ext.vrm1.expressions.preset
def ex(name,keys):
    e=getattr(P,name)
    for k,w in keys:
        b=e.morph_target_binds.add(); b.node.mesh_object_name='Body'; b.index=k; b.weight=w
ex('aa',[('A',1)]);ex('ih',[('I',1)]);ex('ou',[('U',1)]);ex('ee',[('E',1)]);ex('oh',[('O',1)])
ex('blink',[('Eye_toji',1)]);ex('blink_left',[('eye_toji_l',1)]);ex('blink_right',[('eye_toji_r',1)])
ex('happy',[('Eye_nico',1),('Mouth_ワ',1)]);ex('angry',[('Eye_jito',1),('EyeBrow_down',1)])
ex('sad',[('EyeBrow_down',0.6),('Mouth_△',0.5)]);ex('relaxed',[('Eye_nico',1),('Mouth_Open',0.3)])
ex('surprised',[('Mouth_Open',1),('Eye_out',0)])
used={'Basis','A','I','U','E','O','Eye_toji','eye_toji_l','eye_toji_r','Eye_nico','Mouth_ワ','Eye_jito','EyeBrow_down','Mouth_△','Mouth_Open'}
ob=bpy.data.objects['Body']
for kb in list(ob.data.shape_keys.key_blocks):
    if kb.name not in used: ob.shape_key_remove(kb)
# spring bones (VRMC_springBone): one spring per chain
sb=ext.spring_bone1
def chains(root):
    out=[]
    def walk(b,chain):
        chain=chain+[b.name]
        kids=[c for c in b.children if not c.name.endswith('_end')]
        if not kids: out.append(chain)
        for c in kids: walk(c,chain)
    for c in arm.data.bones[root].children: walk(c,[])
    return out
for root,stiff,drag,grav in [('HairRoot',0.9,0.4,0.0),('SkirtRoot',1.4,0.5,0.1),('BackRibbonRoot',0.8,0.4,0.1),('StrapRoot',1.0,0.5,0.1)]:
    if root not in arm.data.bones: continue
    for ch in chains(root):
        bpy.ops.vrm.add_spring_bone1_spring(armature_object_name=arm.name)
        sp=sb.springs[-1]; sp.vrm_name=root
        for n in ch:
            bpy.ops.vrm.add_spring_bone1_spring_joint(armature_object_name=arm.name, spring_index=len(sb.springs)-1)
            j=sp.joints[-1]; j.node.bone_name=n; j.stiffness=stiff; j.drag_force=drag; j.gravity_power=grav; j.hit_radius=0.02
print('SPRINGS',len(sb.springs))
m=ext.vrm1.meta
m.vrm_name='Shapell'; m.version='1.0.3'
if not len(m.authors): m.authors.add()
m.authors[0].value='lowteq'
r=m.references.add(); r.value='https://booth.pm/ja/items/1349366'
m.avatar_permission='everyone'; m.commercial_usage='corporation'; m.credit_notation='unnecessary'
m.allow_redistribution=True; m.modification='allowModificationRedistribution'
m.other_license_url='https://creativecommons.org/publicdomain/zero/1.0/'
if os.path.exists('/tmp/shapell_thumb.png'): m.thumbnail_image=bpy.data.images.load('/tmp/shapell_thumb.png')
r=bpy.ops.export_scene.vrm(filepath=sys.argv[-1], armature_object_name=arm.name)
print('EXPORT',r,os.path.getsize(sys.argv[-1]))
