class GuiConstants(object):
    def __init__(self, path):
        self.screen_scaling = self.__get_screen_scaling(path)
        self.fonts = self.__get_fonts()
        (self.color_set,
         self.color_error) = self.__get_colors()
        self.window_size = self.__get_window_size()
        
    def __get_screen_scaling(self, path):
        with open(path) as config:
            lines = config.readlines()
            screen_scaling = lines[1].split("\t")[1][:-1]
            screen_scaling = float(screen_scaling)
        return screen_scaling
    
    def __get_fonts(self):
        size_l=int(56/self.screen_scaling)
        size_s=int(36/self.screen_scaling)
        size_xs=int(24/self.screen_scaling)

        font_l  = ( 'helvetica', size_l  )
        font_s  = ( 'helvetica', size_s  )
        font_xs = ( 'helvetica', size_xs )

        return { "l": font_l, "s": font_s, "xs": font_xs }
    
    def __get_colors(self):
        color_error="#EC7063"
        color_set=['#e3e4e7','#ffffff','#d9d9d9']
        return color_set, color_error
    
    def __get_window_size(self):
        w = int( 2400 / self.screen_scaling )
        h = int( 1270 / self.screen_scaling )
        return [w, h]

class ScopeConstants(object):
    def __init__(self, path):
        self.nosepieces=["5x","10x","20x","50x","100x"]
        self.overlap = self.__get_overlap(path)
        self.field_of_view = self.__get_fieldofview(path)
        
        self.factors=[1,2,4,10,20]
        self.step_focus = [3,4,5,6,7]
    
    def __get_overlap(self, path):
        with open(path) as config:
            lines = config.readlines()
            screen_scaling = lines[1].split("\t")[1][:-1]
            screen_scaling = float(screen_scaling)
        return screen_scaling

    def __get_fieldofview(self, path):
        with open(path) as config:
            lines = config.readlines()
            line = lines[3].strip()
            line = line.split("\t")
            field_of_view_w = float(line[1])
            field_of_view_h = float(line[2])
        
        field_of_view = [field_of_view_w*(1-self.overlap),
                        field_of_view_h*(1-self.overlap)]

        return field_of_view

class VariablesStore(object):
    def __init__(self):
        self.stitching_running = False
        self.hunting_running = False
        self.stitch_counter = 0
        self.hunt_counter = 0
