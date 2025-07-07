from kivy.uix.floatlayout import FloatLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivymd.uix.button import MDIconButton
from kivymd.uix.label import MDIcon
from kivy_garden.mapview import MapView, MapSource, MapMarker, MapLayer
from kivy.graphics import Line
from kivy.metrics import dp
import math
from kivymd.uix.textfield import MDTextField
from kivymd.uix.dialog import MDDialog
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button
from kivy.uix.widget import Widget
from kivy.graphics import Color, Rectangle
from kivy.uix.scrollview import ScrollView
from kivy.metrics import sp
from kivy.graphics import Color, Mesh

class ColorBox(Widget):
    def __init__(self, color=[1, 1, 0, 1], **kwargs):
        super().__init__(**kwargs)
        self.size_hint = (None, None)
        self.size = (220, 20)
        self.color = color

        with self.canvas:
            self.color_instruction = Color(*self.color)
            self.rect = Rectangle(pos=self.pos, size=self.size)

        self.bind(pos=self.update_rect, size=self.update_rect)

    def update_rect(self, *args):
        self.rect.pos = self.pos
        self.rect.size = self.size

    def set_color(self, color):
        self.color_instruction.rgba = color

class IconMarker(MapMarker):
    def __init__(self, icon_name, marker_size, icon_color=[1, 1, 0, 1], **kwargs):
        super().__init__(**kwargs)
        self.source = "transparent.png"
        self.icon_size_sp = int(sp(marker_size))

        self.icon_widget = MDIcon(
            icon=icon_name,
            theme_text_color="Custom",
            text_color=icon_color,
            size_hint=(None, None),
            font_size=f"{self.icon_size_sp}sp",
            pos=self.pos,
        )

        size_px = dp(self.icon_size_sp)
        self.icon_widget.size = (size_px, size_px)

        self.add_widget(self.icon_widget)
        self.bind(pos=self.update_icon_pos, size=self.update_icon_pos)

    def update_icon_pos(self, *args):
        size_px = dp(self.icon_size_sp)
        self.icon_widget.size = (size_px, size_px)
        self.icon_widget.font_size = f"{self.icon_size_sp}sp"
        # poziționare centrată
        self.icon_widget.pos = (self.pos[0] - size_px / 2, self.pos[1] - size_px / 2)

class LineMapLayer(MapLayer):
    def __init__(self, points_getter, color=[1, 1, 1, 1], width=2, **kwargs):
        super().__init__(**kwargs)
        self.points_getter = points_getter
        self.color = color
        self.width = width
    #     self.bind(parent=self._on_parent_assigned)
    #
    # def _on_parent_assigned(self, instance, value):
    #     if value is not None:
    #         self.reposition()

    def reposition(self):
        self.canvas.clear()
        points = self.points_getter()
        if self.parent is None:
            return
        if len(points) < 2:
            return
        with self.canvas:
            Color(*self.color)
            line_points = []
            for lat, lon in points:
                x, y = self.parent.get_window_xy_from(lat, lon, self.parent.zoom)
                line_points.extend([x, y])
            Line(points=line_points, width=self.width)


class PolygonMapLayer(MapLayer):
    def __init__(self, points_getter, color=[1, 1, 0, 0.2], **kwargs):
        super().__init__(**kwargs)
        self.points_getter = points_getter
        self.color = color

    def reposition(self):
        self.canvas.clear()
        points = self.points_getter()
        if self.parent is None or len(points) < 3:
            return

        with self.canvas:
            Color(*self.color)

            # Convertim coordonatele lat/lon în coordonate pe hartă (pixeli)
            vertices = []
            indices = []
            for lat, lon in points:
                x, y = self.parent.get_window_xy_from(lat, lon, self.parent.zoom)
                vertices.extend([x, y, 0, 0])  # UV coords le punem 0, nu contează aici

            # Creăm triunghiurile pentru mesh (triangulare simplă)
            # Atenție: asta merge doar dacă poligonul nu e complex
            # (Nu are găuri și e convex sau aproape convex)
            for i in range(1, len(points) - 1):
                indices.extend([0, i, i + 1])

            Mesh(vertices=vertices, indices=indices, mode='triangles')

