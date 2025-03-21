import bpy
import bmesh
import os
import sys
import time
import mathutils
from math import pi, radians, sin, cos
from contextlib import contextmanager

#Hides select Blender console output 
@contextmanager
def suppress_stdout():
    with open(os.devnull, "w") as devnull:
        old_stdout = sys.stdout
        sys.stdout = devnull
        try:  
            yield
        finally:
            sys.stdout = old_stdout



###################
## Blender Setup ##
###################

bpy.context.scene.unit_settings.system = 'METRIC'
bpy.context.scene.unit_settings.scale_length = 1
bpy.context.scene.unit_settings.length_unit = 'MILLIMETERS'
bpy.context.scene.cursor.location =  [0, 0, 0]
bpy.context.scene.cursor.rotation_euler =  [0, 0, 0]
bpy.ops.preferences.addon_enable(module='mesh_tools')
bpy.ops.preferences.addon_enable(module='object_print3d_utils')

start_time = time.time()



######################
## Shape Parameters ##
######################

nrows = 5                       # key rows
ncols = 6                       # key columns

alpha = pi / 12.0               # curvature of the columns
beta  = pi / 36.0               # curvature of the rows
centerrow = nrows - 3           # controls front_back tilt
centercol = 3                   # controls left_right tilt / tenting (higher number is more tenting)
tenting_angle = pi / 12.0       # or, change this for more precise tenting control
sa_profile_key_height = 12.7

if nrows > 5:
    column_style = "orthographic"
else:
    column_style = "standard"
#column_style = "cylindrical"


def column_offset(column: int) -> list:
    if column == 2:
        return [0, 2.82, -4.5]
    elif column >= 4:
        return [0, -12, 5.64]   # original [0 -5.8 5.64]
    else:
        return [0, 0, 0]


thumb_offsets = [6, -3, 7]
th_layout = [[ [ -4, -35, 52],  (-56.3, -43.3, -23.5)],
             [ [-16, -33, 54],  (-37.8, -55.3, -25.3)],
             [ [  6, -34, 40],  (  -51,   -25,   -12)],
             [ [ -6, -34, 48],  (  -29,   -40,   -13)],
             [ [ 10, -23, 10],  (  -32,   -15,    -2)],
             [ [ 10, -23, 10],  (  -12,   -16,     3)]]
             

keyboard_z_offset = 9                       # controls overall height# original=9 with centercol=3# use 16 for centercol=2

extra_width = 2.5                           # extra space between the base of keys# original= 2
extra_height = 1.0                          # original= 0.5

wall_z_offset = -15                         # length of the first downward_sloping part of the wall (negative)
wall_xy_offset = 5                          # offset in the x and/or y direction for the first downward_sloping part of the wall (negative)
wall_thickness = 2                          # wall thickness parameter# originally 5
left_wall_x_offset = 2 + wall_xy_offset     # shape of left wall
left_wall_z_offset = 3                      # shape of left wall
key_well_offset =  0.5                      # depth of key from body



###################################
## Shell Parameters and Features ##
###################################

geode_mode = False                # Forces other perameters

body_thickness = 2
body_subsurf_level = 1
relaxed_mesh = True
switch_support = True
loligagger_port = True
wide_pinky = True
ameoba_cut = False                # May cause holes in case walls. Possible fix is to increase wall_xy_offset
hot_swap = False                  # Unused Currently
magnet_bottom = True             
magnet_diameter = 6.2
magnet_height = 2.2
bottom_thickness = 3              # Thickness of Bottom Plate



#######################
## General variables ##
#######################

lastrow = nrows - 1
cornerrow = lastrow - 1
lastcol = ncols - 1



########################
## Create Collections ##
########################

for collection in ["AXIS", "KEYCAP_PROJECTION_OUTER", "KEYCAP_PROJECTION_INNER", "SWITCH_PROJECTION", "SWITCH_PROJECTION_INNER", "SWITCH_HOLE", "SWITCH_SUPPORT"]:
    bpy.context.scene.collection.children.link(bpy.data.collections.new(collection))



############################
## Initialize Tool Shapes ##
############################

print("\n\n{:.2f}".format(time.time()-start_time), "- Initializing Tool Shapes")


bpy.ops.object.empty_add(type='PLAIN_AXES', align='WORLD', location=(0, 0, 0), scale=(1, 1, 1))
bpy.context.selected_objects[0].name = "key_axis"
bpy.ops.object.transform_apply(location=True, rotation=False, scale=True)

keyswitch_height = 14.4
keyswitch_width = 14.4
mount_thickness = 4

mount_height = keyswitch_height + 3
mount_width = keyswitch_width + 3

ameoba_height = 20
ameoba_width = 16.5
ameoba_thickness = 3

for size in [1, 1.5]:
    for shape in [['switch_projection', (0, 0, 5*mount_thickness-1), (mount_width, mount_height*size,  10*mount_thickness)],
                  ['switch_projection_inner', (0, 0, 5*mount_thickness-1), (mount_width+1.8, mount_height*size+1.8, 10*mount_thickness)],
                  ['keycap_projection_outer', (0, 0, mount_thickness + 4 + 2), (19, 19*size, 8)],
                  ['keycap_projection_inner', (0, 0, mount_thickness + 4 + 2 - 2), (19+2, 19*size+2, 8)],
                  ['switch_hole', (0, 0, 0), (keyswitch_width, keyswitch_height, 2.1*mount_thickness)],
                  ['ameoba_cut', (0, 0, -ameoba_thickness/2-0.1), (ameoba_width, ameoba_height, ameoba_thickness)],
                  ['nub_cube', ((1.5 / 2) + 0.5*(keyswitch_width-0.01), 0, 0.5*mount_thickness), (1.5, 2.75, mount_thickness - 0.01)]]:
        
        bpy.ops.mesh.primitive_cube_add(size=1, location=shape[1], scale=shape[2])
        bpy.context.selected_objects[0].name = shape[0] + "_" + str(size) + "u"
        
        if shape[0] in ['switch_projection', 'switch_projection_inner']:
            bpy.ops.object.mode_set(mode = 'EDIT')
            bpy.ops.mesh.select_all(action='DESELECT')
            grid_mesh = bmesh.from_edit_mesh(bpy.context.object.data)
            grid_mesh.verts.ensure_lookup_table()
            for vertex in [0, 2, 4, 6]:
                grid_mesh.verts[vertex].select = True
            bpy.ops.object.vertex_group_assign_new()
            bpy.ops.mesh.select_all(action='SELECT')
            bpy.ops.object.mode_set(mode = 'OBJECT')
            bpy.data.objects[shape[0] + "_" + str(size) + "u"].vertex_groups['Group'].name = 'bottom_project'
        
        elif shape[0] in ['nub_cube']:
            bpy.ops.mesh.primitive_cylinder_add(vertices=50, radius=1.0 - 0.005, depth=2.75, location=(keyswitch_width / 2, 0, 1), rotation=(pi / 2, 0, 0))
            bpy.context.selected_objects[0].name = "switch_support_" + str(size) + "u"
            bpy.data.objects[shape[0] + "_" + str(size) + "u"].select_set(True)
            bpy.ops.object.join()
            bpy.ops.object.mode_set(mode = 'EDIT')
            bpy.ops.mesh.convex_hull()
            bpy.ops.mesh.dissolve_limited(angle_limit=radians(5))
            bpy.ops.object.mode_set(mode = 'OBJECT')
            bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
            bpy.ops.object.origin_set(type='ORIGIN_CURSOR', center='MEDIAN')
            bpy.ops.object.modifier_add(type='MIRROR')
            bpy.ops.object.modifier_apply(modifier="Mirror")
            
    bpy.context.view_layer.objects.active = bpy.data.objects["switch_hole_" + str(size) + "u"]
    
    if (ameoba_cut):
        bpy.ops.object.modifier_add(type='BOOLEAN')
        bpy.context.object.modifiers["Boolean"].operation = 'UNION'
        bpy.context.object.modifiers["Boolean"].object = bpy.data.objects["ameoba_cut_" + str(size) + "u"]
        bpy.ops.object.modifier_apply(modifier="Boolean")

    bpy.ops.object.select_all(action='DESELECT')
    bpy.data.objects["ameoba_cut_" + str(size) + "u"].select_set(True)
    with suppress_stdout(): bpy.ops.object.delete()



##########################
## FINGER KEY LOCATIONS ##
##########################

print("{:.2f}".format(time.time()-start_time), "- Generate Finger Topology")

cap_top_height = mount_thickness + sa_profile_key_height
row_radius = ((mount_height + extra_height) / 2) / (sin(alpha / 2)) + cap_top_height
column_radius = (((mount_width + extra_width) / 2) / (sin(beta / 2))) + cap_top_height


for column in range(ncols):
    for row in range(nrows):
        if (column in [2, 3]) or (not row == lastrow):
            
            if column==ncols-1 and wide_pinky:
                column_angle = beta * (centercol - column - 0.25)
            else:
                column_angle = beta * (centercol - column)
            tool_identifier =  " - " + str(column) + ", " + str(row)

            # CREATE tools for each key location and link into respective Collection
            for tool in [['AXIS',                           'key_axis',                          'key_axis'                           ],
                         ['KEYCAP_PROJECTION_OUTER',        'keycap_projection_outer_1u',        'keycap_projection_outer_1.5u'       ],
                         ['KEYCAP_PROJECTION_INNER',        'keycap_projection_inner_1u',        'keycap_projection_inner_1.5u'       ],
                         ['SWITCH_PROJECTION',              'switch_projection_1u',              'switch_projection_1u'               ],
                         ['SWITCH_PROJECTION_INNER',        'switch_projection_inner_1u',        'switch_projection_inner_1.5u'       ],
                         ['SWITCH_HOLE',                    'switch_hole_1u',                    'switch_hole_1.5u'                   ],
                         ['SWITCH_SUPPORT',                 'switch_support_1u',                 'switch_support_1.5u'                ]]:
                bpy.ops.object.select_all(action='DESELECT')
                if column==ncols-1 and wide_pinky:
                    bpy.ops.object.add_named(name = tool[2])
                    bpy.context.selected_objects[-1].name = tool[0].lower() + tool_identifier
                    bpy.ops.object.select_all(action='DESELECT')
                    if tool[0] not in ['AXIS', 'SWITCH_SUPPORT']:
                        bpy.data.objects[tool[0].lower() + tool_identifier].select_set(True)
                        bpy.ops.transform.rotate(value=1.5708, orient_axis='Z', orient_type='GLOBAL', orient_matrix=((1, 0, 0), (0, 1, 0), (0, 0, 1)), orient_matrix_type='VIEW', mirror=True, use_proportional_edit=False, proportional_edit_falloff='SMOOTH', proportional_size=0.001, use_proportional_connected=False, use_proportional_projected=False)
                else:
                    bpy.ops.object.add_named(name = tool[1])
                    bpy.context.selected_objects[-1].name = tool[0].lower() + tool_identifier

                bpy.data.collections[tool[0]].objects.link(bpy.data.objects[tool[0].lower() + tool_identifier])
                bpy.context.collection.objects.unlink(bpy.data.objects[tool[0].lower() + tool_identifier])
                
            bpy.ops.object.select_all(action='DESELECT')
            # CREATE referecnce location for placing thumb cluster
            if (column == 1 and row == cornerrow):
                bpy.ops.object.empty_add(type='CUBE', align='WORLD', location=(mount_height/2, -mount_width/2, 0), scale=(1, 1, 1))
                bpy.context.active_object.name = "thumb_orgin"
                bpy.data.collections['AXIS'].objects.link(bpy.data.objects["thumb_orgin"])
                bpy.context.collection.objects.unlink(bpy.data.objects["thumb_orgin"])

            # Select all tools
            for tool in ['AXIS', 'KEYCAP_PROJECTION_OUTER', 'KEYCAP_PROJECTION_INNER', 'SWITCH_PROJECTION', 'SWITCH_PROJECTION_INNER', 'SWITCH_HOLE', 'SWITCH_SUPPORT']:
                bpy.data.objects[tool.lower() + tool_identifier].select_set(True)
            
            # Apply transfomations to each set tools
            if (column_style == "standard"):
                bpy.ops.transform.rotate(value=(-alpha * (centerrow - row)), orient_axis='X', center_override=(0.0, 0.0, row_radius))
                bpy.ops.transform.rotate(value=(-column_angle), orient_axis='Y', center_override=(0.0, 0.0, column_radius))
                bpy.ops.transform.translate(value=column_offset(column), orient_type='GLOBAL', orient_matrix=((1, 0, 0), (0, 1, 0), (0, 0, 1)), orient_matrix_type='GLOBAL', constraint_axis=(True, True, True),  mirror=True, use_proportional_edit=False, proportional_edit_falloff='SMOOTH', proportional_size=1, use_proportional_connected=False, use_proportional_projected=False)
                
            elif (column_style == "orthographic"):
                bpy.ops.transform.rotate(value=(-alpha * (centerrow - row)), orient_axis='X', center_override=(0.0, 0.0, row_radius))
                bpy.ops.transform.rotate(value=(-column_angle), orient_axis='Y', center_override=(0.0, 0.0, 0.0))
                if column==ncols-1 and wide_pinky:
                    bpy.ops.transform.translate(value=( (column - centercol + 0.25)*(1 + column_radius * sin(beta)), 0, column_radius * (1 - cos(column_angle))), orient_type='GLOBAL', orient_matrix=((1, 0, 0), (0, 1, 0), (0, 0, 1)), orient_matrix_type='GLOBAL', constraint_axis=(True, True, True),  mirror=True, use_proportional_edit=False, proportional_edit_falloff='SMOOTH', proportional_size=1, use_proportional_connected=False, use_proportional_projected=False)
                else:
                    bpy.ops.transform.translate(value=( (column - centercol)*(1 + column_radius * sin(beta)), 0, column_radius * (1 - cos(column_angle))), orient_type='GLOBAL', orient_matrix=((1, 0, 0), (0, 1, 0), (0, 0, 1)), orient_matrix_type='GLOBAL', constraint_axis=(True, True, True),  mirror=True, use_proportional_edit=False, proportional_edit_falloff='SMOOTH', proportional_size=1, use_proportional_connected=False, use_proportional_projected=False)
                bpy.ops.transform.translate(value=column_offset(column), orient_type='GLOBAL', orient_matrix=((1, 0, 0), (0, 1, 0), (0, 0, 1)), orient_matrix_type='GLOBAL', constraint_axis=(True, True, True),  mirror=True, use_proportional_edit=False, proportional_edit_falloff='SMOOTH', proportional_size=1, use_proportional_connected=False, use_proportional_projected=False)
            
            elif (column_style == "cylindrical"):
                bpy.ops.transform.rotate(value=(-alpha * (centerrow - row)), orient_axis='X', center_override=(0.0, 0.0, row_radius))
                if column==ncols-1 and wide_pinky:
                    bpy.ops.transform.translate(value=( (column - centercol + 0.25)*(1 + column_radius * sin(beta)), 0, column_radius * (1 - cos(column_angle))), orient_type='GLOBAL', orient_matrix=((1, 0, 0), (0, 1, 0), (0, 0, 1)), orient_matrix_type='GLOBAL', constraint_axis=(True, True, True),  mirror=True, use_proportional_edit=False, proportional_edit_falloff='SMOOTH', proportional_size=1, use_proportional_connected=False, use_proportional_projected=False)
                else:
                    bpy.ops.transform.translate(value=( (column - centercol)*(1 + column_radius * sin(beta)), 0, column_radius * (1 - cos(column_angle))), orient_type='GLOBAL', orient_matrix=((1, 0, 0), (0, 1, 0), (0, 0, 1)), orient_matrix_type='GLOBAL', constraint_axis=(True, True, True),  mirror=True, use_proportional_edit=False, proportional_edit_falloff='SMOOTH', proportional_size=1, use_proportional_connected=False, use_proportional_projected=False)
                bpy.ops.transform.translate(value=column_offset(column), orient_type='GLOBAL', orient_matrix=((1, 0, 0), (0, 1, 0), (0, 0, 1)), orient_matrix_type='GLOBAL', constraint_axis=(True, True, True),  mirror=True, use_proportional_edit=False, proportional_edit_falloff='SMOOTH', proportional_size=1, use_proportional_connected=False, use_proportional_projected=False)

                
            bpy.ops.transform.rotate(value=(-tenting_angle), orient_axis='Y', center_override=(0.0, 0.0, 0.0))
            bpy.ops.transform.translate(value=(0, 0, keyboard_z_offset), orient_type='GLOBAL', orient_matrix=((1, 0, 0), (0, 1, 0), (0, 0, 1)), orient_matrix_type='GLOBAL', mirror=True, use_proportional_edit=False, proportional_edit_falloff='SMOOTH', proportional_size=1, use_proportional_connected=False, use_proportional_projected=False)



