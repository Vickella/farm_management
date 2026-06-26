DELETE FROM tabWorkspace WHERE name = 'Farm Management';
DELETE FROM `tabWorkspace Link` WHERE parent = 'Farm Management';
DELETE FROM `tabWorkspace Shortcut` WHERE parent = 'Farm Management';
DELETE FROM `tabWorkspace Chart` WHERE parent = 'Farm Management';
DELETE FROM `tabWorkspace Number Card` WHERE parent = 'Farm Management';
DELETE FROM `tabWorkspace Quick List` WHERE parent = 'Farm Management';
