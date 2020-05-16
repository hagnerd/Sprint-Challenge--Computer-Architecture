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

CMDS = {
    0b00000001: 'HLT',
    0b10000010: 'LDI',
    0b01000111: 'PRN',
    0b10100010: 'MUL',
    0b01000101: 'PUSH',
    0b01000110: 'POP',
    0b01010000: 'CALL',
    0b00010001: 'RET',
    0b10100000: 'ADD'
}


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
        self.equal_flag = 0b00000000

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

    def alu(self, op, reg_a, reg_b):
        """ALU operations."""

        if op == "ADD":
            self.reg[reg_a] += self.reg[reg_b]
        elif op == "SUB":
            self.reg[reg_a] -= self.reg[reg_b]
        elif op == "MUL":
            self.reg[reg_a] *= self.reg[reg_b]
        else:
            raise Exception("Unsupported ALU operation")

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

        if self.ram_read(counter) not in CMDS:
            print("INVALID COMMAND FOUND:")
            print(f"PC: {counter}, val: {self.ram_read(counter)}")

            self.running = False
            return 

        print(f"TRACE: %02X | %s %02X %02X |" % (
            self.pc,
            #self.fl,
            #self.ie,
            CMDS[self.ram_read(self.pc)],
            self.ram_read(self.pc + 1),
            self.ram_read(self.pc + 2)
        ), end='')

        for i in range(8):
            print(" %02X" % self.reg[i], end='')

        print()

    def hlt(self):
        print('THE PROGRAM HAS HALTED')
        self.running = False
        self.pc += 1

    def ldi(self):
        register = self.ram_read(self.pc + 1)
        value = self.ram_read(self.pc + 2)

        self.reg[register] = value
        self.pc += 3

    def prn(self):
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
            self.equal = 0b0000001
        elif status == 'GT':
            self.equal = 0b0000010
        elif status == 'LT':
            self.equal = 0b0000100

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

    def handle_stack_pop(self):
        register = self.ram_read(self.pc + 1)
        val = self._stack_pop()
        self.reg[register] = val
        self.pc += 2

    def handle_stack_push(self):
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
        sub_address = self.reg[subroutine]

        print(f"NEXT: {next_instruction}, SUB: {subroutine}, ADD: {sub_address}")

        self._stack_push(next_instruction)
        self.pc = self.reg[subroutine]

    def handle_ret(self):
        # Pop the next instruction off of the stack

        next_instruction = self._stack_pop()
        self.pc = next_instruction

    def handle_cmp(self):
        first_value = self.ram_read(self.pc + 1)
        second_value = self.ram_read(self.pc + 2)

        cmp_result = None
        if first_value == second_value:
            cmp_result = 'EQ'
        elif first_value > second_value:
            cmp_result = 'GT'
        elif first_value < second_value:
            cmp_result = 'LT'

        self._set_equal_flag(cmp_result)

        self.pc += 3

    def handle_jmp(self):
        register = self.ram_read(self.pc + 1)
        self.pc = register

    def handle_cmd(self, command):
        if command == HLT:
            self.hlt()
        elif command == LDI:
            self.ldi()
        elif command == PRN:
            self.prn()
        elif command == MUL:
            self.alu('MUL', self.ram_read(self.pc + 1),
                     self.ram_read(self.pc + 2))
        elif command == ADD:
            self.alu('ADD', self.ram_read(self.pc + 1), self.ram_read(self.pc +
                                                                      2))
        elif command == PUSH:
            self.handle_stack_push()
        elif command == POP:
            self.handle_stack_pop()
        elif command == CALL:
            self.handle_call()
        elif command == RET:
            self.handle_ret()
        elif command == CMP:
            self.handle_cmp()
        elif command == JMP:
            self.handle_jmp()


    def run(self):
        """Run the CPU."""
    
        self.running = True

        while self.running:
            command = self.ram[self.pc]
            self.handle_cmd(command)
