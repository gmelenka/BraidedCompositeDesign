from kivy.app import App
from kivy.lang import Builder
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.properties import ObjectProperty
from kivy.uix.spinner import Spinner
from kivy.uix.listview import ListItemButton

from kivy.uix.widget import Widget
from kivy.graphics import Color, Line, Rectangle
from kivy.metrics import dp
from kivy.vector import Vector
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.textinput import TextInput
from thumbchooser import FileChooserThumbView
from kivy.core.window import Window
from os import listdir
from os.path import dirname, join
import os
import glob
import math
import shutil

#version required for Buildozer
__version__ = "1.0"


__author__ = "Garrett Melenka, Marcus Ivey"
__copyright__ = "Copyright 2015, The Multipurpose Composites Group- University of Alberta"
__credits__ = ["Garrett Melenka", "Marcus Ivey", "Jason Carey"]
__license__ = "MIT"
__version__ = "1.0.0"
__maintainer__ = "Garrett Melenka"
__email__ = "gmelenka@gmail.com"
__status__ = "Production"


class MainScreen(FloatLayout):
	pass

#Load dialog for angle measure popup window    
class LoadDialog(FloatLayout):
    load = ObjectProperty(None)
    cancel = ObjectProperty(None)
    
    #make sure image file have been selected
    def fileSelect(self, path, name):
        print name
        if name:
            self.load(path, name)
            
#Angle Measurement layout
class AngleLayout(BoxLayout):

    def dismiss_popup(self):
        self._popup.dismiss()

    def show_load(self):
        content = LoadDialog(load=self.load, cancel=self.dismiss_popup)
        self._popup = Popup(title="Select Image", content=content, size_hint=(0.99, 0.99))
        self._popup.open()

    def load(self, path, filename):
        filename = filename[0]
        image = self.ids['image']
        image.source = filename
        self.dismiss_popup()

    def initiate_angle_finder(self):
        button = self.ids['toggle']
        image = self.ids['scatter']
        anchor = self.ids['anchor']
        if button.state == 'down':	
            image.do_scale = False
            image.do_rotation = False
            image.do_translation_x = False
            image.do_translation_y = False
            button.text = 'Clear'
            angleFinder = AngleFinder()
            anchor.add_widget(angleFinder)
        if button.state == 'normal':
            button.text = 'Draw'
            image.do_scale = True
            image.do_rotation = True
            image.do_translation_x = True
            image.do_translation_y = True
            anchor.clear_widgets()

    def reset_image(self):
            button = self.ids['toggle']
            anchor = self.ids['anchor']
            scatter = self.ids['scatter']
            image = self.ids['image']
            anchor2 = self.ids['anchor2']
            scatter.scale = 1
            scatter.rotation = 0
            scatter.pos = (anchor2.center_x - image.center_x, anchor2.center_y - image.center_y) 
            button.state = 'normal'
            button.text = 'Draw'
            scatter.do_scale = True
            scatter.do_rotation = True
            scatter.do_translation_x = True
            scatter.do_translation_y = True
            anchor.clear_widgets()
            
#This is the angle finder widget that allows drawing two straight lines and calculates the minor angle between the two.                
class AngleFinder(Widget):

    #This function initializes the widget with a touch count of zero
    def __init__(self, **kwargs):
        super(AngleFinder, self).__init__(**kwargs)
        self.touch_down_count = 0
        
    #This function defines the actions that take place when a touch event occurs
    def on_touch_down(self, touch):
        #Record the touch coordinates in x and y as variables	
        x1 = touch.x
        y1 = touch.y
        
        #when the touch count is 0 or 1, we will record the touch coordinates and draw a crosshair at the touch location
        if self.touch_down_count > 1:
            return
        with self.canvas:
            touch.ud['label'] = TextInput()
            self.initiate_touch_label(touch.ud['label'], touch)
            self.add_widget(touch.ud['label'])
            #save the touch points to the user dictionary
            touch.ud['x1'] = x1
            touch.ud['y1'] = y1
            #set parameters for crosshair display
            Color(1, 0, 0)
            l = dp(25)
            w = dp(1)
            #draw crosshair
            Rectangle(pos=(touch.ud['x1'] - w / 2, touch.ud['y1'] - l / 2), size=(w, l))
            Rectangle(pos=(touch.ud['x1'] - l / 2, touch.ud['y1'] - w / 2), size=(l, w))
        #Initialize the vector v1
        if self.touch_down_count == 0:
            #Record the touch coordinates to variables
            x2 = touch.x
            y2 = touch.y
            #Save touch coordinates to the user dictionary
            touch.ud['x2'] = x2
            touch.ud['y2'] = y2
            #When the touch count is zero (first touch), we define a vector v1 based on the touch positions in ud
            v1 = (touch.ud['x2'] - touch.ud['x1'], touch.ud['y2'] - touch.ud['y1'])
            self.v1 = v1
        
    #Function to define what happens on a drag action
    def on_touch_move(self, touch):
        #Record the touch coordinates to variables
        x2 = touch.x
        y2 = touch.y
        #Save touch coordinates to the user dictionary
        touch.ud['x2'] = x2
        touch.ud['y2'] = y2
        ud = touch.ud
        #define a group, g, that will be assigned to the line drawn to allow the line to be redrawn as movements occur, leaving only one line on the screen
        ud['group'] = g = str(touch.uid)
        self.canvas.remove_group(g)

        #When the touch count is zero (first touch), we define a vector v1 based on the touch positions in ud
        if self.touch_down_count == 0:
            v1 = (touch.ud['x2'] - touch.ud['x1'], touch.ud['y2'] - touch.ud['y1'])
            self.v1 = v1
            
        #When the touch count is 1 (second touch), we define a vector v2 based on the touch positions in ud. The angle between vectors v1 and v2 is then calculated.
        if self.touch_down_count == 1:
            v2 = (touch.ud['x2'] - touch.ud['x1'], touch.ud['y2'] - touch.ud['y1'])
            self.v2 = v2
            angle = Vector(self.v1).angle(self.v2)
            absoluteAngle = abs(angle)
            #The following if statement is used to ensure the minor angle is always calculated
            if absoluteAngle > 90:
                absoluteAngle = 180 - absoluteAngle
            #The next two lines are used to update the angle label value as the lines are moved around
            touch.ud['angle'] = absoluteAngle
            self.update_touch_label(touch.ud['label'], touch)
                    
        #If the touch count is greater than 1 (third touch), then this function will end and the canvas will clear as in the previous function
        if self.touch_down_count > 1:
            return
        
        #This defines the line and crosshair that is drawn between the initial touch point and where the finger has been dragged
        with self.canvas:
            Color(1, 0, 0)
            l = dp(25)
            w = dp(1)
            Line(points=[touch.ud['x1'], touch.ud['y1'], x2, y2], width=w, group=g)
            Rectangle(pos=(touch.ud['x2'] - w / 2, touch.ud['y2'] - l / 2), size=(w, l), group=g)
            Rectangle(pos=(touch.ud['x2'] - l / 2, touch.ud['y2'] - w / 2), size=(l, w), group=g)
    
    #this function defines what to do when a touch is released. The touch count is simply incremented
    def on_touch_up(self, touch):
        self.touch_down_count += 1
            
    #This function defines how the angle label is to be updated. It indicates the number of digits to show, the label size and position, color, and font type
    def update_touch_label(self, label, touch):		
        degree = unichr(176)
        label.text = '%.1f%s' % ((touch.ud['angle']), degree)
        label.pos = (self.center_x - dp(40), self.height + dp(70))
        label.font_size = dp(24)
        label.size = dp(75), dp(40)
        label.padding_x = [dp(10), dp(10)]
        label.padding_y = [dp(5), dp(5)]
        label.readonly = True
        label.multiline = False
        
    def initiate_touch_label(self, label, touch):	
        degree = unichr(176)
        label.text = '%s%s' % ('---', degree)
        label.pos = (self.center_x - dp(40), self.height + dp(70))
        label.font_size = dp(24)
        label.size = dp(75), dp(40)
        label.padding_x = [dp(10), dp(10)]
        label.padding_y = [dp(5), dp(5)]
        label.readonly = True	
        label.multiline = False


    pass