##########################
## THUMB KEY LOCATIONS ##
##########################

print("{:.2f}".format(time.time()-start_time), "- Generate Thumb Topology")
             
for key in range(len(th_layout)):
    
    tool_identifier =  " - thumb - " + str(key)
    
    # Create tools for each key location and link into respective Collection
    for tool in [['AXIS',                           'key_axis',                          'key_axis'                           ],
                 ['KEYCAP_PROJECTION_OUTER',        'keycap_projection_outer_1u',        'keycap_projection_outer_1.5u'       ],
                 ['KEYCAP_PROJECTION_INNER',        'keycap_projection_inner_1u',        'keycap_projection_inner_1.5u'       ],
                 ['SWITCH_PROJECTION',              'switch_projection_1u',              'switch_projection_1.5u'             ],
                 ['SWITCH_PROJECTION_INNER',        'switch_projection_inner_1u',        'switch_projection_inner_1.5u'       ],
                 ['SWITCH_HOLE',                    'switch_hole_1u',                    'switch_hole_1.5u'                   ],
                 ['SWITCH_SUPPORT',                 'switch_support_1u',                 'switch_support_1.5u'                ]]:
        bpy.ops.object.select_all(action='DESELECT')
        if (key>3):
            bpy.ops.object.add_named(name = tool[2])
        else:
            bpy.ops.object.add_named(name = tool[1])
        bpy.context.selected_objects[-1].name = tool[0].lower() + tool_identifier
        bpy.data.collections[tool[0]].objects.link(bpy.data.objects[tool[0].lower() + tool_identifier])
        bpy.context.collection.objects.unlink(bpy.data.objects[tool[0].lower() + tool_identifier])

       
    # Select all tools
    bpy.ops.object.select_all(action='DESELECT')
    for tool in ['AXIS', 'KEYCAP_PROJECTION_OUTER', 'KEYCAP_PROJECTION_INNER', 'SWITCH_PROJECTION', 'SWITCH_PROJECTION_INNER',  'SWITCH_HOLE', 'SWITCH_SUPPORT']:
        bpy.data.objects[tool.lower() + tool_identifier].select_set(True)

    # Apply rotation    
    bpy.ops.transform.rotate(value=-radians(th_layout[key][0][0]), orient_axis='X', center_override=(0.0, 0.0, 0.0))
    bpy.ops.transform.rotate(value=-radians(th_layout[key][0][1]), orient_axis='Y', center_override=(0.0, 0.0, 0.0))
    bpy.ops.transform.rotate(value=-radians(th_layout[key][0][2]), orient_axis='Z', center_override=(0.0, 0.0, 0.0))

    # Move keys into position
    bpy.ops.transform.translate(value=bpy.data.objects['thumb_orgin'].location, orient_type='GLOBAL', orient_matrix=((1, 0, 0), (0, 1, 0), (0, 0, 1)), orient_matrix_type='GLOBAL', mirror=True, use_proportional_edit=False, proportional_edit_falloff='SMOOTH', proportional_size=1, use_proportional_connected=False, use_proportional_projected=False)
    bpy.ops.transform.translate(value=thumb_offsets, orient_type='GLOBAL', orient_matrix=((1, 0, 0), (0, 1, 0), (0, 0, 1)), orient_matrix_type='GLOBAL', mirror=True, use_proportional_edit=False, proportional_edit_falloff='SMOOTH', proportional_size=1, use_proportional_connected=False, use_proportional_projected=False)
    bpy.ops.transform.translate(value=th_layout[key][1], orient_type='GLOBAL', orient_matrix=((1, 0, 0), (0, 1, 0), (0, 0, 1)), orient_matrix_type='GLOBAL', mirror=True, use_proportional_edit=False, proportional_edit_falloff='SMOOTH', proportional_size=1, use_proportional_connected=False, use_proportional_projected=False)




bpy.ops.object.select_all(action='DESELECT')

for shape in ['keycap_projection_outer_', 'keycap_projection_inner_', 'switch_projection_', 'switch_projection_inner_', 'switch_hole_', 'switch_support_']:
    for size in [1, 1.5]:
        bpy.data.objects[shape + str(size) + 'u' ].select_set(True)
bpy.data.objects['key_axis'].select_set(True)
with suppress_stdout(): bpy.ops.object.delete()






##################
## FINGER PLATE ##
##################

print("{:.2f}".format(time.time()-start_time), "- Generate Finger Plate")

bpy.ops.mesh.primitive_grid_add(x_subdivisions=2*nrows-1, y_subdivisions=2*ncols-1, size=1, rotation=(0, 0, -pi/2))
bpy.ops.transform.resize(value=(2*ncols-1, 2*nrows-1, 1))
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
bpy.context.selected_objects[0].name = "finger_plate"          


bpy.ops.object.mode_set(mode = 'EDIT')
bpy.ops.mesh.select_all(action='DESELECT')
face_is_a_key = []

grid_mesh = bmesh.from_edit_mesh(bpy.context.object.data)
grid_mesh.verts.ensure_lookup_table()
grid_mesh.edges.ensure_lookup_table()
grid_mesh.faces.ensure_lookup_table()

            
for column in range(ncols):
    for row in range(nrows):
        if (column in [2, 3]) or (not row == lastrow):
            
            face_is_a_key.append(row * 2 + column* 2*(2*nrows-1))            
            grid_mesh.faces[face_is_a_key[-1]].select = True
            
            bpy.ops.object.vertex_group_assign_new()
            bpy.data.objects['finger_plate'].vertex_groups['Group'].name = 'switch - '+ str(column) + ', ' + str(row)

            switch_size = 1
            if column==ncols-1 and wide_pinky: switch_size = 1.5
            bpy.ops.transform.resize(value=(mount_height*switch_size + 0.25, mount_width + 0.25, 1))
                        
            bpy.ops.transform.translate(value=-grid_mesh.faces[face_is_a_key[-1]].calc_center_median(), orient_type='GLOBAL')
            bpy.ops.transform.translate(value=(0, 0, mount_thickness+key_well_offset), orient_type='GLOBAL')
            
            bpy.ops.transform.rotate(value=-bpy.data.objects['axis - '+ str(column) + ', ' + str(row)].rotation_euler[0], orient_axis='X', center_override=(0.0, 0.0, 0.0))
            bpy.ops.transform.rotate(value=-bpy.data.objects['axis - '+ str(column) + ', ' + str(row)].rotation_euler[1], orient_axis='Y', center_override=(0.0, 0.0, 0.0))
            bpy.ops.transform.rotate(value=-bpy.data.objects['axis - '+ str(column) + ', ' + str(row)].rotation_euler[2], orient_axis='Z', center_override=(0.0, 0.0, 0.0))
            bpy.ops.transform.translate(value=bpy.data.objects['axis - '+ str(column) + ', ' + str(row)].location, orient_type='GLOBAL')
            bpy.ops.mesh.select_all(action='DESELECT')


for vertex_group_name in ['key_finger', 'finger_TOP', 'finger_LEFT', 'finger_RIGHT', 'finger_BOTTOM', 'finger_corner_BL', 'finger_corner_TL', 'finger_corner_TR', 'finger_corner_BR', 'RING_0', 'RING_1', 'RING_2', 'RING_3', 'BRIDGE_LEFT', 'BRIDGE_MID', 'BRIDGE_RIGHT', 'BRIDGE_LEFT_RING_0', 'BRIDGE_RIGHT_RING_0']:
    bpy.ops.object.vertex_group_assign_new()
    bpy.data.objects['finger_plate'].vertex_groups['Group'].name = vertex_group_name

# Vertex Group - key
for face in face_is_a_key:
    grid_mesh.faces[face].select = True
bpy.ops.object.vertex_group_set_active(group='key_finger')
bpy.ops.object.vertex_group_assign()
bpy.ops.mesh.select_all(action='DESELECT')


# Create vertex group faces
for side in [['finger_TOP',          [0, nrows*(ncols-1)*4 + nrows*2]],
             ['finger_LEFT',         [0, nrows*2-3]],
             ['finger_RIGHT',        [nrows*(ncols-1)*4 + nrows*2, nrows*ncols*4-3]],
             ['finger_BOTTOM',       [nrows*14-1, nrows*ncols*4-3]],
             ['finger_corner_BL',    [nrows*2-3]],
             ['finger_corner_TL',    [0]],
             ['finger_corner_TR',    [nrows*(ncols-1)*4 + nrows*2]],
             ['finger_corner_BR',    [nrows*ncols*4-3]],
             ['BRIDGE_LEFT',         [nrows*2-3, nrows*6-3]],
             ['BRIDGE_MID',          [nrows*6-3, nrows*10-1]],
             ['BRIDGE_RIGHT',        [nrows*10-1, nrows*14-1]],
             ['BRIDGE_LEFT_RING_0',  [nrows*2-3]],
             ['BRIDGE_RIGHT_RING_0', [nrows*14-1]]]:

    bpy.ops.object.vertex_group_set_active(group=side[0])
    for vertex in side[1]:
        grid_mesh.verts[vertex].select = True
    bpy.ops.object.vertex_group_assign()
    bpy.ops.mesh.select_all(action='DESELECT')


# Create temporary vertex groups for adding faces
for side in [['CORRECTION_1', [nrows*8 - 3,  nrows*10 - 2]],
             ['CORRECTION_2', [nrows*16 - 1, nrows*20 - 3]]]:

    for vertex in side[1]:
        grid_mesh.verts[vertex].select = True
    bpy.ops.object.vertex_group_assign_new()
    bpy.data.objects['finger_plate'].vertex_groups['Group'].name = side[0]
    bpy.ops.mesh.select_all(action='DESELECT')


# Remove unused faces
bpy.ops.object.vertex_group_set_active(group='key_finger')
bpy.ops.object.vertex_group_select()
bpy.ops.mesh.select_mode(type="FACE")
bpy.ops.mesh.select_all(action='INVERT')
bpy.ops.mesh.delete(type='FACE')
bpy.ops.mesh.select_mode(type="VERT")


