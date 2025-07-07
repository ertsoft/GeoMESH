from kivy.uix.floatlayout import FloatLayout
from kivy.uix.popup import Popup
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.behaviors import ButtonBehavior
from kivy_garden.mapview import MapSource
from basemap_container import Basemap_Container

osm_source = MapSource(
    url="http://a.tile.openstreetmap.org/{z}/{x}/{y}.png",
    attribution="basemap@OpenStreetMap",
    tile_size=256,
    image_ext="png"
)
esri_source = MapSource(
    url="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
    attribution="basemap@Esri",
    tile_size=256,
    image_ext="jpg"
)


#creare buton-imagine (în kivy nu există ImageButton)
class ClickableImage(ButtonBehavior, Image):
    pass

class SwitchBasemap(FloatLayout):
    def __init__(self, init_basemap, **kwargs):
        super().__init__(**kwargs)
        self.init_basemap = init_basemap

    def open_basemap_popup(self):
        layout = BoxLayout(orientation='horizontal', spacing=10, padding=10)

        # Selectare basemap: OSM
        osm_box = BoxLayout(orientation='vertical')
        osm_img = ClickableImage(source='imgs_basemap/osm_basemap.png', size_hint=(1, 0.8))
        osm_label = Label(text='OpenStreetMap', size_hint=(1, 0.2))
        osm_img.bind(on_release=lambda x: self.select_basemap('osm', popup))
        osm_box.add_widget(osm_img)
        osm_box.add_widget(osm_label)

        # Selectare basemap: Esri
        esri_box = BoxLayout(orientation='vertical')
        esri_img = ClickableImage(source='imgs_basemap/esri_basemap.png', size_hint=(1, 0.8))
        esri_label = Label(text='Esri Satellite', size_hint=(1, 0.2))
        esri_img.bind(on_release=lambda x: self.select_basemap('esri', popup))
        esri_box.add_widget(esri_img)
        esri_box.add_widget(esri_label)

        layout.add_widget(osm_box)
        layout.add_widget(esri_box)

        popup = Popup(title='Selectează Basemap', content=layout,
                      size_hint=(None, None), size=(320, 180), auto_dismiss=True)
        popup.open()

    def select_basemap(self, key, popup):
        if key == 'osm':
            self.init_basemap.mapview.map_source = osm_source
        elif key == 'esri':
            self.init_basemap.mapview.map_source = esri_source
        popup.dismiss()