#Layout for static about screen
class About_Screen(FloatLayout):
    pass
#About popup for Micromechanics window
class MicroMechanicsAbout(FloatLayout):
    load = ObjectProperty(None)
    cancel = ObjectProperty(None)    

#Calculation of micromechanics properties for a unidirectional lamina
class MicroMechanics(FloatLayout):
    def dismiss_popup(self):
        self._popup.dismiss()
    def AboutMicromechanics(self):        
        content = MicroMechanicsAbout(load=self.load, cancel=self.dismiss_popup)
        self._popup = Popup(title="Micro-mechanics About", content=content, size_hint=(0.9, 0.9))
        self._popup.open()
        
    def load(self):
        pass

    def fiberSelect(self):
    
        fiberType = self.ids.yarnSelectSpinner.text
        
        #E-glass properties
        if fiberType == "E-Glass":
            self.ids.longitudinalModulus.text = str(73.0)
            self.ids.transverseModulus.text = str(73.0)
            self.ids.shearModulus.text = str(30.0)
            self.ids.majorPoissonRatio.text = str(0.23)
        #S-glass properties
        if fiberType == "S-Glass":
            self.ids.longitudinalModulus.text = str(86.0)
            self.ids.transverseModulus.text = str(86.0)
            self.ids.shearModulus.text = str(35)
            self.ids.majorPoissonRatio.text = str(0.23)
        #AS4 Carbon fiber properties    
        if fiberType == "AS4-Carbon":
            self.ids.longitudinalModulus.text = str(235.0)
            self.ids.transverseModulus.text = str(15)
            self.ids.shearModulus.text = str(27)
            self.ids.majorPoissonRatio.text = str(0.20)
        #T300 Carbon fiber properties
        if fiberType == "T300 Carbon":
            self.ids.longitudinalModulus.text = str(230.0)
            self.ids.transverseModulus.text = str(15)
            self.ids.shearModulus.text = str(27)
            self.ids.majorPoissonRatio.text = str(0.20)    
        #Boron fiber properties
        if fiberType == "Boron":
            self.ids.longitudinalModulus.text = str(395.0)
            self.ids.transverseModulus.text = str(395)
            self.ids.shearModulus.text = str(165)
            self.ids.majorPoissonRatio.text = str(0.13)
        #Kevlar 49 fiber properties
        if fiberType == "Kevlar 49":
            self.ids.longitudinalModulus.text = str(131.0)
            self.ids.transverseModulus.text = str(7)
            self.ids.shearModulus.text = str(21)
            self.ids.majorPoissonRatio.text = str(0.33)        
        #
        if fiberType == "Custom":
            self.ids.longitudinalModulus.text = str(100.0)
            self.ids.transverseModulus.text = str(10)
            self.ids.shearModulus.text = str(20)
            self.ids.majorPoissonRatio.text = str(0.20)    
    
    def matrixSelect(self):
        matrixType = self.ids.matrixSelectSpinner.text
        #Epoxy mechanical properties
        if matrixType == "Epoxy":
            self.ids.matrixModulus.text = str(4.3)
            self.ids.matrixShearModulus.text = str(1.6)
            self.ids.matrixPoissonRatio.text = str(0.35)
        #polyester mechanical properties    
        if matrixType == "Polyester":
            self.ids.matrixModulus.text = str(3.2)
            self.ids.matrixShearModulus.text = str(0.7)
            self.ids.matrixPoissonRatio.text = str(0.35)
        #Polyimides mechanical properties
        if matrixType == "Polyimides":
            self.ids.matrixModulus.text = str(1.4)
            self.ids.matrixShearModulus.text = str(3.1)
            self.ids.matrixPoissonRatio.text = str(0.35)
        #PEEK mechanical properties    
        if matrixType == "PEEK":
            self.ids.matrixModulus.text = str(1.32)
            self.ids.matrixShearModulus.text = str(3.7)
            self.ids.matrixPoissonRatio.text = str(0.35)

    def CalculateVF(self, data):
    
        matrixVal = self.ids.matrixSelectSpinner.text
        yarnVal = self.ids.yarnSelectSpinner.text
        
        
        if yarnVal != 'Select Yarn' and matrixVal != 'Select Matrix':
    
            Ef1 = float(self.ids.longitudinalModulus.text)
            Ef2 = float(self.ids.transverseModulus.text)
            Gf12 = float(self.ids.shearModulus.text)
            nuf12 = float(self.ids.majorPoissonRatio.text)
            
            VF = float(self.ids.volumeFraction.text)
            
            Em = float(self.ids.matrixModulus.text)
            Gm = float(self.ids.matrixShearModulus.text)
            num = float(self.ids.matrixPoissonRatio.text)
            
            if VF>=0 and VF <1:

                #Calculate Longitudinal Elastic Modulus
                E1 = Ef1 * VF + Em * (1-VF)
                #Calculate Transverse Elastic Modulus
                E2 = Ef2*Em / (Ef2*(1-VF) + Em*VF)
                #Calculate Major Poisson's Ratio
                nu12 = nuf12*VF + num*(1-VF)
                #Calculate Shear Modulus
                G12 = Gf12*Gm / (Gm * VF+ Gf12 * (1 - VF))
                
                #Write values to screen
                self.ids.modulusE1.text = '{0:.3f}'.format(E1)
                self.ids.modulusE2.text = '{0:.3f}'.format(E2)
                self.ids.modulusG12.text = '{0:.3f}'.format(G12)
                self.ids.poissonNu12.text = '{0:.3f}'.format(nu12)
        
    def volumeFractionUp(self):

            VF = float(self.ids.volumeFraction.text)
            VF_new = VF + 0.1
            if VF_new <= 1.0:
                self.ids.volumeFraction.text = str(VF_new)
    
    def volumeFractionDown(self):
        VF = float(self.ids.volumeFraction.text)
        VF_new = VF - 0.1
        if VF_new > 0.0:
            self.ids.volumeFraction.text = str(VF_new)
    
    def EF1Up(self):
        matrixVal = self.ids.matrixSelectSpinner.text
        yarnVal = self.ids.yarnSelectSpinner.text
        if yarnVal != 'Select Yarn':
            EF1 = float(self.ids.longitudinalModulus.text)
            EF1_new = EF1 + 1.0
            #if EF1_new  <= 1.0:
            self.ids.longitudinalModulus.text = str(EF1_new)
    
    def EF1Down(self):
        matrixVal = self.ids.matrixSelectSpinner.text
        yarnVal = self.ids.yarnSelectSpinner.text
        if yarnVal != 'Select Yarn':
            EF1 = float(self.ids.longitudinalModulus.text)
            EF1_new = EF1 - 1.0
            if EF1_new > 0.0:
                self.ids.longitudinalModulus.text = str(EF1_new)
        
    def EF2Up(self):
        matrixVal = self.ids.matrixSelectSpinner.text
        yarnVal = self.ids.yarnSelectSpinner.text
        if yarnVal != 'Select Yarn':
            EF2 = float(self.ids.transverseModulus.text)
            EF2_new = EF2 + 1.0
            #if EF1_new  <= 1.0:
            self.ids.transverseModulus.text = str(EF2_new)
    
    def EF2Down(self):
        matrixVal = self.ids.matrixSelectSpinner.text
        yarnVal = self.ids.yarnSelectSpinner.text
        if yarnVal != 'Select Yarn':
            EF2 = float(self.ids.transverseModulus.text)
            EF2_new = EF2 - 1.0
            if EF2_new > 0.0:
                self.ids.transverseModulus.text = str(EF2_new)    
    
    def GF12Up(self):
        matrixVal = self.ids.matrixSelectSpinner.text
        yarnVal = self.ids.yarnSelectSpinner.text
        if yarnVal != 'Select Yarn':
            GF12 = float(self.ids.shearModulus.text)
            GF12_new = GF12 + 1.0
            #if EF1_new  <= 1.0:
            self.ids.shearModulus.text = str(GF12_new)
    
    def GF12Down(self):
        matrixVal = self.ids.matrixSelectSpinner.text
        yarnVal = self.ids.yarnSelectSpinner.text
        if yarnVal != 'Select Yarn':
            GF12 = float(self.ids.shearModulus.text)
            GF12_new = GF12 - 1.0
            if GF12_new > 0.0:
                self.ids.shearModulus.text = str(GF12_new)
     
    def nuf12Up(self):
        matrixVal = self.ids.matrixSelectSpinner.text
        yarnVal = self.ids.yarnSelectSpinner.text
        if yarnVal != 'Select Yarn':
            nuf12 = float(self.ids.majorPoissonRatio.text)
            nuf12_new = nuf12 + 0.1
            #if EF1_new  <= 1.0:
            self.ids.majorPoissonRatio.text = str(nuf12_new)
    
    def nuf12Down(self):
        matrixVal = self.ids.matrixSelectSpinner.text
        yarnVal = self.ids.yarnSelectSpinner.text
        if yarnVal != 'Select Yarn':
            nuf12 = float(self.ids.majorPoissonRatio.text)
            nuf12_new = nuf12 - 0.1
            if nuf12_new > 0.0:
                self.ids.majorPoissonRatio.text = str(nuf12_new)

    def EmUp(self):
        matrixVal = self.ids.matrixSelectSpinner.text
        yarnVal = self.ids.yarnSelectSpinner.text
        if matrixVal != 'Select Matrix':
            Em = float(self.ids.matrixModulus.text)
            Em_new = Em + 0.1
            #if EF1_new  <= 1.0:
            self.ids.matrixModulus.text = str(Em_new)
    
    def EmDown(self):
        matrixVal = self.ids.matrixSelectSpinner.text
        yarnVal = self.ids.yarnSelectSpinner.text
        if matrixVal != 'Select Matrix':
            Em = float(self.ids.matrixModulus.text)
            Em_new = Em - 0.1
            if Em_new > 0.0:
                self.ids.matrixModulus.text = str(Em_new)

    def GmUp(self):
        matrixVal = self.ids.matrixSelectSpinner.text
        yarnVal = self.ids.yarnSelectSpinner.text
        if matrixVal != 'Select Matrix':
            Gm = float(self.ids.matrixShearModulus.text)
            Gm_new = Gm + 0.1
            #if EF1_new  <= 1.0:
            self.ids.matrixShearModulus.text = str(Gm_new)
    
    def GmDown(self):
        matrixVal = self.ids.matrixSelectSpinner.text
        yarnVal = self.ids.yarnSelectSpinner.text
        if matrixVal != 'Select Matrix':
            Gm = float(self.ids.matrixShearModulus.text)
            Gm_new = Gm - 0.1
            if Gm_new > 0.0:
                self.ids.matrixShearModulus.text = str(Gm_new)             
    
    def NuMUp(self):
        matrixVal = self.ids.matrixSelectSpinner.text
        yarnVal = self.ids.yarnSelectSpinner.text
        if matrixVal != 'Select Matrix':
            Num = float(self.ids.matrixPoissonRatio.text)
            Num_new = Num + 0.1
            #if EF1_new  <= 1.0:
            self.ids.matrixPoissonRatio.text = str(Num_new)
    
    def NuMDown(self):
        matrixVal = self.ids.matrixSelectSpinner.text
        yarnVal = self.ids.yarnSelectSpinner.text
        if matrixVal != 'Select Matrix':
            Num = float(self.ids.matrixPoissonRatio.text)
            Num_new = Num - 0.1
            if Num_new > 0.0:
                self.ids.matrixPoissonRatio.text = str(Num_new)