# Add correction faces
for side in ['CORRECTION_1', 'CORRECTION_2']:
    bpy.ops.object.vertex_group_set_active(group=side)
    bpy.ops.object.vertex_group_select()
    bpy.ops.mesh.shortest_path_select(edge_mode='SELECT')
    bpy.ops.mesh.edge_face_add()
    bpy.ops.mesh.quads_convert_to_tris(quad_method='BEAUTY', ngon_method='BEAUTY')
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.vertex_group_remove()


# Add connecting edges to vertex groups
for side in ['finger_TOP', 'finger_LEFT', 'finger_RIGHT', 'finger_BOTTOM', 'BRIDGE_LEFT', 'BRIDGE_MID', 'BRIDGE_RIGHT']:
    bpy.ops.object.vertex_group_set_active(group=side)
    bpy.ops.object.vertex_group_select()
    bpy.ops.mesh.shortest_path_select(edge_mode='SELECT', use_topology_distance=True)
    bpy.ops.object.vertex_group_assign()
    bpy.ops.mesh.select_all(action='DESELECT')


bpy.ops.object.mode_set(mode = 'OBJECT')
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)



#################
## THUMB PLATE ##
#################

print("{:.2f}".format(time.time()-start_time), "- Generate Thumb Plate")

#bpy.ops.object.select_all(action='DESELECT')

bpy.ops.mesh.primitive_grid_add(x_subdivisions=3, y_subdivisions=7, size=1, location=(0, 0, mount_thickness), rotation=(0, 0, -pi/2))
bpy.ops.transform.resize(value=(7, 3, 1), orient_type='GLOBAL', orient_matrix=((1, 0, 0), (0, 1, 0), (0, 0, 1)), orient_matrix_type='GLOBAL', constraint_axis=(False, True, False), mirror=True, use_proportional_edit=False, proportional_edit_falloff='SMOOTH', proportional_size=1, use_proportional_connected=False, use_proportional_projected=False)
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
bpy.context.selected_objects[0].name = "thumb_plate"


bpy.ops.object.mode_set(mode = 'EDIT')
bpy.ops.mesh.select_all(action='DESELECT')
    
grid_mesh = bmesh.from_edit_mesh(bpy.context.object.data)
grid_mesh.verts.ensure_lookup_table()
grid_mesh.edges.ensure_lookup_table()
grid_mesh.faces.ensure_lookup_table()


faces_to_use = [0, 2, 6, 8, 12, 18]

# Apply transfomations to each key face
for thumb in range(len(faces_to_use)):
    grid_mesh.faces[faces_to_use[thumb]].select = True
    
    bpy.ops.object.vertex_group_assign_new()
    bpy.data.objects['thumb_plate'].vertex_groups['Group'].name = 'switch - thumb - ' + str(thumb)
    
    switch_size = 1
    if thumb>3: switch_size = 1.5               
    bpy.ops.transform.resize(value=(mount_height+0.25, mount_height*switch_size+0.25, 1))
    
    bpy.ops.transform.translate(value=-grid_mesh.faces[faces_to_use[thumb]].calc_center_median(), orient_type='GLOBAL')
    bpy.ops.transform.translate(value=(0, 0, mount_thickness+key_well_offset), orient_type='GLOBAL')

    bpy.ops.transform.rotate(value=-bpy.data.objects['axis - thumb - ' + str(thumb)].rotation_euler[0], orient_axis='X', center_override=(0.0, 0.0, 0.0))
    bpy.ops.transform.rotate(value=-bpy.data.objects['axis - thumb - ' + str(thumb)].rotation_euler[1], orient_axis='Y', center_override=(0.0, 0.0, 0.0))
    bpy.ops.transform.rotate(value=-bpy.data.objects['axis - thumb - ' + str(thumb)].rotation_euler[2], orient_axis='Z', center_override=(0.0, 0.0, 0.0))
    bpy.ops.transform.translate(value=bpy.data.objects['axis - thumb - ' + str(thumb)].location, orient_type='GLOBAL', orient_matrix=((1, 0, 0), (0, 1, 0), (0, 0, 1)), orient_matrix_type='GLOBAL', mirror=True, use_proportional_edit=False, proportional_edit_falloff='SMOOTH', proportional_size=1, use_proportional_connected=False, use_proportional_projected=False)

    bpy.ops.transform.translate(value=(0, 0, key_well_offset), orient_type='NORMAL', orient_matrix=((1, 0, 0), (0, 1, 0), (0, 0, 1)), orient_matrix_type='GLOBAL', constraint_axis=(True, True, True), mirror=True, use_proportional_edit=False, proportional_edit_falloff='SMOOTH', proportional_size=0.001, use_proportional_connected=False, use_proportional_projected=False)
    
    bpy.ops.mesh.select_all(action='DESELECT')


for vertex_group_name in ['key_thumb', 'thumb_LEFT', 'thumb_RIGHT', 'thumb_BOTTOM', 'thumb_corner_TL', 'thumb_corner_TLL', 'thumb_corner_ML', 'thumb_corner_BL', 'thumb_corner_BR', 'BRIDGE_LEFT', 'BRIDGE_MID', 'BRIDGE_RIGHT', 'BRIDGE_LEFT_RING_0', 'BRIDGE_RIGHT_RING_0']:
    bpy.ops.object.vertex_group_assign_new()
    bpy.data.objects['thumb_plate'].vertex_groups['Group'].name = vertex_group_name

# Remove unused faces
grid_mesh.faces.ensure_lookup_table()
for num in faces_to_use:
    grid_mesh.faces[num].select = True
bpy.ops.mesh.select_mode(type="VERT")
bpy.ops.mesh.select_all(action='INVERT')
bpy.ops.mesh.delete(type='VERT')
grid_mesh.faces.ensure_lookup_table()
grid_mesh.faces[7].select = True
bpy.ops.mesh.delete(type='FACE')



# Add correction faces
grid_mesh.verts.ensure_lookup_table()
for correction in [[15, 21, 23],
                   [14, 15, 19, 21],
                   [14, 17, 19],
                   [ 9, 10, 13, 14, 17]]:
    for vertex in correction:
        grid_mesh.verts[vertex].select = True
    bpy.ops.mesh.edge_face_add()
    bpy.ops.mesh.quads_convert_to_tris(quad_method='BEAUTY', ngon_method='BEAUTY')
    bpy.ops.mesh.select_all(action='DESELECT')



# Vertex Group - key
bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.object.vertex_group_set_active(group='key_thumb')
bpy.ops.object.vertex_group_assign()
bpy.ops.mesh.select_all(action='DESELECT')



# Create vertex group faces
for side in [['thumb_LEFT',   [0, 12]],
             ['thumb_RIGHT',  [3, 23]],
             ['thumb_BOTTOM', [0, 3]],
             ['thumb_corner_TL',  [16]],
             ['thumb_corner_TLL', [12]],
             ['thumb_corner_ML',  [8]],
             ['thumb_corner_BL',  [0]],
             ['thumb_corner_BR',  [3]],
             ['BRIDGE_LEFT',         [16, 20]],
             ['BRIDGE_MID',          [20, 23]],
             ['BRIDGE_RIGHT',        [23]],
             ['BRIDGE_LEFT_RING_0',  [12, 16]],
             ['BRIDGE_RIGHT_RING_0', [23]]]:

    bpy.ops.object.vertex_group_set_active(group=side[0])
    for vertex in side[1]:
        grid_mesh.verts[vertex].select = True
    bpy.ops.object.vertex_group_assign()
    bpy.ops.mesh.select_all(action='DESELECT')



# Add connecting edges to vertex groups
for side in ['thumb_LEFT', 'thumb_RIGHT', 'thumb_BOTTOM', 'BRIDGE_LEFT', 'BRIDGE_MID']:
    bpy.ops.object.vertex_group_set_active(group=side)
    bpy.ops.object.vertex_group_select()
    bpy.ops.mesh.shortest_path_select(edge_mode='SELECT', use_topology_distance=True)
    bpy.ops.object.vertex_group_assign()
    bpy.ops.mesh.select_all(action='DESELECT')

bpy.ops.object.mode_set(mode = 'OBJECT')
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)




####################
## CONNECT PLATES ##
####################

print("{:.2f}".format(time.time()-start_time), "- Connect Finger and Thumb Plates")

# Join finger_plate and thumb_plate meshes
bpy.data.objects["thumb_plate"].select_set(True)
bpy.data.objects["finger_plate"].select_set(True)
bpy.ops.object.join()
bpy.context.active_object.name = "body"

bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

bpy.ops.object.mode_set(mode = 'EDIT')


# Bridge connection between plates
for bridge in ['BRIDGE_MID', 'BRIDGE_LEFT', 'BRIDGE_RIGHT']:
    bpy.ops.object.vertex_group_set_active(group=bridge)
    bpy.ops.object.vertex_group_select()
    bpy.ops.mesh.edge_face_add()
    bpy.ops.mesh.quads_convert_to_tris(ngon_method='BEAUTY')
    bpy.ops.mesh.select_all(action='DESELECT')




################
## CASE WALLS ##
################

print("{:.2f}".format(time.time()-start_time), "- Generate Body Walls")

# Vertex Group - RING_0
bpy.ops.mesh.select_non_manifold()
bpy.ops.object.vertex_group_set_active(group='RING_0')
bpy.ops.object.vertex_group_assign()
bpy.ops.mesh.select_all(action='DESELECT')


# Construct Ring Skeleton
for build_edge in [ ['finger_TOP',    [[wall_thickness, -1],
                                       [wall_xy_offset + wall_thickness, wall_z_offset], 
                                       [wall_xy_offset + wall_thickness, wall_z_offset -1.5 - wall_thickness]]],
                    ['finger_RIGHT',  [[wall_thickness, -1],
                                       [wall_xy_offset + wall_thickness, wall_z_offset], 
                                       [wall_xy_offset + wall_thickness+1, wall_z_offset-10]]],
                    ['finger_LEFT',   [[wall_thickness, -1],
                                       [left_wall_x_offset+wall_thickness+1.5, -2.5-left_wall_x_offset], 
                                       [left_wall_x_offset+wall_thickness-1.5, -2.5-3*left_wall_x_offset]]],
                    ['finger_BOTTOM', [[wall_thickness, -1],
                                       [wall_xy_offset + wall_thickness, wall_z_offset], 
                                       [wall_xy_offset + wall_thickness, wall_z_offset -1.5 - wall_thickness]]],
                    ['thumb_BOTTOM',  [[wall_thickness, -1],
                                       [wall_xy_offset + wall_thickness, wall_z_offset], 
                                       [wall_xy_offset + wall_thickness, wall_z_offset -1.5 - wall_thickness]]],
                    ['thumb_LEFT',    [[wall_thickness, -1],
                                       [wall_xy_offset + wall_thickness, wall_z_offset], 
                                       [wall_xy_offset + wall_thickness, wall_z_offset -1.5 - wall_thickness]]],
                    ['thumb_RIGHT',  [[wall_thickness, -1],
                                       [wall_xy_offset + wall_thickness, wall_z_offset], 
                                       [wall_xy_offset + wall_thickness, wall_z_offset -1.5 - wall_thickness]]]]:
    for ring_num in range(0, 3):
        bpy.ops.object.vertex_group_set_active(group=build_edge[0])
        bpy.ops.object.vertex_group_select()
        with suppress_stdout():
            bpy.ops.mesh.offset_edges( width=build_edge[1][ring_num][0], depth=build_edge[1][ring_num][1], depth_mode='depth', follow_face=True, mirror_modifier=False, edge_rail=False, caches_valid=False)
        bpy.ops.object.vertex_group_set_active(group='RING_' + str(ring_num+1))
        bpy.ops.object.vertex_group_assign()
        for group in ['key_finger', 'key_thumb', 'finger_LEFT', 'finger_TOP', 'finger_RIGHT', 'finger_BOTTOM', 'thumb_BOTTOM', 'thumb_LEFT', 'thumb_RIGHT', 'RING_0', 'RING_' + str(ring_num)]:
            bpy.ops.object.vertex_group_set_active(group=group)
            bpy.ops.object.vertex_group_remove_from()
        bpy.ops.mesh.select_all(action='DESELECT')


# Connect Rings
for corner in ['finger_corner_BL', 'finger_corner_TL', 'finger_corner_TR', 'finger_corner_BR', 'thumb_corner_BL', 'thumb_corner_BR', 'BRIDGE_RIGHT_RING_0']:
    for ring_num in range(1,4):
        bpy.ops.object.vertex_group_set_active(group=corner)
        bpy.ops.object.vertex_group_select()
        for ring_group in range(0,4):
            if ring_num != ring_group:
                bpy.ops.object.vertex_group_set_active(group="RING_" + str(ring_group))
                bpy.ops.object.vertex_group_deselect()
        bpy.ops.mesh.edge_face_add()
bpy.ops.mesh.select_all(action='DESELECT')



