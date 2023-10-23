class GuiConstants(object):
    def __init__(self, path):
        self.screen_scaling = self.__get_screen_scaling(path)
        self.police_sizes = self.__get_police_sizes()
        (self.color_set,
         self.color_error) = self.__get_colors()
        self.window_size = self.__get_window_size()
        
    def __get_screen_scaling(self, path):
        with open(path) as config:
            lines = config.readlines()
            screen_scaling = lines[1].split("\t")[1][:-1]
            screen_scaling = float(screen_scaling)
        return screen_scaling
    
    def __get_police_sizes(self):
        size_l=int(56/self.screen_scaling)
        size_s=int(36/self.screen_scaling)
        size_xs=int(24/self.screen_scaling)
        return size_l, size_s, size_xs
    
    def __get_colors(self):
        color_error="#EC7063"
        color_set=['#e3e4e7','#ffffff','#d9d9d9']
        return color_set, color_error
    
    def __get_window_size(self):
        w = int( 2400 / self.screen_scaling )
        h = int( 1270 / self.screen_scaling )
        return [w, h]
