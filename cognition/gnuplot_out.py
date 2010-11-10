# gnuplot_out.py
# output functions for generating graphs with Gnuplot

import Gnuplot

def output(data, x_label="x_label", y_label="y_label", filename = "gnuplot_output"):
    """ data format = [ [data, x_title], [data, x_title]]
        function supports up to 10 data sets
    """
    gp = Gnuplot.Gnuplot(persist = 1)
    gp('set data style lines')
    gp('set key right bottom')
    x_string = 'set xlabel " %s"' % x_label
    y_string = 'set ylabel " %s"' % y_label
    gp(x_string)
    gp(y_string)
    gp('set ytics 0.1')
    gp('set yrange [0.0:1.0]')
    plots = []
    for i in data:
        x_title = i[1]
        output = []
        for x, j in enumerate(i[0]):
            output.append([x, j])
        plots.append(Gnuplot.PlotItems.Data(output, with_="lines", title=x_title))
        
    if len(plots) == 1:
        gp.plot(plots[0])
    if len(plots) == 2:
        gp.plot(plots[0], plots[1])
    if len(plots) == 3:
        gp.plot(plots[0], plots[1], plots[2])
    if len(plots) == 4:
        gp.plot(plots[0], plots[1], plots[2], plots[3])
    if len(plots) == 5:
        gp.plot(plots[0], plots[1], plots[2], plots[3], plots[4])
    if len(plots) == 6:
        gp.plot(plots[0], plots[1], plots[2], plots[3], plots[4], plots[5])
    if len(plots) == 7:
        gp.plot(plots[0], plots[1], plots[2], plots[3], plots[4], plots[5], plots[6])
    if len(plots) == 8:
        gp.plot(plots[0], plots[1], plots[2], plots[3], plots[4], plots[5], plots[6], plots[7])
    if len(plots) == 9:
        gp.plot(plots[0], plots[1], plots[2], plots[3], plots[4], plots[5], plots[6], plots[7], plots[8])
    if len(plots) == 10:
        gp.plot(plots[0], plots[1], plots[2], plots[3], plots[4], plots[5], plots[6], plots[7], plots[8], plots[9])
    gp.hardcopy(filename + '.ps', color=True)