# Fill in Rings
for ring in range(0, 3):
    
    if ring == 2:
        bpy.ops.object.vertex_group_set_active(group='thumb_corner_TLL')
        bpy.ops.object.vertex_group_select()
        bpy.ops.object.vertex_group_set_active(group='finger_corner_BL')
        bpy.ops.object.vertex_group_select()
        for ring_again in range(0, 3):
                bpy.ops.object.vertex_group_set_active(group='RING_' + str(ring_again))
                bpy.ops.object.vertex_group_deselect()
        bpy.ops.mesh.edge_face_add()
    
    bpy.ops.object.vertex_group_set_active(group='RING_' + str(ring))
    bpy.ops.object.vertex_group_select()
    bpy.ops.object.vertex_group_set_active(group='RING_' + str(ring+1))
    bpy.ops.object.vertex_group_select()
    bpy.ops.object.vertex_group_set_active(group='thumb_corner_TL')
    bpy.ops.object.vertex_group_deselect()
    bpy.ops.mesh.bridge_edge_loops()
    bpy.ops.mesh.tris_convert_to_quads(face_threshold=3.14159, shape_threshold=3.14159)
    bpy.ops.mesh.select_all(action='DESELECT')
    
    if ring<2:    
        bpy.ops.object.vertex_group_set_active(group='finger_corner_BL')
        bpy.ops.object.vertex_group_select()
        for ring_again in range(0, 4):
            if not (ring_again != ring) != (ring_again != ring+1)  :
                bpy.ops.object.vertex_group_set_active(group='RING_' + str(ring_again))
                bpy.ops.object.vertex_group_deselect()
        bpy.ops.object.vertex_group_set_active(group='thumb_corner_TL')
        bpy.ops.object.vertex_group_select()
        bpy.ops.mesh.edge_face_add()
        bpy.ops.mesh.select_all(action='DESELECT')
        
        bpy.ops.object.vertex_group_set_active(group='thumb_corner_TLL')
        bpy.ops.object.vertex_group_select()
        for ring_again in range(0, 4):
            if not (ring_again != ring) != (ring_again != ring+1)  :
                bpy.ops.object.vertex_group_set_active(group='RING_' + str(ring_again))
                bpy.ops.object.vertex_group_deselect()
        bpy.ops.object.vertex_group_set_active(group='thumb_corner_TL')
        bpy.ops.object.vertex_group_select()
        bpy.ops.mesh.edge_face_add()
        bpy.ops.mesh.select_all(action='DESELECT')
        
        if ring == 1:
            bpy.ops.object.vertex_group_set_active(group='thumb_corner_TLL')
            bpy.ops.object.vertex_group_select()
            bpy.ops.object.vertex_group_set_active(group='finger_corner_BL')
            bpy.ops.object.vertex_group_select()
            for ring_again in range(0, 4):
                if ring_again != ring+1:
                    bpy.ops.object.vertex_group_set_active(group='RING_' + str(ring_again))
                    bpy.ops.object.vertex_group_deselect()
            bpy.ops.object.vertex_group_set_active(group='thumb_corner_TL')
            bpy.ops.object.vertex_group_select()
            bpy.ops.mesh.edge_face_add()
            bpy.ops.mesh.select_all(action='DESELECT')


# Close Top Left Thumb Hole
bpy.ops.object.vertex_group_set_active(group='BRIDGE_LEFT_RING_0')
bpy.ops.object.vertex_group_select()
bpy.ops.mesh.edge_face_add()
bpy.ops.mesh.quads_convert_to_tris(quad_method='BEAUTY', ngon_method='BEAUTY')
bpy.ops.mesh.select_all(action='DESELECT')

# Correct Odd Knotch
bpy.ops.object.vertex_group_set_active(group='BRIDGE_LEFT_RING_0')
bpy.ops.object.vertex_group_select()
for ring_group in range(0,3):
    bpy.ops.object.vertex_group_set_active(group="RING_" + str(ring_group))
    bpy.ops.object.vertex_group_deselect()
bpy.ops.transform.resize(value=(0, 5, 1), orient_type='GLOBAL', orient_matrix=((1, 0, 0), (0, 1, 0), (0, 0, 1)), orient_matrix_type='GLOBAL', constraint_axis=(True, True, True), mirror=True, use_proportional_edit=False, proportional_edit_falloff='SMOOTH', proportional_size=1, use_proportional_connected=False, use_proportional_projected=False)
bpy.ops.mesh.select_all(action='DESELECT')


# Extrude to floor
bpy.ops.mesh.select_non_manifold()
bpy.ops.mesh.extrude_region_move(MESH_OT_extrude_region={"use_normal_flip":False, "use_dissolve_ortho_edges":False, "mirror":False}, TRANSFORM_OT_translate={"value":(-0, -0, -100), "orient_type":'GLOBAL', "orient_matrix":((1, 0, 0), (0, 1, 0), (0, 0, 1)), "orient_matrix_type":'GLOBAL', "constraint_axis":(False, False, True), "mirror":False, "use_proportional_edit":False, "proportional_edit_falloff":'SMOOTH', "proportional_size":1, "use_proportional_connected":False, "use_proportional_projected":False, "snap":False, "snap_target":'CLOSEST', "snap_point":(0, 0, 0), "snap_align":False, "snap_normal":(0, 0, 0), "gpencil_strokes":False, "cursor_transform":False, "texture_space":False, "remove_on_cancel":False, "release_confirm":False, "use_accurate":False, "use_automerge_and_split":False})
bpy.ops.transform.resize(value=(1, 1, 0), orient_type='GLOBAL', orient_matrix=((1, 0, 0), (0, 1, 0), (0, 0, 1)), orient_matrix_type='GLOBAL', constraint_axis=(True, True, True), mirror=True, use_proportional_edit=False, proportional_edit_falloff='SMOOTH', proportional_size=1, use_proportional_connected=False, use_proportional_projected=False)
bpy.ops.mesh.select_all(action='DESELECT')

for vertex_group in ['finger_corner_TL', 'finger_corner_TR', 'finger_corner_BR', 'thumb_corner_BL', 'thumb_corner_BR']:
    bpy.ops.object.vertex_group_set_active(group=vertex_group)
    bpy.ops.object.vertex_group_select()
for vertex_group in ['RING_0', 'RING_3', ]:
    bpy.ops.object.vertex_group_set_active(group=vertex_group)
    bpy.ops.object.vertex_group_deselect()
bpy.ops.mesh.subdivide(smoothness=1)



bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.object.vertex_group_set_active(group='key_finger')
bpy.ops.object.vertex_group_deselect()
bpy.ops.object.vertex_group_set_active(group='key_thumb')
bpy.ops.object.vertex_group_deselect()
bpy.ops.object.vertex_group_set_active(group='thumb_corner_ML')
bpy.ops.object.vertex_group_deselect()
bpy.ops.object.vertex_group_set_active(group='RING_2')
bpy.ops.object.vertex_group_select()
bpy.ops.object.vertex_group_set_active(group='RING_3')
bpy.ops.object.vertex_group_select()

if relaxed_mesh:
    bpy.ops.mesh.vertices_smooth(factor=1, wait_for_input=False)
    with suppress_stdout(): bpy.ops.mesh.relax()

for vertex_group in ['finger_corner_TL', 'finger_corner_TR', 'finger_corner_BR', 'thumb_corner_BL', 'thumb_corner_BR']:
    bpy.ops.object.vertex_group_set_active(group=vertex_group)
    bpy.ops.object.vertex_group_select()
for vertex_group in ['RING_2', 'RING_3', ]:
    bpy.ops.object.vertex_group_set_active(group=vertex_group)
    bpy.ops.object.vertex_group_deselect()

bpy.ops.mesh.quads_convert_to_tris(quad_method='BEAUTY', ngon_method='BEAUTY')

bpy.ops.object.mode_set(mode = 'OBJECT')
bpy.context.view_layer.objects.active = bpy.data.objects["body"]





###########################
## Form Switch Locations ##
###########################

print("{:.2f}".format(time.time()-start_time), "- Punch out Switch Locations " + str(body_subsurf_level) + "x")

bpy.ops.object.select_all(action='DESELECT')
bpy.context.view_layer.objects.active = bpy.data.objects["body"]
bpy.data.objects["body"].select_set(True)
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)


bpy.ops.object.modifier_add(type='SOLIDIFY')
bpy.context.object.modifiers["Solidify"].solidify_mode = 'NON_MANIFOLD'
bpy.context.object.modifiers["Solidify"].nonmanifold_thickness_mode = 'CONSTRAINTS'
bpy.context.object.modifiers["Solidify"].nonmanifold_boundary_mode = 'NONE'
bpy.context.object.modifiers["Solidify"].thickness = body_thickness
bpy.context.object.modifiers["Solidify"].use_rim = False
bpy.ops.object.modifier_apply(modifier="Solidify")

bpy.ops.object.mode_set(mode = 'EDIT')
bpy.ops.mesh.select_all(action='DESELECT')
bpy.ops.mesh.separate(type='LOOSE')
bpy.ops.object.mode_set(mode = 'OBJECT')
bpy.context.selected_objects[1].name = "body_inner"



bpy.ops.object.select_all(action='DESELECT')
bpy.context.view_layer.objects.active = bpy.data.objects["body"]
bpy.data.objects["body"].select_set(True)


if geode_mode:
    body_subsurf_level=3
    bpy.ops.object.duplicate_move(OBJECT_OT_duplicate={"linked":False, "mode":'TRANSLATION'}, TRANSFORM_OT_translate={"value":(0, 0, 0), "orient_type":'GLOBAL', "orient_matrix":((1, 0, 0), (0, 1, 0), (0, 0, 1)), "orient_matrix_type":'GLOBAL', "constraint_axis":(False, False, False), "mirror":True, "use_proportional_edit":False, "proportional_edit_falloff":'SMOOTH', "proportional_size":1, "use_proportional_connected":False, "use_proportional_projected":False, "snap":False, "snap_target":'CLOSEST', "snap_point":(0, 0, 0), "snap_align":False, "snap_normal":(0, 0, 0), "gpencil_strokes":False, "cursor_transform":False, "texture_space":False, "remove_on_cancel":False, "release_confirm":False, "use_accurate":False, "use_automerge_and_split":False})
    bpy.ops.object.mode_set(mode = 'EDIT')
    bpy.ops.mesh.select_non_manifold()
    bpy.ops.mesh.extrude_region_move(MESH_OT_extrude_region={"use_normal_flip":False, "use_dissolve_ortho_edges":False, "mirror":False}, TRANSFORM_OT_translate={"value":(-0, -0, -20), "orient_type":'GLOBAL', "orient_matrix":((1, 0, 0), (0, 1, 0), (0, 0, 1)), "orient_matrix_type":'GLOBAL', "constraint_axis":(False, False, True), "mirror":False, "use_proportional_edit":False, "proportional_edit_falloff":'SMOOTH', "proportional_size":1, "use_proportional_connected":False, "use_proportional_projected":False, "snap":False, "snap_target":'CLOSEST', "snap_point":(0, 0, 0), "snap_align":False, "snap_normal":(0, 0, 0), "gpencil_strokes":False, "cursor_transform":False, "texture_space":False, "remove_on_cancel":False, "release_confirm":False, "use_accurate":False, "use_automerge_and_split":False})
    bpy.ops.object.mode_set(mode = 'OBJECT')
    
    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = bpy.data.objects["body"]
    bpy.data.objects["body"].select_set(True)
    
    bpy.ops.object.mode_set(mode = 'EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.object.vertex_group_set_active(group="key_finger")
    bpy.ops.object.vertex_group_deselect()
    bpy.ops.object.vertex_group_set_active(group="key_thumb")
    bpy.ops.object.vertex_group_deselect()

    for x in range(5):
        bpy.ops.mesh.quads_convert_to_tris(quad_method='BEAUTY', ngon_method='BEAUTY')
        bpy.ops.mesh.subdivide(number_cuts=1, smoothness=1, ngon=True, quadcorner='INNERVERT')
        bpy.ops.mesh.decimate(ratio=.33)
    bpy.ops.object.mode_set(mode = 'OBJECT')
    
    bpy.ops.object.modifier_add(type='SHRINKWRAP')
    bpy.context.object.modifiers["Shrinkwrap"].wrap_method = 'PROJECT'
    bpy.context.object.modifiers["Shrinkwrap"].wrap_mode = 'ON_SURFACE'
    bpy.context.object.modifiers["Shrinkwrap"].cull_face = 'FRONT'
    bpy.context.object.modifiers["Shrinkwrap"].target = bpy.data.objects["body.001"]
    bpy.ops.object.modifier_apply(modifier="Shrinkwrap")
    
    bpy.ops.object.select_all(action='DESELECT')
    bpy.data.objects["body.001"].select_set(True)
    with suppress_stdout(): bpy.ops.object.delete()
    
    
    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = bpy.data.objects["body"]
    bpy.data.objects["body"].select_set(True)

elif (body_subsurf_level>0):
    bpy.ops.object.modifier_add(type='SUBSURF')
    bpy.context.object.modifiers["Subdivision"].levels = body_subsurf_level
    bpy.ops.object.modifier_apply(modifier="Subdivision")


bpy.ops.object.mode_set(mode = 'EDIT')
bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.mesh.quads_convert_to_tris(quad_method='BEAUTY', ngon_method='BEAUTY')
bpy.ops.object.vertex_group_assign_new()
bpy.data.objects['body'].vertex_groups['Group'].name = "all"
bpy.ops.mesh.select_all(action='DESELECT')
bpy.ops.mesh.select_non_manifold()
bpy.ops.object.vertex_group_assign_new()
bpy.data.objects["body"].vertex_groups['Group'].name = 'bottom_non_manifold'
bpy.ops.mesh.select_all(action='DESELECT')
bpy.ops.object.mode_set(mode = 'OBJECT')



bpy.ops.object.select_all(action='DESELECT')
bpy.context.view_layer.objects.active = bpy.data.objects["body_inner"]
bpy.data.objects["body_inner"].select_set(True)
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

if (body_subsurf_level>0):
    bpy.ops.object.modifier_add(type='SUBSURF')
    if (body_subsurf_level<=3):
        bpy.context.object.modifiers["Subdivision"].levels = body_subsurf_level
    else:
        bpy.context.object.modifiers["Subdivision"].levels = 3
    bpy.ops.object.modifier_apply(modifier="Subdivision")

if geode_mode:
    bpy.ops.object.modifier_add(type='SHRINKWRAP')
    bpy.context.object.modifiers["Shrinkwrap"].wrap_method = 'TARGET_PROJECT'
    bpy.context.object.modifiers["Shrinkwrap"].target = bpy.data.objects["body"]
    bpy.context.object.modifiers["Shrinkwrap"].offset = body_thickness
    bpy.ops.object.modifier_apply(modifier="Shrinkwrap")

bpy.ops.object.duplicate_move(OBJECT_OT_duplicate={"linked":False, "mode":'TRANSLATION'}, TRANSFORM_OT_translate={"value":(0, 0, 0), "orient_type":'GLOBAL', "orient_matrix":((1, 0, 0), (0, 1, 0), (0, 0, 1)), "orient_matrix_type":'GLOBAL', "constraint_axis":(False, False, False), "mirror":True, "use_proportional_edit":False, "proportional_edit_falloff":'SMOOTH', "proportional_size":1, "use_proportional_connected":False, "use_proportional_projected":False, "snap":False, "snap_target":'CLOSEST', "snap_point":(0, 0, 0), "snap_align":False, "snap_normal":(0, 0, 0), "gpencil_strokes":False, "cursor_transform":False, "texture_space":False, "remove_on_cancel":False, "release_confirm":False, "use_accurate":False, "use_automerge_and_split":False})
bpy.ops.object.modifier_add(type='SOLIDIFY')
bpy.context.object.modifiers["Solidify"].thickness = -0.01
bpy.context.object.modifiers["Solidify"].offset = 1
bpy.context.object.modifiers["Solidify"].use_rim = False
bpy.ops.object.modifier_apply(modifier="Solidify")
bpy.ops.object.mode_set(mode = 'EDIT')
bpy.ops.mesh.separate(type='LOOSE')
bpy.ops.object.mode_set(mode = 'OBJECT')
bpy.ops.object.select_all(action='DESELECT')

bpy.context.view_layer.objects.active = bpy.data.objects["body_inner.001"]
bpy.data.objects["body_inner.001"].select_set(True)
with suppress_stdout(): bpy.ops.object.delete()

bpy.ops.object.select_all(action='DESELECT')
bpy.context.view_layer.objects.active = bpy.data.objects["body_inner.002"]
bpy.data.objects["body_inner.002"].select_set(True)
bpy.context.selected_objects[0].name = "body_inner_reference"
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)


