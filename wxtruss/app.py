# -*- coding: utf-8 -*-
#
# wxtruss 
# License: MIT License
# Author: Pedro Jorge De Los Santos
# E-mail: delossantosmfq@gmail.com
# ~ from __future__ import division
import wx
import wx.grid as grid
import wx.html as html
import numpy as np
import matplotlib
matplotlib.use('WXAgg')
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas
from matplotlib.backends.backend_wxagg import NavigationToolbar2WxAgg as NavigationToolbar
import matplotlib.lines as mlines
import wxtruss.iconos as ic
from nusa import * # FEA library
import webbrowser
import pandas as pd
import json
import os


# For  versioning
dir_setup = os.path.dirname(os.path.realpath(__file__))

with open(os.path.join(dir_setup, '', 'version.py')) as f:
    # Defines __version__
    exec(f.read())


class wxTruss(wx.Frame):
    def __init__(self,parent):
        wx.Frame.__init__(self,parent,title="wxTruss",size=(900,600))
        
        self.init_menu()
        self.init_ctrls()
        self.init_model_data()
        
        self.SetBackgroundColour("#FFFFFF")
        self.SetIcon(ic.wxtruss.GetIcon())
        self.Centre(True)
        self.Show()
        
    def init_ctrls(self):
        self.mainsz = wx.BoxSizer(wx.HORIZONTAL)
        self.upsz = wx.BoxSizer(wx.HORIZONTAL)
        self.figsz = wx.BoxSizer(wx.VERTICAL)

        self.toolbar = Toolbar(self)
        self.toolbar.Realize()
        self.upsz.Add(self.toolbar, 0, wx.ALIGN_LEFT)
        
        # Creating figures, axes and canvas
        self._set_mpl()
        self.figure = Figure()
        self.axes = self.figure.add_subplot(111)
        self.canvas = FigureCanvas(self, -1, self.figure)
        self.mpl_toolbar = NavigationToolbar(self.canvas)
        self.mpl_toolbar.Realize()
        self.figsz.Add(self.canvas, 12, wx.EXPAND|wx.ALL, 2)
        self.figsz.Add(self.mpl_toolbar, 1, wx.EXPAND|wx.ALL, 20)
        #~ self.figure.set_facecolor("w")
        
        self.txtout = HTMLWindow(self)
        #~ self.txtout.SetMinSize((200,-1))
        #~ self.txtout.SetPage("<html></html>")
        
        self.upsz.Add(self.figsz, 1, wx.EXPAND|wx.ALL, 2)
        self.mainsz.Add(self.upsz, 5, wx.EXPAND)
        self.mainsz.Add(self.txtout, 3, wx.EXPAND)
        self.SetSizer(self.mainsz)
        
        # toolbar events
        self.Bind(wx.EVT_TOOL, self.add_nodes, self.toolbar.nodes_tool)
        self.Bind(wx.EVT_TOOL, self.add_elements, self.toolbar.elements_tool)
        self.Bind(wx.EVT_TOOL, self.add_constraints, self.toolbar.constraints_tool)
        self.Bind(wx.EVT_TOOL, self.add_forces, self.toolbar.forces_tool)
        self.Bind(wx.EVT_TOOL, self.plot_model, self.toolbar.plot_model_tool)
        self.Bind(wx.EVT_TOOL, self.solve_model, self.toolbar.solve_tool)
        self.Bind(wx.EVT_TOOL, self.plot_deformed_shape, self.toolbar.plot_deformed_shape_tool)
        
    def _set_mpl(self):
        matplotlib.rc('figure', facecolor="#ffffff")
        matplotlib.rc('axes', facecolor="#ffffff", linewidth=0.1, grid=False)
        # ~ matplotlib.rc('font', family="Times New Roman")
    
    def init_menu(self):
        m_file = wx.Menu()
        from_json = m_file.Append(-1, "Read model from Truss/JSON file... \tCtrl+J")
        quit_app = m_file.Append(-1, "Quit \tCtrl+Q")
        
        m_help = wx.Menu()
        _help = m_help.Append(-1, "Help")
        about = m_help.Append(-1, "About...")
        
        menu_bar = wx.MenuBar()
        menu_bar.Append(m_file, "File")
        menu_bar.Append(m_help, "Help")
        self.SetMenuBar(menu_bar)
        
        self.Bind(wx.EVT_MENU, self.on_from_json, from_json)
        self.Bind(wx.EVT_MENU, self.on_about, about)
        self.Bind(wx.EVT_MENU, self.on_help, _help)
        self.Bind(wx.EVT_MENU, self.on_quit, quit_app)
        
    def init_model_data(self):
        try:
            self.read_model_from_json("data/example_03.truss")
        except:
            self.nodes = np.array([[0,0],[2,0],[0,2]])
            self.elements = np.array([[1,2,200e9,1e-4],[2,3,200e9,1e-4],[1,3,200e9,1e-4]])
            self.forces = np.array([[3,1000,0]])
            self.constraints = np.array([[1, 0, 0], [2, 0, 0]])
        
    def isempty(self,arg):
        if not arg:
            return True
        return False
        
    def on_about(self,event):
        AboutDialog(None)
        
    def on_help(self,event):
        print("Help unavailable")
    
    def on_quit(self,event):
        self.Close()
        
        
    def on_from_json(self,event):
        path = ""
        wildcard = "Truss file (*.truss)|*.truss| JSON file (*.json)|*.json"
        dlg = wx.FileDialog(self, message="Select a Truss/JSON file...",
        defaultDir=os.getcwd(), wildcard=wildcard, style=wx.FD_OPEN)
        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.GetPath()
        dlg.Destroy()
        if not path:
            wx.MessageBox('Not file selected', 'wxTruss', wx.OK | wx.ICON_INFORMATION)
        else:
            self.read_model_from_json(path)
        
    def build_model(self):        
        nc = self.nodes
        ec = self.elements
        x,y = nc[:,0], nc[:,1]

        nodos = []
        elementos = []

        for k,nd in enumerate(nc):
            cn = Node((x[k],y[k]))
            nodos.append(cn)
            
        for k,elm in enumerate(ec):
            i,j,E,A = int(elm[0]-1),int(elm[1]-1),elm[2],elm[3]
            ni,nj = nodos[i],nodos[j]
            ce = Truss((ni,nj), E, A)
            elementos.append(ce)
            
        self.model = TrussModel("Truss Model")
        for n in nodos: self.model.add_node(n)
        for e in elementos: self.model.add_element(e)
        
        for c in self.constraints:
            k,ux,uy = int(c[0]),c[1],c[2]
            if ~np.isnan(ux) and ~np.isnan(uy):
                self.model.add_constraint(nodos[k-1], ux=ux, uy=uy)
            elif ~np.isnan(ux):
                self.model.add_constraint(nodos[k-1], ux=ux)
            elif ~np.isnan(uy):
                self.model.add_constraint(nodos[k-1], uy=uy)
        
        for f in self.forces:
            k,fx,fy = int(f[0]),f[1],f[2]
            self.model.add_force(nodos[k-1],(fx,fy))
        
    def solve_model(self,event):
        self.build_model()
        self.model.solve()
        self.html_report()
        
    def html_report(self):        
        m = self.model
        
        NODES = [n.label+1 for n in m.get_nodes()]
        ELEMENTS = [e.label+1 for e in m.get_elements()]
        
        el = [e.get_nodes() for e in m.get_elements()]
        ELEMENTS_CONN = [(ni.label+1,nj.label+1) for ni,nj in el]
        NODAL_COORDS = [[n.x,n.y] for n in m.get_nodes()]
        NODAL_DISPLACEMENTS = [[n.ux,n.uy] for n in m.get_nodes()]
        NODAL_FORCES = [[n.fx,n.fy] for n in m.get_nodes()]
        ELEMENT_FORCES = [e.f for e in m.get_elements()]
        ELEMENT_STRESSES = [e.s for e in m.get_elements()]
        
        EL_INFO = pd.DataFrame(ELEMENTS_CONN, columns=["Ni","Nj"], index=ELEMENTS).to_html()
        ND_COORDS = pd.DataFrame(NODAL_COORDS, columns=["X","Y"], index=NODES).to_html()
        ND = pd.DataFrame(NODAL_DISPLACEMENTS, columns=["UX","UY"], index=NODES).to_html()
        NF = pd.DataFrame(NODAL_FORCES, columns=["FX","FY"], index=NODES).to_html()
        EF = pd.DataFrame(ELEMENT_FORCES, columns=["F",], index=ELEMENTS).to_html()
        ES = pd.DataFrame(ELEMENT_STRESSES, columns=["S",], index=ELEMENTS).to_html()
        
        txt = REPORT_TEMPLATE.format(nodal_displacements=ND, nodal_forces=NF, 
                                     element_forces=EF, element_stresses=ES,
                                     nodal_coords=ND_COORDS, elements=EL_INFO)  
        self.txtout.SetPage(txt)
        
    def add_nodes(self,event):
        data = self.nodes
        dlg = NodesDialog(self,data)
        if dlg.ShowModal() == wx.ID_OK:
            data = dlg.GetData()
            self.nodes = data
        dlg.Destroy()
        print(data)
        
    def add_elements(self,event):
        data = self.elements
        dlg = ElementsDialog(self,data)
        if dlg.ShowModal() == wx.ID_OK:
            data = dlg.GetData()
            self.elements = data
        dlg.Destroy()
        print(data)
        
    def add_constraints(self,event):
        data = self.constraints
        dlg = ConstraintsDialog(self,data)
        if dlg.ShowModal() == wx.ID_OK:
            data = dlg.GetData()
            self.constraints = data
        dlg.Destroy()
        print(data)
        
    def add_forces(self,event):
        data = self.forces
        dlg = ForcesDialog(self,data)
        if dlg.ShowModal() == wx.ID_OK:
            data = dlg.GetData()
            self.forces = data
        dlg.Destroy()
        print(data)

    def plot_model(self,event):
        """
        Plot the mesh model, including bcs
        """
        self.build_model()
        ax = self.axes
        ax.cla()
        
        for elm in self.model.get_elements():
            ni, nj = elm.get_nodes()
            ax.plot([ni.x,nj.x],[ni.y,nj.y],"b-o", markersize=3)
            for nd in (ni,nj):
                if nd.fx > 0: self._draw_xforce(ax,nd.x,nd.y,1)
                if nd.fx < 0: self._draw_xforce(ax,nd.x,nd.y,-1)
                if nd.fy > 0: self._draw_yforce(ax,nd.x,nd.y,1)
                if nd.fy < 0: self._draw_yforce(ax,nd.x,nd.y,-1)
                if nd.ux == 0: self._draw_xconstraint(ax,nd.x,nd.y)
                if nd.uy == 0: self._draw_yconstraint(ax,nd.x,nd.y)
        
        
        x0,x1,y0,y1 = self.rect_region()
        xf,yf = abs(x1-x0)/20, abs(y1-y0)/20
        # ~ bbox = dict(boxstyle=f"circle", fc="#fafafa")
        # ~ for nd in self.model.get_nodes():
            # ~ cstr = str(nd.label+1)
            # ~ ax.text(nd.x - xf, nd.y + yf, cstr, fontsize=7, color="#F41313",
            # ~ zorder=10000, bbox=bbox)
        ax.axis('equal')
        ax.set_xlim(x0,x1)
        ax.set_ylim(y0,y1)
        self.canvas.draw()

    def _draw_xforce(self,axes,x,y,ddir=1):
        """
        Draw horizontal arrow -> Force in x-dir
        """
        dx, dy = self._calculate_arrow_size(), 0
        HW = dx/5.0
        HL = dx/3.0
        arrow_props = dict(head_width=HW, head_length=HL, fc='r', ec='r')
        axes.arrow(x, y, ddir*dx, dy, **arrow_props)
        
    def _draw_yforce(self,axes,x,y,ddir=1):
        """
        Draw vertical arrow -> Force in y-dir
        """
        dx,dy = 0, self._calculate_arrow_size()
        HW = dy/5.0
        HL = dy/3.0
        arrow_props = dict(head_width=HW, head_length=HL, fc='r', ec='r')
        axes.arrow(x, y, dx, ddir*dy, zorder=1000, **arrow_props)
        
    def _draw_xconstraint(self,axes,x,y):
        axes.plot(x, y, "b<", markersize=10, alpha=0.6)
    
    def _draw_yconstraint(self,axes,x,y):
        axes.plot(x, y, "gv", markersize=10, alpha=0.6)
        
    def _calculate_arrow_size(self):
        x0,x1,y0,y1 = self.rect_region(factor=50)
        sf = 5e-2
        kfx = sf*(x1-x0)
        kfy = sf*(y1-y0)
        return np.mean([kfx,kfy])
        
    def rect_region(self,factor=7.0):
        nx,ny = [],[]
        for n in self.model.get_nodes():
            nx.append(n.x)
            ny.append(n.y)
        xmn,xmx,ymn,ymx = min(nx),max(nx),min(ny),max(ny)
        kx = (xmx-xmn)/factor
        ky = (ymx-ymn)/factor
        return xmn-kx, xmx+kx, ymn-ky, ymx+ky
        
    def plot_deformed_shape(self,event,dfactor=1.0):
        ax = self.axes
        ax.cla() #clear axes
        
        df = dfactor*self._calculate_deformed_factor()
        
        for elm in self.model.get_elements():
            ni,nj = elm.get_nodes()
            x, y = [ni.x,nj.x], [ni.y,nj.y]
            xx = [ni.x+ni.ux*df, nj.x+nj.ux*df]
            yy = [ni.y+ni.uy*df, nj.y+nj.uy*df]
            ax.plot(x,y,'bo-')
            ax.plot(xx,yy,'ro--')
        
        undefor = mlines.Line2D([], [], linestyle="-", color='b', marker='o', 
                                  markersize=5, label='Undeformed')
        defor = mlines.Line2D([], [], linestyle="--", color='r', marker='o', 
                                  markersize=5, label="Deformed (Factor: x{:0.0f})".format(self._calculate_deformed_factor()))
        
        # Shrink current axis by 20%
        # ~ box = ax.get_position()
        # ~ ax.set_position([box.x0, box.y0 + box.height * 0.1,
                 # ~ box.width, box.height * 0.9])
        
        ax.legend(handles=[defor,undefor], loc='upper center', bbox_to_anchor=(0.5, -0.05),
          fancybox=True, shadow=True, ncol=5)
        
        x0,x1,y0,y1 = self.rect_region()
        ax.axis('equal')
        ax.set_xlim(x0,x1)
        ax.set_ylim(y0,y1)
        self.canvas.draw()
        
    def _calculate_deformed_factor(self):
        x0,x1,y0,y1 = self.rect_region()
        ux = np.abs(np.array([n.ux for n in self.model.get_nodes()]))
        uy = np.abs(np.array([n.uy for n in self.model.get_nodes()]))
        sf = 1.5e-2
        if ux.max()==0 and uy.max()!=0:
            kfx = sf*(y1-y0)/uy.max()
            kfy = sf*(y1-y0)/uy.max()
        if uy.max()==0 and ux.max()!=0:
            kfx = sf*(x1-x0)/ux.max()
            kfy = sf*(x1-x0)/ux.max()
        if ux.max()!=0 and uy.max()!=0:
            kfx = sf*(x1-x0)/ux.max()
            kfy = sf*(y1-y0)/uy.max()
        return np.mean([kfx,kfy])
    
    def read_model_from_json(self,filename):
        json_file = filename
        with open(json_file, 'r') as myfile:
            data=myfile.read()
        obj = json.loads(data)
        
        nn = len(obj["nodes"])
        nodes = np.zeros((nn,2))
        for i,m in enumerate(obj["nodes"]):
            nodes[i,0] = m["x"]
            nodes[i,1] = m["y"]
        self.nodes = nodes
        
        nn = len(obj["elements"])
        elementos = np.zeros((nn,4))
        for i,m in enumerate(obj["elements"]):
            elementos[i,0] = m["ni"]
            elementos[i,1] = m["nj"]
            elementos[i,2] = m["E"]
            elementos[i,3] = m["A"]
        self.elements = elementos
        
        nn = len(obj["constraints"])
        const = np.zeros((nn,3))
        for i,m in enumerate(obj["constraints"]):
            const[i,1] = np.nan if m["ux"] == "free" else m["ux"]
            const[i,2] = np.nan if m["uy"] == "free" else m["uy"]
            const[i,0] = m["node"]
        self.constraints = const
        
        nn = len(obj["forces"])
        fuerzas = np.zeros((nn,3))
        for i,m in enumerate(obj["forces"]):
            fuerzas[i,1] = m["fx"]
            fuerzas[i,2] = m["fy"]
            fuerzas[i,0] = m["node"]
        self.forces = fuerzas
        self.plot_model([])
            

