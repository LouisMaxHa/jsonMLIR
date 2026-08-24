import { parseScalar, Scalar } from '../utils/enum_scalars.js';
import { FieldType } from '../variables/memory.js';
import type { TyNode } from '../variables/ty/ty_base.js';
import { parseTy, parseTyOrScalar } from '../variables/ty/ty.js';
import type { BaseValue, ModuleStatement } from './base.js';
import { AllocOp, type AllocSize } from './op_alloc.js';
import { AllocaOp } from './op_alloca.js';
import { BinaryOp } from './op_binary.js';
import { CallOp } from './op_call.js';
import { CondOp } from './op_cond.js';
import { ConstOp } from './op_constant.js';
import { DefineFunctionOp } from './op_define_function.js';
import { DefineStructOp } from './op_define_struct.js';
import { FunctionOp, type FunctionArg } from './op_function.js';
import { MathOp } from './op_math.js';
import { ModuleJsonOp } from './op_module.js';
import {
    MathOperator,
    Operator,
    parseMathOperator,
    parseOperator,
    parseUnaryOperator,
    UnaryOperator,
} from './op_operator.js';
import { PrintOp } from './op_print.js';
import { SetOp, type SetValue } from './op_set.js';
import { UnaryOp } from './op_unary.js';
import { VarOp, type VarIndex } from './op_var.js';
import { WhileOp } from './op_while.js';

/** Field spec: ``[name, type, offset, size]`` or an existing ``FieldType``. */
export type FieldSpec =
    | FieldType
    | readonly [string, string | TyNode, number, number];

function parseField(field: FieldSpec): FieldType {
    if (field instanceof FieldType) {
        return field;
    }
    const [name, ty, offset, size] = field;
    return new FieldType(name, parseTyOrScalar(ty), offset, size);
}

function parseArg(arg: readonly [string, string | TyNode]): FunctionArg {
    return [arg[0], parseTyOrScalar(arg[1])];
}

export function Module(body: readonly ModuleStatement[] = []): ModuleJsonOp {
    return new ModuleJsonOp(body);
}

export function DefineStruct(
    name: string,
    size: number,
    fields: readonly FieldSpec[],
): DefineStructOp {
    return new DefineStructOp(name, size, fields.map(parseField));
}

export function DefineFunction(
    name: string,
    args: readonly (readonly [string, string | TyNode])[] = [],
    returnTypes: readonly (string | TyNode)[] = [],
): DefineFunctionOp {
    return new DefineFunctionOp(
        name,
        args.map(parseArg),
        returnTypes.map(t => parseTyOrScalar(t)),
    );
}

export function Function(
    name: string,
    args: readonly (readonly [string, string | TyNode])[] = [],
    body: readonly BaseValue[] = [],
): FunctionOp {
    return new FunctionOp(name, args.map(parseArg), body);
}

export function Var(
    name: string,
    indices: readonly VarIndex[] = [],
    type?: string | TyNode,
): VarOp {
    return new VarOp(
        name,
        indices,
        type === undefined ? undefined : parseTyOrScalar(type),
    );
}

export function Const(
    val: number,
    type: string | Scalar = Scalar.i64,
): ConstOp {
    return new ConstOp(val, parseScalar(type));
}

export function Binary(
    ope: string | Operator,
    lhs: BaseValue,
    rhs: BaseValue,
): BinaryOp {
    return new BinaryOp(parseOperator(ope), lhs, rhs);
}

export function Unary(
    ope: string | UnaryOperator,
    value: BaseValue,
): UnaryOp {
    return new UnaryOp(parseUnaryOperator(ope), value);
}

export function Math(
    ope: string | MathOperator,
    value: BaseValue,
): MathOp {
    return new MathOp(parseMathOperator(ope), value);
}

export function Set(var_: VarOp, val: SetValue): SetOp {
    return new SetOp(var_, val);
}

export function While(
    cond: BaseValue,
    thenBlock: readonly BaseValue[],
): WhileOp {
    return new WhileOp(cond, thenBlock);
}

export function Cond(
    cond: BaseValue,
    thenBlock: readonly BaseValue[],
    elseBlock?: readonly BaseValue[],
): CondOp {
    return new CondOp(cond, thenBlock, elseBlock);
}

export function Call(
    name: string,
    args: readonly BaseValue[] = [],
): CallOp {
    return new CallOp(name, args);
}

export function Print(value: BaseValue): PrintOp {
    return new PrintOp(value);
}

export function Alloc(
    name: string,
    type: string | TyNode,
    size: readonly AllocSize[] = [],
): AllocOp {
    return new AllocOp(name, parseTyOrScalar(type), size);
}

export function Alloca(
    name: string,
    type: string | TyNode,
    size: readonly AllocSize[] = [],
): AllocaOp {
    return new AllocaOp(name, parseTyOrScalar(type), size);
}

// Re-export parseTy for callers that already hold a JSON type blob.
export { parseTy, parseScalar };