#About popup for lamina strength window
class LaminaStrengthAbout(FloatLayout):
    load = ObjectProperty(None)
    cancel = ObjectProperty(None)    

#Calculation of lamina strength properties of a unidirectional lamina    
class LaminaStrength(BoxLayout):

    def dismiss_popup(self):
        self._popup.dismiss()
    def AboutStrength(self):        
        content = LaminaStrengthAbout(load=self.load, cancel=self.dismiss_popup)
        self._popup = Popup(title="Lamina Strength About", content=content, size_hint=(0.9, 0.9))
        self._popup.open()
        
    def load(self):
        pass
    
    def fiberSelect(self):
    
        fiberType = self.ids.yarnSelectSpinner.text
        
        #E-glass properties
        if fiberType == "E-Glass":
            self.ids.fiberStrength.text = str(3450.0)
            self.ids.fiberModulus.text = str(73.0)
        #S-glass properties
        if fiberType == "S-Glass":
            self.ids.fiberStrength.text = str(4500.0)
            self.ids.fiberModulus.text = str(86.0)
        #AS4 Carbon fiber properties    
        if fiberType == "AS4-Carbon":
            self.ids.fiberStrength.text = str(3700.0)
            self.ids.fiberModulus.text = str(235.0)
        #T300 Carbon fiber properties
        if fiberType == "T300 Carbon":
            self.ids.fiberStrength.text = str(3100.0)
            self.ids.fiberModulus.text = str(230.0)
        #Boron fiber properties
        if fiberType == "Boron":
            self.ids.fiberStrength.text = str(3450.0)
            self.ids.fiberModulus.text = str(395.0)
        #Kevlar 49 fiber properties
        if fiberType == "Kevlar 49":
            self.ids.fiberStrength.text = str(3800.0)
            self.ids.fiberModulus.text = str(131.0)
        #
        if fiberType == "Custom":
            self.ids.fiberStrength.text = str(1000.0)
            self.ids.fiberModulus.text = str(100.0)
    
    def matrixSelect(self):
        matrixType = self.ids.matrixSelectSpinner.text
        #Epoxy mechanical properties
        if matrixType == "Epoxy":
            self.ids.matrixModulus.text = str(4.3)
            self.ids.matrixShearModulus.text = str(1.6)
            #self.ids.matrixPoissonRatio.text = str(0.35)
        #polyester mechanical properties    
        if matrixType == "Polyester":
            self.ids.matrixModulus.text = str(3.2)
            self.ids.matrixShearModulus.text = str(0.7)
            #self.ids.matrixPoissonRatio.text = str(0.35)
        #Polyimides mechanical properties
        if matrixType == "Polyimides":
            self.ids.matrixModulus.text = str(1.4)
            self.ids.matrixShearModulus.text = str(3.1)
            #self.ids.matrixPoissonRatio.text = str(0.35)
        #PEEK mechanical properties    
        if matrixType == "PEEK":
            self.ids.matrixModulus.text = str(1.32)
            self.ids.matrixShearModulus.text = str(3.7)
            #self.ids.matrixPoissonRatio.text = str(0.35)
    
    #Calculate the strength properties of a composite lamina
    def CalculateLaminaStrength(self):
    
            yarnVal = self.ids.yarnSelectSpinner.text
            matrixVal = self.ids.matrixSelectSpinner.text
            
            if yarnVal != 'Select Yarn' and matrixVal != 'SelectMatrix':
    
    
                Ef = float(self.ids.fiberModulus.text)
                Em = float(self.ids.matrixModulus.text)
                Gm = float(self.ids.matrixShearModulus.text)
                Vf = float(self.ids.volumeFraction.text)
                sigmaF = float(self.ids.fiberStrength.text)
                
                if Ef > 0:
                    
                    if Vf >=0 and Vf <1:
                        #Calculate ultimate tensile strength
                        
                        sigmaFiber = sigmaF * Vf + sigmaF * (Em / Ef) * (1-Vf)
                        
                        self.ids.tensileStrength.text = '{0:.1f}'.format(sigmaFiber)
                                    
                        #Calculate ultimate compressive strength
                        num = Vf * Em * Ef
                        den = 3 * (1 - Vf)
                        sqrt = math.sqrt(num / den)
                        sigmaC = 2 * Vf * sqrt
                        
                        self.ids.compressiveStrength.text = '{0:.1f}'.format(sigmaC)       
                    
                        #Calculate ultimate compressive strength shear mode
                        
                        sigmaCshear = (Gm / (1 - Vf)) * 1000
                        
                        self.ids.compressiveStrengthShear.text = '{0:.1f}'.format(sigmaCshear)    
    
    def volumeFractionUp(self):
        VF = float(self.ids.volumeFraction.text)
        VF_new = VF + 0.1
        if VF_new <= 1.0:
            self.ids.volumeFraction.text = str(VF_new)
    
    def volumeFractionDown(self):
        VF = float(self.ids.volumeFraction.text)
        VF_new = VF - 0.1
        if VF_new > 0.0:
            self.ids.volumeFraction.text = str(VF_new)
            
    def fiberModulusUp(self):
        yarnVal = self.ids.yarnSelectSpinner.text
        matrixVal = self.ids.matrixSelectSpinner.text
        
        if yarnVal != 'Select Yarn':
            EF = float(self.ids.fiberModulus.text)
            EF_new = EF + 1.0
            #if EF_new <= 1.0:
            self.ids.fiberModulus.text = str(EF_new)
    
    def fiberModulusDown(self):
        
        yarnVal = self.ids.yarnSelectSpinner.text
        matrixVal = self.ids.matrixSelectSpinner.text
            
        if yarnVal != 'Select Yarn':
            EF = float(self.ids.fiberModulus.text)
            EF_new = EF - 1.0
            if EF_new > 0.0:
                self.ids.fiberModulus.text = str(EF_new)
            
    def fiberStrengthUp(self):
        yarnVal = self.ids.yarnSelectSpinner.text
        matrixVal = self.ids.matrixSelectSpinner.text
            
        if yarnVal != 'Select Yarn':
            SF = float(self.ids.fiberStrength.text)
            SF_new = SF + 10.0
            #if EF_new <= 1.0:
            self.ids.fiberStrength.text = str(SF_new)
    
    def fiberStrengthDown(self):
        yarnVal = self.ids.yarnSelectSpinner.text
        matrixVal = self.ids.matrixSelectSpinner.text
            
        if yarnVal != 'Select Yarn':
            SF = float(self.ids.fiberStrength.text)
            SF_new = SF - 10.0
            if SF_new > 0.0:
                self.ids.fiberStrength.text = str(SF_new)

    def matrixModulusUp(self):
        yarnVal = self.ids.yarnSelectSpinner.text
        matrixVal = self.ids.matrixSelectSpinner.text
            
        if  matrixVal  != 'Select Matrix':
            EM = float(self.ids.matrixModulus.text)
            EM_new = EM + 1.0
            #if EF_new <= 1.0:
            self.ids.matrixModulus.text = str(EM_new)
    
    def matrixModulusDown(self):
        yarnVal = self.ids.yarnSelectSpinner.text
        matrixVal = self.ids.matrixSelectSpinner.text
            
        if  matrixVal  != 'Select Matrix':
            EM = float(self.ids.matrixModulus.text)
            EM_new = EM - 1.0
            if EM_new > 0.0:
                self.ids.matrixModulus.text = str(EM_new)

    def matrixShearModulusUp(self):
        yarnVal = self.ids.yarnSelectSpinner.text
        matrixVal = self.ids.matrixSelectSpinner.text
            
        if  matrixVal  != 'Select Matrix':
            GM = float(self.ids.matrixShearModulus.text)
            GM_new = GM + 1.0
            #if EF_new <= 1.0:
            self.ids.matrixShearModulus.text = str(GM_new)
    
    def matrixShearModulusDown(self):
        yarnVal = self.ids.yarnSelectSpinner.text
        matrixVal = self.ids.matrixSelectSpinner.text
            
        if  matrixVal  != 'Select Matrix':
            GM = float(self.ids.matrixShearModulus.text)
            GM_new = GM - 1.0
            if GM_new > 0.0:
                self.ids.matrixShearModulus.text = str(GM_new)        
    