class AboutDialog(wx.Frame):
    def __init__(self,parent,*args,**kwargs):
        _styles = wx.CAPTION|wx.CLOSE_BOX
        wx.Frame.__init__(self,parent=parent,title="wxTruss",
        size=(350,220), style=_styles)
        self.SetIcon(ic.wxtruss.GetIcon())
        self.winhtml = HTMLWindow(self)
        self.winhtml.SetPage(ABOUT_HTML)
        self.Centre(True)
        self.Show()


ABOUT_HTML = """
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <meta http-equiv="X-UA-Compatible" content="IE=edge">
  <title></title>
  <link rel="stylesheet" href="">
</head>
<body bgcolor="#0A3865" link="#E5E5E5" vlink="#F0F0F0" alink="#F0F0F0">
  <center>
  <h1><font color="#FFFF00"> wxTruss {version} </font></h1>


  <font color="#ADD8E6">
  <b>Developer:</b> Pedro Jorge De Los Santos <br>
  <b>E-mail:</b> delossantosmfq@gmail.com <br>
  <b>License:</b> MIT (<a href="https://opensource.org/licenses/MIT">See license</a>) <br>
  <a href="https://github.com/JorgeDeLosSantos/wxtruss">Project Repository</a>
  </font>
  
  </center>
</body>
</html>
""".format(version=__version__)

