class Theme:
    def __init__(self, color, fillcolor, fillcolorC, bgcolor, icolor, tcolor, style, shape, pencolor, penwidth):
        self.color = color
        self.fillcolor = fillcolor
        self.fillcolorC = fillcolorC
        self.bgcolor = bgcolor
        self.icolor = icolor
        self.tcolor = tcolor
        self.style = style
        self.shape = shape
        self.pencolor = pencolor
        self.penwidth = penwidth

    @staticmethod
    def get_theme(name):
        themes = {
            "Common Gray": Theme("#6c6c6c", "#e0e0e0", "#f5f5f5", "#e0e0e0", "#000000", "#000000", "rounded", "Mrecord", "#696969", "1"),
            "Blue Navy": Theme("#1a5282", "#1a5282", "#ffffff", "#1a5282", "#000000", "#ffffff", "rounded", "Mrecord", "#0078d7", "2")
        }
        return themes[name]