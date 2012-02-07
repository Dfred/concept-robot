###################################################################
# gui_main.py                                                     #
#                                                                 #
# The CONCEPT project. University of Plymouth, United Kingdom     #
# More information at http://www.tech.plym.ac.uk/SoCCE/CONCEPT/   #
#                                                                 #
# Copyright (C) 2011 Joachim de Greeff (www.joachimdegreeff.eu)   #
#                                                                 #
# This program is free software: you can redistribute it and/or   #
# modify it under the terms of the GNU General Public License as  # 
# published by the Free Software Foundation, either version 3 of  #
# the License, or (at your option) any later version.             #
#                                                                 #
# This program is distributed in the hope that it will be useful, #
# but WITHOUT ANY WARRANTY; without even the implied warranty of  #
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the    # 
# GNU General Public License for more details.                    #
###################################################################


import cfg, vision


if __name__ == "__main__":
    vis = vision.Vision(cfg.use_gui)
    vis.start_camera()


