from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.textfield import MDTextField

class JoinTeamContent(MDBoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.spacing = dp(5)
        self.size_hint_y = None

        # Creează cele două câmpuri de text
        self.team_id_input = MDTextField(
            hint_text="team id",
            size_hint_y=None,
            height=dp(48),
        )
        self.user_id_input = MDTextField(
            hint_text="user id",
            size_hint_y=None,
            height=dp(48),
        )

        # Adaugă câmpurile în layout
        self.add_widget(self.team_id_input)
        self.add_widget(self.user_id_input)

        # Setează înălțimea totală în funcție de widgeturi și spațiere
        total_height = self.team_id_input.height + self.user_id_input.height + self.spacing
        self.height = total_height