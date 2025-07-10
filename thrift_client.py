from thrift.transport import TSocket, TTransport
from thrift.protocol import TBinaryProtocol
from TimestampService import TimestampService


def get_timestamp():
    """
    Connects to the Apache Thrift server to fetch a timestamp.
    Returns the timestamp as a string in the format YYYY-MM-DD HH:MM:SS
    (compatible with Django's DateTimeField).
    """
    try:
        # Set up the transport and protocol
        transport = TSocket.TSocket('localhost', 10000)  # Replace with the correct host/port
        transport = TTransport.TBufferedTransport(transport)
        protocol = TBinaryProtocol.TBinaryProtocol(transport)

        # Create a client to communicate with the Thrift server
        client = TimestampService.Client(protocol)

        # Open the transport connection
        transport.open()

        # Fetch the timestamp from the Thrift server
        timestamp = client.getTimestamp()

        # Close the transport connection
        transport.close()

        # Return the timestamp as-is
        return timestamp

    except Exception as e:
        # Log any error and return None as a fallback
        print(f"Thrift client error: {e}")
        return None
