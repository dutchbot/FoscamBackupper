from io import StringIO
import unittest.mock as umock

def mocked_append(*args, **kwargs):
    APPEND.buffer += args[0]

def mocked_write(*args, **kwargs):
    WRITE.buffer += args[0]

READ_STATE = umock.MagicMock(name="open", spec=str)
READ_STATE.read = umock.Mock(return_value=StringIO("{\"20160501_220030.avi\":1, \"done\":1, \"path\":\"record/20160501\"}"), spec=str)

READ_S = umock.MagicMock(name="open", spec=str)
READ_S.read = umock.Mock(return_value=StringIO("record/20160501"), spec=str)

APPEND = umock.MagicMock(name="open")
APPEND.write = umock.MagicMock()
APPEND.write.side_effect = mocked_append
APPEND.buffer = str()

WRITE = umock.MagicMock(name="open", spec=bytes)
WRITE.write = umock.MagicMock()
WRITE.write.side_effect = mocked_write
WRITE.buffer = str()
