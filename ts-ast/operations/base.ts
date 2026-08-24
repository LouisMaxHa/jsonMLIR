import { AllocOp } from './op_alloc.js';
import { AllocaOp } from './op_alloca.js';
import { BinaryOp } from './op_binary.js';
import { CallOp } from './op_call.js';
import { CondOp } from './op_cond.js';
import { ConstOp } from './op_constant.js';
import { DefineFunctionOp } from './op_define_function.js';
import { DefineStructOp } from './op_define_struct.js';
import { FunctionOp } from './op_function.js';
import { MathOp } from './op_math.js';
import { PrintOp } from './op_print.js';
import { SetOp } from './op_set.js';
import { UnaryOp } from './op_unary.js';
import { VarOp } from './op_var.js';
import { WhileOp } from './op_while.js';

/** Statements allowed inside a function / while / if body. */
export type BaseValue =
    | BinaryOp
    | CallOp
    | ConstOp
    | CondOp
    | VarOp
    | WhileOp
    | PrintOp
    | SetOp
    | AllocOp
    | AllocaOp
    | MathOp
    | UnaryOp;

/** Top-level module statements. */
export type ModuleStatement = DefineStructOp | DefineFunctionOp | FunctionOp;
