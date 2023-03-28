from kivy.config import Config
Config.set('graphics', 'resizable', False)
Config.set('graphics', 'width', '900')
Config.set('graphics', 'height', '700')

from kivy.uix.screenmanager import Screen, ScreenManager
from kivy.app import App
from kivy.core.window import Window

from plyer import filechooser
from kivy.uix.popup import Popup
from kivy.uix.label import Label
from kivy.uix.floatlayout import FloatLayout
from hide import hide
from unhide import unhide

imgPath = ''
dataPath = ''

class MyScreenManager(ScreenManager):
    pass

class Home(Screen):
    pass

class Guide(Screen):
    pass

class stegoOpt(Screen):
    pass

class UnhideData(Screen):
    def select_file(self):
        try:
            filechooser.open_file(on_selection = self.selected)
        except:
            show_popup("Please Select the file.")
        #filechooser.open_file(on_selection = self.selected)
    
    def selected(self, selection):
        try:
            
            fileName = selection[0]
            if fileName.lower().endswith(('.png')):
                global imgPath
                imgPath = fileName
        except:
            pass
    
    def btn(self):
        try:    
            print(f'Img: {imgPath}')
            unhidedata = unhide(imgName=imgPath)
            print(unhidedata)
            f = (imgPath.split('\\')[-1]).split('.')[0] 
            with open(f'{f}.txt', 'w') as fs:
                fs.write((unhidedata.decode('utf-8')))
            show_popup("Data Retrive")
        except:
            show_popup("You haven't select image file!")

class Stego(Screen):
    def select_file(self):
        try:
            filechooser.open_file(on_selection = self.selected)
        except:
            show_popup("Please Select the file.")
            
    def selected(self, selection):
        try:
            fileName = selection[0]
            if fileName.lower().endswith(('.png')):
                global imgPath
                imgPath = fileName
            elif fileName.lower().endswith(('.txt')):
                global dataPath
                dataPath = fileName
            else:
                pass
        except:
            pass

    def btn(self):
        # print(f'Img: {imgPath}')
        # print(f"Data: {dataPath}")
        try:

            with open(dataPath, "r") as f:
                data = f.read()

            try:

                lst = hide(data=data, imgName=imgPath )
                
                #print(lst)
                show_popup("Submitted")
        
            except Exception as e:
               print(e)
        
        except:
           show_popup("You haven't select any file!")

class P(FloatLayout):
    pass

def show_popup(msg):
    show = P()
    popupWindow = Popup(title="Notification", content=Label(text=msg), size_hint=(None,None),size=(300,200))

    popupWindow.open()

class MAINApp(App):
    def build(self):

        Window.clearcolor =("#41CBC7")
        self.title = 'Securing Medical Domain using Image Encryption and Steganography'


        return MyScreenManager()

if __name__ == '__main__':
    MAINApp().run()