bpy.ops.object.select_all(action='DESELECT')
bpy.context.view_layer.objects.active = bpy.data.objects["body_inner"]
bpy.data.objects["body_inner"].select_set(True)

bpy.ops.object.mode_set(mode = 'EDIT')
bpy.ops.mesh.select_all(action='DESELECT')
bpy.ops.object.mode_set(mode = 'OBJECT')

bpy.ops.object.mode_set(mode = 'EDIT')
bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.object.vertex_group_assign_new()
bpy.data.objects['body_inner'].vertex_groups['Group'].name = "all_inside"
bpy.ops.mesh.select_all(action='DESELECT')
bpy.ops.mesh.select_non_manifold()
bpy.ops.object.vertex_group_assign_new()
bpy.data.objects["body_inner"].vertex_groups['Group'].name = 'bottom_non_manifold'
bpy.ops.mesh.select_all(action='DESELECT')
bpy.ops.object.mode_set(mode = 'OBJECT')



#Ensure Corners hit body
for thing in bpy.data.collections['SWITCH_PROJECTION'].objects:
    bpy.context.view_layer.objects.active = thing
    bpy.ops.object.modifier_add(type='SHRINKWRAP')
    bpy.context.object.modifiers["Shrinkwrap"].wrap_method = 'PROJECT'
    bpy.context.object.modifiers["Shrinkwrap"].use_negative_direction = True
    bpy.context.object.modifiers["Shrinkwrap"].use_positive_direction = False
    bpy.context.object.modifiers["Shrinkwrap"].use_project_z = True
    bpy.context.object.modifiers["Shrinkwrap"].target = bpy.data.objects["body"]
    bpy.context.object.modifiers["Shrinkwrap"].vertex_group = "bottom_project"
    bpy.context.object.modifiers["Shrinkwrap"].offset = -0.2
    bpy.context.object.modifiers["Shrinkwrap"].cull_face = 'BACK'
    bpy.ops.object.modifier_apply(modifier="Shrinkwrap")

bpy.context.view_layer.objects.active = bpy.data.objects["body"]
bpy.data.objects["body"].select_set(True)




