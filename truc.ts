// Generated from Pydantic AST models — DO NOT EDIT.

// Types
export type Scalar = "i64" | "i32" | "i16" | "i8" | "i1" | "I64" | "I32" | "I16" | "I8" | "I1" | "f16" | "f32" | "f64" | "f80" | "f128" | "index" ;
export type OperatorOp = "+" | "-" | "*" | "/" | "/f" | "+f" | "-f" | "*f" | "and" | "or" | "xor" | "==" | "!=" | ">" | "<" | ">=" | "<=" ;
export type UnaryOperator = "-" | "!" ;
export type MathOperator = "sqrt" ;

// Types union
export type TyNode = TyBuffer | TyScalar | TyPtr | TyMemref | TyStruct | TySOA | TySSA;
export type JsonOp = ConstOp | AllocaOp | BinaryOp | WhileOp | IfOp | SetOp | VarOp | AllocOp | MathOp | UnaryOp | CallOp | PrintOp;
export type ModuleStatement = FunctionOp | DefineFunctionOp | DefineStructOp;
export type ReturnTypes = TyNode[];

// Tuples
export type StructField = [string, TyNode, number, number];
export type FunctionArg = [string, TyNode];

// Class
export class AllocOp {
	op: "alloc" = "alloc";
	name: string;
	type: TyNode;
	size: (number | VarOp)[];

	constructor(
		name: string,
		type: TyNode,
		size: (number | VarOp)[],
	) {
		this.name = name;
		this.type = type;
		this.size = size;
	}
}
export class AllocaOp {
	op: "alloca" = "alloca";
	name: string;
	type: TyNode;
	size: (number | VarOp)[];

	constructor(
		name: string,
		type: TyNode,
		size: (number | VarOp)[],
	) {
		this.name = name;
		this.type = type;
		this.size = size;
	}
}
export class BinaryOp {
	op: "binary" = "binary";
	lhs: JsonOp;
	rhs: JsonOp;
	ope: OperatorOp;

	constructor(
		lhs: JsonOp,
		rhs: JsonOp,
		ope: OperatorOp,
	) {
		this.lhs = lhs;
		this.rhs = rhs;
		this.ope = ope;
	}
}
export class CallOp {
	op: "call" = "call";
	name: string;
	args: JsonOp[] = [];

	constructor(
		name: string,
		args: JsonOp[] = [],
	) {
		this.name = name;
		this.args = args;
	}
}
export class ConstOp {
	op: "const" = "const";
	val: number;
	type: Scalar = "i64";

	constructor(
		val: number,
	) {
		this.val = val;
	}
}
export class DefineFunctionOp {
	op: "define_function" = "define_function";
	name: string;
	args: [string, TyNode][] = [];
	return_types: TyNode[] = [];

	constructor(
		name: string,
		args: [string, TyNode][] = [],
		return_types: TyNode[] = [],
	) {
		this.name = name;
		this.args = args;
		this.return_types = return_types;
	}
}
export class DefineStructOp {
	op: "define struct" = "define struct";
	name: string;
	size: number;
	fields: StructField[];

	constructor(
		name: string,
		size: number,
		fields: StructField[],
	) {
		this.name = name;
		this.size = size;
		this.fields = fields;
	}
}
export class FunctionOp {
	op: "function" = "function";
	name: string;
	args: [string, TyNode][] = [];
	body: JsonOp[] = [];

	constructor(
		name: string,
		args: [string, TyNode][] = [],
		body: JsonOp[] = [],
	) {
		this.name = name;
		this.args = args;
		this.body = body;
	}
}
export class IfOp {
	op: "if" = "if";
	cond: JsonOp;
	thenBlock: JsonOp[];
	elseBlock: JsonOp[] | null = null;

	constructor(
		cond: JsonOp,
		thenBlock: JsonOp[],
		elseBlock: JsonOp[] | null = null,
	) {
		this.cond = cond;
		this.thenBlock = thenBlock;
		this.elseBlock = elseBlock;
	}
}
export class MathOp {
	op: "math" = "math";
	ope: MathOperator;
	value: JsonOp;

	constructor(
		ope: MathOperator,
		value: JsonOp,
	) {
		this.ope = ope;
		this.value = value;
	}
}
export class ModuleJsonOp {
	op: "module" = "module";
	body: ModuleStatement[] = [];

	constructor(
		body: ModuleStatement[] = [],
	) {
		this.body = body;
	}
}
export class PrintOp {
	op: "print" = "print";
	value: JsonOp;

	constructor(
		value: JsonOp,
	) {
		this.value = value;
	}
}
export class SetOp {
	op: "set" = "set";
	var: VarOp;
	val: BinaryOp | ConstOp | VarOp | CallOp | UnaryOp;

	constructor(
		var_: VarOp,
		val: BinaryOp | ConstOp | VarOp | CallOp | UnaryOp,
	) {
		this.var = var_;
		this.val = val;
	}
}
export class TyBuffer {
	type: "buffer" = "buffer";
	dims: (number | null)[];
	base: string;

	constructor(
		dims: (number | null)[],
		base: string,
	) {
		this.dims = dims;
		this.base = base;
	}
}
export class TyMemref {
	type: "memref" = "memref";
	dims: (number | null)[];
	base: TyNode;

	constructor(
		dims: (number | null)[],
		base: TyNode,
	) {
		this.dims = dims;
		this.base = base;
	}
}
export class TyPtr {
	type: "ptr" = "ptr";
	base: TyNode;

	constructor(
		base: TyNode,
	) {
		this.base = base;
	}
}
export class TySOA {
	type: "soa" = "soa";
	dims: (number | null)[];
	base: string;

	constructor(
		dims: (number | null)[],
		base: string,
	) {
		this.dims = dims;
		this.base = base;
	}
}
export class TySSA {
	type: "ssa" = "ssa";

	constructor(
	) {
	}
}
export class TyScalar {
	type: "scalar" = "scalar";
	name: Scalar;

	constructor(
		name: Scalar,
	) {
		this.name = name;
	}
}
export class TyStruct {
	type: "struct" = "struct";
	name: string;

	constructor(
		name: string,
	) {
		this.name = name;
	}
}
export class UnaryOp {
	op: "unary" = "unary";
	ope: UnaryOperator;
	value: JsonOp;

	constructor(
		ope: UnaryOperator,
		value: JsonOp,
	) {
		this.ope = ope;
		this.value = value;
	}
}
export class VarOp {
	op: "var" = "var";
	name: string;
	indices: (number | string | VarOp)[];
	type: TyNode | null = null;

	constructor(
		name: string,
		indices: (number | string | VarOp)[],
	) {
		this.name = name;
		this.indices = indices;
	}
}
export class WhileOp {
	op: "while" = "while";
	cond: JsonOp;
	thenBlock: JsonOp[] = [];

	constructor(
		cond: JsonOp,
		thenBlock: JsonOp[] = [],
	) {
		this.cond = cond;
		this.thenBlock = thenBlock;
	}
}
