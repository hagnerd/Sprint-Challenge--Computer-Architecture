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
        self.ram = [0] * 256
        self.reg = [0] * 8
        self.pc = 0
        # STACK POINTER
        self.reg[-1] = len(self.ram) - 1
        self.running = False
        # THE FLAG REGISTER
        self.reg[-2] = 0b00000000
        self.cmds = self._init_cmds()

    def _init_cmds(self):
        cmds = {}
        cmds[HLT] = self.handle_halt
        cmds[LDI] = self.ldi
        cmds[PRN] = self.handle_print

        cmds[MUL] = self.handle_mul
        cmds[ADD] = self.handle_add
        cmds[PUSH] = self.handle_push
        cmds[POP] = self.handle_pop
        cmds[CALL] = self.handle_call
        cmds[RET] = self.handle_ret
        cmds[CMP] = self.handle_cmp
        cmds[JMP] = self.handle_jmp
        cmds[JEQ] = self.handle_jeq
        cmds[JNE] = self.handle_jne

        return cmds

    def load(self):
        """Load a program into memory."""

        if len(sys.argv) < 2:
            self.ram[0] = HLT
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
                self.ram[address] = int(line.strip(), 2)
                address += 1

    def ram_read(self, register):
        return self.ram[register]

    def ram_write(self, register, value):
        self.ram[register] = value

    def get_alu_regs(self):
        reg_a = self.ram_read(self.pc + 1)
        reg_b = self.ram_read(self.pc + 2)
        return reg_a, reg_b

    def handle_mul(self):
        reg_a, reg_b = self.get_alu_regs()
        self.reg[reg_a] *= self.reg[reg_b]
        self.pc += 3

    def handle_add(self):
        reg_a, reg_b = self.get_alu_regs()
        self.reg[reg_a] += self.reg[reg_b]
        self.pc += 3

    def handle_sub(self):
        reg_a, reg_b = self.get_alu_regs()
        self.reg[reg_a] -= self.reg[reg_b]
        self.pc += 3

    def get_stack_pointer(self):
        return self.reg[-1]

    def inc_stack_pointer(self):
        self.reg[-1] += 1

    def dec_stack_pointer(self):
        self.reg[-1] -= 1

    def trace(self):
        """
        Handy function to print out the CPU state. You might want to call this
        from run() if you need help debugging.
        """

        counter = self.pc

        if self.ram_read(counter) not in self.cmds:
            print("INVALID COMMAND FOUND:")
            print(f"PC: {counter}, val: {self.ram_read(counter)}")

            self.running = False
            return 

        print(f"TRACE: %02X | %s %02X %02X |" % (
            self.pc,
            #self.fl,
            #self.ie,
            self.ram_read(self.pc),
            self.ram_read(self.pc + 1),
            self.ram_read(self.pc + 2)
        ), end='')

        for i in range(8):
            print(" %02X" % self.reg[i], end='')

        print()

    def handle_halt(self):
        print('THE PROGRAM HAS HALTED')
        self.running = False
        self.pc += 1

    def ldi(self):
        register = self.ram_read(self.pc + 1)
        value = self.ram_read(self.pc + 2)

        self.reg[register] = value
        self.pc += 3

    def handle_print(self):
        """
        Prints the following register
        """
        register = self.ram_read(self.pc + 1)

        print(self.reg[register])

        self.pc += 2

    def _stack_push(self, value):
        """
        Adds an item to the stack
        """
        self.dec_stack_pointer()
        self.ram_write(self.get_stack_pointer(), value)

    def _set_equal_flag(self, status):
        if status == 'EQ':
            self.reg[-2] = 0b0000001
        elif status == 'GT':
            self.reg[-2] = 0b0000010
        elif status == 'LT':
            self.reg[-2] = 0b0000100

    def _stack_pop(self):
        """
        Removes an item from the stack
        """
        # Retrieve the value from RAM at the address in SP
        # Store the value at the register passed in
        # Increment SP
        val = self.ram_read(self.get_stack_pointer())
        self.inc_stack_pointer()
        return val

    def handle_pop(self):
        register = self.ram_read(self.pc + 1)
        val = self._stack_pop()
        self.reg[register] = val
        self.pc += 2

    def handle_push(self):
        register = self.ram_read(self.pc + 1)
        value = self.reg[register]
        self._stack_push(value)
        self.pc += 2

    def handle_call(self):
        # pc = CALL instruction
        # pc+1 = address of subroutine
        # Place the address of the next instruction on the stack
        # Set the PC to the address of the subroutine

        next_instruction = self.pc + 2
        subroutine = self.ram_read(self.pc + 1)
        self._stack_push(next_instruction)
        self.pc = self.reg[subroutine]

    def handle_ret(self):
        next_instruction = self._stack_pop()
        self.pc = next_instruction

    def is_equal_flag(self):
        return self.reg[-2] == 1

    def handle_cmp(self):

        first_value = self.reg[self.ram_read(self.pc + 1)]
        second_value = self.reg[self.ram_read(self.pc + 2)]

        cmp_result = None
        if first_value == second_value:
            cmp_result = 'EQ'
        elif first_value > second_value:
            cmp_result = 'GT'
        elif first_value < second_value:
            cmp_result = 'LT'

        print(f"V1: {first_value}, V2: {second_value}, RES: {cmp_result}")

        self._set_equal_flag(cmp_result)

        self.pc += 3

    def handle_jmp(self):
        register = self.ram_read(self.pc + 1)
        self.pc = self.reg[register]

    def handle_jne(self):
        if not self.is_equal_flag():
            self.handle_jmp()
        else:
            self.pc += 2

    def handle_jeq(self):
        if self.is_equal_flag():
            self.handle_jmp()
        else:
            self.pc += 2

    def handle_cmd(self, command):
        """
        Handles running the command
        """
        if command not in self.cmds:
            print(f"UNKNOWN COMMAND: {command}")
            sys.exit(1)
            return 

        self.cmds[command]()

    def run(self):
        """Run the CPU."""
    
        self.running = True

        while self.running:
            command = self.ram[self.pc]
            self.trace()
            self.handle_cmd(command)
