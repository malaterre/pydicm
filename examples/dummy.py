from pydicm import *

fn = "/tmp/input.dcm"

with open(fn, "rb") as f:
    io = IO(f)
    parser = Parser()
    parser.set_input(io)
    done = False
    while not done:
        ret = parser.next_event()
        etype = ret
        # print(etype)
        if etype == DICM_ELEMENT_KEY_EVENT:
            key = parser.key()
            print(key)
        elif etype == DICM_ELEMENT_VALUE_EVENT:
            vl = parser.value_length()
            buflen = 4096
            while vl != 0:
                length = vl if vl < buflen else buflen
                ba = parser.read_value(length)
                vl -= length
        done = etype == DICM_STREAM_END_EVENT