for projection_type in [['body',       'keycap_projection_outer', mount_thickness + 2, 'all'       ],
                        ['body',       'switch_projection'      , mount_thickness,     'all'       ],
                        ['body_inner', 'keycap_projection_inner', mount_thickness,     'all_inside'],
                        ['body_inner', 'switch_projection_inner', 0,                   'all_inside']]:

    for thing in bpy.data.collections[projection_type[1].upper()].objects:
        print("    ---" + thing.name)
        vertex_group_name = thing.name
            
        bpy.context.scene.cursor.location = bpy.data.objects['axis' + thing.name[len(projection_type[1]):]].location
        bpy.context.scene.cursor.rotation_euler =  bpy.data.objects['axis' + thing.name[len(projection_type[1]):]].rotation_euler
        
        bpy.ops.object.select_all(action='DESELECT')
        bpy.context.view_layer.objects.active = bpy.data.objects[projection_type[0]]
        bpy.data.objects[projection_type[0]].select_set(True)
        
        bpy.ops.object.mode_set(mode = 'EDIT')
        bpy.ops.object.vertex_group_set_active(group='switch' + thing.name[len(projection_type[1]):])
        bpy.ops.object.vertex_group_select()
        bpy.ops.mesh.select_more()
        bpy.ops.mesh.separate(type='SELECTED')
        bpy.ops.object.mode_set(mode = 'OBJECT')
        bpy.context.view_layer.objects.active = bpy.data.objects[projection_type[0] + ".001"]
        bpy.data.objects[projection_type[0]].select_set(False)
        bpy.context.selected_objects[0].name = "temp"
            
        thing.select_set(True)
        bpy.ops.object.join()

        bpy.ops.object.mode_set(mode = 'EDIT')   

        with suppress_stdout(): bpy.ops.mesh.intersect(mode='SELECT_UNSELECT', separate_mode='ALL', solver='EXACT')

        bpy.ops.mesh.separate(type='LOOSE')
        
        bpy.ops.object.mode_set(mode = 'OBJECT')
        bpy.ops.object.select_all(action='DESELECT')

        mesh_size = len(bpy.data.objects['temp'].data.vertices)
        for mesh_object in bpy.context.scene.objects:
            if 'temp'+'.' in mesh_object.name:
                if len(mesh_object.data.vertices) > mesh_size:
                    bpy.data.objects['temp'].select_set(True)
                    with suppress_stdout(): bpy.ops.object.delete()
                    mesh_object.name = 'temp'
                    mesh_size = len(mesh_object.data.vertices)
                else:
                    mesh_object.select_set(True)
                    with suppress_stdout(): bpy.ops.object.delete()
        
        bpy.context.view_layer.objects.active = bpy.data.objects['temp']
        bpy.ops.object.mode_set(mode = 'EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.object.vertex_group_set_active(group='switch' + vertex_group_name[len(projection_type[1]):])
        bpy.ops.object.vertex_group_assign()
        bpy.ops.object.mode_set(mode = 'OBJECT')

        bpy.context.view_layer.objects.active = bpy.data.objects[projection_type[0]]
        bpy.data.objects[projection_type[0]].select_set(True)
        bpy.data.objects['temp'].select_set(True)
        bpy.ops.object.join()
        

        bpy.ops.object.mode_set(mode = 'EDIT')
        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.mesh.select_non_manifold()
        with suppress_stdout(): bpy.ops.mesh.remove_doubles()
        bpy.ops.mesh.select_all(action='DESELECT')
        
        
        bpy.ops.object.vertex_group_set_active(group=projection_type[3])
        bpy.ops.object.vertex_group_select()
        bpy.ops.mesh.select_all(action='INVERT')
        bpy.ops.mesh.edge_face_add()


        bpy.ops.mesh.inset(thickness=0, depth=0)
        bpy.ops.transform.resize(value=(1, 1, 0), orient_type='CURSOR', orient_matrix=((1, 0, 0), (0, 1, 0), (0, 0, 1)), orient_matrix_type='GLOBAL', constraint_axis=(True, True, True), mirror=True, use_proportional_edit=False, proportional_edit_falloff='SMOOTH', proportional_size=1, use_proportional_connected=False, use_proportional_projected=False)

        bpy.ops.object.vertex_group_assign_new()
        bpy.data.objects[projection_type[0]].vertex_groups['Group'].name = vertex_group_name

       
        bpy.ops.object.mode_set(mode = 'OBJECT')
        bpy.data.objects[projection_type[0]].select_set(False)
        with suppress_stdout(): bpy.ops.object.delete()
        bpy.data.objects[projection_type[0]].select_set(True)
       
        bpy.ops.mesh.primitive_plane_add(enter_editmode=False, size=40, align='CURSOR', scale=(1, 1, 1))
        bpy.ops.transform.translate(value=(0, 0, projection_type[2]), orient_type='CURSOR')
        bpy.context.view_layer.objects.active = bpy.data.objects[projection_type[0]]
        
        bpy.ops.object.modifier_add(type='SHRINKWRAP')
        bpy.context.object.modifiers["Shrinkwrap"].wrap_method = 'NEAREST_SURFACEPOINT'
        bpy.context.object.modifiers["Shrinkwrap"].target = bpy.data.objects["Plane"]
        bpy.context.object.modifiers["Shrinkwrap"].vertex_group = vertex_group_name

        bpy.ops.object.modifier_apply(modifier="Shrinkwrap")

        bpy.ops.object.mode_set(mode = 'EDIT')
      
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.object.vertex_group_set_active(group=projection_type[3])
        bpy.ops.object.vertex_group_assign()
        
        bpy.ops.object.vertex_group_set_active(group='bottom_non_manifold')
        bpy.ops.object.vertex_group_deselect()
        bpy.ops.mesh.fill_holes(sides=0)

        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.object.mode_set(mode = 'OBJECT')

        bpy.ops.object.select_all(action='DESELECT')
        bpy.data.objects["Plane"].select_set(True)
        with suppress_stdout(): bpy.ops.object.delete()


  
bpy.context.scene.cursor.location =  [0, 0, 0]
bpy.context.scene.cursor.rotation_euler =  [0, 0, 0]
bpy.ops.object.select_all(action='DESELECT')

bpy.ops.object.modifier_add(type='SHRINKWRAP')
bpy.context.object.modifiers["Shrinkwrap"].wrap_method = 'TARGET_PROJECT'
bpy.context.object.modifiers["Shrinkwrap"].wrap_mode = 'INSIDE'
bpy.context.object.modifiers["Shrinkwrap"].target = bpy.data.objects["body_inner_reference"]
bpy.ops.object.modifier_apply(modifier="Shrinkwrap")



###########################
##  Loligagger Formation ##
###########################

if loligagger_port:
        bpy.ops.object.select_all(action='DESELECT')
        bpy.ops.mesh.primitive_cube_add(size=1, enter_editmode=False, align='WORLD', location=(bpy.data.objects['axis - 0, 0'].location[0] - sin(bpy.data.objects['axis - 0, 0'].rotation_euler[0])*mount_width*0.5, 100, 0), scale=(1, 1, 1))
        bpy.context.active_object.name = 'holder_projection'
        bpy.ops.object.modifier_add(type='SHRINKWRAP')
        bpy.context.object.modifiers["Shrinkwrap"].target = bpy.data.objects["body"]
        bpy.context.object.modifiers["Shrinkwrap"].wrap_method = 'PROJECT'
        bpy.context.object.modifiers["Shrinkwrap"].use_project_y = True
        bpy.context.object.modifiers["Shrinkwrap"].use_negative_direction = True
        bpy.context.object.modifiers["Shrinkwrap"].offset = 0
        bpy.ops.object.modifier_apply(modifier="Shrinkwrap")
        bpy.ops.object.origin_set(type='ORIGIN_CENTER_OF_MASS', center='MEDIAN')

        holder_width = 31.74
        holder_height = 15.5

        holder_hole_width = 29.5
        holder_hole_offset = 1.15
        holder_hole_height = 12.25
        
        holder_hole_2_width = 33.6
        holder_hole_2_offset = -0.5


        #Ouside Mesh
        bpy.ops.mesh.primitive_cube_add(size=1, location=bpy.data.objects['holder_projection'].location + mathutils.Vector((holder_width/2, 0, (holder_height - bottom_thickness - 20)/2)), scale=(holder_width, 2.25+20, holder_height + bottom_thickness + 20))
        bpy.context.selected_objects[0].name = "holder_outside"
        bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
        
        bpy.context.view_layer.objects.active = bpy.data.objects["body"]
        bpy.data.objects["body"].select_set(True)
        bpy.ops.object.join()
        

        
        bpy.ops.object.mode_set(mode = 'EDIT')
        with suppress_stdout(): bpy.ops.mesh.intersect()
        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.mesh.separate(type='LOOSE')
        bpy.ops.object.mode_set(mode = 'OBJECT')
        bpy.data.objects["body.001"].select_set(False)
        bpy.ops.object.mode_set(mode = 'EDIT')
        
        bpy.ops.object.vertex_group_set_active(group='all')
        bpy.ops.object.vertex_group_select()
        bpy.ops.mesh.select_all(action='INVERT')
        bpy.ops.mesh.loop_to_region()
        bpy.ops.mesh.delete(type='FACE')
        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.object.vertex_group_set_active(group='all')
        bpy.ops.object.vertex_group_select()
        bpy.ops.mesh.select_all(action='INVERT')
        
        bpy.ops.mesh.edge_face_add()
        bpy.ops.mesh.inset(thickness=0, depth=0)
        bpy.ops.object.vertex_group_assign_new()
        bpy.data.objects['body'].vertex_groups['Group'].name = "holder_outside"
        bpy.ops.transform.resize(value=(1, 0, 1), orient_type='GLOBAL', orient_matrix=((1, 0, 0), (0, 1, 0), (0, 0, 1)), orient_matrix_type='GLOBAL', constraint_axis=(True, True, True), mirror=True, use_proportional_edit=False, proportional_edit_falloff='SMOOTH', proportional_size=0.001, use_proportional_connected=False, use_proportional_projected=False)
        
        bpy.ops.object.mode_set(mode = 'OBJECT')
        bpy.ops.mesh.primitive_plane_add(size=200, enter_editmode=False, align='WORLD', location=bpy.data.objects['holder_projection'].location + mathutils.Vector((holder_width/2, 0, (holder_height - bottom_thickness - 20)/2)), rotation=(-1.5708, 0, 0), scale=(1, 1, 1))
        bpy.context.view_layer.objects.active = bpy.data.objects["body"]
          
        bpy.ops.object.modifier_add(type='SHRINKWRAP')
        bpy.context.object.modifiers["Shrinkwrap"].wrap_method = 'NEAREST_SURFACEPOINT'
        bpy.context.object.modifiers["Shrinkwrap"].target = bpy.data.objects["Plane"]
        bpy.context.object.modifiers["Shrinkwrap"].vertex_group = "holder_outside"
        bpy.ops.object.modifier_apply(modifier="Shrinkwrap")
    
        bpy.ops.object.mode_set(mode = 'EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.object.vertex_group_set_active(group='all')
        bpy.ops.object.vertex_group_assign()
        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.object.mode_set(mode = 'OBJECT')

        bpy.ops.object.select_all(action='DESELECT')
        bpy.data.objects["body.001"].select_set(True)
        bpy.data.objects["Plane"].select_set(True)
        with suppress_stdout(): bpy.ops.object.delete()



        #Inside Mesh
        bpy.ops.mesh.primitive_cube_add(size=1, location=bpy.data.objects['holder_projection'].location + mathutils.Vector((holder_width/2, 0, (holder_height - bottom_thickness - 20)/2)), scale=(holder_width + 1.5 + 2*body_thickness, 2.25+20, holder_height + bottom_thickness  + 2*body_thickness + 20))
        bpy.context.selected_objects[0].name = "holder_outside"
        bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
        
        bpy.context.view_layer.objects.active = bpy.data.objects["body_inner"]
        bpy.data.objects["body_inner"].select_set(True)
        bpy.ops.object.join()
        
        bpy.ops.object.mode_set(mode = 'EDIT')
        with suppress_stdout(): bpy.ops.mesh.intersect()
        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.mesh.separate(type='LOOSE')
        bpy.ops.object.mode_set(mode = 'OBJECT')
        bpy.data.objects["body_inner.001"].select_set(False)
        bpy.ops.object.mode_set(mode = 'EDIT')
        
        bpy.ops.object.vertex_group_set_active(group='all_inside')
        bpy.ops.object.vertex_group_select()
        bpy.ops.mesh.select_all(action='INVERT')
        bpy.ops.mesh.loop_to_region()
        bpy.ops.mesh.delete(type='FACE')
        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.object.vertex_group_set_active(group='all_inside')
        bpy.ops.object.vertex_group_select()
        bpy.ops.mesh.select_all(action='INVERT')

        
        bpy.ops.mesh.edge_face_add()
        bpy.ops.mesh.inset(thickness=0, depth=0)
        bpy.ops.object.vertex_group_assign_new()
        bpy.data.objects['body_inner'].vertex_groups['Group'].name = "holder_inside"
        bpy.ops.transform.resize(value=(1, 0, 1), orient_type='GLOBAL', orient_matrix=((1, 0, 0), (0, 1, 0), (0, 0, 1)), orient_matrix_type='GLOBAL', constraint_axis=(True, True, True), mirror=True, use_proportional_edit=False, proportional_edit_falloff='SMOOTH', proportional_size=0.001, use_proportional_connected=False, use_proportional_projected=False)

        
        bpy.ops.object.mode_set(mode = 'OBJECT')
        bpy.ops.mesh.primitive_plane_add(size=200, enter_editmode=False, align='WORLD', location=bpy.data.objects['holder_projection'].location + mathutils.Vector((holder_width/2, -6, (holder_height - bottom_thickness - 20)/2)), rotation=(-1.5708, 0, 0), scale=(1, 1, 1))
        bpy.context.view_layer.objects.active = bpy.data.objects["body_inner"]
          
        bpy.ops.object.modifier_add(type='SHRINKWRAP')
        bpy.context.object.modifiers["Shrinkwrap"].wrap_method = 'NEAREST_SURFACEPOINT'
        bpy.context.object.modifiers["Shrinkwrap"].target = bpy.data.objects["Plane"]
        bpy.context.object.modifiers["Shrinkwrap"].vertex_group = "holder_inside"
        bpy.ops.object.modifier_apply(modifier="Shrinkwrap")

        bpy.ops.object.mode_set(mode = 'EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.object.vertex_group_set_active(group='all_inside')
        bpy.ops.object.vertex_group_assign()
        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.object.mode_set(mode = 'OBJECT')

        bpy.ops.object.select_all(action='DESELECT')
        bpy.data.objects["body_inner.001"].select_set(True)
        bpy.data.objects["Plane"].select_set(True)
        with suppress_stdout(): bpy.ops.object.delete()




####################################
## Join Inner and Outer Body Mesh ##
####################################

print("{:.2f}".format(time.time()-start_time), "- Join Inner and Outer Body Mesh")

bpy.ops.mesh.primitive_cube_add(size=400, enter_editmode=False, align='WORLD', location=(0, 0, -200 - bottom_thickness), scale=(1, 1, 1))
bpy.context.selected_objects[0].name = "cut_cube"

bpy.ops.object.select_all(action='DESELECT')
bpy.data.objects["body"].select_set(True)
bpy.data.objects["body_inner"].select_set(True)
bpy.context.view_layer.objects.active = bpy.data.objects['body']
bpy.ops.object.join()

bpy.ops.object.mode_set(mode = 'EDIT')
bpy.ops.mesh.select_all(action='DESELECT')
bpy.ops.object.vertex_group_set_active(group='bottom_non_manifold')
bpy.ops.object.vertex_group_select()
bpy.ops.mesh.fill()
bpy.ops.object.vertex_group_remove_from()

bpy.ops.mesh.select_all(action='DESELECT')
with suppress_stdout():
    bpy.ops.mesh.normals_make_consistent()
    bpy.ops.mesh.print3d_clean_non_manifold()
bpy.ops.mesh.select_all(action='DESELECT')
bpy.ops.object.mode_set(mode = 'OBJECT')

bpy.ops.object.select_all(action='DESELECT')
bpy.context.view_layer.objects.active = bpy.data.objects['body']
bpy.data.objects['body'].select_set(True)
bpy.ops.object.modifier_add(type='BOOLEAN')
bpy.context.object.modifiers["Boolean"].object = bpy.data.objects["cut_cube"]
bpy.context.object.modifiers["Boolean"].solver = 'FAST'
bpy.ops.object.modifier_apply(modifier="Boolean")

bpy.ops.object.mode_set(mode = 'EDIT')
bpy.ops.object.vertex_group_assign()
bpy.ops.mesh.select_all(action='DESELECT')
grid_mesh = bmesh.from_edit_mesh(bpy.context.object.data)
for vertex in grid_mesh.verts:
    if vertex.co[2] < -bottom_thickness:
        vertex.select = True
bpy.ops.object.vertex_group_deselect()
bpy.ops.mesh.delete(type='VERT')
bpy.ops.object.mode_set(mode = 'OBJECT')

bpy.ops.object.select_all(action='DESELECT')
bpy.data.objects["cut_cube"].select_set(True)
with suppress_stdout(): bpy.ops.object.delete()

bpy.ops.object.mode_set(mode = 'EDIT')
bpy.ops.object.vertex_group_set_active(group='bottom_non_manifold')
bpy.ops.object.vertex_group_assign()

bpy.ops.mesh.select_all(action='DESELECT')
bpy.ops.object.vertex_group_set_active(group='all')
bpy.ops.object.vertex_group_select()
bpy.ops.mesh.select_more()
bpy.ops.object.vertex_group_assign()

bpy.ops.mesh.select_all(action='INVERT')
bpy.ops.object.vertex_group_set_active(group='all_inside')
bpy.ops.object.vertex_group_assign()
bpy.ops.mesh.select_all(action='DESELECT')

bpy.ops.object.mode_set(mode = 'OBJECT')



###########################
## GENERATE BOTTOM PLATE ##
###########################

print("{:.2f}".format(time.time()-start_time), "- Generate Bottom Plate")

bpy.ops.object.mode_set(mode = 'EDIT')

bpy.ops.mesh.select_all(action='DESELECT')
bpy.ops.object.vertex_group_set_active(group='all_inside')
bpy.ops.object.vertex_group_select()
bpy.ops.object.vertex_group_set_active(group='bottom_non_manifold')
bpy.ops.object.vertex_group_deselect()
bpy.ops.object.vertex_group_set_active(group='all')
bpy.ops.object.vertex_group_select()
bpy.ops.mesh.select_all(action='INVERT')

with suppress_stdout():
    bpy.ops.mesh.remove_doubles(threshold=0.2)
    bpy.ops.mesh.offset_edges(geometry_mode='offset', width=-0.2, angle=0, caches_valid=False, angle_presets='0°')
bpy.ops.mesh.edge_face_add()
bpy.ops.mesh.separate(type='LOOSE')
        
bpy.ops.object.mode_set(mode = 'OBJECT')
bpy.ops.object.select_all(action='DESELECT')

mesh_size = len(bpy.data.objects['body.001'].data.vertices)
for mesh_object in bpy.context.scene.objects:
    if 'body.001' == mesh_object.name:
        continue
    elif 'body.' in mesh_object.name:
        if len(mesh_object.data.vertices) > mesh_size:
            bpy.data.objects['body.001'].select_set(True)
            with suppress_stdout(): bpy.ops.object.delete()
            mesh_object.name = 'body.001'
            mesh_size = len(mesh_object.data.vertices)
        else:
            mesh_object.select_set(True)
            with suppress_stdout(): bpy.ops.object.delete()

bpy.ops.object.select_all(action='DESELECT')
bpy.context.view_layer.objects.active = bpy.data.objects["body.001"]
bpy.data.objects["body.001"].select_set(True)
bpy.context.selected_objects[0].name = "bottom"

bpy.ops.object.mode_set(mode = 'EDIT')
bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.object.vertex_group_assign_new()
bpy.data.objects['bottom'].vertex_groups['Group'].name = 'bottom_lower'

bpy.ops.mesh.extrude_region_move(MESH_OT_extrude_region={"use_normal_flip":False, "use_dissolve_ortho_edges":False, "mirror":False}, TRANSFORM_OT_translate={"value":(0, 0, 2.5), "orient_type":'GLOBAL', "orient_matrix":((0, 1, 0), (1, 0, 0), (0, 0, 1)), "orient_matrix_type":'NORMAL', "constraint_axis":(True, True, True), "mirror":False, "use_proportional_edit":False, "proportional_edit_falloff":'SMOOTH', "proportional_size":1, "use_proportional_connected":False, "use_proportional_projected":False, "snap":False, "snap_target":'CLOSEST', "snap_point":(0, 0, 0), "snap_align":False, "snap_normal":(0, 0, 0), "gpencil_strokes":False, "cursor_transform":False, "texture_space":False, "remove_on_cancel":False, "release_confirm":False, "use_accurate":False, "use_automerge_and_split":False})
bpy.ops.object.vertex_group_remove()
bpy.ops.object.vertex_group_assign_new()
bpy.data.objects['bottom'].vertex_groups['Group'].name = 'bottom_upper'
bpy.ops.mesh.edge_face_add()
bpy.ops.mesh.normals_make_consistent(inside=False)
bpy.ops.object.mode_set(mode = 'OBJECT')

bpy.ops.object.modifier_add(type='SHRINKWRAP')
bpy.context.object.modifiers["Shrinkwrap"].wrap_method = 'TARGET_PROJECT'
bpy.context.object.modifiers["Shrinkwrap"].wrap_mode = 'INSIDE'
bpy.context.object.modifiers["Shrinkwrap"].target = bpy.data.objects["body_inner_reference"]
bpy.context.object.modifiers["Shrinkwrap"].offset = 0.2
bpy.context.object.modifiers["Shrinkwrap"].vertex_group = "bottom_upper"
bpy.ops.object.modifier_apply(modifier="Shrinkwrap")

bpy.ops.object.mode_set(mode = 'EDIT')
grid_mesh = bmesh.from_edit_mesh(bpy.context.object.data)
for vertex in grid_mesh.verts:
    if vertex.select:
        vertex.co[2] = -0.5
bpy.ops.object.mode_set(mode = 'OBJECT')


# Clip off protusions into bottom
bpy.ops.object.select_all(action='DESELECT')
bpy.context.view_layer.objects.active = bpy.data.objects['body']
bpy.data.objects['body'].select_set(True)

bpy.ops.object.mode_set(mode = 'EDIT')
bpy.ops.mesh.select_all(action='DESELECT')

for column in range(ncols):
    for row in range(nrows):
        if (column in [2, 3]) or (not row == lastrow):
            bpy.ops.object.vertex_group_set_active(group="switch_projection_inner - " + str(column) + ", " + str(row))
            bpy.ops.object.vertex_group_select()

for thumb in range(6):
    bpy.ops.object.vertex_group_set_active(group="switch_projection_inner - thumb - " + str(thumb))
    bpy.ops.object.vertex_group_select()

bpy.ops.mesh.select_more()
bpy.ops.object.vertex_group_set_active(group="all")
bpy.ops.object.vertex_group_deselect()

grid_mesh = bmesh.from_edit_mesh(bpy.context.object.data)
for vertex in grid_mesh.verts:
    if vertex.select and vertex.co[2] <= 0.1:
        vertex.co[2] = 0.1
bpy.ops.mesh.select_all(action='DESELECT')
bpy.ops.object.mode_set(mode = 'OBJECT')


bpy.ops.object.select_all(action='DESELECT')
bpy.context.view_layer.objects.active = bpy.data.objects["body_inner_reference"]
bpy.data.objects["body_inner_reference"].select_set(True)
with suppress_stdout(): bpy.ops.object.delete()



##########################
## Loligagger Body Hole ##
##########################

if loligagger_port:
    bpy.ops.mesh.primitive_cube_add(size=1, location=bpy.data.objects['holder_projection'].location + mathutils.Vector((holder_hole_width/2 + holder_hole_offset, 0, 0)), scale=(holder_hole_width, 10, 2*holder_hole_height))
    bpy.context.selected_objects[0].name = "holder_outside"
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

    bpy.context.view_layer.objects.active = bpy.data.objects["body"]
    bpy.data.objects["body"].select_set(True)
    bpy.ops.object.modifier_add(type='BOOLEAN')
    bpy.context.object.modifiers["Boolean"].object = bpy.data.objects["holder_outside"]
    bpy.context.object.modifiers["Boolean"].use_hole_tolerant = True
    bpy.ops.object.modifier_apply(modifier="Boolean")
    
    
    bpy.ops.mesh.primitive_cube_add(size=1, location=bpy.data.objects['holder_projection'].location + mathutils.Vector((holder_hole_2_width/2 + holder_hole_2_offset, -8.5, 0)), scale=(holder_hole_2_width, 10, 2*holder_hole_height + 1))
    bpy.context.selected_objects[0].name = "holder_inside"
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    
    bpy.ops.object.mode_set(mode = 'EDIT')
    bpy.ops.mesh.select_all(action='DESELECT')
    grid_mesh = bmesh.from_edit_mesh(bpy.context.object.data)
    grid_mesh.verts.ensure_lookup_table()
    for vertex in [2, 3]:
        grid_mesh.verts[vertex].select = True
    bpy.ops.object.mode_set(mode = 'OBJECT')
    bpy.ops.object.mode_set(mode = 'EDIT')
    bpy.ops.mesh.bevel(offset=1.5, offset_pct=0, affect='EDGES')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.object.mode_set(mode = 'OBJECT')

    
    bpy.context.view_layer.objects.active = bpy.data.objects["body"]
    bpy.data.objects["body"].select_set(True)
    bpy.ops.object.modifier_add(type='BOOLEAN')
    bpy.context.object.modifiers["Boolean"].object = bpy.data.objects["holder_inside"]
    #bpy.context.object.modifiers["Boolean"].use_hole_tolerant = True
    bpy.ops.object.modifier_apply(modifier="Boolean")
    
    #bottom extension
    bpy.ops.mesh.primitive_cube_add(size=1, location=bpy.data.objects['holder_projection'].location + mathutils.Vector(((holder_hole_2_width-0.4)/2 + holder_hole_2_offset + 0.2, -10-3.7, -(bottom_thickness-0.5)/2 - 0.5)), scale=(holder_hole_2_width-0.4, 20, bottom_thickness-0.01-0.5))
    bpy.context.selected_objects[0].name = "holder_bottom_2"
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    
    bpy.ops.object.mode_set(mode = 'EDIT')
    bpy.ops.mesh.select_all(action='DESELECT')
    grid_mesh = bmesh.from_edit_mesh(bpy.context.object.data)
    grid_mesh.verts.ensure_lookup_table()
    for vertex in [2, 3]:
        grid_mesh.verts[vertex].select = True
    bpy.ops.object.mode_set(mode = 'OBJECT')
    bpy.ops.object.mode_set(mode = 'EDIT')
    bpy.ops.mesh.bevel(offset=1.5, offset_pct=0, affect='EDGES')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.object.mode_set(mode = 'OBJECT')

    bpy.context.view_layer.objects.active = bpy.data.objects["bottom"]
    bpy.data.objects["bottom"].select_set(True)
    bpy.ops.object.modifier_add(type='BOOLEAN')
    bpy.context.object.modifiers["Boolean"].operation = 'UNION'
    bpy.context.object.modifiers["Boolean"].object = bpy.data.objects["holder_bottom_2"]
    #bpy.context.object.modifiers["Boolean"].use_self = True
    #bpy.context.object.modifiers["Boolean"].use_hole_tolerant = True
    bpy.context.object.modifiers["Boolean"].solver = 'FAST'
    bpy.ops.object.modifier_apply(modifier="Boolean")
    
    bpy.ops.mesh.primitive_cube_add(size=1, location=bpy.data.objects['holder_projection'].location + mathutils.Vector(((holder_hole_width-0.4)/2 + holder_hole_offset + 0.2, -10, -(bottom_thickness-0.5)/2 - 0.5)), scale=(holder_hole_width-0.4, 20, bottom_thickness-0.02-0.5))
    bpy.context.selected_objects[0].name = "holder_bottom_1"
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    
    bpy.context.view_layer.objects.active = bpy.data.objects["bottom"]
    bpy.data.objects["bottom"].select_set(True)
    bpy.ops.object.modifier_add(type='BOOLEAN')
    bpy.context.object.modifiers["Boolean"].operation = 'UNION'
    bpy.context.object.modifiers["Boolean"].object = bpy.data.objects["holder_bottom_1"]
    #bpy.context.object.modifiers["Boolean"].use_self = True
    #bpy.context.object.modifiers["Boolean"].use_hole_tolerant = True
    bpy.context.object.modifiers["Boolean"].solver = 'FAST'
    bpy.ops.object.modifier_apply(modifier="Boolean")

    
    bpy.ops.object.select_all(action='DESELECT')
    bpy.data.objects["holder_projection"].select_set(True)
    bpy.data.objects["holder_outside"].select_set(True)
    bpy.data.objects["holder_inside"].select_set(True)
    bpy.data.objects["holder_bottom_1"].select_set(True)
    bpy.data.objects["holder_bottom_2"].select_set(True)
    with suppress_stdout(): bpy.ops.object.delete()
    


########################
##  Magnet Connectors ##
########################

if magnet_bottom:

    print("{:.2f}".format(time.time()-start_time), "- Adding Magnet Connectors")

    bpy.ops.object.select_all(action='DESELECT')

    bpy.ops.mesh.primitive_cylinder_add(vertices=50, radius=magnet_diameter/2 + 1, depth=magnet_height+2, enter_editmode=False, align='WORLD', location=(0, 0, 0), scale=(1, 1, 1))
    bpy.context.active_object.name = 'mag_template'
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)


    bpy.ops.object.mode_set(mode = 'EDIT')
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.mesh.select_mode(type="VERT")
    grid_mesh = bmesh.from_edit_mesh(bpy.context.object.data)
    grid_mesh.faces.ensure_lookup_table()
    for vertex in grid_mesh.verts:
        if (vertex.co[0] < .1):
            vertex.co[0] = 0
            vertex.select = True

    bpy.ops.transform.translate(value=(magnet_diameter/2 + 1.5 , 0, 0), orient_type='GLOBAL', orient_matrix=((1, 0, 0), (0, 1, 0), (0, 0, 1)), orient_matrix_type='GLOBAL', constraint_axis=(True, False, False), mirror=True, use_proportional_edit=False, proportional_edit_falloff='SMOOTH', proportional_size=1, use_proportional_connected=False, use_proportional_projected=False)


    bpy.ops.object.vertex_group_assign_new()
    bpy.ops.object.mode_set(mode = 'OBJECT')
    bpy.data.objects['mag_template'].vertex_groups['Group'].name = 'connection'

    bpy.ops.object.mode_set(mode = 'EDIT')
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.mesh.select_mode(type="VERT")
    grid_mesh = bmesh.from_edit_mesh(bpy.context.object.data)
    grid_mesh.faces.ensure_lookup_table()
    for vertex in grid_mesh.verts:
        if (vertex.co[2] < .1):
            vertex.select = True

    bpy.ops.object.vertex_group_assign_new()
    bpy.ops.object.mode_set(mode = 'OBJECT')
    bpy.data.objects['mag_template'].vertex_groups['Group'].name = 'bottom'


    bpy.ops.transform.translate(value=(magnet_diameter/2 + 1 + 2.5, 0, 0.5*(magnet_height+2)), orient_type='GLOBAL', orient_matrix=((1, 0, 0), (0, 1, 0), (0, 0, 1)), orient_matrix_type='GLOBAL', mirror=True, use_proportional_edit=False, proportional_edit_falloff='SMOOTH', proportional_size=1, use_proportional_connected=False, use_proportional_projected=False)
    bpy.ops.object.origin_set(type='ORIGIN_CURSOR', center='MEDIAN')

    bpy.context.active_object.select_set(False)
    bpy.ops.object.select_all(action='DESELECT')

    bpy.ops.mesh.primitive_cylinder_add(vertices=64, radius=magnet_diameter/2+0.4, depth=2*magnet_height+0.2, enter_editmode=False, align='WORLD', location=(0, 0, 0), scale=(1, 1, 1))
    bpy.context.active_object.name = 'mag_h_template'
    bpy.ops.object.transform_apply(location=True, rotation=False, scale=True)
    bpy.ops.transform.translate(value=(magnet_diameter/2 + 1 + 2.5, 0, -0.2), orient_type='GLOBAL', orient_matrix=((1, 0, 0), (0, 1, 0), (0, 0, 1)), orient_matrix_type='GLOBAL', mirror=True, use_proportional_edit=False, proportional_edit_falloff='SMOOTH', proportional_size=1, use_proportional_connected=False, use_proportional_projected=False)
    bpy.ops.object.origin_set(type='ORIGIN_CURSOR', center='MEDIAN')

    bpy.ops.curve.primitive_bezier_circle_add(radius=magnet_diameter/2+0.7, enter_editmode=False, align='WORLD', location=(0, 0, 0), scale=(1, 1, 1))
    bpy.context.active_object.name = 'mag_h_curve'
    bpy.ops.object.transform_apply(location=True, rotation=False, scale=True)
    bpy.ops.transform.translate(value=(magnet_diameter/2 + 1 + 2.5, 0, -0.2), orient_type='GLOBAL', orient_matrix=((1, 0, 0), (0, 1, 0), (0, 0, 1)), orient_matrix_type='GLOBAL', mirror=True, use_proportional_edit=False, proportional_edit_falloff='SMOOTH', proportional_size=1, use_proportional_connected=False, use_proportional_projected=False)
    bpy.ops.object.origin_set(type='ORIGIN_CURSOR', center='MEDIAN')

    bpy.ops.mesh.primitive_cylinder_add(radius=.8, depth=2*magnet_height+5, enter_editmode=False, align='WORLD', location=(0, 0, 0), scale=(1, 1, 1))
    bpy.context.active_object.name = 'mag_h_template_rib'
    bpy.ops.object.transform_apply(location=True, rotation=False, scale=True)
    bpy.ops.transform.translate(value=(magnet_diameter/2 + 1 + 2.5, 0, -0.2), orient_type='GLOBAL', orient_matrix=((1, 0, 0), (0, 1, 0), (0, 0, 1)), orient_matrix_type='GLOBAL', mirror=True, use_proportional_edit=False, proportional_edit_falloff='SMOOTH', proportional_size=1, use_proportional_connected=False, use_proportional_projected=False)
    bpy.ops.object.origin_set(type='ORIGIN_CURSOR', center='MEDIAN')

    bpy.ops.object.modifier_add(type='ARRAY')
    bpy.context.object.modifiers["Array"].count = 5
    bpy.context.object.modifiers["Array"].relative_offset_displace[0] = 2*pi*(magnet_diameter/2+0.7)/5/0.8
    bpy.ops.object.modifier_apply(modifier="Array")

    bpy.ops.object.modifier_add(type='CURVE')
    bpy.context.object.modifiers["Curve"].object = bpy.data.objects["mag_h_curve"]
    bpy.ops.object.modifier_apply(modifier="Curve")

    bpy.ops.object.select_all(action='DESELECT')
    bpy.data.objects['mag_h_template'].select_set(True)
    bpy.context.view_layer.objects.active = bpy.data.objects["mag_h_template"]
    bpy.ops.object.modifier_add(type='BOOLEAN')
    bpy.context.object.modifiers["Boolean"].object = bpy.data.objects["mag_h_template_rib"]
    bpy.ops.object.modifier_apply(modifier="Boolean")



    #              [location,                                       direction, rotation] 
    magnet_data = [['axis - 0, 0',                                  'axis - 0, 0',                                  [0, radians(90), 0] ],
                   ['axis - ' + str(ncols-2) + ', 0',               'axis - ' + str(ncols-2) + ', 0',               [radians(90), 0, 0] ],
                   ['axis - ' + str(ncols-2) + ', ' + str(nrows-2), 'axis - ' + str(ncols-2) + ', ' + str(nrows-2), [radians(-90), 0, 0]],
                   ['axis - thumb - 5',                             'axis - thumb - 5',                             [radians(-90), 0, 0]],
                   ['axis - 0, ' + str(nrows-2),                    'axis - 0, ' + str(nrows-2),                    [0, radians(90), 0] ],
                   ['axis - ' + str(ncols-1) + ', 0',               'axis - ' + str(ncols-1) + ', ' + str(nrows-2 - (nrows-1)%2 ), [0, radians(-90), 0]]]
    for item in range(len(magnet_data)):
        bpy.ops.object.select_all(action='DESELECT')
        bpy.ops.mesh.primitive_plane_add(enter_editmode=False, align='WORLD', location=((bpy.data.objects[magnet_data[item][0]].location[0]+bpy.data.objects[magnet_data[item][1]].location[0])/2, (bpy.data.objects[magnet_data[item][0]].location[1]+bpy.data.objects[magnet_data[item][1]].location[1])/2, 2), rotation=magnet_data[item][2], scale=(1, 1, 1))
        bpy.context.active_object.name = 'mag_' + str(item)
        bpy.ops.object.modifier_add(type='SHRINKWRAP')
        bpy.context.object.modifiers["Shrinkwrap"].target = bpy.data.objects["body"]
        bpy.context.object.modifiers["Shrinkwrap"].wrap_method = 'PROJECT'

        bpy.context.object.modifiers["Shrinkwrap"].use_positive_direction = False
        bpy.context.object.modifiers["Shrinkwrap"].use_negative_direction = True
        bpy.context.object.modifiers["Shrinkwrap"].offset = -body_thickness + 1
        bpy.ops.object.modifier_apply(modifier="Shrinkwrap")
        bpy.ops.transform.translate(value=(0, 0, -1.99), orient_type='GLOBAL', orient_matrix=((1, 0, 0), (0, 1, 0), (0, 0, 1)), orient_matrix_type='GLOBAL', mirror=True, use_proportional_edit=False, proportional_edit_falloff='SMOOTH', proportional_size=1, use_proportional_connected=False, use_proportional_projected=False)
        bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
        bpy.ops.object.origin_set(type='ORIGIN_CENTER_OF_MASS', center='MEDIAN')

    for x in range(len(magnet_data)):        
        bpy.ops.object.select_all(action='DESELECT')
        bpy.ops.object.add_named(name = 'mag_template')
        bpy.context.selected_objects[-1].name = 'maghole_' + str(x)
        bpy.ops.object.select_all(action='DESELECT')
        bpy.data.objects['maghole_' + str(x)].select_set(True)        
        bpy.ops.transform.translate(value=bpy.data.objects['mag_' + str(x)].location, orient_type='GLOBAL', orient_matrix=((1, 0, 0), (0, 1, 0), (0, 0, 1)), orient_matrix_type='GLOBAL', mirror=True, use_proportional_edit=False, proportional_edit_falloff='SMOOTH', proportional_size=1, use_proportional_connected=False, use_proportional_projected=False)

        bpy.context.object.rotation_mode = 'QUATERNION'
        bpy.context.object.rotation_quaternion = mathutils.Vector((bpy.data.objects['mag_' + str(x)].data.polygons[0].normal[0], bpy.data.objects['mag_' + str(x)].data.polygons[0].normal[1], 0)).to_track_quat('X','Z')
        bpy.ops.object.modifier_add(type='SHRINKWRAP')
        bpy.context.object.modifiers["Shrinkwrap"].wrap_method = 'PROJECT'
        bpy.context.object.modifiers["Shrinkwrap"].use_project_x = True
        bpy.context.object.modifiers["Shrinkwrap"].use_negative_direction = True
        bpy.context.object.modifiers["Shrinkwrap"].use_positive_direction = False
        bpy.context.object.modifiers["Shrinkwrap"].target = bpy.data.objects["body"]
        bpy.context.object.modifiers["Shrinkwrap"].offset = -body_thickness/2
        bpy.context.object.modifiers["Shrinkwrap"].vertex_group = "connection"
        bpy.ops.object.modifier_apply(modifier="Shrinkwrap")
        
        bpy.ops.object.mode_set(mode = 'EDIT')
        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.mesh.select_mode(type="VERT")
        grid_mesh = bmesh.from_edit_mesh(bpy.context.object.data)
        grid_mesh.faces.ensure_lookup_table()

        bpy.ops.object.vertex_group_set_active(group="bottom")
        bpy.ops.object.vertex_group_select()

        for vertex in grid_mesh.verts:
            if (vertex.select):
                vertex.co[2] = 0


        bpy.ops.object.mode_set(mode = 'OBJECT')

    for x in range(len(magnet_data)):
        bpy.ops.object.select_all(action='DESELECT')
        bpy.ops.object.add_named(name = 'mag_h_template')
        bpy.context.selected_objects[-1].name = 'mag_h_' + str(x)
        bpy.ops.object.select_all(action='DESELECT')
        bpy.data.objects['mag_h_' + str(x)].select_set(True)    
        
        bpy.ops.transform.translate(value=bpy.data.objects['mag_' + str(x)].location, orient_type='GLOBAL', orient_matrix=((1, 0, 0), (0, 1, 0), (0, 0, 1)), orient_matrix_type='GLOBAL', mirror=True, use_proportional_edit=False, proportional_edit_falloff='SMOOTH', proportional_size=1, use_proportional_connected=False, use_proportional_projected=False)
        bpy.context.object.rotation_mode = 'QUATERNION'
        bpy.context.object.rotation_quaternion = mathutils.Vector((bpy.data.objects['mag_' + str(x)].data.polygons[0].normal[0], bpy.data.objects['mag_' + str(x)].data.polygons[0].normal[1], 0)).to_track_quat('X','Z')

    bpy.ops.object.select_all(action='DESELECT')


    for x in range(len(magnet_data)):
        bpy.data.objects['mag_h_' + str(x)].select_set(True)
        bpy.context.view_layer.objects.active = bpy.data.objects['mag_h_' + str(x)]
    bpy.ops.object.join()
    bpy.context.selected_objects[0].name = "mag_h"

    bpy.context.active_object.select_set(False)
    bpy.ops.object.select_all(action='DESELECT')
    for x in range(len(magnet_data)):
        bpy.data.objects['maghole_' + str(x)].select_set(True)
        bpy.context.view_layer.objects.active = bpy.data.objects['maghole_' + str(x)]
    bpy.ops.object.join()
    bpy.context.selected_objects[0].name = "maghole"

    bpy.context.active_object.select_set(False)
    bpy.context.view_layer.objects.active = bpy.data.objects['body']

    bpy.ops.object.modifier_add(type='BOOLEAN')
    bpy.context.object.modifiers["Boolean"].operation = 'UNION'
    bpy.context.object.modifiers["Boolean"].object = bpy.data.objects["maghole"]
    bpy.context.object.modifiers["Boolean"].solver = 'FAST'
    bpy.ops.object.modifier_apply(modifier="Boolean")


    bpy.ops.object.modifier_add(type='BOOLEAN')
    bpy.context.object.modifiers["Boolean"].operation = 'DIFFERENCE'
    bpy.context.object.modifiers["Boolean"].object = bpy.data.objects["mag_h"]
    bpy.context.object.modifiers["Boolean"].solver = 'FAST'
    bpy.ops.object.modifier_apply(modifier="Boolean")


    bpy.context.view_layer.objects.active = bpy.data.objects["maghole"]
    bpy.ops.object.mode_set(mode = 'EDIT')
    bpy.ops.transform.shrink_fatten(value=1, use_even_offset=False, mirror=True, use_proportional_edit=False, proportional_edit_falloff='SMOOTH', proportional_size=1, use_proportional_connected=False, use_proportional_projected=False)

    grid_mesh = bmesh.from_edit_mesh(bpy.context.object.data)
    grid_mesh.faces.ensure_lookup_table()
    for vertex in grid_mesh.verts:
        if (vertex.co[2] < .1):
            vertex.co[2] = 0
    bpy.ops.object.mode_set(mode = 'OBJECT')


    bpy.context.view_layer.objects.active = bpy.data.objects["bottom"]

    bpy.ops.object.modifier_add(type='BOOLEAN')
    bpy.context.object.modifiers["Boolean"].operation = 'DIFFERENCE'
    bpy.context.object.modifiers["Boolean"].object = bpy.data.objects["mag_h"]
    #bpy.context.object.modifiers["Boolean"].use_self = True
    bpy.context.object.modifiers["Boolean"].solver = 'FAST'
    bpy.ops.object.modifier_apply(modifier="Boolean")

    bpy.context.view_layer.objects.active = bpy.data.objects["body"]

    bpy.ops.object.select_all(action='DESELECT')
    for object in ['mag_0', 'mag_1', 'mag_2', 'mag_3', 'mag_4', 'mag_5', 'mag_template', 'mag_h_template', 'mag_h', 'maghole', 'mag_template', 'mag_h_template_rib', 'mag_h_curve']:
        bpy.data.objects[object].select_set(True)
    with suppress_stdout(): bpy.ops.object.delete()




#########################
## Create Switch Holes ##
#########################

print("{:.2f}".format(time.time()-start_time), "- Add Switch Holes")

bpy.context.view_layer.objects.active = bpy.data.objects["body"]
bpy.data.objects['body'].select_set(True)

bpy.ops.object.modifier_add(type='BOOLEAN')
bpy.context.object.modifiers["Boolean"].operand_type = 'COLLECTION'
bpy.context.object.modifiers["Boolean"].solver = 'FAST'
bpy.context.object.modifiers["Boolean"].collection = bpy.data.collections["SWITCH_HOLE"]
bpy.ops.object.modifier_apply(modifier="Boolean")


'''
for thing in bpy.data.collections['SWITCH_HOLE'].objects:
    print("   ---" + thing.name)
    bpy.ops.object.modifier_add(type='BOOLEAN')
    bpy.context.object.modifiers["Boolean"].object = thing
    #bpy.context.object.modifiers["Boolean"].use_self = True
    bpy.context.object.modifiers["Boolean"].use_hole_tolerant = True
    bpy.ops.object.modifier_apply(modifier="Boolean")
'''


#########################
## Add Switch Supports ##
#########################

if switch_support:
    print("{:.2f}".format(time.time()-start_time), "- Add Switch Supports")
    
    bpy.context.view_layer.objects.active = bpy.data.objects["body"]
    bpy.data.objects['body'].select_set(True)
    
    bpy.ops.object.modifier_add(type='BOOLEAN')
    bpy.context.object.modifiers["Boolean"].operation = 'UNION'
    bpy.context.object.modifiers["Boolean"].operand_type = 'COLLECTION'
    bpy.context.object.modifiers["Boolean"].solver = 'FAST'
    bpy.context.object.modifiers["Boolean"].collection = bpy.data.collections["SWITCH_SUPPORT"]
    bpy.ops.object.modifier_apply(modifier="Boolean")
    '''
    for thing in bpy.data.collections['SWITCH_SUPPORT'].objects:
        print("   ---" + thing.name)
        bpy.ops.object.modifier_add(type='BOOLEAN')
        bpy.context.object.modifiers["Boolean"].operation = 'UNION'
        bpy.context.object.modifiers["Boolean"].object = thing
        bpy.ops.object.modifier_apply(modifier="Boolean")
    '''



##############
## Clean Up ##
##############

print("{:.2f}".format(time.time()-start_time), "- Clean Up")

bpy.ops.object.select_all(action='DESELECT')

for collection in ['AXIS', 'SWITCH_SUPPORT', 'SWITCH_HOLE', 'SWITCH_PROJECTION', 'SWITCH_PROJECTION_INNER', 'KEYCAP_PROJECTION_OUTER', 'KEYCAP_PROJECTION_INNER']:
    for thing in bpy.data.collections[collection].objects:
        thing.select_set(True)
    with suppress_stdout(): bpy.ops.object.delete()
    bpy.data.collections.remove(bpy.data.collections[collection])

print("{:.2f}".format(time.time()-start_time), "- DONE")
