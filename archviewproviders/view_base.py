# ***************************************************************************
# *   Copyright (c) 2020 Carlo Pavan                                        *
# *                                                                         *
# *   This program is free software; you can redistribute it and/or modify  *
# *   it under the terms of the GNU Lesser General Public License (LGPL)    *
# *   as published by the Free Software Foundation; either version 2 of     *
# *   the License, or (at your option) any later version.                   *
# *   for detail see the LICENCE text file.                                 *
# *                                                                         *
# *   This program is distributed in the hope that it will be useful,       *
# *   but WITHOUT ANY WARRANTY; without even the implied warranty of        *
# *   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the         *
# *   GNU Library General Public License for more details.                  *
# *                                                                         *
# *   You should have received a copy of the GNU Library General Public     *
# *   License along with this program; if not, write to the Free Software   *
# *   Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  *
# *   USA                                                                   *
# *                                                                         *
# ***************************************************************************
"""Provide the object code for Arch base viewprovider."""
## @package view_base
# \ingroup ARCH
# \brief Provide the code for Arch base viewproviders.

from pivy import coin
import FreeCAD as App
import FreeCADGui as Gui

import Part


class ViewProviderShapeGroup(object):
    """
    The ShapeGroup object is the base object for Arch Walls.
    It provides the possibility to display the object own shape and also
    the grouped objects shape at the same time.
    The object was designed by realthunder.

    ref: Python object with OriginGroupExtension
         https://forum.freecadweb.org/viewtopic.php?f=22&t=44701
         https://gist.github.com/realthunder/40cd71a3085be666c3e2d718171de133
    """

    def __init__(self, vobj=None):
        self.group_node = None
        if vobj:
            vobj.Proxy = self
            self.attach(vobj)
        else:
            self.ViewObject = None

    def attach(self, vobj):
        vobj.addExtension("Gui::ViewProviderGeoFeatureGroupExtensionPython")
        self.ViewObject = vobj
        self.setupShapeGroup()

    def setupShapeGroup(self):
        vobj = self.ViewObject
        if getattr(self, "group_node", None) or vobj.SwitchNode.getNumChildren() < 2:
            return
        self.group_node = vobj.SwitchNode.getChild(0)
        for i in range(1, vobj.SwitchNode.getNumChildren()):
            node = coin.SoSeparator()
            node.addChild(self.group_node)
            node.addChild(vobj.SwitchNode.getChild(i))
            vobj.SwitchNode.replaceChild(i, node)
        try:
            vobj.SwitchNode.defaultChild = 1
        except Exception:
            pass

    def getDefaultDisplayMode(self):
        return "Flat Lines"

    def getDetailPath(self, subname, path, append):
        if not subname or not getattr(self, "group_node", None):
            raise NotImplementedError
        subs = Part.splitSubname(subname)
        objs = subs[0].split(".")

        vobj = self.ViewObject
        mode = vobj.SwitchNode.whichChild.getValue()
        if mode <= 0:
            raise NotImplementedError

        if append:
            path.append(vobj.RootNode)
            path.append(vobj.SwitchNode)

        node = vobj.SwitchNode.getChild(mode)
        path.append(node)
        if mode > 0:
            if not objs[0]:
                path.append(node.getChild(1))
            else:
                path.append(node.getChild(0))
        if not objs[0]:
            return vobj.getDetailPath(subname, path, False)

        for child in vobj.claimChildren():
            if child.Name == objs[0]:
                sub = Part.joinSubname(".".join(objs[1:]), subs[1], subs[2])
                return child.ViewObject.getDetailPath(sub, path, True)

    def getElementPicked(self, pp):
        if not getattr(self, "group_node", None):
            raise NotImplementedError
        vobj = self.ViewObject
        path = pp.getPath()
        if path.findNode(self.group_node) < 0:
            raise NotImplementedError
        for child in vobj.claimChildren():
            if path.findNode(child.ViewObject.RootNode) < 0:
                continue
            return child.Name + "." + child.ViewObject.getElementPicked(pp)

    def onChanged(self, _vobj, prop):
        if prop == "DisplayMode":
            self.setupShapeGroup()

    def onDelete(self, vobj, subelements):  # subelements is a tuple of strings
        """
        Activated when object is deleted
        """
        from PySide import QtGui

        # ask if the user is sure and wants to delete contained objects
        if not vobj.Object.Group:
            return True

        msgBox = QtGui.QMessageBox()
        msgBox.setText("Deleting wall object " + vobj.Object.Label + ".")
        msgBox.setInformativeText("Do you want to delete also contained objects?")
        msgBox.setStandardButtons(
            QtGui.QMessageBox.Yes | QtGui.QMessageBox.No | QtGui.QMessageBox.Cancel
        )
        msgBox.setDefaultButton(QtGui.QMessageBox.Yes)
        ret = msgBox.exec_()

        if ret == QtGui.QMessageBox.Yes:
            delete_children = True
        elif ret == QtGui.QMessageBox.No:
            delete_children = False
        elif ret == QtGui.QMessageBox.Cancel:
            # the object won't be deleted
            return False
        else:
            # the object won't be deleted
            return False

        if delete_children:
            for o in vobj.Object.Group:
                App.ActiveDocument.removeObject(o.Name)

        # the object will be deleted
        return True

    def __getstate__(self):
        return None

    def __setstate__(self, _state):
        return None