class HTMLWindow(html.HtmlWindow):
    def __init__(self,parent,**kwargs):
        html.HtmlWindow.__init__(self,parent=parent,**kwargs)
    
    def OnLinkClicked(self, link):
        webbrowser.open(link.GetHref())



class DataGrid(grid.Grid):
    def __init__(self,parent,gridsize,**kwargs):
        grid.Grid.__init__(self,parent=parent,id=-1,**kwargs)
        rows = int(gridsize[0])
        cols = int(gridsize[1])
        self.CreateGrid(rows,cols)
        self.SetRowLabelSize(20)
        
        self.Bind(grid.EVT_GRID_CELL_CHANGED, self.OnCellEdit)
        self.Bind(grid.EVT_GRID_CELL_RIGHT_CLICK, self.OnRightClick)
        
    def UpdateGridSize(self,rows,cols):
        self.ClearGrid()
        ccols = self.GetNumberCols()
        crows = self.GetNumberRows()
        
        if rows > crows:
            self.AppendRows(rows-crows)
        elif rows < crows:
            self.DeleteRows(0,crows-rows)
            
        if cols > ccols:
            self.AppendCols(cols-ccols)
        elif cols < ccols:
            self.DeleteCols(0,ccols-cols)
            
    def SetArrayData(self,data):
        """
        Data must be a numpy array
        """
        r,c = data.shape # For numpy array
        self.UpdateGridSize(r,c)
        for i in range(r):
            for j in range(c):
                if i==0: self.SetColFormatFloat(5, 6, 4)
                val = str(data[i][j])
                self.SetCellValue(i,j,val)
        
    def GetArrayData(self):
        nrows = self.GetNumberRows()
        ncols = self.GetNumberCols()
        X = np.zeros((nrows,ncols))
        for i in range(nrows):
            for j in range(ncols):
                cval = self.GetCellValue(i,j)
                if not self.isempty(cval):
                    try:
                        X[i][j] = float(cval)
                    except:
                        # Revisar valores devueltos
                        X[i][j] = np.nan
                else:
                    X[i][j] = np.nan
        X = X[~np.isnan(X).any(axis=1)] # Complete rows
        return X
        
    def GetSelectedData(self):
        scols = self.GetSelectedCols()
        srows = self.GetSelectedRows()
        X = np.zeros((len(srows),len(scols)))
        for ii,row in enumerate(srows):
            for jj,col in enumerate(scols):
                try:
                    X[ii][jj] = self.GetCellValue(row,col)
                except ValueError:
                    X[ii][jj] = np.nan
        return X
                
        
    def GetSelectedCols(self):
        scols = []
        top_left = self.GetSelectionBlockTopLeft()
        bottom_right = self.GetSelectionBlockBottomRight()
        if not self.isempty(bottom_right) and not self.isempty(top_left):
            max_col = bottom_right[0][1]
            min_col = top_left[0][1]
            scols = range(min_col,max_col+1)
        return scols
        
    def GetSelectedRows(self):
        srows = []
        top_left = self.GetSelectionBlockTopLeft()
        bottom_right = self.GetSelectionBlockBottomRight()
        if not self.isempty(bottom_right) and not self.isempty(top_left):
            max_row = bottom_right[0][0]
            min_row = top_left[0][0]
            srows = range(min_row,max_row+1)
        return srows
        
    def OnCellEdit(self,event):
        """
        """
        row,col = (event.GetRow(),event.GetCol())
        cval = self.GetCellValue(row,col)
        if cval.startswith("="):
            try:
                cval = str(eval(cval[1:]))
                self.SetCellValue(row,col,cval)
            except:
                pass
        try:
            cval = float(cval)
        except ValueError:
            cval = np.nan
        self.SetCellValue(row,col,str(cval))
        
            
    def OnRightClick(self,event):
        """
        On right click, show pop-up menu.
        """
        pum = wx.Menu()
        addrow = wx.MenuItem(pum, -1, "Add rows...")
        pum.AppendItem(addrow)
        delrows = wx.MenuItem(pum, -1, "Delete rows")
        pum.AppendItem(delrows)
        pum.AppendSeparator()
        randomfill = wx.MenuItem(pum, -1, "Fill columns randomly")
        pum.AppendItem(randomfill)
        
        # Binds
        pum.Bind(wx.EVT_MENU, self.del_rows, delrows)
        pum.Bind(wx.EVT_MENU, self.add_row, addrow)
        pum.Bind(wx.EVT_MENU, self.random_fill, randomfill)
        
        # Show 
        self.PopupMenu(pum)
        pum.Destroy()

    def del_rows(self,event):
        """
        Delete rows
        """
        rows = self.GetSelectedRows()
        if not self.isempty(rows):
            self.DeleteRows(rows[0],len(rows))
        
    def add_row(self,event):
        """
        Add row
        """
        self.AppendRows(1)
    
    def random_fill(self,event):
        """
        Fill columns randomly
        """
        cols = self.GetSelectedCols()
        nrows = self.GetNumberRows()
        for ii in range(nrows):
            for col in cols:
                val = str(np.random.rand())
                self.SetCellValue(ii,col,val)
                
    def isempty(self,iterable):
        return True if len(iterable)==0 else False



