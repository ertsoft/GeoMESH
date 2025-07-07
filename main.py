import requests
from kivy.uix.floatlayout import FloatLayout
from kivymd.app import MDApp
from kivy.lang import Builder
from kivymd.uix.button import MDFlatButton
from kivymd.uix.dialog import MDDialog
from kivymd.uix.textfield import MDTextField
from basemap_container import Basemap_Container
from change_basemap_btn import SwitchBasemap
from join_team import JoinTeamContent
import asyncio


class MainApp(MDApp):
    dialog = None
    join_dialog = None

    def build(self):
        self.vectors_hidden = False

        self.theme_cls.theme_style = "Dark"
        self.theme_cls.primary_palette = "BlueGray"
        self.root = FloatLayout()
        self.nav_drawer = Builder.load_file("nav_drawer.kv")
        self.root.add_widget(self.nav_drawer)
        self.basemap_container = Basemap_Container() # basemap initial

        #trebuie salvata o instanta a clasei, pentru a fi apelata in .kv, nu poate fi apelata clasa direct
        self.switch_basemap = SwitchBasemap(self.basemap_container)

        main_box = self.nav_drawer .ids.main_box
        main_box.add_widget(self.basemap_container)

        #pentru masurararea pe harta
        self.measuring_enabled = False
        self.basemap_container.measuring_enabled = False

        # dezactivare butoane pt editare
        self.stop_edit()

        return self.root

    def open_basemap(self):
         self.switch_basemap.open_basemap_popup()

    def create_new_team(self):
        if not self.dialog:
            self.team_name_input = MDTextField(
                hint_text="Numele echipei",
                helper_text="Introduceți un nume unic",
                helper_text_mode="on_focus",
                max_text_length=30,
                pos_hint={"center_x": 0.5},
                size_hint_x=0.8,
            )
            self.team_name_input.foreground_color = (1, 1, 1, 1)  # text alb
            self.team_name_input.hint_text_color = (1, 1, 1, 0.6)

            self.dialog = MDDialog(
                title="Creează echipă nouă",
                type="custom",
                content_cls=self.team_name_input,
                buttons=[
                    MDFlatButton(text="ANULEAZĂ", on_release=self.close_dialog),
                    MDFlatButton(text="CREAZĂ", on_release=self.create_team_btn_func),
                ],
            )
        self.dialog.open()

    def close_dialog(self, *args):
        self.dialog.dismiss()

    def create_team_btn_func(self, *args):
        team_id = self.team_name_input.text.strip()
        if not team_id:
            self.team_name_input.error = True
            self.team_name_input.helper_text = "Numele echipei nu poate fi gol"
            return

        self.team_name_input.error = False

        server_ip = "http://192.168.0.200:8000"

        url = f"{server_ip}/create_team/{team_id}"
        try:
            response = requests.post(url)
            if response.status_code == 200:
                data = response.json()
                if "error" in data:
                    if data["error"] == "Team already exists":
                        self.show_message_dialog("Echipa există deja.")
                    else:
                        self.show_message_dialog(f"Eroare server: {data['error']}")
                else:
                    self.show_message_dialog(data["message"])
            else:
                self.show_message_dialog(f"Eroare HTTP: {response.status_code}")
        except Exception as e:
            self.show_message_dialog(f"Nu s-a putut conecta la server: {e}")
        finally:
            self.dialog.dismiss()

    def show_message_dialog(self, message):
        dialog = MDDialog(
            title="Info",
            text=message,
            buttons=[MDFlatButton(text="OK", on_release=lambda x: dialog.dismiss())],
        )
        dialog.open()

    def join_team(self):
        if not hasattr(self, 'join_dialog') or self.join_dialog is None:
            self.join_content = JoinTeamContent()

            self.join_dialog = MDDialog(
                title="Alătură-te unei echipe\n",
                type="custom",
                content_cls=self.join_content,
                buttons=[
                    MDFlatButton(text="ANULEAZĂ", on_release=self.close_join_dialog),
                    MDFlatButton(text="ALĂTURĂ-TE", on_release=self.join_team_btn_func),
                ],
            )
        self.join_dialog.open()

    def close_join_dialog(self, *args):
        if self.join_dialog:
            self.join_dialog.dismiss()

    def join_team_btn_func(self, *args):
        team_id = self.join_content.team_id_input.text.strip()
        user_id = self.join_content.user_id_input.text.strip()

        if not team_id:
            self.join_content.team_id_input.error = True
            self.join_content.team_id_input.helper_text = "ID-ul echipei nu poate fi gol"
            return
        else:
            self.join_content.team_id_input.error = False

        if not user_id:
            self.join_content.user_id_input.error = True
            self.join_content.user_id_input.helper_text = "ID-ul utilizatorului nu poate fi gol"
            return
        else:
            self.join_content.user_id_input.error = False

        server_ip = "http://192.168.0.200:8000"
        url = f"{server_ip}/join_team/{team_id}"
        params = {"user_id": user_id}

        try:
            response = requests.post(url, params=params)
            if response.status_code == 200:
                data = response.json()
                if "error" in data:
                    self.show_message_dialog(f"Eroare server: {data['error']}")
                else:
                    self.show_message_dialog(f"{data['message']}\n(ID utilizator: {user_id})")

                    connection_icon = self.nav_drawer.ids.connection_icon
                    connection_label = self.nav_drawer.ids.connection_label

                    connection_icon.text_color = (0, 1, 0, 1)
                    connection_label.text = f"{team_id} - {user_id}"

            elif response.status_code == 404:
                self.show_message_dialog("Echipa nu există.")
            else:
                self.show_message_dialog(f"Eroare HTTP: {response.status_code}")
        except Exception as e:
            self.show_message_dialog(f"Nu s-a putut conecta la server: {e}")
        finally:
            self.join_dialog.dismiss()

    def deconecteaza(self):
        connection_label = self.nav_drawer.ids.connection_label
        # connection_icon = self.nav_drawer.ids.connection_icon

        # Verificăm dacă este conectat (presupunem că textul default e „Neconectat”)
        if connection_label.text.strip().lower() == "neconectat":
            self.show_message_dialog("Nu ești conectat/conectată")
            return

        self.logout_dialog = MDDialog(
            title="Confirmare",
            text="Sigur vrei să părăsești echipa ?",
            buttons=[
                MDFlatButton(
                    text="ANULEAZĂ",
                    on_release=lambda x: self.logout_dialog.dismiss()
                ),
                MDFlatButton(
                    text="OK",
                    on_release=lambda x: self.confirm_logout()
                ),
            ],
        )
        self.logout_dialog.open()

    def confirm_logout(self):
        # Restare UI
        connection_label = self.nav_drawer.ids.connection_label
        connection_icon = self.nav_drawer.ids.connection_icon

        connection_label.text = "Neconectat"
        connection_icon.text_color = (1, 0, 0, 1)  # roșu
        self.logout_dialog.dismiss()

        # Confirmare deconectare
        self.show_message_dialog("Te-ai deconectat cu succes.")

    def zoom_in(self):
        if hasattr(self, "basemap_container"):
            # Apelăm metoda zoom_in din Basemap_Container
            self.basemap_container.zoom_in()

    def zoom_out(self):
        if hasattr(self, "basemap_container"):
            # Apelăm metoda zoom_out din Basemap_Container
            self.basemap_container.zoom_out()

    def measure(self):
        if hasattr(self, 'basemap_container'):
            self.basemap_container.measure()

    def create_point(self):
        if hasattr(self, 'basemap_container'):
            current_team_id = self.join_content.team_id_input.text.strip()
            current_user_id = self.join_content.user_id_input.text.strip()
            self.basemap_container.set_mode("point", current_user_id, current_team_id)

    def create_line(self):
        if hasattr(self, 'basemap_container'):
            current_team_id = self.join_content.team_id_input.text.strip()
            current_user_id = self.join_content.user_id_input.text.strip()
            self.basemap_container.set_mode("line", current_user_id, current_team_id)

    def create_polygon(self):
        if hasattr(self, 'basemap_container'):
            current_team_id = self.join_content.team_id_input.text.strip()
            current_user_id = self.join_content.user_id_input.text.strip()
            self.basemap_container.set_mode("polygon", current_user_id, current_team_id)

    def start_edit(self):
        if self.nav_drawer.ids.connection_label.text == "Neconectat":
            return self.show_message_dialog("Trebuie să fii conectat la o echipă ca să începi editarea.")
        else:
            self.nav_drawer.ids.btn_start_edit.disabled = True
            self.nav_drawer.ids.btn_start_edit.opacity = 0.5

            self.nav_drawer.ids.btn_point.disabled = False
            self.nav_drawer.ids.btn_point.opacity = 1

            self.nav_drawer.ids.btn_line.disabled = False
            self.nav_drawer.ids.btn_line.opacity = 1

            self.nav_drawer.ids.btn_polygon.disabled = False
            self.nav_drawer.ids.btn_polygon.opacity = 1

            self.nav_drawer.ids.btn_stop_edit.disabled = False
            self.nav_drawer.ids.btn_stop_edit.opacity = 1

    def stop_edit(self):
        self.nav_drawer.ids.btn_start_edit.disabled = False
        self.nav_drawer.ids.btn_start_edit.opacity = 1

        self.nav_drawer.ids.btn_point.disabled = True
        self.nav_drawer.ids.btn_point.opacity = 0.5

        self.nav_drawer.ids.btn_line.disabled = True
        self.nav_drawer.ids.btn_line.opacity = 0.5

        self.nav_drawer.ids.btn_polygon.disabled = True
        self.nav_drawer.ids.btn_polygon.opacity = 0.5

        self.nav_drawer.ids.btn_stop_edit.disabled = True
        self.nav_drawer.ids.btn_stop_edit.opacity = 0.5

        self.basemap_container.set_mode("", "", "")

    def toggle_vectors(self, *args):
        if hasattr(self, 'basemap_container'):
            btn = self.nav_drawer.ids.btn_hide_vectors

            if not self.vectors_hidden:
                # Ascunde vectorii
                result = self.basemap_container.hide_all_vectors()
                if result is False:
                    self.show_message_dialog("Nu există elemente vectoriale.")
                    return
                btn.icon = "eye"
                self.vectors_hidden = True
            else:
                # Arată vectorii
                self.basemap_container.show_all_vectors()
                btn.icon = "eye-off"
                self.vectors_hidden = False

    def find_my_location(self):pass
    def find_user(self): pass

    def delete_elements(self, *args):
        if hasattr(self, "basemap_container"):
            self.basemap_container.delete_elements()

            #dezactiveaza butonul de DELETE
            btn_delete = self.nav_drawer.ids.btn_delete
            btn_delete.theme_text_color = "Custom"
            btn_delete.text_color = [0.5, 0.5, 0.5, 1]

            #dezactiveaza selectarea
            btn_select = self.nav_drawer.ids.btn_select_vector
            btn_select.theme_text_color = "Custom"
            btn_select.text_color = [1, 1, 1, 1]

            #dezactiveaza butonul de CLEAR
            btn_clear = self.nav_drawer.ids.btn_clear_selections
            btn_clear.theme_text_color = "Custom"
            btn_clear.text_color = [0.5, 0.5, 0.5, 1]

    def open_atribute_table(self, *args):
        if hasattr(self, "basemap_container"):
            if not self.basemap_container.selected_features:
                self.show_message_dialog("Nu există elemente selectate.")
                return
            self.basemap_container.set_mode("atribute", "", "")

    def select_element(self, *args):
        if hasattr(self, 'basemap_container'):
            if self.basemap_container.features:
                self.basemap_container.set_mode("select", "", "")
                btn_select = self.nav_drawer.ids.btn_select_vector
                btn_select.theme_text_color = "Custom"
                btn_select.text_color = [0, 1, 0, 1] #albastru deschis

                btn_clear = self.nav_drawer.ids.btn_clear_selections
                btn_clear.theme_text_color = "Custom"
                btn_clear.text_color = [1, 1, 1, 1]

                # dezactiveaza butonul de DELETE
                btn_delete = self.nav_drawer.ids.btn_delete
                btn_delete.theme_text_color = "Custom"
                btn_delete.text_color = [1,1,1,1]

            else:
                self.show_message_dialog("Nu există elemente vectoriale pentru a fi selectate.")

    def clear_selection(self, *args):
        if hasattr(self, 'basemap_container'):
            self.basemap_container.clear_selection()

            btn_select = self.nav_drawer.ids.btn_select_vector
            btn_select.theme_text_color = "Custom"
            btn_select.text_color = [1, 1, 1, 1]

            btn_clear = self.nav_drawer.ids.btn_clear_selections
            btn_clear.theme_text_color = "Custom"
            btn_clear.text_color = [0.5, 0.5, 0.5, 1]

            # dezactiveaza butonul de DELETE
            btn_delete = self.nav_drawer.ids.btn_delete
            btn_delete.theme_text_color = "Custom"
            btn_delete.text_color = [0.5, 0.5, 0.5, 1]

    def switch_layereee(self):pass

if __name__ == '__main__':
    MainApp().run()


