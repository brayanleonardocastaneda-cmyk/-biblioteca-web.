from django import forms
from .models import Escenario


class EscenarioForm(forms.ModelForm):
    class Meta:
        model = Escenario
        fields = ['nombre', 'deporte', 'superficie', 'precio_hora', 'ubicacion',
                  'descripcion', 'reglas', 'servicios']
        widgets = {
            'descripcion': forms.Textarea(attrs={'rows': 3}),
            'reglas': forms.Textarea(attrs={'rows': 2}),
            'servicios': forms.CheckboxSelectMultiple,
        }
        labels = {
            'precio_hora': 'Precio por hora',
            'ubicacion': 'Ubicación',
            'descripcion': 'Descripción detallada',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['deporte'].choices = Escenario.DEPORTES  # sin la opción vacía: Fútbol por defecto
        for nombre, campo in self.fields.items():
            if nombre != 'servicios':
                campo.widget.attrs['class'] = 'input'
