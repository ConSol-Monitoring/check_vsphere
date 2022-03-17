def get_obj_by_name(si, vimtype, name):
    view = si.content.viewManager.CreateContainerView(
        si.content.rootFolder,
        [vimtype],
        True
    )
    for obj in view.view:
        if obj.name == name:
            return obj
    
    return None