if __name__ == '__main__':
  import sys
  import logging
  from threading import Thread

  from utils import LOGFORMATINFO
  from utils.comm import (ASCIICommandClient, ASCIIRequestHandlerCmds,
                          create_server)

  if len(sys.argv) < 2:
    print "usage: %s port" % sys.argv[0]
    print "If port is a number use tcp mode, if a path use udp."
    exit(1)
  addr_port = ['localhost',sys.argv[1]]
  if sys.argv[1].isdigit():
    addr_port[1] = int(addr_port[1])

  logging.basicConfig(level=logging.DEBUG,**LOGFORMATINFO)
  LOG = logging.getLogger()

  # Create a test thread that connects to the server.
  class TestClient(ASCIICommandClient):
    def handle_connect(self):
      LOG.info("%s connected", self.__class__.__name__)
      self.send_msg('ping my other args')
    def cmd_pong(self, args):
      LOG.info("sending shutdown")
      self.send_msg('shutdown')
      self.abort()

  class TestHandler(ASCIIRequestHandlerCmds):
    def cmd_ping(self, args):
      LOG.info("got ping '%s'", args)
      self.send_msg('pong')

  try:
    client = TestClient(addr_port)
    c = Thread(target=client.connect_and_run)
    LOG.info("created client thread for test")
    c.start()

    # Reminder for threading_info: server thread, clients threaded
    server = create_server(TestHandler, addr_port, threading_info=(False,False))
    server.start()
    if not server.is_threaded():     # threaded servers start serving in start()
      server.serve_forever()
  except KeyboardInterrupt:
    print "user abort!"
    server.shutdown()
  c.join()
  print "server and client exited."