class NodesTable(DataGrid):
    def __init__(self,parent,data=[],**kwargs):
        DataGrid.__init__(self,parent=parent,gridsize=(10,2),**kwargs)
        
        self.SetColLabelValue(0, "X")
        self.SetColLabelValue(1, "Y")
        
        if isinstance(data,list):
            nodes_info = np.array([[0,0],[2,0],[0,2]])
        else:
            nodes_info = data
        self.SetArrayData(nodes_info)
        
        
class ElementsTable(DataGrid):
    def __init__(self,parent,data=[],**kwargs):
        DataGrid.__init__(self,parent=parent,gridsize=(10,4),**kwargs)

        self.SetColLabelValue(0, "Ni")
        self.SetColLabelValue(1, "Nj")
        self.SetColLabelValue(2, "E")
        self.SetColLabelValue(3, "A")
        self.SetColSize(0, 50)
        self.SetColSize(1, 50)
        
        if isinstance(data,list):
            E,A = 200e9, 0.01
            elm_info = np.array([[1,2,E,A],[2,3,E,A],[3,1,E,A]])
        else:
            elm_info = data
        self.SetArrayData(elm_info)
        

    def OnCellEdit(self,event):
        row,col = (event.GetRow(),event.GetCol())
        cval = self.GetCellValue(row,col)
        try:
            if col==0 or col==1:
                cval = int(cval)
            else:
                cval = float(cval)
        except ValueError:
            cval = np.nan
        self.SetCellValue(row,col,str(cval))


