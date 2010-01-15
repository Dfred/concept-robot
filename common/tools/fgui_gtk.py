import pygtk
pygtk.require('2.0')
import gtk


class FeederGui:
    """GTK interface presenting sliders"""

    def quit():
        self.quit = True
        self.main_loop and gtk.main_quit()

    def delete_event(self, widget, event, data=None):
        self.quit = True
        self.main_loop and gtk.main_quit()
        return False
    
    def value_changed(self, get, esink):
        sink = self.sinks[get]
        esink.update(sink[0], sink[1].value)

    def set_title(self, title):
        self.window.set_title = title

    def __init__(self, esink, title):
        self.sinks = {}
        self.quit = False
        self.main_loop = None
        
        self.window = gtk.Window(gtk.WINDOW_TOPLEVEL,)
        self.window.set_title(title)
        self.window.connect("delete_event", self.delete_event)
        self.window.set_size_request(640,480)
        
        self.hbox = gtk.HBox(True, 0)
        self.window.add(self.hbox)
        for name, value in esink.sinks.iteritems():
            vbox = gtk.VBox(False, 0)
            label = gtk.Label(name)
            vbox.pack_start(label, False,False, 0)
            label.show()
            
            adjust = gtk.Adjustment(value, 0, 1, .01, .1)
            slider = gtk.VScale(adjust)
            slider.connect("value_changed", self.value_changed, esink)
            vbox.pack_start(slider, True, True, 0)
            slider.show()
            slider.set_digits(3)
            self.sinks[slider] = (name, adjust)

            self.hbox.pack_start(vbox)
            vbox.show()

        self.hbox.show()
        self.window.show()

    def run(self):
        self.main_loop = True
        return gtk.main()

    def iterate(self, blocking=False):
        self.main_loop = blocking
        return gtk.main_iteration(blocking)
