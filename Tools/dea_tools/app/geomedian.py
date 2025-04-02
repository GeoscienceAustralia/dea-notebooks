"""
Geomedian widget: generates an interactive visualisation of
the geomedian summary statistic. 
"""

# Load modules 
import ipywidgets as widgets
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import numpy as np
import xarray as xr
from odc.algo import xr_geomedian

def run_app():
    
    """
    An interactive app that allows users to visualise the difference between the median and geomedian time-series summary statistics. By modifying the red-green-blue values of three timesteps for a given pixel, the user changes the output summary statistics. 
    
    This allows a visual representation of the difference through the output values, RGB colour, as well as showing values plotted as a vector on a 3-dimensional  space.
    
    Last modified: December 2021
    """
    
    # Define the red-green-blue sliders for timestep 1
    p1r = widgets.IntSlider(description='Red', max=255, value=58)
    p1g = widgets.IntSlider(description='Green', max=255, value=153)
    p1b = widgets.IntSlider(description='Blue', max=255, value=68)

    # Define the red-green-blue sliders for timestep 2
    p2r = widgets.IntSlider(description='Red', max=255, value=208)
    p2g = widgets.IntSlider(description='Green', max=255, value=221)
    p2b = widgets.IntSlider(description='Blue', max=255, value=203)

    # Define the red-green-blue sliders for timestep 3
    p3r = widgets.IntSlider(description='Red', max=255, value=202)
    p3g = widgets.IntSlider(description='Green', max=255, value=82)
    p3b = widgets.IntSlider(description='Blue', max=255, value=33)

    # Define the median calculation for the timesteps
    def f(p1r, p1g, p1b, p2r, p2g, p2b, p3r, p3g, p3b):
        print('Red Median = {}'.format(np.median([p1r, p2r, p3r])))
        print('Green Median = {}'.format(np.median([p1g, p2g, p3g])))
        print('Blue Median = {}'.format(np.median([p1b, p2b, p3b])))

    # Define the geomedian calculation for the timesteps
    def g(p1r, p1g, p1b, p2r, p2g, p2b, p3r, p3g, p3b):
        print('Red Geomedian = {:.2f}'.format(xr_geomedian(xr.Dataset({"red": (("x", "y", "time"), [[[np.float32(p1r), np.float32(p2r), np.float32(p3r)]]]), "green": (("x", "y", "time"), [[[np.float32(p1g), np.float32(p2g), np.float32(p3g)]]]),  "blue": (("x", "y", "time"), [[[np.float32(p1b), np.float32(p2b), np.float32(p3b)]]])})).red.values.ravel()[0]))    
        print('Green Geomedian = {:.2f}'.format(xr_geomedian(xr.Dataset({"red": (("x", "y", "time"), [[[np.float32(p1r), np.float32(p2r), np.float32(p3r)]]]), "green": (("x", "y", "time"), [[[np.float32(p1g), np.float32(p2g), np.float32(p3g)]]]),  "blue": (("x", "y", "time"), [[[np.float32(p1b), np.float32(p2b), np.float32(p3b)]]])})).green.values.ravel()[0]))    
        print('Blue Geomedian = {:.2f}'.format(xr_geomedian(xr.Dataset({"red": (("x", "y", "time"), [[[np.float32(p1r), np.float32(p2r), np.float32(p3r)]]]), "green": (("x", "y", "time"), [[[np.float32(p1g), np.float32(p2g), np.float32(p3g)]]]),  "blue": (("x", "y", "time"), [[[np.float32(p1b), np.float32(p2b), np.float32(p3b)]]])})).blue.values.ravel()[0]))    

    # Define the Timestep 1 box colour
    def h(p1r, p1g, p1b):
        fig1, axes1 = plt.subplots(figsize=(2,2))
        fig1 = plt.imshow([[(p1r, p1g, p1b)]])
        axes1.set_title('Timestep 1')
        axes1.axis('off')
        plt.show(fig1)

    # Define the Timestep 2 box colour
    def hh(p2r, p2g, p2b):    
        fig2, axes2 = plt.subplots(figsize=(2,2))
        fig2 = plt.imshow([[(p2r, p2g, p2b)]])
        axes2.set_title('Timestep 2')
        axes2.axis('off')
        plt.show(fig2)

    # Define the Timestep 3 box colour
    def hhh(p3r, p3g, p3b):    
        fig3, axes3 = plt.subplots(figsize=(2,2))
        fig3 = plt.imshow([[(p3r, p3g, p3b)]])
        axes3.set_title('Timestep 3')
        axes3.axis('off')
        plt.show(fig3)

    # Define the Median RGB colour box
    def i(p1r, p1g, p1b, p2r, p2g, p2b, p3r, p3g, p3b):
        fig4, axes4 = plt.subplots(figsize=(3,3))
        fig4 = plt.imshow([[(int(np.median([p1r, p2r, p3r])), int(np.median([p1g, p2g, p3g])), int(np.median([p1b, p2b, p3b])))]])
        axes4.set_title('Median RGB - All timesteps')
        axes4.axis('off')
        plt.show(fig4)

    # Define the Geomedian RGB colour box
    def ii(p1r, p1g, p1b, p2r, p2g, p2b, p3r, p3g, p3b):
        fig5, axes5 = plt.subplots(figsize=(3,3))
        fig5 = plt.imshow([[(int(xr_geomedian(xr.Dataset({"red": (("x", "y", "time"), [[[np.float32(p1r), np.float32(p2r), np.float32(p3r)]]]), "green": (("x", "y", "time"), [[[np.float32(p1g), np.float32(p2g), np.float32(p3g)]]]),  "blue": (("x", "y", "time"), [[[np.float32(p1b), np.float32(p2b), np.float32(p3b)]]])})).red.values.ravel()[0]), int(xr_geomedian(xr.Dataset({"red": (("x", "y", "time"), [[[np.float32(p1r), np.float32(p2r), np.float32(p3r)]]]), "green": (("x", "y", "time"), [[[np.float32(p1g), np.float32(p2g), np.float32(p3g)]]]),  "blue": (("x", "y", "time"), [[[np.float32(p1b), np.float32(p2b), np.float32(p3b)]]])})).green.values.ravel()[0]), int(xr_geomedian(xr.Dataset({"red": (("x", "y", "time"), [[[np.float32(p1r), np.float32(p2r), np.float32(p3r)]]]), "green": (("x", "y", "time"), [[[np.float32(p1g), np.float32(p2g), np.float32(p3g)]]]),  "blue": (("x", "y", "time"), [[[np.float32(p1b), np.float32(p2b), np.float32(p3b)]]])})).blue.values.ravel()[0]))]])
        axes5.set_title('Geomedian RGB - All timesteps')
        axes5.axis('off')
        plt.show(fig5)

    # Define 3-D axis to display vectors on 
    def j(p1r, p1g, p1b, p2r, p2g, p2b, p3r, p3g, p3b):
        fig6 = plt.figure()
        axes6 = fig6.add_subplot(111, projection='3d')
        x = [p1r, p2r, p3r, int(np.median([p1r, p2r, p3r])), int(xr_geomedian(xr.Dataset({"red": (("x", "y", "time"), [[[np.float32(p1r), np.float32(p2r), np.float32(p3r)]]]), "green": (("x", "y", "time"), [[[np.float32(p1g), np.float32(p2g), np.float32(p3g)]]]),  "blue": (("x", "y", "time"), [[[np.float32(p1b), np.float32(p2b), np.float32(p3b)]]])})).red.values.ravel()[0])]
        y = [p1g, p2g, p3g, int(np.median([p1g, p2g, p3g])), int(xr_geomedian(xr.Dataset({"red": (("x", "y", "time"), [[[np.float32(p1r), np.float32(p2r), np.float32(p3r)]]]), "green": (("x", "y", "time"), [[[np.float32(p1g), np.float32(p2g), np.float32(p3g)]]]),  "blue": (("x", "y", "time"), [[[np.float32(p1b), np.float32(p2b), np.float32(p3b)]]])})).green.values.ravel()[0])]
        z = [p1b, p2b, p3b, int(np.median([p1b, p2b, p3b])), int(xr_geomedian(xr.Dataset({"red": (("x", "y", "time"), [[[np.float32(p1r), np.float32(p2r), np.float32(p3r)]]]), "green": (("x", "y", "time"), [[[np.float32(p1g), np.float32(p2g), np.float32(p3g)]]]),  "blue": (("x", "y", "time"), [[[np.float32(p1b), np.float32(p2b), np.float32(p3b)]]])})).blue.values.ravel()[0])]
        labels = [' 1', ' 2', ' 3', ' median', ' geomedian']
        axes6.scatter(x, y, z, c=['black','black','black','r', 'blue'], marker='o')
        axes6.set_xlabel('Red')
        axes6.set_ylabel('Green')
        axes6.set_zlabel('Blue')
        axes6.set_xlim3d(0, 255)
        axes6.set_ylim3d(0, 255)
        axes6.set_zlim3d(0, 255)
        for ax, ay, az, label in zip(x, y, z, labels):
            axes6.text(ax, ay, az, label)
        plt.title('Each band represents a dimension.')
        plt.show()

    # Define outputs
    outf = widgets.interactive_output(f, {'p1r': p1r, 'p2r': p2r,'p3r': p3r, 'p1g': p1g, 'p2g': p2g,'p3g': p3g, 'p1b': p1b, 'p2b': p2b,'p3b': p3b})
    outg = widgets.interactive_output(g, {'p1r': p1r, 'p2r': p2r,'p3r': p3r, 'p1g': p1g, 'p2g': p2g,'p3g': p3g, 'p1b': p1b, 'p2b': p2b,'p3b': p3b})

    outh = widgets.interactive_output(h, {'p1r': p1r, 'p1g': p1g, 'p1b': p1b})
    outhh = widgets.interactive_output(hh, {'p2r': p2r, 'p2g': p2g, 'p2b': p2b})
    outhhh = widgets.interactive_output(hhh, {'p3r': p3r, 'p3g': p3g, 'p3b': p3b})

    outi = widgets.interactive_output(i, {'p1r': p1r, 'p2r': p2r,'p3r': p3r, 'p1g': p1g, 'p2g': p2g,'p3g': p3g, 'p1b': p1b, 'p2b': p2b,'p3b': p3b})
    outii = widgets.interactive_output(ii, {'p1r': p1r, 'p2r': p2r,'p3r': p3r, 'p1g': p1g, 'p2g': p2g,'p3g': p3g, 'p1b': p1b, 'p2b': p2b,'p3b': p3b})

    outj = widgets.interactive_output(j, {'p1r': p1r, 'p2r': p2r,'p3r': p3r, 'p1g': p1g, 'p2g': p2g,'p3g': p3g, 'p1b': p1b, 'p2b': p2b,'p3b': p3b})

    app_output = widgets.HBox([widgets.VBox([widgets.HBox([outh, widgets.VBox([ p1r, p1g, p1b])]), widgets.HBox([outhh, widgets.VBox([p2r, p2g, p2b])]), widgets.HBox([outhhh, widgets.VBox([ p3r, p3g, p3b])])]), widgets.VBox([widgets.HBox([widgets.VBox([outf, outi]), widgets.VBox([outg, outii])]), outj])])
    
    return app_output