class ConstraintsTable(DataGrid):
    def __init__(self,parent,data=[],**kwargs):
        DataGrid.__init__(self,parent=parent,gridsize=(10,3),**kwargs)
        
        self.SetColLabelValue(0, "Node")
        self.SetColLabelValue(1, "UX")
        self.SetColLabelValue(2, "UY")
        
        if isinstance(data,list):
            cinfo = np.array([[1,0,0],[2,np.nan,0]])
        else:
            cinfo = data
        self.SetArrayData(cinfo)
     
    def GetArrayData(self):
        nrows = self.GetNumberRows()
        ncols = self.GetNumberCols()
        X = np.zeros((nrows,ncols))
        for i in range(nrows):
            for j in range(ncols):
                cval = self.GetCellValue(i,j)
                if not self.isempty(cval):
                    try:
                        X[i][j] = float(cval)
                    except:
                        # Revisar valores devueltos
                        X[i][j] = np.nan
                else:
                    X[i][j] = np.nan
        return X


class ForcesTable(DataGrid):
    def __init__(self,parent,data=[],**kwargs):
        DataGrid.__init__(self,parent=parent,gridsize=(10,3),**kwargs)
        
        self.SetColLabelValue(0, "Node")
        self.SetColLabelValue(1, "FX")
        self.SetColLabelValue(2, "FY")
        
        if isinstance(data,list):
            finfo = np.array([[3,1000,0]])
        else:
            finfo = data
        self.SetArrayData(finfo)





