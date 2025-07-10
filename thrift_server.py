import logging
from datetime import datetime
from thrift.transport import TSocket
from thrift.transport import TTransport
from thrift.protocol import TBinaryProtocol
from thrift.server import TServer
from TimestampService import TimestampService

class TimestampHandler:
    def getTimestamp(self):
        # Return the current datetime in the Django-compatible format
        return datetime.now().strftime('%Y-%m-%d %H:%M:%S')

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    handler = TimestampHandler()
    processor = TimestampService.Processor(handler)
    transport = TSocket.TServerSocket(port=10000)
    tfactory = TTransport.TBufferedTransportFactory()
    pfactory = TBinaryProtocol.TBinaryProtocolFactory()

    server = TServer.TSimpleServer(processor, transport, tfactory, pfactory)
    logging.info("Starting Thrift server...")
    server.serve()

