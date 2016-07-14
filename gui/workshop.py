

def common(context, layout, guiClsInstance):
    name = guiClsInstance.itemName
    box = layout.box()
    op = box.operator("prk.workshop_start_template")
    op.objectNameBase = name[0].capitalize() + name[1:]
    box.operator("prk.workshop_add_part")
    box.operator("prk.workshop_assign_node")
    box.operator("prk.workshop_set_child_offset")
    box.operator("prk.workshop_make_item", text = "Make a " + name)