class NodesDialog(wx.Dialog):
    def __init__(self,parent,data,**kwargs):
        wx.Dialog.__init__(self,parent=parent,title="Nodes", size=(220,400))
        #~ self.LABEL_FONT = wx.Font(10, wx.SWISS, wx.NORMAL, wx.BOLD)
        self.data = data
        self.SetBackgroundColour("#ffffff")
        self.initCtrls()
        self.Centre(True)
        
    def initCtrls(self):
        self.sz = wx.BoxSizer(wx.VERTICAL)
        self.btsz = wx.BoxSizer(wx.HORIZONTAL)
        
        self.grid = NodesTable(self,self.data)
        self.grid.SetLabelBackgroundColour("#ffffff")
        
        self.okbt = wx.Button(self, wx.ID_OK, u"OK")
        self.cancelbt = wx.Button(self, wx.ID_CANCEL, u"Cancel")
        
        self.sz.Add(self.grid, 8, wx.ALIGN_CENTRE|wx.ALL, 5)
        self.btsz.Add(self.okbt, 1, wx.ALIGN_CENTRE|wx.ALL, 5)
        self.btsz.Add(self.cancelbt, 1, wx.ALIGN_CENTRE|wx.ALL, 5)
        
        self.sz.Add(self.btsz, 1, wx.ALIGN_CENTRE|wx.ALL, 5)
        self.SetSizer(self.sz)
        
    def GetData(self):
        return self.grid.GetArrayData()


