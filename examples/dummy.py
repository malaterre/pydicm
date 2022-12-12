from pydicm import *

fn = "/tmp/input.dcm"

with open(fn, "rb") as f:
    parser = Parser()
    parser.set_input(f)
    done = False
    while not done:
        ret = parser.next_event()
        etype = ret
        # print(etype)
        if etype == Parser.EventType.ELEMENT_KEY:
            key = parser.key()
            print(key)
        elif etype == Parser.EventType.ELEMENT_VALUE:
            vl = parser.value_length()
            buflen = 4096
            while vl != 0:
                length = vl if vl < buflen else buflen
                ba = parser.read_value(length)
                vl -= length
        done = etype == Parser.EventType.STREAM_END
