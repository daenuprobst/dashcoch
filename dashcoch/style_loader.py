class StyleLoader:
    def __init__(self):
        self.colors = [
            "#7a8871",
            "#a359e3",
            "#91e63f",
            "#dd47ba",
            "#5ad358",
            "#6e7edc",
            "#d9dd3d",
            "#c376bc",
            "#a8cc5f",
            "#d95479",
            "#63de9f",
            "#de4f37",
            "#74deda",
            "#dd892d",
            "#71adcf",
            "#dbbd59",
            "#797ca6",
            "#4e9648",
            "#d4b7d8",
            "#8a873d",
            "#489889",
            "#b1743d",
            "#a8d5a2",
            "#a87575",
            "#d6cead",
            "#e59780",
        ]

        self.color_scale = [
            "#f2fffb",
            "#bbffeb",
            "#98ffe0",
            "#79ffd6",
            "#6df0c8",
            "#69e7c0",
            "#59dab2",
            "#45d0a5",
            "#31c194",
            "#2bb489",
            "#25a27b",
            "#1e906d",
            "#188463",
            "#157658",
            "#11684d",
            "#10523e",
        ]

        self.canton_colors = {
            "AG": "#87ceeb",
            "AI": "#57606f",
            "AR": "#57606f",
            "BE": "#EE5A24",
            "BL": "#e9403c",
            "BS": "#F8EFBA",
            "FR": "#ffffff",
            "GE": "#ffd134",
            "GL": "#B53471",
            "GR": "#eccc68",
            "JU": "#6D214F",
            "LU": "#258bcc",
            "NE": "#17a74e",
            "NW": "#e7423e",
            "OW": "#D980FA",
            "SG": "#17a74e",
            "SH": "#ffd829",
            "SO": "#e8423f",
            "SZ": "#ff0000",
            "TG": "#12CBC4",
            "TI": "#0271ac",
            "UR": "#ffd72e",
            "VD": "#007f01",
            "VS": "#e8423f",
            "ZG": "#278bcc",
            "ZH": "#0abde3",
        }

        self.theme = {
            "background": "#252e3f",
            "background_secondary": "#402C36",
            "foreground": "#2cfec1",
            "foreground_secondary": "#F2EB80",
            "accent": "#7fafdf",
            "accent_secondary": "#de95ce",
            "red": "#fc5c65",
            "yellow": "#fed330",
            "blue": "#45aaf2",
        }

        self.turbo = self.get_turbo()

    def get_turbo(self):
        scale = [
            "#2D384D",
            "#DB4453",
        ]

        return [(x / (len(scale) - 1), s) for x, s, in enumerate(scale)]