class ElementsDialog(wx.Dialog):
    def __init__(self,parent,data,**kwargs):
        wx.Dialog.__init__(self,parent=parent,title="Elements", size=(400,400))
        #~ self.LABEL_FONT = wx.Font(10, wx.SWISS, wx.NORMAL, wx.BOLD)
        self.data = data
        self.SetBackgroundColour("#ffffff")
        self.initCtrls()
        self.Centre(True)
        
    def initCtrls(self):
        self.sz = wx.BoxSizer(wx.VERTICAL)
        self.btsz = wx.BoxSizer(wx.HORIZONTAL)
        
        self.grid = ElementsTable(self,self.data)
        self.grid.SetLabelBackgroundColour("#ffffff")
        
        self.okbt = wx.Button(self, wx.ID_OK, u"OK")
        self.cancelbt = wx.Button(self, wx.ID_CANCEL, u"Cancel")
        
        self.sz.Add(self.grid, 8, wx.ALIGN_CENTRE|wx.ALL, 5)
        self.btsz.Add(self.okbt, 1, wx.ALIGN_CENTRE|wx.ALL, 5)
        self.btsz.Add(self.cancelbt, 1, wx.ALIGN_CENTRE|wx.ALL, 5)
        
        self.sz.Add(self.btsz, 1, wx.ALIGN_CENTRE|wx.ALL, 5)
        self.SetSizer(self.sz)
        
    def GetData(self):
        return self.grid.GetArrayData()



class ConstraintsDialog(wx.Dialog):
    def __init__(self,parent,data,**kwargs):
        wx.Dialog.__init__(self,parent=parent,title="Constraints", size=(300,400))
        #~ self.LABEL_FONT = wx.Font(10, wx.SWISS, wx.NORMAL, wx.BOLD)
        self.data = data
        self.SetBackgroundColour("#ffffff")
        self.initCtrls()
        self.Centre(True)
        
    def initCtrls(self):
        self.sz = wx.BoxSizer(wx.VERTICAL)
        self.btsz = wx.BoxSizer(wx.HORIZONTAL)
        
        self.grid = ConstraintsTable(self,self.data)
        self.grid.SetLabelBackgroundColour("#ffffff")
        
        self.okbt = wx.Button(self, wx.ID_OK, u"OK")
        self.cancelbt = wx.Button(self, wx.ID_CANCEL, u"Cancel")
        
        self.sz.Add(self.grid, 8, wx.ALIGN_CENTRE|wx.ALL, 5)
        self.btsz.Add(self.okbt, 1, wx.ALIGN_CENTRE|wx.ALL, 5)
        self.btsz.Add(self.cancelbt, 1, wx.ALIGN_CENTRE|wx.ALL, 5)
        
        self.sz.Add(self.btsz, 1, wx.ALIGN_CENTRE|wx.ALL, 5)
        self.SetSizer(self.sz)
        
    def GetData(self):
        return self.grid.GetArrayData()