class Basemap_Container(FloatLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.features = []
        self.next_feature_id = 1

        self.selected_features = []

        self.current_user_id = None
        self.current_team_id = None

        #puncte
        self.points_markers = []

        # Lines
        self.line_layers = []
        self.current_line_coords = []
        self.lines_markers = []
        self.drawing_line = False

        # Polygons
        #self.polygon_coords = []
        self.current_polygon_coords = []
        self.polygon_layers = []
        self.polygon_markers = []
        self.drawing_polygon = False

        # Measurements
        self.points = []
        self.measurements_markers = []

        self.selected_point_color = [1, 1, 0, 1] # culoare initiala=galben
        self.selected_line_color = [1, 0.5, 0, 1]  # portocaliu
        self.selected_polygon_color = [1, 1, 0, 1]
        self.selected_point_symbol = "map-marker"
        self.selected_atribute_color =[1,1,1,1]

        self.osm_source = MapSource(
            url="http://a.tile.openstreetmap.org/{z}/{x}/{y}.png",
            attribution="basemap@OpenStreetMap",
            tile_size=256,
            image_ext="png"
        )
        self.esri_source = MapSource(
            url="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
            attribution="basemap@Esri",
            tile_size=256,
            image_ext="jpg"
        )
        self.mapview = MapView(zoom=10, lat=45.1, lon=25.2, map_source=self.esri_source)
        self.add_widget(self.mapview)

        self.measuring_enabled = False
        self.mode = 'distance'
        self.mapview.bind(on_touch_down=self.on_map_touch)

        # Layers
        self.measurements_line_layer = LineMapLayer(points_getter=lambda: self.points,color=[1, 1, 0, 1], width=2)
        self.mapview.add_layer(self.measurements_line_layer)

        self.current_line_layer = LineMapLayer(points_getter=lambda: self.current_line_coords,color=[1, 0.5, 0, 1],width=2)
        self.mapview.add_layer(self.current_line_layer)

        self.current_polygon_layer = LineMapLayer(points_getter=lambda: self.current_polygon_coords,color=[1, 0.5, 0, 1],width=2)
        self.mapview.add_layer(self.current_polygon_layer)

        self.distance_box = self.build_distance_box()
        self.point_box = self.build_point_box()
        self.line_box = self.build_line_box()
        self.polygon_box = self.build_polygon_box()
        self.atribute_box = self.open_atribute_table()

    def build_distance_box(self):
        distance_box = BoxLayout(
            orientation='vertical',
            size_hint=(None, 1),
            width=dp(265),
            pos_hint={'right': 1, 'top': 1},
            padding=[dp(16), dp(16), dp(16), dp(16)],
            spacing=dp(12),
            opacity=0,
        )
        with distance_box.canvas.before:
            Color(0, 0, 0, 0.85)
            self.rect = Rectangle(size=distance_box.size, pos=distance_box.pos)
        distance_box.bind(size=self._update_rect, pos=self._update_rect)

        top_row = BoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height=dp(40),
            spacing=dp(10),
        )

        ruler_icon = MDIcon(icon="ruler")
        ruler_icon.size_hint = (None, None)
        ruler_icon.size = (dp(28), dp(28))
        ruler_icon.pos_hint = {'center_y': 0.5}
        top_row.add_widget(ruler_icon)

        measure_label = Label(
            text="Masurare",
            size_hint_x=None,
            width=dp(100),
            halign='left',
            valign='middle',
            color=(1, 1, 1, 1),
            font_size=dp(16),
        )
        measure_label.bind(size=lambda inst, val: setattr(inst, 'text_size', val))
        top_row.add_widget(measure_label)

        refresh_btn = MDIconButton(icon="refresh")
        refresh_btn.size_hint = (None, None)
        refresh_btn.size = (dp(28), dp(28))
        refresh_btn.pos_hint = {'center_y': 0.5}
        refresh_btn.bind(on_release=self.reset_measurement)
        top_row.add_widget(refresh_btn)

        close_btn = MDIconButton(icon="close")
        close_btn.size_hint = (None, None)
        close_btn.size = (dp(28), dp(28))
        close_btn.pos_hint = {'center_y': 0.5}
        close_btn.bind(on_release=self.close_panel)
        top_row.add_widget(close_btn)

        distance_box.add_widget(top_row)

        buttons_layout = BoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height=dp(40),
            spacing=dp(10),
        )

        self.btn_distance = Button(
            text="Distanță",
            size_hint_x=0.5,
            font_size=dp(14),
        )
        buttons_layout.add_widget(self.btn_distance)

        self.btn_area = Button(
            text="Arie",
            size_hint_x=0.5,
            font_size=dp(14),
        )
        buttons_layout.add_widget(self.btn_area)

        distance_box.add_widget(buttons_layout)
        distance_box.add_widget(BoxLayout(size_hint_y=None, height=dp(10)))

        self.data_label = Label(
            text="",
            size_hint_y=None,
            height=dp(40),
            halign='left',
            valign='top',
            color=(1, 1, 1, 1),
            font_size=dp(14),
            text_size=(distance_box.width - dp(32), dp(40)),
        )
        self.data_label.bind(size=lambda inst, val: setattr(inst, 'text_size', (val[0] - dp(32), val[1])))
        distance_box.add_widget(self.data_label)
        distance_box.add_widget(BoxLayout())

        self.btn_distance.bind(on_release=lambda *a: self.set_mode("measure_distance", "", ""))
        self.btn_area.bind(on_release=lambda *a: self.set_mode("measure_area", "", ""))

        return distance_box

    def _update_rect(self, instance, value):
        self.rect.pos = instance.pos
        self.rect.size = instance.size
        self.data_label.text_size = (self.distance_box.width - dp(32), self.data_label.height)

    def set_mode(self, mode, current_user_id, current_team_id):
        self.current_team_id = current_team_id
        self.current_user_id = current_user_id

        # dezleagă vechile evenimente
        self.mapview.unbind(on_touch_down=self.on_select_tap)

        if self.mode == "line" and mode != "line":
            self.finalize_current_line()

        self.mode = mode

        self.measuring_enabled = mode.startswith("measure")

        if self.measuring_enabled:
            self.reset_measurement()

        # Eliminare de pe ecran a panourilor vechi
        for box in [self.point_box, self.distance_box, self.line_box, self.polygon_box]:
            if box.parent:
                box.opacity = 0
                box.disabled = True
                self.remove_widget(box)

        # Afișăm doar panoul necesar
        if mode == "point":
            self.point_box.opacity = 1
            self.point_box.disabled = False
            self.add_widget(self.point_box)

        elif mode.startswith("measure"):
            self.distance_box.opacity = 1
            self.measurements_line_layer = LineMapLayer(
                points_getter=lambda: self.points,
                color=[1, 0.5, 0, 1],
                width=2
            )
            self.mapview.add_layer(self.measurements_line_layer)
            self.distance_box.disabled = False
            self.add_widget(self.distance_box)

        elif mode == "polygon":
            self.reset_current_polygon()
            self.current_polygon_layer = LineMapLayer(
                points_getter=lambda: self.current_polygon_coords,
                color=self.selected_polygon_color,
                width=2
            )
            self.mapview.add_layer(self.current_polygon_layer)
            self.polygon_box.opacity = 1
            self.polygon_box.disabled = False
            self.add_widget(self.polygon_box)

        elif mode == "line":
            self.reset_current_line()
            self.current_line_layer = LineMapLayer(
                points_getter=lambda: self.current_line_coords,
                color=self.selected_line_color,
                width=2
            )
            self.mapview.add_layer(self.current_line_layer)
            self.drawing_line = True
            self.line_box.opacity = 1
            self.line_box.disabled = False
            self.add_widget(self.line_box)

        elif mode == "select":
            self.mode = "select"
            self.mapview.bind(on_touch_down=self.on_select_tap)

        elif mode == 'atribute':
            self.atribute_box.opacity = 1
            self.atribute_box.disabled = False
            self.add_widget(self.atribute_box)

        self.data_label.text = f"Mod activ: {mode}"

    def on_map_touch(self, instance, touch):
        if not self.mapview.collide_point(*touch.pos):
            return False

        if touch.button != 'left':
            return False

        if not self.measuring_enabled and self.mode not in ["point", "line", "polygon"]:
            # nu interceptăm event-ul → lasă MapView să se miște
            return False

        lat, lon = self.mapview.get_latlon_at(*touch.pos)

        if self.mode == "point":
            description = self.point_description_input.text.strip()
            point_color = self.selected_point_color
            symbol = self.selected_point_symbol

            feature = {
                "id": self.next_feature_id,
                "type": "Point",
                "coords": [(lat, lon)],
                "user_id": self.current_user_id,
                "team_id": self.current_team_id,
                "symbol": symbol,
                "color": point_color,
                "description": description,
            }
            self.features.append(feature)
            self.next_feature_id += 1

            # Creezi markerul grafic
            marker = IconMarker(
                icon_name=symbol,
                icon_color=point_color,
                lat=lat,
                lon=lon,
                marker_size=dp(18),
            )
            self.mapview.add_marker(marker)
            self.points_markers.append(marker)

        elif self.mode == "line":
            if not self.drawing_line:
                self.reset_current_line()
                self.drawing_line = True

            self.current_line_coords.append((lat, lon))
            marker = IconMarker(
                icon_name="circle",
                marker_size=dp(12),
                icon_color=self.selected_line_color,
                lat=lat,
                lon=lon,
            )
            self.mapview.add_marker(marker)
            self.lines_markers.append(marker)
            self.current_line_layer.reposition()

        elif self.mode == "polygon":
            polygon_description = self.polygon_description_input.text.strip()
            if not self.drawing_polygon:
                self.reset_current_polygon()
                self.drawing_polygon = True

            if len(self.current_polygon_coords) > 0:
                x_new, y_new = self.mapview.get_window_xy_from(lat, lon, self.mapview.zoom)
                x_first, y_first = self.mapview.get_window_xy_from(*self.current_polygon_coords[0], self.mapview.zoom)
                dist_pix = math.hypot(x_new - x_first, y_new - y_first)
                if dist_pix < 20:
                    self.current_polygon_coords.append(self.current_polygon_coords[0])

                    feature = {
                        "id": self.next_feature_id,
                        "type": "Polygon",
                        "coords": self.current_polygon_coords.copy(),
                        "user_id": self.current_user_id,
                        "team_id": self.current_team_id,
                        "color": self.selected_polygon_color,
                        "description": polygon_description,
                    }
                    self.features.append(feature)
                    self.next_feature_id += 1

                    new_layer = PolygonMapLayer(
                        points_getter=lambda coords=feature["coords"]: coords,
                        color=feature["color"],
                    )

                    self.mapview.add_layer(new_layer)
                    new_layer.reposition()
                    self.polygon_layers.append(new_layer)

                    self.reset_current_polygon()
                    self.drawing_polygon = False
                    print(self.features)

                    return True

            self.current_polygon_coords.append((lat, lon))
            marker = IconMarker(
                icon_name="circle",
                marker_size=dp(12),
                icon_color=self.selected_polygon_color,
                lat=lat,
                lon=lon,
            )
            self.mapview.add_marker(marker)
            self.polygon_markers.append(marker)
            self.current_polygon_layer.reposition()

        elif self.mode == "measure_distance":
            self.add_measurement_point(lat, lon)

        elif self.mode == "measure_area":
            self.add_measurement_point(lat, lon, area_mode=True)

        return True

    def finalize_current_line(self):
        line_description=self.line_description_input.text.strip()
        if self.drawing_line and self.current_line_coords:
            # Creăm feature-ul
            feature = {
                "id": self.next_feature_id,
                "type": "Line",
                "coords": self.current_line_coords.copy(),
                "user_id": self.current_user_id,
                "team_id": self.current_team_id,
                "color": self.selected_line_color,  # portocaliu
                "width": 2,
                "description": line_description,
            }
            self.features.append(feature)
            self.next_feature_id += 1

            # Creezi Layer-ul ca să fie desenat pe hartă
            new_layer = LineMapLayer(
                points_getter=lambda coords=feature["coords"]: coords,
                color=self.selected_line_color,
                width=2
            )
            self.mapview.add_layer(new_layer)
            new_layer.reposition()
            self.line_layers.append(new_layer)

        self.reset_current_line()

    def reset_current_line(self):
        self.current_line_coords.clear()
        for marker in self.lines_markers:
            self.mapview.remove_marker(marker)
        self.lines_markers.clear()
        if hasattr(self, 'current_line_layer'):
            self.safe_remove_layer(self.current_line_layer)
        self.drawing_line = False

    def reset_current_polygon(self):
        self.current_polygon_coords.clear()
        for marker in self.polygon_markers:
            self.mapview.remove_marker(marker)
        self.polygon_markers.clear()
        self.current_polygon_layer.reposition()
        self.drawing_polygon = False

    def safe_remove_layer(self, layer):
        if layer in self.mapview._layers:
            self.mapview.remove_layer(layer)

    def add_measurement_point(self, lat, lon, area_mode=False):
        x_new, y_new = self.mapview.get_window_xy_from(lat, lon, self.mapview.zoom)

        for i, (plat, plon) in enumerate(self.points):
            x_old, y_old = self.mapview.get_window_xy_from(plat, plon, self.mapview.zoom)
            dist_pix = math.hypot(x_new - x_old, y_new - y_old)
            if dist_pix <= 20:
                lat, lon = plat, plon
                if len(self.points) > 0 and (lat, lon) == self.points[-1]:
                    return
                self.points.append((lat, lon))
                break
        else:
            self.points.append((lat, lon))
            marker = IconMarker(
                icon_name="circle",
                marker_size=dp(12),
                icon_color=[1, 1, 0, 1],
                lat=lat,
                lon=lon,
            )
            self.mapview.add_marker(marker)
            self.measurements_markers.append(marker)

        self.measurements_line_layer.reposition()

        if not area_mode:
            if len(self.points) >= 2:
                total_dist = sum(
                    self.haversine(self.points[i], self.points[i + 1])
                    for i in range(len(self.points) - 1)
                )
                self.show_distance(total_dist)
        else:
            if len(self.points) >= 3 and self.points[0] == self.points[-1]:
                area_m2, perimeter_m = self.calculate_area_and_perimeter(self.points[:-1])
                self.data_label.text = f"Aria: {area_m2:.2f} m²\nPerimetrul: {perimeter_m:.2f} m"
                self.measuring_enabled = False
            else:
                self.data_label.text = f"Puncte: {len(self.points)} (închide poligonul atingând primul punct)"

    def haversine(self, point1, point2):
        lat1, lon1 = point1
        lat2, lon2 = point2
        R = 6371
        phi1 = math.radians(lat1)
        phi2 = math.radians(lat2)
        dphi = math.radians(lat2 - lat1)
        dlambda = math.radians(lon2 - lon1)

        a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        return R * c

    def format_distance(self, dist_km):
        dist_m = dist_km * 1000
        if dist_m < 1000:
            return f"{dist_m:.0f} m"
        else:
            return f"{dist_km:.2f} km"

    def show_distance(self, dist_km):
        dist_str = self.format_distance(dist_km)
        self.data_label.text = f"Distanța măsurată: {dist_str}"
        self.distance_box.opacity = 1

    def calculate_area_and_perimeter(self, points):
        def latlon_to_xy(lat, lon):
            R = 6371000
            x = math.radians(lon) * R * math.cos(math.radians(lat))
            y = math.radians(lat) * R
            return (x, y)

        xy_points = [latlon_to_xy(lat, lon) for lat, lon in points]
        perimeter = 0
        n = len(xy_points)
        for i in range(n):
            x1, y1 = xy_points[i]
            x2, y2 = xy_points[(i + 1) % n]
            perimeter += math.hypot(x2 - x1, y2 - y1)

        area = 0
        for i in range(n):
            x1, y1 = xy_points[i]
            x2, y2 = xy_points[(i + 1) % n]
            area += x1 * y2 - x2 * y1
        area = abs(area) / 2

        return area, perimeter

    def reset_measurement(self, *args):
        self.points = []
        for marker in self.measurements_markers:
            self.mapview.remove_marker(marker)
        self.measurements_markers.clear()
        self.measurements_line_layer.canvas.clear()
        self.data_label.text = ""

    def close_panel(self, *args):
        self.reset_measurement()
        if self.distance_box.parent:
            self.distance_box.opacity = 0
            self.distance_box.disabled = True
            self.remove_widget(self.distance_box)
        self.measuring_enabled = False

    def measure(self):
        self.set_mode("", "", "")
        self.set_mode("measure_distance", "", "")

    def zoom_in(self):
        if self.mapview.zoom < 20:
            self.mapview.zoom += 1

    def zoom_out(self):
        if self.mapview.zoom > 1:
            self.mapview.zoom -= 1

    def build_point_box(self):

        def open_symbol_palette(*args):
            layout = GridLayout(
                cols=7,
                spacing=10,
                padding=10,
                size_hint_y=None
            )
            layout.bind(minimum_height=layout.setter("height"))

            icon_names = [
                # Locație / GPS / Hărți
                "map-marker", "map-marker-outline", "map-marker-radius", "map-marker-plus",
                "map-marker-path", "crosshairs-gps", "crosshairs", "earth", "circle",
                "pin", "flag", "navigation", "target", "satellite",

                # Geometrie / forme
                "ruler", "ruler-square", "vector-polyline", "vector-line",
                "vector-square", "vector-curve", "shape-outline", "shape",
                "shape-rectangle-plus", "shape-circle-plus", "shape-polygon-plus",

                # Clădiri / construcții
                "home", "home-outline", "domain", "office-building",
                "city", "factory", "garage", "warehouse", "fence", "bridge",
                "lighthouse",
                # Tools / instrumente
                "wrench", "hammer", "toolbox"
                ,"flashlight", "radar",

                # Transport
                "truck", "excavator",
                "car", "car-electric", "bicycle", "airplane",
                "train", "bus",

                # Simboluri diverse utile
                "grid", "grid-large", "cube",
                "selection", "flash", "cloud", "cog"
            ]

            def select_symbol(icon_name):
                print(f"Ai ales simbolul: {icon_name}")
                self.selected_point_symbol = icon_name
                self.symbol_preview.icon = icon_name
                symbol_dialog.dismiss()

            for icon_name in icon_names:
                btn = MDIconButton(
                    icon=icon_name,
                    icon_size=dp(32),
                    theme_text_color="Custom",
                    text_color=(1, 1, 1, 1),
                    on_release=lambda btn, name=icon_name: select_symbol(name),
                )
                layout.add_widget(btn)

            scroll = ScrollView(size_hint=(1, None), height=dp(400))
            scroll.add_widget(layout)

            symbol_dialog = MDDialog(
                title="Selectează un simbol",
                type="custom",
                content_cls=scroll,
                buttons=[],
            )

            symbol_dialog.open()

        def open_color_palette(*args):
            colors = [
                ([1, 0, 0, 1], "Roșu"),
                ([1, 0.5, 0, 1], "Portocaliu"),
                ([1, 1, 0, 1], "Galben"),
                ([0.5, 1, 0, 1], "Galben-Verzui"),
                ([0, 1, 0, 1], "Verde"),
                ([0, 1, 1, 1], "Turcoaz"),
                ([0, 0, 1, 1], "Albastru"),
                ([0.5, 0, 1, 1], "Indigo"),
                ([1, 0, 1, 1], "Magenta"),
                ([1, 0.75, 0.8, 1], "Roz"),
                ([0.5, 0.5, 0.5, 1], "Gri"),
                ([0.25, 0.25, 0.25, 1], "Gri Închis"),
                ([0.75, 0.75, 0.75, 1], "Gri Deschis"),
                ([0, 0, 0, 1], "Negru"),
                ([1, 1, 1, 1], "Alb"),
                ([0.8, 0.4, 0, 1], "Maro"),
                ([0.5, 0, 0, 1], "Burgundy"),
                ([0, 0.5, 0, 1], "Verde Închis"),
                ([0, 0, 0.5, 1], "Bleumarin"),
                ([0.5, 0, 0.5, 1], "Violet"),
                ([1, 0.84, 0, 1], "Auriu"),
                ([0.75, 0.75, 0, 1], "Măsliniu"),
                ([0.72, 0.45, 0.2, 1], "Cafeniu"),
                ([0.96, 0.64, 0.38, 1], "Piatră"),
            ]

            layout = GridLayout(cols=8, spacing=10, padding=10, size_hint_y=None)
            layout.bind(minimum_height=layout.setter("height"))

            color_dialog = MDDialog(
                title="Selectează o culoare",
                type="custom",
                content_cls=layout,
                buttons=[],
            )

            def select_color(color, name):
                print(f"Ai ales culoarea: {name}")
                self.selected_point_color = color
                self.color_pct_preview.set_color(color)
                color_dialog.dismiss()

            for rgba, name in colors:
                btn = Button(
                    background_normal='',
                    background_color=rgba,
                    size_hint=(None, None),
                    size=(50, 50),
                    on_release=lambda btn, c=rgba, n=name: select_color(c, n),
                )
                layout.add_widget(btn)

            color_dialog.open()

        point_box = BoxLayout(
            orientation='vertical',
            size_hint=(None, 1),
            width=dp(265),
            pos_hint={'right': 1, 'top': 1},
            padding=[dp(16), dp(16), dp(16), dp(16)],
            spacing=dp(12),
            opacity=0,
        )
        with point_box.canvas.before:
            Color(0, 0, 0, 0.85)
            self.rect_point = Rectangle(size=point_box.size, pos=point_box.pos)
        point_box.bind(size=self._update_rect_point, pos=self._update_rect_point)

        first_row = BoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height=dp(40),
            spacing=dp(10),
        )

        icon = MDIcon(icon="plus-circle-outline")
        icon.size_hint = (None, None)
        icon.size = (dp(28), dp(28))
        icon.pos_hint = {'center_y': 0.5}
        first_row.add_widget(icon)

        label = Label(
            text="Creare Punct",
            size_hint_x=None,
            width=dp(150),
            halign='left',
            valign='middle',
            color=(1, 1, 1, 1),
            font_size=dp(16),
        )
        label.bind(size=lambda inst, val: setattr(inst, 'text_size', val))
        first_row.add_widget(label)

        close_btn = MDIconButton(icon="close")
        close_btn.size_hint = (None, None)
        close_btn.size = (dp(28), dp(28))
        close_btn.pos_hint = {'center_y': 0.5}
        close_btn.bind(on_release=self.close_point_panel)
        first_row.add_widget(close_btn)

        point_box.add_widget(first_row)

        self.point_description_input = MDTextField(
            hint_text="Descriere punct",
            size_hint_y=None,
            height=dp(48),
            multiline=False,
        )
        point_box.add_widget(self.point_description_input)

        second_row = BoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height=dp(40),
            spacing=dp(10),
        )

        label_culoare = Label(
            text="  Selectează culoarea punctului",
            size_hint_x=None,
            width=dp(197),
            halign='left',
            valign='middle',
            color=(1, 1, 1, 1),
            font_size=dp(16),
        )
        second_row.add_widget(label_culoare)

        arrow_btn = MDIconButton(
            icon="chevron-down",
            size_hint=(None, None),
            size=(dp(28), dp(28)),
            pos_hint={'center_y': 0.5}
        )
        arrow_btn.size_hint_x = None
        arrow_btn.width = dp(28)

        arrow_btn.bind(on_release=open_color_palette)
        second_row.add_widget(arrow_btn)
        point_box.add_widget(second_row)

        third_row = BoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height=dp(20),
            spacing=dp(1),
        )
        self.color_pct_preview = ColorBox(color=self.selected_point_color)
        third_row.add_widget(self.color_pct_preview)

        point_box.add_widget(third_row)

        fourth_row = BoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height=dp(40),
            spacing=dp(10),
        )

        label_simbol = Label(
            text="  Selectează simbolul punctului",
            size_hint_x=None,
            width=dp(197),
            halign='left',
            valign='middle',
            color=(1, 1, 1, 1),
            font_size=dp(16),
        )
        fourth_row.add_widget(label_simbol)

        arrow_btn_symbol = MDIconButton(
            icon="chevron-down",
            size_hint=(None, None),
            size=(dp(28), dp(28)),
            pos_hint={'center_y': 0.5}
        )
        arrow_btn_symbol.size_hint_x = None
        arrow_btn_symbol.width = dp(28)
        arrow_btn_symbol.bind(on_release=open_symbol_palette)

        fourth_row.add_widget(arrow_btn_symbol)
        point_box.add_widget(fourth_row)

        # Preview icon:
        fifth_row = BoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height=dp(120),
            spacing=dp(10),
        )

        self.symbol_preview = MDIcon(
            icon=self.selected_point_symbol,
            size_hint=(None, None),
            size=(dp(28), dp(28)),
            theme_text_color="Custom",
            text_color=(1, 1, 1, 1),
            pos_hint={'center_x': 0.5}
        )

        fifth_row.add_widget(Widget())
        fifth_row.add_widget(self.symbol_preview)
        fifth_row.add_widget(Widget())

        point_box.add_widget(fifth_row)
        point_box.add_widget(BoxLayout())

        return point_box

    def build_line_box(self):

        def open_color_palette(*args):
            colors = [
                ([1, 0, 0, 1], "Roșu"),
                ([1, 0.5, 0, 1], "Portocaliu"),
                ([1, 1, 0, 1], "Galben"),
                ([0.5, 1, 0, 1], "Galben-Verzui"),
                ([0, 1, 0, 1], "Verde"),
                ([0, 1, 1, 1], "Turcoaz"),
                ([0, 0, 1, 1], "Albastru"),
                ([0.5, 0, 1, 1], "Indigo"),
                ([1, 0, 1, 1], "Magenta"),
                ([1, 0.75, 0.8, 1], "Roz"),
                ([0.5, 0.5, 0.5, 1], "Gri"),
                ([0.25, 0.25, 0.25, 1], "Gri Închis"),
                ([0.75, 0.75, 0.75, 1], "Gri Deschis"),
                ([0, 0, 0, 1], "Negru"),
                ([1, 1, 1, 1], "Alb"),
                ([0.8, 0.4, 0, 1], "Maro"),
                ([0.5, 0, 0, 1], "Burgundy"),
                ([0, 0.5, 0, 1], "Verde Închis"),
                ([0, 0, 0.5, 1], "Bleumarin"),
                ([0.5, 0, 0.5, 1], "Violet"),
                ([1, 0.84, 0, 1], "Auriu"),
                ([0.75, 0.75, 0, 1], "Măsliniu"),
                ([0.72, 0.45, 0.2, 1], "Cafeniu"),
                ([0.96, 0.64, 0.38, 1], "Piatră"),
            ]

            layout = GridLayout(cols=8, spacing=10, padding=10, size_hint_y=None)
            layout.bind(minimum_height=layout.setter("height"))

            color_dialog = MDDialog(
                title="Selectează o culoare",
                type="custom",
                content_cls=layout,
                buttons=[],
            )

            def select_color(color, name):
                self.selected_line_color = color
                self.color_line_preview.set_color(color)
                color_dialog.dismiss()

            for rgba, name in colors:
                btn = Button(
                    background_normal='',
                    background_color=rgba,
                    size_hint=(None, None),
                    size=(50, 50),
                    on_release=lambda btn, c=rgba, n=name: select_color(c, n),
                )
                layout.add_widget(btn)

            color_dialog.open()

        line_box = BoxLayout(
            orientation='vertical',
            size_hint=(None, 1),
            width=dp(265),
            pos_hint={'right': 1, 'top': 1},
            padding=[dp(16), dp(16), dp(16), dp(16)],
            spacing=dp(12),
            opacity=0,
        )
        with line_box.canvas.before:
            Color(0, 0, 0, 0.85)
            self.rect_line = Rectangle(size=line_box.size, pos=line_box.pos)
        line_box.bind(size=self._update_rect_line, pos=self._update_rect_line)

        first_row = BoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height=dp(40),
            spacing=dp(10),
        )

        icon = MDIcon(icon="vector-polyline-plus")
        icon.size_hint = (None, None)
        icon.size = (dp(28), dp(28))
        icon.pos_hint = {'center_y': 0.5}
        first_row.add_widget(icon)

        label = Label(
            text="Creare Linie",
            size_hint_x=None,
            width=dp(150),
            halign='left',
            valign='middle',
            color=(1, 1, 1, 1),
            font_size=dp(16),
        )
        label.bind(size=lambda inst, val: setattr(inst, 'text_size', val))
        first_row.add_widget(label)

        close_btn = MDIconButton(icon="close")
        close_btn.size_hint = (None, None)
        close_btn.size = (dp(28), dp(28))
        close_btn.pos_hint = {'center_y': 0.5}
        close_btn.bind(on_release=self.close_line_panel)
        first_row.add_widget(close_btn)

        line_box.add_widget(first_row)

        self.line_description_input = MDTextField(
            hint_text="Descriere linie",
            size_hint_y=None,
            height=dp(48),
            multiline=False,
        )
        line_box.add_widget(self.line_description_input)
        second_row = BoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height=dp(40),
            spacing=dp(10),
        )

        label_culoare = Label(
            text="  Selectează culoarea liniei",
            size_hint_x=None,
            width=dp(197),
            halign='left',
            valign='middle',
            color=(1, 1, 1, 1),
            font_size=dp(16),
        )
        second_row.add_widget(label_culoare)

        arrow_btn = MDIconButton(
            icon="chevron-down",
            size_hint=(None, None),
            size=(dp(28), dp(28)),
            pos_hint={'center_y': 0.5}
        )
        arrow_btn.size_hint_x = None
        arrow_btn.width = dp(28)

        arrow_btn.bind(on_release=open_color_palette)
        second_row.add_widget(arrow_btn)
        line_box.add_widget(second_row)

        third_row = BoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height=dp(20),
            spacing=dp(1),
        )
        self.color_line_preview = ColorBox(color=self.selected_line_color)
        third_row.add_widget(self.color_line_preview)

        line_box.add_widget(third_row)

        btn_finalize = Button(text="Finalizează Linie", size_hint_y=None, height=dp(40), width=dp(200))
        btn_finalize.bind(on_release= self.finish_line)

        line_box.add_widget(BoxLayout())
        line_box.add_widget(btn_finalize)
        return line_box

    def build_polygon_box(self):

        def open_color_palette(*args):
            colors = [
                ([1, 0, 0, 0.4], "Roșu"),
                ([1, 0.5, 0, 0.4], "Portocaliu"),
                ([1, 1, 0, 0.4], "Galben"),
                ([0.5, 1, 0, 0.4], "Galben-Verzui"),
                ([0, 1, 0, 0.4], "Verde"),
                ([0, 1, 1, 0.4], "Turcoaz"),
                ([0, 0, 1, 0.4], "Albastru"),
                ([0.5, 0, 1, 0.4], "Indigo"),
                ([1, 0, 1, 0.4], "Magenta"),
                ([1, 0.75, 0.8, 0.4], "Roz"),
                ([0.5, 0.5, 0.5, 0.4], "Gri"),
                ([0.25, 0.25, 0.25, 0.4], "Gri Închis"),
                ([0.75, 0.75, 0.75, 0.4], "Gri Deschis"),
                ([0, 0, 0, 0.4], "Negru"),
                ([1, 1, 1, 0.4], "Alb"),
                ([0.8, 0.4, 0, 0.4], "Maro"),
                ([0.5, 0, 0, 0.4], "Burgundy"),
                ([0, 0.5, 0, 0.4], "Verde Închis"),
                ([0, 0, 0.5, 0.4], "Bleumarin"),
                ([0.5, 0, 0.5, 0.4], "Violet"),
                ([1, 0.84, 0, 0.4], "Auriu"),
                ([0.75, 0.75, 0, 0.4], "Măsliniu"),
                ([0.72, 0.45, 0.2, 0.4], "Cafeniu"),
                ([0.96, 0.64, 0.38, 0.4], "Piatră"),
            ]

            layout = GridLayout(cols=8, spacing=10, padding=10, size_hint_y=None)
            layout.bind(minimum_height=layout.setter("height"))

            color_dialog = MDDialog(
                title="Selectează o culoare",
                type="custom",
                content_cls=layout,
                buttons=[],
            )

            def select_color(color, name):
                self.selected_polygon_color = color
                self.color_polygon_preview.set_color(color)
                color_dialog.dismiss()

            for rgba, name in colors:
                btn = Button(
                    background_normal='',
                    background_color=rgba,
                    size_hint=(None, None),
                    size=(50, 50),
                    on_release=lambda btn, c=rgba, n=name: select_color(c, n),
                )
                layout.add_widget(btn)

            color_dialog.open()

        polygon_box = BoxLayout(
            orientation='vertical',
            size_hint=(None, 1),
            width=dp(265),
            pos_hint={'right': 1, 'top': 1},
            padding=[dp(16), dp(16), dp(16), dp(16)],
            spacing=dp(12),
            opacity=0,
        )
        with polygon_box.canvas.before:
            Color(0, 0, 0, 0.85)
            self.rect_polygon = Rectangle(size=polygon_box.size, pos=polygon_box.pos)
        polygon_box.bind(size=self._update_rect_polygon, pos=self._update_rect_polygon)

        first_row = BoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height=dp(40),
            spacing=dp(10),
        )

        icon = MDIcon(icon="shape-polygon-plus")
        icon.size_hint = (None, None)
        icon.size = (dp(28), dp(28))
        icon.pos_hint = {'center_y': 0.5}
        first_row.add_widget(icon)

        label = Label(
            text="Creare Arie",
            size_hint_x=None,
            width=dp(150),
            halign='left',
            valign='middle',
            color=(1, 1, 1, 1),
            font_size=dp(16),
        )
        label.bind(size=lambda inst, val: setattr(inst, 'text_size', val))
        first_row.add_widget(label)

        close_btn = MDIconButton(icon="close")
        close_btn.size_hint = (None, None)
        close_btn.size = (dp(28), dp(28))
        close_btn.pos_hint = {'center_y': 0.5}
        close_btn.bind(on_release=self.close_polygon_panel)
        first_row.add_widget(close_btn)

        polygon_box.add_widget(first_row)

        self.polygon_description_input = MDTextField(
            hint_text="Descriere Suprafață",
            size_hint_y=None,
            height=dp(48),
            multiline=False,
        )
        polygon_box.add_widget(self.polygon_description_input)
        second_row = BoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height=dp(40),
            spacing=dp(10),
        )

        label_culoare = Label(
            text="  Selectează culoarea ariei",
            size_hint_x=None,
            width=dp(197),
            halign='left',
            valign='middle',
            color=(1, 1, 1, 1),
            font_size=dp(16),
        )
        second_row.add_widget(label_culoare)

        arrow_btn = MDIconButton(
            icon="chevron-down",
            size_hint=(None, None),
            size=(dp(28), dp(28)),
            pos_hint={'center_y': 0.5}
        )
        arrow_btn.size_hint_x = None
        arrow_btn.width = dp(28)

        arrow_btn.bind(on_release=open_color_palette)
        second_row.add_widget(arrow_btn)
        polygon_box.add_widget(second_row)

        third_row = BoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height=dp(20),
            spacing=dp(1),
        )
        self.color_polygon_preview = ColorBox(color=self.selected_polygon_color)
        third_row.add_widget(self.color_polygon_preview)

        polygon_box.add_widget(third_row)

        polygon_box.add_widget(BoxLayout())
        return polygon_box

    def finish_line(self, *args):
        self.finalize_current_line()
        self.close_line_panel()
        self.set_mode("", "", "")

    def _update_rect_point(self, instance, value):
        self.rect_point.pos = instance.pos
        self.rect_point.size = instance.size

    def _update_rect_line(self, instance, value):
        self.rect_line.pos = instance.pos
        self.rect_line.size = instance.size

    def _update_rect_atribute(self, instance, value):
        self.rect_atribute.pos = instance.pos
        self.rect_atribute.size = instance.size

    def _update_rect_polygon(self, instance, value):
        self.rect_polygon.pos = instance.pos
        self.rect_polygon.size = instance.size

    def close_point_panel(self, *args):
        if self.point_box.parent:
            self.point_box.opacity = 0
            self.point_box.disabled = True
            self.remove_widget(self.point_box)
        self.set_mode("", "", "")

    def close_line_panel(self, *args):
        if self.line_box.parent:
            self.line_box.opacity = 0
            self.line_box.disabled = True
            self.remove_widget(self.line_box)
        self.set_mode("", "", "")

    def close_atribute_panel(self, *args):
        if self.atribute_box.parent:
            self.atribute_box.opacity = 0
            self.atribute_box.disabled = True
            self.remove_widget(self.atribute_box)
        self.set_mode("", "", "")

    def close_polygon_panel(self, *args):
        if self.polygon_box.parent:
            self.polygon_box.opacity = 0
            self.polygon_box.disabled = True
            self.remove_widget(self.polygon_box)
        self.set_mode("", "", "")

    def hide_all_vectors(self):

        if len(self.features)==0:
            print("Nu există elemente vectoriale.")
            return False
        else:
            for marker in self.points_markers:
                self.mapview.remove_marker(marker)
            self.points_markers.clear()

            for layer in self.line_layers:
                self.safe_remove_layer(layer)

            if hasattr(self, 'current_line_layer'):
                self.safe_remove_layer(self.current_line_layer)

            for layer in self.polygon_layers:
                self.safe_remove_layer(layer)

            if hasattr(self, 'current_polygon_layer'):
                self.safe_remove_layer(self.current_polygon_layer)

            for marker in self.measurements_markers:
                self.mapview.remove_marker(marker)
            self.measurements_markers.clear()

            if hasattr(self, 'measurements_line_layer'):
                self.safe_remove_layer(self.measurements_line_layer)

            print(len(self.features))
            return True

    def show_all_vectors(self):
        # redesenează punctele
        for feature in self.features:
            if feature["type"] == "Point":
                lat, lon = feature["coords"][0]
                marker = IconMarker(
                    icon_name=feature["symbol"],
                    icon_color=feature["color"],
                    lat=lat,
                    lon=lon,
                    marker_size=dp(18),
                )
                self.mapview.add_marker(marker)
                self.points_markers.append(marker)

            elif feature["type"] == "Line":
                coords = feature["coords"]

                def points_getter(coords=coords):
                    return coords

                new_layer = LineMapLayer(
                    points_getter=points_getter,
                    color=feature["color"],
                    width=feature.get("width", 2)
                )
                self.mapview.add_layer(new_layer)
                new_layer.reposition()
                self.line_layers.append(new_layer)

            elif feature["type"] == "Polygon":
                coords = feature["coords"]

                def points_getter(coords=coords):
                    return coords

                new_layer = PolygonMapLayer(
                    points_getter=points_getter,
                    color=feature["color"],
                )
                self.mapview.add_layer(new_layer)
                new_layer.reposition()
                self.polygon_layers.append(new_layer)

        # readaugă layer-urile curente (pentru editare)
        if self.current_line_layer and self.current_line_layer not in self.mapview._layers:
            self.mapview.add_layer(self.current_line_layer)

        if self.current_polygon_layer and self.current_polygon_layer not in self.mapview._layers:
            self.mapview.add_layer(self.current_polygon_layer)

        if self.measurements_line_layer and self.measurements_line_layer not in self.mapview._layers:
            self.mapview.add_layer(self.measurements_line_layer)

    def on_select_tap(self, mapview, touch):
        if self.mode != "select":
            return False

        lat, lon = mapview.get_latlon_at(touch.x, touch.y)

        # verifică întâi punctele
        for marker in self.points_markers:
            if self.is_point_near_marker(lat, lon, marker, tolerance_px=30):
                print("Ai selectat un punct!")
                self.highlight_feature(marker)
                return True

        # verifică linii
        for layer in self.line_layers:
            if self.is_point_near_line(lat, lon, layer.points_getter()):
                print("Ai selectat o linie!")
                self.highlight_feature(layer)
                return True

        # verifică poligoane
        for layer in self.polygon_layers:
            if self.is_point_in_polygon(lat, lon, layer.points_getter()):
                print("Ai selectat un poligon!")
                self.highlight_feature(layer)
                return True

        print("Nu ai selectat nimic.")
        return False

    def is_point_near_line(self, lat, lon, line_coords, tolerance=0.0005):
        for i in range(len(line_coords) - 1):
            p1 = line_coords[i]
            p2 = line_coords[i + 1]
            if self.point_near_segment(lat, lon, p1, p2, tolerance):
                return True
        return False

    def point_near_segment(self, lat, lon, p1, p2, tolerance):
        # calculează distanța minimă de la punct la segment
        from math import hypot

        x, y = lon, lat
        x1, y1 = p1[1], p1[0]
        x2, y2 = p2[1], p2[0]

        dx = x2 - x1
        dy = y2 - y1

        if dx == dy == 0:
            return hypot(x - x1, y - y1) < tolerance

        t = ((x - x1) * dx + (y - y1) * dy) / (dx * dx + dy * dy)
        t = max(0, min(1, t))
        proj_x = x1 + t * dx
        proj_y = y1 + t * dy

        dist = hypot(x - proj_x, y - proj_y)
        return dist < tolerance

    def is_point_in_polygon(self, lat, lon, polygon_coords):
        from shapely.geometry import Point, Polygon
        poly = Polygon([(p[1], p[0]) for p in polygon_coords])
        return poly.contains(Point(lon, lat))

    def is_point_near_marker(self, lat, lon, marker, tolerance_px=10):
        marker_px = self.mapview.get_window_xy_from(lat=marker.lat, lon=marker.lon, zoom=self.mapview.zoom)
        tap_px = self.mapview.get_window_xy_from(lat=lat, lon=lon, zoom=self.mapview.zoom)

        dist_x = abs(marker_px[0] - tap_px[0])
        dist_y = abs(marker_px[1] - tap_px[1])

        return (dist_x ** 2 + dist_y ** 2) ** 0.5 < tolerance_px

    def highlight_feature(self, feature_obj):
        light_blue = [0.094, 0.89, 1, 1] # albastru deschis

        if isinstance(feature_obj, IconMarker):
            if not hasattr(feature_obj, "original_color"):
                feature_obj.original_color = feature_obj.icon_widget.text_color[:]
            feature_obj.icon_widget.text_color = light_blue
            feature_obj.icon_widget.canvas.ask_update()
        else:
            if not hasattr(feature_obj, "original_color"):
                feature_obj.original_color = feature_obj.color[:]
            feature_obj.color = light_blue
            feature_obj.reposition()

        if feature_obj not in self.selected_features:
            self.selected_features.append(feature_obj)

    def clear_selection(self):
        if self.selected_features:
            for feature_obj in self.selected_features:
                if isinstance(feature_obj, IconMarker):
                    if hasattr(feature_obj, "original_color"):
                        feature_obj.icon_widget.theme_text_color = "Custom"
                        feature_obj.icon_widget.text_color = feature_obj.original_color  # ← aici e modificarea corectă
                        feature_obj.icon_widget.canvas.ask_update()
                else:
                    if hasattr(feature_obj, "original_color"):
                        feature_obj.color = feature_obj.original_color
                        feature_obj.reposition()

            print("Toate selecțiile au fost anulate.")
            self.selected_features.clear()
            self.set_mode("", "", "")
        else:
            return None

    def open_atribute_table(self):

        def open_color_palette(*args):
            colors = [
                ([1, 0, 0, 1], "Roșu"),
                ([1, 0.5, 0, 1], "Portocaliu"),
                ([1, 1, 0, 1], "Galben"),
                ([0.5, 1, 0, 1], "Galben-Verzui"),
                ([0, 1, 0, 1], "Verde"),
                ([0, 1, 1, 1], "Turcoaz"),
                ([0, 0, 1, 1], "Albastru"),
                ([0.5, 0, 1, 1], "Indigo"),
                ([1, 0, 1, 1], "Magenta"),
                ([1, 0.75, 0.8, 1], "Roz"),
                ([0.5, 0.5, 0.5, 1], "Gri"),
                ([0.25, 0.25, 0.25, 1], "Gri Închis"),
                ([0.75, 0.75, 0.75, 1], "Gri Deschis"),
                ([0, 0, 0, 1], "Negru"),
                ([1, 1, 1, 1], "Alb"),
                ([0.8, 0.4, 0, 1], "Maro"),
                ([1, 0, 0, 0.5], "Burgundy"),
                ([0, 1, 0, 0.5], "Verde"),
                ([0, 0, 0.5, 1], "Bleumarin"),
                ([0.5, 0, 0.5, 1], "Violet"),
                ([1, 0.84, 0, 1], "Auriu"),
                ([0.75, 0.75, 0, 1], "Măsliniu"),
                ([0.72, 0.45, 0.2, 1], "Cafeniu"),
                ([0.96, 0.64, 0.38, 1], "Piatră"),
            ]

            layout = GridLayout(cols=8, spacing=10, padding=10, size_hint_y=None)
            layout.bind(minimum_height=layout.setter("height"))

            color_dialog = MDDialog(
                title="Selectează o culoare",
                type="custom",
                content_cls=layout,
                buttons=[],
            )

            def select_color(color, name):
                self.selected_atribute_color = color
                self.color_atribute_preview.set_color(color)
                color_dialog.dismiss()
                print(self.selected_atribute_color)

            for rgba, name in colors:
                btn = Button(
                    background_normal='',
                    background_color=rgba,
                    size_hint=(None, None),
                    size=(50, 50),
                    on_release=lambda btn, c=rgba, n=name: select_color(c, n),
                )
                layout.add_widget(btn)

            color_dialog.open()

        atribute_box = BoxLayout(
            orientation='vertical',
            size_hint=(None, 1),
            width=dp(265),
            pos_hint={'right': 1, 'top': 1},
            padding=[dp(16), dp(16), dp(16), dp(16)],
            spacing=dp(12),
            opacity=0,
        )
        with atribute_box.canvas.before:
            Color(0, 0, 0, 0.85)
            self.rect_atribute = Rectangle(size=atribute_box.size, pos=atribute_box.pos)
        atribute_box.bind(size=self._update_rect_atribute, pos=self._update_rect_atribute)

        first_row = BoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height=dp(40),
            spacing=dp(10),
        )

        icon = MDIcon(icon="table-large")
        icon.size_hint = (None, None)
        icon.size = (dp(28), dp(28))
        icon.pos_hint = {'center_y': 0.5}
        first_row.add_widget(icon)

        label = Label(
            text="Modifică atribute",
            size_hint_x=None,
            width=dp(150),
            halign='left',
            valign='middle',
            color=(1, 1, 1, 1),
            font_size=dp(16),
        )
        label.bind(size=lambda inst, val: setattr(inst, 'text_size', val))
        first_row.add_widget(label)

        close_btn = MDIconButton(icon="close")
        close_btn.size_hint = (None, None)
        close_btn.size = (dp(28), dp(28))
        close_btn.pos_hint = {'center_y': 0.5}
        close_btn.bind(on_release=self.close_atribute_panel)
        first_row.add_widget(close_btn)

        atribute_box.add_widget(first_row)

        second_row = BoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height=dp(40),
            spacing=dp(10),
        )

        label_culoare = Label(
            text="  Selectează culoarea ",
            size_hint_x=None,
            width=dp(197),
            halign='left',
            valign='middle',
            color=(1, 1, 1, 1),
            font_size=dp(16),
        )
        second_row.add_widget(label_culoare)

        arrow_btn = MDIconButton(
            icon="chevron-down",
            size_hint=(None, None),
            size=(dp(28), dp(28)),
            pos_hint={'center_y': 0.5}
        )
        arrow_btn.size_hint_x = None
        arrow_btn.width = dp(28)

        arrow_btn.bind(on_release=open_color_palette)
        second_row.add_widget(arrow_btn)
        atribute_box.add_widget(second_row)

        third_row = BoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height=dp(20),
            spacing=dp(1),
        )
        self.color_atribute_preview = ColorBox(color=self.selected_atribute_color)
        third_row.add_widget(self.color_atribute_preview)

        atribute_box.add_widget(third_row)

        btn_finalize = Button(text="Finalizează modificările", size_hint_y=None, height=dp(40), width=dp(200))
        btn_finalize.bind(on_release= self.update_color)

        atribute_box.add_widget(BoxLayout())
        atribute_box.add_widget(btn_finalize)
        return atribute_box

    def update_color(self, *args):
        # Schimbă elementele vizual
        for feature_obj in self.selected_features:
            if isinstance(feature_obj, IconMarker):
                feature_obj.icon_widget.text_color = self.selected_atribute_color
                feature_obj.original_color = self.selected_atribute_color[:]  # noul original
                feature_obj.icon_widget.canvas.ask_update()
            else:
                feature_obj.color = self.selected_atribute_color
                feature_obj.original_color = self.selected_atribute_color[:]  # noul original
                feature_obj.reposition()

        # Schimbă și în self.features
        for feature_obj in self.selected_features:
            for feature in self.features:
                if feature["type"] == "Point" and isinstance(feature_obj, IconMarker):
                    if feature_obj.lat == feature["coords"][0][0] and feature_obj.lon == feature["coords"][0][1]:
                        feature["color"] = self.selected_atribute_color[:]
                        break
                elif feature["type"] == "Line" and not isinstance(feature_obj, IconMarker):
                    if feature_obj.points_getter() == feature["coords"]:
                        feature["color"] = self.selected_atribute_color[:]
                        break
                elif feature["type"] == "Polygon" and not isinstance(feature_obj, IconMarker):
                    if feature_obj.points_getter() == feature["coords"]:
                        feature["color"] = self.selected_atribute_color[:]
                        break

    def delete_elements(self, *args):
        # Mai întâi ștergem obiectele de pe hartă
        for feature_obj in self.selected_features:
            if isinstance(feature_obj, IconMarker):
                if feature_obj in self.points_markers:
                    self.points_markers.remove(feature_obj)
                self.mapview.remove_marker(feature_obj)
            else:
                if feature_obj in self.line_layers:
                    self.line_layers.remove(feature_obj)
                elif feature_obj in self.polygon_layers:
                    self.polygon_layers.remove(feature_obj)
                self.mapview.remove_layer(feature_obj)

        # Apoi ștergem din self.features
        to_remove = []

        for feature_obj in self.selected_features:
            for feature in self.features:
                if feature["type"] == "Point" and isinstance(feature_obj, IconMarker):
                    if feature_obj.lat == feature["coords"][0][0] and feature_obj.lon == feature["coords"][0][1]:
                        to_remove.append(feature)
                        break
                elif feature["type"] == "Line" and not isinstance(feature_obj, IconMarker):
                    if feature_obj.points_getter() == feature["coords"]:
                        to_remove.append(feature)
                        break
                elif feature["type"] == "Polygon" and not isinstance(feature_obj, IconMarker):
                    if feature_obj.points_getter() == feature["coords"]:
                        to_remove.append(feature)
                        break

        for feature in to_remove:
            self.features.remove(feature)

        # Golește lista de selecții
        self.selected_features.clear()

        print("Elementele selectate au fost șterse.")