#cooridnate system transfomation matrix 
class CoordinateTransform(BoxLayout):

    def CalculateTransform(self):
        angle = float(self.ids.braidAngle.text)
        
        angleRad = angle * (math.pi / 180)
        
        
        T11 = math.cos(angleRad) ** 2
        T12 = math.cos(angleRad) ** 2
        T13 = 2*math.cos(angleRad) * math.sin(angleRad)
        
        T21 = T12
        T22 = math.sin(angleRad) ** 2
        T23 = -T13
        
        T31 = math.cos(angleRad) * math.sin(angleRad)
        T32 = -T31
        T33 = (math.cos(angleRad) ** 2) - (math.sin(angleRad) ** 2)
        
        T11inv = T11
        T12inv = T12
        T13inv = -T13
        
        T21inv = T12inv
        T22inv = T22
        T23inv = T13
        
        T31inv = -T31
        T32inv = -T31inv
        T33inv = T33
        
        
        #Display transformation matrix to screen
        #format output for 3 digits after decimal place
        self.ids.T11.text = '{0:.3f}'.format(T11)
        self.ids.T12.text = '{0:.3f}'.format(T12)
        self.ids.T13.text = '{0:.3f}'.format(T13)
        
        self.ids.T21.text = '{0:.3f}'.format(T21)
        self.ids.T22.text = '{0:.3f}'.format(T22)
        self.ids.T23.text = '{0:.3f}'.format(T23)
        
        self.ids.T31.text = '{0:.3f}'.format(T31)
        self.ids.T32.text = '{0:.3f}'.format(T32)
        self.ids.T33.text = '{0:.3f}'.format(T33)
        
        #Display inverse transformation matrix to screen
        self.ids.T11inv.text = '{0:.3f}'.format(T11inv)
        self.ids.T12inv.text = '{0:.3f}'.format(T12inv)
        self.ids.T13inv.text = '{0:.3f}'.format(T13inv)
        
        self.ids.T21inv.text = '{0:.3f}'.format(T21inv)
        self.ids.T22inv.text = '{0:.3f}'.format(T22inv)
        self.ids.T23inv.text = '{0:.3f}'.format(T23inv)
        
        self.ids.T31inv.text = '{0:.3f}'.format(T31inv)
        self.ids.T32inv.text = '{0:.3f}'.format(T32inv)
        self.ids.T33inv.text = '{0:.3f}'.format(T33inv)
    
    def AngleDown(self):
        angle = float(self.ids.braidAngle.text)
        angleNew = angle - 1.0
        self.ids.braidAngle.text = '{0:.1f}'.format(angleNew)
        
    def AngleUp(self):
        angle = float(self.ids.braidAngle.text)
        angleNew = angle + 1.0
        self.ids.braidAngle.text = '{0:.1f}'.format(angleNew)    

