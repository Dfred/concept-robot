from utils import

UTTERANCES = join(dirname(__file__),'./performance.txt')
REPLIES = join(dirname(__file__),'./performance_replies.txt')

class Utterances(object):
    def __init__(self):
        self.file = file(UTTERANCES, 'r', 1)
        self.next_time = None
        self.buff = None

    def __del__(self):
        if hasattr(self, 'file'):
            self.file.close()

    def next(self):
        """Switch to next line. Also, check self.lock() for deferred reading.
        """
        if not self.next_time:
            self.next_time = time.time()
        if time.time() >= self.next_time:
            line = self.file.readline().strip()
            if not line:
                return 'EOF'
            if line.startswith('EOSECTION'):
                return 'EOSECTION'
            min_dur, datablock = line.split(None,1)
            return float(min_dur), datablock.strip(), datablock.split(';')[-1]
        return None

    def lock(self, duration):
        """Lock iterating over the file for duration seconds.
        """
        self.next_time = time.time() + duration

class Replies(object):
    def __init__(self):
        self.int = []
        self.rep = []
        self.nod = []
        with file(REPLIES, 'r', 1) as f:
            for i,l in enumerate(f.readlines()):
                try:
                    group, line = l.split('  ')
                    getattr(self, group).append(line)
                except AttributeError, e:
                    print 'bad keyword in replies file line %i: %s %s' % (i,l,e)
                except Exception, e:
                    raise ValueError('replies file line %i: %s (%s)' % (i,l,e))

class InteractivePlayer(FSM_Builder):
    """A simple player reading monologue file.
    """

    def read_section(self):
        """
        Returns: 'EOSECTION',FSM.STOPPED
        """
        line = self.utterances.next()
        if line == 'EOSECTION':
            return line
        if line == 'EOF':
            return FSM.STOPPED
        if line:
            pause, datablock, tag = line
            self.comm_expr.send_msg(datablock+'read')
            self.comm_expr.wait_reply(tag+'read')
            self.utterances.lock(pause)

    def listenTo_participant(self):
        """
        Returns: 'P_QUESTION', 'P_STATEMENT', 'P_TIMEOUT'
        """
        return 'P_QUESTION'
        return 'P_STATEMENT'
        return 'P_TIMEOUT'

    def answer_participant(self):
        """
        Returns: 'REPLIED'
        """
        line = random.Random().choice(self.replies.rep).strip()
        self.comm_expr.send_msg(line+'answer')
        self.comm_expr.wait_reply('answer')
        return 'REPLIED'

    def nodTo_participant(self):
        """
        Returns: 'REPLIED'
        """
        line = random.Random().choice(self.replies.nod).strip()
        self.comm_expr.send_msg(line+'nod')
        self.comm_expr.wait_reply('nod')
        return 'REPLIED'

    def interrupt_participant(self):
        """
        Returns: 'REPLIED'
        """
        line = random.Random().choice(self.replies.int).strip()
        self.comm_expr.send_msg(line+'int')
        self.comm_expr.wait_reply('int')
        return 'REPLIED'

    def search_participant(self):
        """
        Returns: 'FOUND_PART'
        """
        self.faces = self.vision.find_faces()
        if self.vision.gui:
            self.vision.mark_rects(self.faces)
            self.vision.gui.show_frame(self.vision.frame)
        return self.faces and 'FOUND_PART' or None

    def adjust_gaze_neck(self):
        """
        Returns: 'ADJUSTED'
        """
        eyes = self.vision.find_eyes([self.faces[0]])[0]
        center = Frame(((eyes[0].x + eyes[1].x)/2, (eyes[0].y+eyes[1].y)/2,
                        self.faces[0].w, self.faces[0].h))
        gaze_xyz = self.vision.camera.get_3Dfocus(center)
        neck = ((.0,.0,.0),(.0,.0,.0))
        # TODO: ideally, we would not have to set the neck if gaze is enough to
        #  drive the neck (an expr2 instinct could do it).
        if not self.vision.camera.is_within_tolerance(center.x, center.y):
            neck = (gaze_xyz,(.0,.0,.0))
        self.comm_expr.set_gaze(gaze_xyz)
        self.comm_expr.set_neck(*neck)
        tag = self.comm_expr.send_datablock('gaze_neck')
        self.comm_expr.wait_reply(tag)
        return 'ADJUSTED'

    def finish(self, name):
        """Called on FSM.STOPPED state.
        name: name of the machine.
        """
        del self.utterances
        return None


    PLAYER_DEF = ( ((FSM.STARTED, 'FOUND_PART', 'REPLIED'), self.read_section),
                   ('EOSECTION',  self.finish),
                   ('EOSECTION',  self.listenTo_participant),
                   ('P_QUESTION', self.answer_participant),
                   ('P_STATEMENT', self.nodTo_participant),
                   ('P_TIMEOUT', self.interrupt_participant),
                   (FSM.STOPPED, self.finish),
               )

    FRACKER_DEF = ( ((FSM.STARTED,'ADJUSTED'), self.search_participant),
                    ('FOUND_PART', self.adjust_gaze_neck),
                    (FSM.STOPPED, self.finish),
                  )

    def __init__(self):
        """
        """
        FSM_Builder.__init__(self, [('player',PLAYER_DEF,None),
                                    ('tracker',FTRACKER_DEF,'player')])
        self.utterances = Utterances()
        self.replies = Replies()