class ForcesDialog(wx.Dialog):
    def __init__(self,parent,data,**kwargs):
        wx.Dialog.__init__(self,parent=parent,title="Forces", size=(300,400))
        #~ self.LABEL_FONT = wx.Font(10, wx.SWISS, wx.NORMAL, wx.BOLD)
        self.data = data
        self.SetBackgroundColour("#ffffff")
        self.initCtrls()
        self.Centre(True)
        
    def initCtrls(self):
        self.sz = wx.BoxSizer(wx.VERTICAL)
        self.btsz = wx.BoxSizer(wx.HORIZONTAL)
        
        self.grid = ForcesTable(self,self.data)
        self.grid.SetLabelBackgroundColour("#ffffff")
        
        self.okbt = wx.Button(self, wx.ID_OK, u"OK")
        self.cancelbt = wx.Button(self, wx.ID_CANCEL, u"Cancel")
        
        self.sz.Add(self.grid, 8, wx.ALIGN_CENTRE|wx.ALL, 5)
        self.btsz.Add(self.okbt, 1, wx.ALIGN_CENTRE|wx.ALL, 5)
        self.btsz.Add(self.cancelbt, 1, wx.ALIGN_CENTRE|wx.ALL, 5)
        
        self.sz.Add(self.btsz, 1, wx.ALIGN_CENTRE|wx.ALL, 5)
        self.SetSizer(self.sz)
        
    def GetData(self):
        return self.grid.GetArrayData()




class Toolbar(wx.ToolBar):
    def __init__(self,parent,**kwargs):
        wx.ToolBar.__init__(self,parent=parent,style=wx.TB_VERTICAL,**kwargs)
        tbsize = (28,28)
        self.SetToolBitmapSize(tbsize)
        self.SetBackgroundColour("#ffffff")
        
        # Bitmaps
        nodes = ic.nodes.GetBitmap()
        elements = ic.elements.GetBitmap()
        constraints = ic.constraints.GetBitmap()
        forces = ic.forces.GetBitmap()
        plot_model = ic.plot_model.GetBitmap()
        solve = ic.solve.GetBitmap()
        plot_deformed_shape = ic.plot_deformed_shape.GetBitmap()
        
        # Add
        self.nodes_tool = self.AddTool(-1, "Add nodes...", 
        nodes, shortHelp="Add nodal coordinates")
        
        self.elements_tool = self.AddTool(-1, "Add elements...", 
        elements, shortHelp="Add element connectivity")
        
        #~ self.AddSeparator()
        
        self.constraints_tool = self.AddTool(-1, "Add constraint", 
        constraints, shortHelp="Add constraints...")
        
        self.forces_tool = self.AddTool(-1, "Add force", 
        forces, shortHelp="Add forces...")
        
        self.plot_model_tool = self.AddTool(-1, "Plot model", 
        plot_model, shortHelp="Plot model...")
        
        self.solve_tool = self.AddTool(-1, "Solve model", 
        solve, shortHelp="Solve model...")
        
        self.plot_deformed_shape_tool = self.AddTool(-1, "Plot deformed shape", 
        plot_deformed_shape, shortHelp="Plot deformed shape")


REPORT_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title></title>
</head>
<body bgcolor="#FFFFFF" link="#E5E5E5" vlink="#F0F0F0" alink="#F0F0F0">

<center>

  <b><font color="#0F0F0F"> SIMPLE REPORT </font></b>
  <br><br><br>

  <b>Nodal coordinates</b> <br>
  {nodal_coords}
  <br><br><br>

  <b>Elements</b> <br>
  {elements}
  <br><br><br>

  <b>Nodal displacements</b> <br>
  {nodal_displacements}
  <br><br><br>
  
  <b>Nodal forces</b> <br>
  {nodal_forces}
  <br><br><br>
  
  <b>Element forces</b> <br>
  {element_forces}
  <br><br><br>
  
  <b>Element stresses</b> <br>
  {element_stresses}
  <br>

</center>
</body>
</html>
"""



class App(wx.App):
    """
    Override OnInit
    """
    def OnInit(self):
        frame = wxTruss(None)
        return True

def run():
    """
    Entry point for wxTruss
    """
    REDIRECT = False
    LOG_FILE = "truss.log"
    app = App(REDIRECT)
    app.MainLoop()


if __name__=='__main__':
    run() # Run app