#Calculation of braid manufacturing parameters using input braid geometry and braid machine kinematics
class BraidManufacturingAbout(FloatLayout):
    load = ObjectProperty(None)
    cancel = ObjectProperty(None)            
        
        
class BraidManufacturing(BoxLayout):

    def dismiss_popup(self):
        self._popup.dismiss()
        
    def AboutManufacturing(self):        
        content = BraidManufacturingAbout(load=self.load, cancel=self.dismiss_popup)
        self._popup = Popup(title="Braid Manufacturing About", content=content, size_hint=(0.9, 0.9))
        self._popup.open()
        
    def load(self):
        pass
    
    def CalculateManufacture(self):
        R = float(self.ids.radius.text)
        mandrelVelocity = float(self.ids.mandrelVelocity.text)
        rotationalVelocity = float(self.ids.carrierSpeed.text)
        Wy = float(self.ids.yarnWidth.text)        
        gamma = math.radians(float(self.ids.halfConeAngle.text))
        N = float(self.ids.carriers.text)
        
        #Calculate braid angle from mandrel/ carrier speed
        rho = 2 * math.pi * R * (mandrelVelocity / rotationalVelocity)
        angle = math.atan(rho) * (180 / math.pi)
        self.ids.braidAngle.text = '{0:.1f}'.format(angle)
        
        #Calculate Braid Jam Angle
        numerator = Wy * math.sin(gamma)
        denominator = 2 * R * math.sin(2 * math.pi * math.sin(gamma) / N)
        thetaJammed = (math.acos(numerator / denominator)) * (180 / math.pi)
        self.ids.braidJamAngle.text = '{0:.1f}'.format(thetaJammed)
        
        #Calculate Yarn Undulation and Shift angle
                #angle = float(self.ids.braidAngle.text)
        beta = 2 * math.pi / N
        Angle = math.radians(angle)
        Lund = R*beta / math.sin(Angle)
        self.ids.yarnUndulation.text = '{0:.3f}'.format(Lund)
        self.ids.shiftAngle.text = '{0:.3f}'.format(beta)

    def RadiusDown(self):
        radius = float(self.ids.radius.text)
        radiusNew = radius - 0.1
        if radiusNew > 0.0:
            self.ids.radius.text = '{0:.1f}'.format(radiusNew)
        
    def RadiusUp(self):
        radius = float(self.ids.radius.text)
        radiusNew = radius + 0.1
        self.ids.radius.text = '{0:.1f}'.format(radiusNew)
        
    def yarnWidthDown(self):
        yarnWidth = float(self.ids.yarnWidth.text)
        yarnWidthNew = yarnWidth - 0.1
        if yarnWidthNew > 0.0:
            self.ids.yarnWidth.text = '{0:.1f}'.format(yarnWidthNew)
        
    def yarnWidthUp(self):
        yarnWidth = float(self.ids.yarnWidth.text)
        yarnWidthNew =yarnWidth + 0.1
        self.ids.yarnWidth.text = '{0:.1f}'.format(yarnWidthNew) 

    def CarriersDown(self):
        carriers = int(self.ids.carriers.text)
        carriersNew = carriers - 1
        if carriersNew > 0:
            self.ids.carriers.text = '{0:d}'.format(carriersNew)
        
    def CarriersUp(self):
        carriers = int(self.ids.carriers.text)
        carriersNew =carriers + 1
        self.ids.carriers.text = '{0:d}'.format(carriersNew)
        
    def mandrelVelocityDown(self):
        mandrelVelocity = float(self.ids.mandrelVelocity.text)
        mandrelVelocityNew = mandrelVelocity - 1.0
        if mandrelVelocityNew > 0.0:
            self.ids.mandrelVelocity.text = '{0:.1f}'.format(mandrelVelocityNew)
        
    def mandrelVelocityUp(self):
        mandrelVelocity = float(self.ids.mandrelVelocity.text)
        mandrelVelocityNew =mandrelVelocity + 1.0
        self.ids.mandrelVelocity.text = '{0:.1f}'.format(mandrelVelocityNew)

    def carrierSpeedDown(self):
        carrierSpeed = float(self.ids.carrierSpeed.text)
        carrierSpeedNew = carrierSpeed - 1.0
        if carrierSpeedNew > 0.0:
            self.ids.carrierSpeed.text = '{0:.1f}'.format(carrierSpeedNew)
        
    def carrierSpeedUp(self):
        carrierSpeed = float(self.ids.carrierSpeed.text)
        carrierSpeedNew = carrierSpeed + 1.0
        self.ids.carrierSpeed.text = '{0:.1f}'.format(carrierSpeedNew)

    def halfConeAngleDown(self):
        halfConeAngle = float(self.ids.halfConeAngle.text)
        halfConeAngleNew = halfConeAngle - 1.0
        if halfConeAngleNew > 0.0:
            self.ids.halfConeAngle.text = '{0:.1f}'.format(halfConeAngleNew)
        
    def halfConeAngleUp(self):
        halfConeAngle = float(self.ids.halfConeAngle.text)
        halfConeAngleNew = halfConeAngle + 1.0
        self.ids.halfConeAngle.text = '{0:.1f}'.format(halfConeAngleNew)            
        
