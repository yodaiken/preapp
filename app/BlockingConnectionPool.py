from redis.connection import Connection, ConnectionError
from Queue import LifoQueue, Full, Empty
import os

class BlockingConnectionPool(object):
    """
    Thread-safe blocking connection pool::

        >>> from redis.client import Redis
        >>> client = Redis(connection_pool=BlockingConnectionPool())

    It performs the same function as the default
    ``:py:class: ~redis.connection.ConnectionPool`` implementation, in that,
    it maintains a pool of reusable connections that can be shared by
    multiple redis clients (safely across threads if required).

    The difference is that, in the event that a client tries to get a
    connection from the pool when all of connections are in use, rather than
    raising a ``:py:class: ~redis.exceptions.ConnectionError`` (as the default
    ``:py:class: ~redis.connection.ConnectionPool`` implementation does), it
    makes the client wait ("blocks") for a specified number of seconds until
    a connection becomes available.

    Use ``max_connections`` to increase / decrease the pool size::

        >>> pool = BlockingConnectionPool(max_connections=10)

    Use ``timeout`` to tell it either how many seconds to wait for a connection
    to become available, or to block forever:

        # Block forever.
        >>> pool = BlockingConnectionPool(timeout=None)

        # Raise a ``ConnectionError`` after five seconds if a connection is
        # not available.
        >>> pool = BlockingConnectionPool(timeout=5)
    """
    def __init__(self, max_connections=50, timeout=20, connection_class=None,
                 queue_class=None, **connection_kwargs):
        "Compose and assign values."
        # Compose.
        if connection_class is None:
            connection_class = Connection
        if queue_class is None:
            queue_class = LifoQueue

        # Assign.
        self.connection_class = connection_class
        self.connection_kwargs = connection_kwargs
        self.queue_class = queue_class
        self.max_connections = max_connections
        self.timeout = timeout

        # Validate the ``max_connections``.  With the "fill up the queue"
        # algorithm we use, it must be a positive integer.
        is_valid = isinstance(max_connections, int) and max_connections > 0
        if not is_valid:
            raise ValueError('``max_connections`` must be a positive integer')

        # Get the current process id, so we can disconnect and reinstantiate if
        # it changes.
        self.pid = os.getpid()

        # Create and fill up a thread safe queue with ``None`` values.
        self.pool = self.queue_class(max_connections)
        while True:
            try:
                self.pool.put_nowait(None)
            except Full:
                break

        # Keep a list of actual connection instances so that we can
        # disconnect them later.
        self._connections = []

    def _checkpid(self):
        """
        Check the current process id.  If it has changed, disconnect and
        re-instantiate this connection pool instance.
        """
        # Get the current process id.
        pid = os.getpid()

        # If it hasn't changed since we were instantiated, then we're fine, so
        # just exit, remaining connected.
        if self.pid == pid:
            return

        # If it has changed, then disconnect and re-instantiate.
        self.disconnect()
        self.reinstantiate()

    def make_connection(self):
        "Make a fresh connection."
        connection = self.connection_class(**self.connection_kwargs)
        self._connections.append(connection)
        return connection

    def get_connection(self, command_name, *keys, **options):
        """
        Get a connection, blocking for ``self.timeout`` until a connection
        is available from the pool.

        If the connection returned is ``None`` then creates a new connection.
        Because we use a last-in first-out queue, the existing connections
        (having been returned to the pool after the initial ``None`` values
        were added) will be returned before ``None`` values. This means we only
        create new connections when we need to, i.e.: the actual number of
        connections will only increase in response to demand.
        """
        # Make sure we haven't changed process.
        self._checkpid()

        # Try and get a connection from the pool. If one isn't available within
        # self.timeout then raise a ``ConnectionError``.
        connection = None
        try:
            connection = self.pool.get(block=True, timeout=self.timeout)
        except Empty:
            # Note that this is not caught by the redis client and will be
            # raised unless handled by application code. If you want never to
            raise ConnectionError("No connection available.")

        # If the ``connection`` is actually ``None`` then that's a cue to make
        # a new connection to add to the pool.
        if connection is None:
            connection = self.make_connection()

        return connection

    def release(self, connection):
        "Releases the connection back to the pool."
        # Make sure we haven't changed process.
        self._checkpid()

        # Put the connection back into the pool.
        try:
            self.pool.put_nowait(connection)
        except Full:
            # This shouldn't normally happen but might perhaps happen after a
            # reinstantiation. So, we can handle the exception by not putting
            # the connection back on the pool, because we definitely do not
            # want to reuse it.
            pass

    def disconnect(self):
        "Disconnects all connections in the pool."
        for connection in self._connections:
            connection.disconnect()

    def reinstantiate(self):
        """
        Reinstatiate this instance within a new process with a new connection
        pool set.
        """
        self.__init__(max_connections=self.max_connections,
                      timeout=self.timeout,
                      connection_class=self.connection_class,
                      queue_class=self.queue_class, **self.connection_kwargs)