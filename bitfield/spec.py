"""Parse DSL into a simple data structure.

Perform load-time sanity checks on the input.

DSL isn't recursive, just defines a flat data structure. Therefore parser is
adhoc and doesn't use a grammar. May be worth refactoring in the future.
"""

class BitfieldError(Exception): pass
class SizeError(BitfieldError): pass
class AlignmentError(BitfieldError): pass
class SyntaxError(BitfieldError): pass
class TotalityError(BitfieldError): pass

class Region(object):
    """Monoidal memory regions containing bitfields.
    
    Define in global module scope such that data structure is generated at
    module load time, triggering any assertions early.
    """
    def __init__(self, from_addr, to_addr, code, 
            bit_e='little', byte_e='little', bit_align=8, mode='rw',
            enums={}):

        if from_addr > to_addr:
            raise BitfieldError("memory region not sequential")
        if from_addr < 0 or to_addr < 0:
            raise BitfieldError("no negative addresses")

        self.from_addr = from_addr
        self.to_addr = to_addr

        # The following are metadata saved in the structure, to be
        # used by the code generators/parsers/packers later.
        # When possible, it is checked for sanity at load-time.
        self.bit_e = bit_e 
        self.byte_e = byte_e
        self.bit_align = bit_align

        # The following store the parsed DSL contents.
        self.registers = {}
        self.fields = {}
        self.enums = enums # will be checked

        self._parse_code(code)
        self._check_enums(enums)


    def _parse_code(self, code):
        addr = self.from_addr
        # note awesome indentation-awareness hack:
        for line in [s for s in code.replace('\n ', ' ').split('\n') if s]:
            toks = line.split()
            if len(toks) < 2:
                raise SyntaxError("no field(s) defined in", line)
            register, fields = toks[0], toks[1:]
            if register in self.registers:
                raise SyntaxError("duplicate register", register)
            
            self.registers[register] = addr
            addr += self.bit_align / 8

            bit_index = 0
            for field in fields:
                field = Field(field, max_width=self.bit_align - bit_index,
                              byte_base=addr, bit_base=bit_index)
                bit_index += field.width

                if field.name in ['unused', 'magic', 'reserved']: 
                    # TODO handle magic field names/enum names
                    continue

                if field.name in self.fields:
                    raise SyntaxError("duplicate field name", field.name)

                self.fields[field.name] = field

        if addr != self.to_addr:
            raise TotalityError('not all registers in range',
                    hex(self.from_addr), hex(self.to_addr))


    def _check_enums(self, enums):
        for field in enums:
            if field not in self.fields:
                raise SyntaxError("unknown enum field name", field)
            if (2**self.fields[field].width) < len(enums[field]):
                raise SizeError("enum too large for field", field)


    def __add__(self, value):
        """Monoid with some sanity checks."""
        def check_dups(a,b,err):
            dup = set(a.keys()).intersection( set(b.keys()))
            if dup:
                raise SyntaxError(err, dup)
        check_dups(self.registers, value.registers, "duplicate registers")
        check_dups(self.fields, value.fields, "duplicate fields")
        check_dups(self.enums, value.enums, "duplicate enums")

        # let's simplify, not sure if I'll even use these in this project
        assert self.bit_e is value.bit_e
        assert self.byte_e is value.byte_e
        assert self.bit_align is value.bit_align

        for r in value.registers:
            self.registers[r] = value.registers[r] 
        for r in value.fields:
            self.fields[r] = value.fields[r] 

        self.from_addr = min(self.from_addr, value.from_addr)
        self.to_addr = max(self.to_addr, value.to_addr)

        return self

        


class Field(object):
    def __init__(self, text, max_width, byte_base, bit_base):
        text = text.split(':') 
        if len(text) == 1:
            bits = 0
            field_name = text[0]
        else:
            bits,field_name = text
            bits = int(bits)

        if bits > max_width:
            raise SizeError("field doesn't fit in register", fields)

        self.name = field_name
        self.width = bits
        self.byte_base = byte_base
        self.bit_base = bit_base