class ScreenMenu(Spinner):
    pass	
    
class MainBar(BoxLayout):
    pass

class MachineSetupAbout(FloatLayout):
    load = ObjectProperty(None)
    cancel = ObjectProperty(None) 

#Visual guide for the setup of a braiding machine to produce different braiding patterns    
class MachineSetup(BoxLayout):
    
    def dismiss_popup(self):
        self._popup.dismiss()
        
    def AboutMachineSetup(self):        
        content = MachineSetupAbout(load=self.load, cancel=self.dismiss_popup)
        self._popup = Popup(title="Braid Machine Setup About", content=content, size_hint=(0.9, 0.9))
        self._popup.open()
        
    def load(self):
        pass
    
    
    fileNames = 'None'
    
    def patternSelect(self):
        braidPattern = self.ids.braidPatternSpinner.text
              
        curdir = os.path.dirname(os.path.realpath(__file__))
        braidFileType = "*.jpg"
        startImg = 0
        
        if braidPattern == "Diamond Full":
            
            DiamondBraid = '\Diamond_FullLoad\BraidMachine_V3_Step01-01.tif'

            folder = "Diamond_FullLoad"

            pathName = os.path.join(curdir, folder)
        
            names = os.path.join(pathName, braidFileType)
            fileNames = sorted(glob.glob(names))
            
            self.ids.patternImage.source = fileNames[startImg]
            
            numImg = len(fileNames)
            
            self.ids.imageProgressBar.max = numImg - 1
            self.ids.imageProgressBar.value = startImg
            
        elif braidPattern == "Diamond Half":
            braid = "\Diamond_HalfLoad\*.jpg"
            
            folder = "Diamond_HalfLoad"
            
            pathName = os.path.join(curdir, folder)
            
            names = os.path.join(pathName, braidFileType)
            
            fileNames = sorted(glob.glob(names))
            
            self.ids.patternImage.source = fileNames[startImg]
            
            numImg = len(fileNames)
            
            self.ids.imageProgressBar.max = numImg - 1
            self.ids.imageProgressBar.value = startImg
                        
            
        elif braidPattern == "Regular Full":
            
            braid = "\RegularFullLoad\*.jpg"
            
            folder = "RegularFullLoad"
            pathName = os.path.join(curdir, folder)
            names = os.path.join(pathName, braidFileType)
            
            fileNames = sorted(glob.glob(names))
            
            self.ids.patternImage.source = fileNames[startImg]
            
            numImg = len(fileNames)
            
            self.ids.imageProgressBar.max = numImg - 1
            self.ids.imageProgressBar.value = startImg
        
        elif braidPattern == "Regular One-Third":
            
            braid = "\RegularThirdLoad\*.jpg"
            
            folder = "RegularThirdLoad"
            pathName = os.path.join(curdir, folder)
            names = os.path.join(pathName, braidFileType)
            
            fileNames = sorted(glob.glob(names))
           
            self.ids.patternImage.source = fileNames[startImg]
            
            numImg = len(fileNames)
            
            self.ids.imageProgressBar.max = numImg - 1
            self.ids.imageProgressBar.value = startImg
   
        elif braidPattern == "Hercules":
            braid = "\HerculesHalfLoad\*.jpg"
            
            folder = "HerculesHalfLoad"
            pathName = os.path.join(curdir, folder)
            names = os.path.join(pathName, braidFileType)
            
            fileNames = sorted(glob.glob(names))

            
            self.ids.patternImage.source = fileNames[startImg]
            
            numImg = len(fileNames)
            
            self.ids.imageProgressBar.max = numImg - 1
            self.ids.imageProgressBar.value = startImg
            
        global fileNames, startImg
        

    def backButton(self):
    
        braidPatternVal = self.ids.braidPatternSpinner.text
        
        if braidPatternVal != 'Select Braid Pattern':
            global fileNames, startImg
            
            if startImg > 0:
                startImg = startImg - 1
                self.ids.patternImage.source = fileNames[startImg]
                self.ids.imageProgressBar.value = startImg
                

        
    def forwardButton(self):
        braidPatternVal = self.ids.braidPatternSpinner.text
        if braidPatternVal != 'Select Braid Pattern':
            global fileNames, startImg
            
            
            numImg = len(fileNames)
            
            if startImg < numImg:
                self.ids.patternImage.source = fileNames[startImg]
                self.ids.imageProgressBar.value = startImg
                startImg = startImg + 1
                
            #print startImg    

