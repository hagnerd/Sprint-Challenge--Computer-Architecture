"""CPU functionality."""

import sys
import re

# STOP THE PROGRAM FROM RUNNING
HLT = 0b00000001
# REGISTER register value
LDI = 0b10000010
# PRINT register
PRN = 0b01000111

MUL = 0b10100010
ADD = 0b10100000

PUSH = 0b01000101
POP = 0b01000110

CALL = 0b01010000
RET = 0b00010001

CMP = 0b10100111

JMP = 0b01010100
JEQ = 0b01010101
JNE = 0b01010110

class CPU:
    """Main CPU class."""

    def __init__(self):
        """Construct a new CPU."""
        self._ram = [0] * 256
        self._reg = [0] * 8
        self._pc = 0
        # STACK POINTER
        self._reg[-1] = len(self._ram) - 1
        self._running = False
        # THE FLAG REGISTER
        self._reg[-2] = 0b00000000
        self._cmds = self._init_cmds()
        self._alu = self._init_alu_cmds()

    def _init_cmds(self):
        cmds = {}
        cmds[HLT] = self._handle_halt
        cmds[LDI] = self._handle_ldi
        cmds[PRN] = self._handle_print

        cmds[PUSH] = self._handle_push
        cmds[POP] = self._handle_pop
        cmds[CALL] = self._handle_call
        cmds[RET] = self._handle_ret

        cmds[JMP] = self._handle_jmp
        cmds[JEQ] = self._handle_jeq
        cmds[JNE] = self._handle_jne

        cmds[MUL] = lambda: self._handle_alu(MUL)
        cmds[ADD] = lambda: self._handle_alu(ADD)
        cmds[CMP] = lambda: self._handle_alu(CMP)

        return cmds

    def _init_alu_cmds(self):
        cmds = {}
        cmds[ADD] = self._handle_add
        cmds[MUL] = self._handle_mul
        cmds[CMP] = self._handle_cmp

        return cmds

    def load(self):
        """Load a program into memory."""

        if len(sys.argv) < 2:
            self._ram[0] = HLT
            print('Not a valid program')
            print('HALTING NOW')
            return

        address = 0
        path = sys.argv[1]
        file = open(path, 'r')
        lines = file.readlines()

        for line in lines:
            line = re.sub('#.*', '', line)
            if line.strip() != "":
                self._ram[address] = int(line.strip(), 2)
                address += 1

    def _ram_read(self, register):
        return self._ram[register]

    def _ram_write(self, register, value):
        self._ram[register] = value

    def _handle_mul(self, reg_a, reg_b):
        self._reg[reg_a] *= self._reg[reg_b]

    def _handle_add(self, reg_a, reg_b):
        self._reg[reg_a] += self._reg[reg_b]

    def _handle_sub(self, reg_a, reg_b):
        self._reg[reg_a] -= self._reg[reg_b]

    def _handle_alu(self, operation):
        reg_a = self._ram_read(self._pc + 1)
        reg_b = self._ram_read(self._pc + 2)

        if operation not in self._alu:
            raise Exception("Unsupported ALU operation")

        self._alu[operation](reg_a, reg_b)
        self._pc += 3

    def _handle_cmp(self, reg_a, reg_b):
        first_value = self._reg[reg_a]
        second_value = self._reg[reg_b]

        cmp_result = None
        if first_value == second_value:
            cmp_result = 'EQ'
        elif first_value > second_value:
            cmp_result = 'GT'
        elif first_value < second_value:
            cmp_result = 'LT'

        self._set_equal_flag(cmp_result)

    def _get_stack_pointer(self):
        return self._reg[-1]

    def _inc_stack_pointer(self):
        self._reg[-1] += 1

    def _dec_stack_pointer(self):
        self._reg[-1] -= 1

    def _trace(self):
        """
        Handy function to print out the CPU state. You might want to call this
        from run() if you need help debugging.
        """

        counter = self._pc

        if self._ram_read(counter) not in self._cmds:
            print("INVALID COMMAND FOUND:")
            print(f"PC: {counter}, val: {self._ram_read(counter)}")

            self._running = False
            return

        print(f"TRACE: %02X | %s %02X %02X |" % (
            self._pc,
            #self.fl,
            #self.ie,
            self._ram_read(self._pc),
            self._ram_read(self._pc + 1),
            self._ram_read(self._pc + 2)
        ), end='')

        for i in range(8):
            print(" %02X" % self._reg[i], end='')

        print()

    def _handle_halt(self):
        print('THE PROGRAM HAS HALTED')
        self._running = False
        self._pc += 1

    def _handle_ldi(self):
        register = self._ram_read(self._pc + 1)
        value = self._ram_read(self._pc + 2)

        self._reg[register] = value
        self._pc += 3

    def _handle_print(self):
        """
        Prints the following register
        """
        register = self._ram_read(self._pc + 1)

        print(self._reg[register])

        self._pc += 2

    def _stack_push(self, value):
        """
        Adds an item to the stack
        """
        self._dec_stack_pointer()
        self._ram_write(self._get_stack_pointer(), value)

    def _set_equal_flag(self, status):
        if status == 'EQ':
            self._reg[-2] = 0b0000001
        elif status == 'GT':
            self._reg[-2] = 0b0000010
        elif status == 'LT':
            self._reg[-2] = 0b0000100

    def _stack_pop(self):
        """
        Removes an item from the stack
        """
        val = self._ram_read(self._get_stack_pointer())
        self._inc_stack_pointer()
        return val

    def _handle_pop(self):
        register = self._ram_read(self._pc + 1)
        val = self._stack_pop()
        self._reg[register] = val
        self._pc += 2

    def _handle_push(self):
        register = self._ram_read(self._pc + 1)
        value = self._reg[register]
        self._stack_push(value)
        self._pc += 2

    def _handle_call(self):
        next_instruction = self._pc + 2
        subroutine = self._ram_read(self._pc + 1)
        self._stack_push(next_instruction)
        self._pc = self._reg[subroutine]

    def _handle_ret(self):
        next_instruction = self._stack_pop()
        self._pc = next_instruction

    def _is_flag_equal(self):
        return self._reg[-2] == 1

    def _handle_jmp(self):
        register = self._ram_read(self._pc + 1)
        self._pc = self._reg[register]

    def _handle_jne(self):
        if not self._is_flag_equal():
            self._handle_jmp()
        else:
            self._pc += 2

    def _handle_jeq(self):
        if self._is_flag_equal():
            self._handle_jmp()
        else:
            self._pc += 2

    def _handle_cmd(self, command):
        """
        Handles running the command
        """
        if command not in self._cmds:
            print(f"UNKNOWN COMMAND: {command}")
            sys.exit(1)
            return

        self._cmds[command]()

    def run(self):
        """Run the CPU."""
        self._running = True

        while self._running:
            command = self._ram[self._pc]
            self._trace()
            self._handle_cmd(command)