class VolumeFractionAbout(FloatLayout):
    load = ObjectProperty(None)
    cancel = ObjectProperty(None)            
	
#Volume Fraction and Cover Factor Calculation
class VolumeFraction(BoxLayout):
    
    def dismiss_popup(self):
        self._popup.dismiss()
        
    def AboutVolumeFraction(self):        
        content = VolumeFractionAbout(load=self.load, cancel=self.dismiss_popup)
        self._popup = Popup(title="Volume Fraction About", content=content, size_hint=(0.9, 0.9))
        self._popup.open()
        
    def load(self):
        pass
    
    
    def CalculateVF(self, data):
    
        braidVal = self.ids.braidType.text
        yarnShapeVal = self.ids.braidCrossSection.text
        
        if braidVal != 'Braid Type' and yarnShapeVal != "Select Yarn Shape":

            #get input values from user
            r0 = float(self.ids.braidRadius.text)
            yarnWidth = float(self.ids.yarnWidth.text)
            yarnThickness = float(self.ids.yarnThickness.text)
            numberYarns = float(self.ids.numberYarns.text)
            thetaDeg = float(self.ids.theta.text)
            theta = math.radians(thetaDeg)
            braidType = self.ids.braidType.text
            braidCrossSection = self.ids.braidCrossSection.text
            
            #print braidCrossSection
            
            if yarnThickness > 0 and yarnWidth > 0 and numberYarns > 0 and theta > 0 and r0 > 0:
            
                t = 2* yarnThickness
                #calculate yarn cross sectional shape
                if braidCrossSection == "Ellipse":
                    yarnArea = math.pi * yarnWidth * 0.5 * yarnThickness * 0.5
                elif braidCrossSection == "Circle":
                    yarnArea = math.pi * (math.pow(yarnWidth * 0.5, 2))
                elif braidCrossSection == "Rectangle":
                    yarnArea = yarnWidth * yarnThickness
                
                
                
                if braidType == "Diamond":
                    jammed = yarnArea * 4 * numberYarns / (2 * math.pi * r0 * t*math.cos(theta))
                    if jammed <= 1:
                        Vf = yarnArea * 4 * numberYarns / (2 * math.pi * r0 * t*math.cos(theta))
                    elif jammed >=1:
                        Vf = 1

                    coverJammed = yarnWidth * numberYarns / (math.pi * r0 * math.cos(theta))
                    if coverJammed <= 1:
                        CF = coverJammed
                    elif coverJammed >1:
                        CF = 1

                self.ids.volumeFraction.text = '{0:.3f}'.format(Vf)
                self.ids.coverFactor.text = '{0:.3f}'.format(CF)

    def ShowBraidPattern(self):
        braidPattern = self.ids.braidType.text
        if braidPattern == "Diamond":
            self.ids.braidPatternImage.source = 'DiamondBraid_45deg.jpg'
        elif braidPattern == "Regular":
            self.ids.braidPatternImage.source = 'RegularBraid_45deg.jpg'
        elif braidPattern == "Hercules":
            self.ids.braidPatternImage.source = 'HerculesBraid_45deg.jpg'

#This is the angle finder widget that allows drawing two straight lines and calculates the minor angle between the two.
class Angle(Widget):	
	#This function initializes the widget with a touch count of zero
	def __init__(self, **kwargs):
		super(Angle, self).__init__(**kwargs)
		self.touch_down_count = 0

	#This function defines the actions that take place when a touch event occurs
	def on_touch_down(self, touch):
		
		#when touch count = 2, the canvas is cleared, getting rid of the lines and angle
		if self.touch_down_count == 2:
			self.canvas.clear()
			return
						
		#when touch count is greater than 2, we reset the count to zero to allow for new lines to be drawn and measured
		if self.touch_down_count > 2:
			self.touch_down_count = 0
		
		#Record the touch coordinates in x and y as variables	
		x1 = touch.x
		y1 = touch.y
		#create a label on touch and store it in the user dictionary to be accessed later by an update function
		touch.ud['label'] = Label(size_hint=(None, None))
		
		#when the touch count is 0 or 1, we will record the touch coordinates and draw a crosshair at the touch location
		if self.touch_down_count <= 1:
			#add a label widget
			self.add_widget(touch.ud['label'])
			
			with self.canvas:
				#save the touch points to the user dictionary
				touch.ud['x1'] = x1
				touch.ud['y1'] = y1
				#set parameters for crosshair display
				Color(1, 0, 0)
				l = dp(40)
				w = dp(3)
				#draw crosshair
				Rectangle(pos=(touch.ud['x1'] - w / 2, touch.ud['y1'] - l / 2), size=(w, l))
				Rectangle(pos=(touch.ud['x1'] - l / 2, touch.ud['y1'] - w / 2), size=(l, w))
		
	#Function to define what happens on a drag action
	def on_touch_move(self, touch):
		#Record the touch coordinates to variables
		x2 = touch.x
		y2 = touch.y
		#Save touch coordinates to the user dictionary
		touch.ud['x2'] = x2
		touch.ud['y2'] = y2
		ud = touch.ud
		#define a group, g, that will be assigned to the line drawn to allow the line to be redrawn as movements occur, leaving only one line on the screen
		ud['group'] = g = str(touch.uid)
		self.canvas.remove_group(g)

		#When the touch count is zero (first touch), we define a vector v1 based on the touch positions in ud
		if self.touch_down_count == 0:
			v1 = (touch.ud['x2'] - touch.ud['x1'], touch.ud['y2'] - touch.ud['y1'])
			self.v1 = v1
		
		#When the touch count is 1 (second touch), we define a vector v2 based on the touch positions in ud. The angle between vectors v1 and v2 is then calculated.
		if self.touch_down_count == 1:
			v2 = (touch.ud['x2'] - touch.ud['x1'], touch.ud['y2'] - touch.ud['y1'])
			self.v2 = v2
			angle = Vector(self.v1).angle(self.v2)
			absoluteAngle = abs(angle)
			#The following if statement is used to ensure the minor angle is always calculated
			if absoluteAngle > 90:
				absoluteAngle = 180 - absoluteAngle
			#The next two lines are used to update the angle label value as the lines are moved around
			touch.ud['angle'] = absoluteAngle
			self.update_touch_label(touch.ud['label'], touch)
		
		#If the touch count is greater than 1 (third touch), then this function will end and the canvas will clear as in the previous function
		if self.touch_down_count > 1:
			return
		
		#This defines the line and crosshair that is drawn between the initial touch point and where the finger has been dragged
		with self.canvas:
			Color(1, 0, 0)
			l = dp(40)
			w = dp(3)
			Line(points=[touch.ud['x1'], touch.ud['y1'], x2, y2], width=dp(1.5), group=g)
			Rectangle(pos=(touch.ud['x2'] - w / 2, touch.ud['y2'] - l / 2), size=(w, l), group=g)
			Rectangle(pos=(touch.ud['x2'] - l / 2, touch.ud['y2'] - w / 2), size=(l, w), group=g)
	
	#this function defines what to do when a touch is released. The touch count is simply incremented
	def on_touch_up(self, touch):
		self.touch_down_count += 1
			
	#This function defines how the angle label is to be updated. It indicates the number of digits to show, the label size and position, color, and font type
	def update_touch_label(self, label, touch):
		label.text = '%.3f deg' % (touch.ud['angle'])
		label.pos = (self.center_x, self.height - dp(60))
		label.font_size = '25 dp'
		label.size = 1, 1
		label.color = 0, 0, 0, 1
		label.bold = 1

class BraidedCompositeDesignApp(App):

    def build(self):
        self.screen = None
        self.root = GridLayout(rows = 2, cols = 1)
        self.screen_layout = BoxLayout()
        self.menu = ScreenMenu()
        self.root.add_widget(self.menu)
        self.root.add_widget(self.screen_layout)
        

        self.menu.bind(text=self.select_screen)
        self.show('Main')
        
        #control window size for screen shots
        Window.size= (360,640)
        
        return self.root

    def select_screen(self, *args):
        self.show(self.menu.text)
        
    def ensure_dir(self,f):
        d = os.path.dirname(f)
        if not os.path.exists(d):
            os.makedirs(d)
            curdir = os.path.dirname(os.path.realpath(__file__))
            print 'current dir', curdir
            
            img1 = "Test Images/pic1.jpg"
            img2 = "Test Images/pic2.jpg"
            img3 = "Test Images/pic3.jpg"
            img4 = "Test Images/pic4.jpg"
            img5 = "Test Images/pic5.jpg"
            
            name1 = os.path.join(curdir, img1)
            name2 = os.path.join(curdir, img2)
            name3 = os.path.join(curdir, img3)
            name4 = os.path.join(curdir, img4)
            name5 = os.path.join(curdir, img5)
            
            shutil.copy(name1, d)
            shutil.copy(name2, d)
            shutil.copy(name3, d)
            shutil.copy(name4, d)
            shutil.copy(name5, d)
    
    def on_pause(self):
    
        return True
        
    def on_resume(self):
        pass
    

    def show(self, name='Main'):
                if self.screen is not None:
                        self.screen_layout.remove_widget(self.screen)
                        self.screen = None
                if name == 'Main':
                        screen = MainScreen()
                elif name == 'Micromechanics':
                        screen = MicroMechanics()
                elif name == 'Lamina Strength':
                        screen = LaminaStrength()
                elif name == 'CS Transform':
                        screen = CoordinateTransform()
                elif name == 'Braid Manufacturing':
                        screen = BraidManufacturing()
                        #screen = braidManufacture()
                elif name == 'Volume Fraction':
                        screen = VolumeFraction()
                elif name == 'Angle':
                        
                        #check to see if directory is available, if not create new directory and load test images
                        #into this directory
                        filename = "/sdcard/Pictures/BraidedCompositeApp/TestImages/"
                        self.ensure_dir(filename)
                        
                        screen = AngleLayout()
                elif name == 'Braid Machine Setup':
                        screen = MachineSetup()
                elif name == 'About':
                        screen = About_Screen()
                else:
                        raise Exception('Invalid screen name')
                self.screen = screen
                self.screen_layout.add_widget(screen)


if __name__ == "__main__":
    BraidedCompositeDesignApp().run()
