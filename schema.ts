
// Generated from Pydantic AST models - DO NOT EDIT.

// Manual alias
export type StructAttribut = [string, TyNode, number, number];
export type FunctionArg = [string, TyNode];
export type ReturnTypes = TyNode[];

// Enum
export type Scalar = "i64" | "i32" | "i16" | "i8" | "i1" | "I64" | "I32" | "I16" | "I8" | "I1" | "f16" | "f32" | "f64" | "f80" | "f128" | "index";

export type OperatorOp = "+" | "-" | "*" | "/" | "/f" | "+f" | "-f" | "*f" | "and" | "or" | "xor" | "==" | "!=" | ">" | "<" | ">=" | "<=";

export type UnaryOperator = "-" | "-f" | "!";

export type MathOperator = "sqrt";

// Unions
export type TyNode = TyNotSupported | TySOA | TySSA | TyMemref | TyBuffer | TyStruct | TyMdspan | TyScalar | TyPtr;

export type JsonOp = BinaryOp | SetOp | AllocaOp | MathOp | AllocOp | NotSupportedOp | PrintOp | IfOp | UnaryOp | CallOp | VarOp | CommentOp | ConstOp | WhileOp;

export type ModuleStatement = DefineStructOp | DefineFunctionOp | FunctionOp | CommentOp;

export type other = ModuleJsonOp;


// Type Guards
const TY_NODE_SET = new Set(["notSupported", "soa", "ssa", "memref", "buffer", "struct", "mdspan", "scalar", "ptr"]);
export function isTyNode(node: any): node is TyNode {
	return typeof node === "object" && node !== null && TY_NODE_SET.has(node.type);
}

const JSON_OP_SET = new Set(["binary", "set", "alloca", "math", "alloc", "notSupported", "print", "if", "unary", "call", "var", "comment", "const", "while"]);
export function isJsonOp(node: any): node is JsonOp {
	return typeof node === "object" && node !== null && JSON_OP_SET.has(node.op);
}

const MODULE_STATEMENT_SET = new Set(["define struct", "define_function", "function", "comment"]);
export function isModuleStatement(node: any): node is ModuleStatement {
	return typeof node === "object" && node !== null && MODULE_STATEMENT_SET.has(node.op);
}

const OTHER_SET = new Set(["module"]);
export function isother(node: any): node is other {
	return typeof node === "object" && node !== null && OTHER_SET.has(node.op);
}


// Class
export class AllocOp {
	static readonly op = "alloc";
	op: "alloc" = "alloc";
	name: string;
	type: TyNode;
	size: (number | VarOp)[] = [];

	constructor(
		name: string,
		type_: TyNode,
		size: (number | VarOp)[] = [],
	) {
		this.name = name;
		this.type = type_;
		this.size = size;
	}
}
export class AllocaOp {
	static readonly op = "alloca";
	op: "alloca" = "alloca";
	name: string;
	type: TyNode;
	size: (number | VarOp)[] = [];

	constructor(
		name: string,
		type_: TyNode,
		size: (number | VarOp)[] = [],
	) {
		this.name = name;
		this.type = type_;
		this.size = size;
	}
}
export class BinaryOp {
	static readonly op = "binary";
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
	static readonly op = "call";
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
export class CommentOp {
	static readonly op = "comment";
	op: "comment" = "comment";
	msg: string;

	constructor(
		msg: string,
	) {
		this.msg = msg;
	}
}
export class ConstOp {
	static readonly op = "const";
	op: "const" = "const";
	val: number | boolean;
	type: Scalar | null = null;

	constructor(
		val: number | boolean,
		type_: Scalar | null = null,
	) {
		this.val = val;
		this.type = type_;
	}
}
export class DefineFunctionOp {
	static readonly op = "define_function";
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
	static readonly op = "define struct";
	op: "define struct" = "define struct";
	name: string;
	size: number;
	fields: StructAttribut[];

	constructor(
		name: string,
		size: number,
		fields: StructAttribut[],
	) {
		this.name = name;
		this.size = size;
		this.fields = fields;
	}
}
export class FunctionOp {
	static readonly op = "function";
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
	static readonly op = "if";
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
	static readonly op = "math";
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
	static readonly op = "module";
	op: "module" = "module";
	body: ModuleStatement[] = [];

	constructor(
		body: ModuleStatement[] = [],
	) {
		this.body = body;
	}
}
export class NotSupportedOp {
	static readonly op = "notSupported";
	op: "notSupported" = "notSupported";
	msg: string;

	constructor(
		msg: string,
	) {
		this.msg = msg;
	}
}
export class PrintOp {
	static readonly op = "print";
	op: "print" = "print";
	value: JsonOp;

	constructor(
		value: JsonOp,
	) {
		this.value = value;
	}
}
export class SetOp {
	static readonly op = "set";
	op: "set" = "set";
	var: VarOp;
	val: JsonOp;

	constructor(
		var_: VarOp,
		val: JsonOp,
	) {
		this.var = var_;
		this.val = val;
	}
}
export class TyBuffer {
	static readonly type = "buffer";
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
export class TyMdspan {
	static readonly type = "mdspan";
	type: "mdspan" = "mdspan";
	dims: number | null;
	base: TyNode;

	constructor(
		dims: number | null,
		base: TyNode,
	) {
		this.dims = dims;
		this.base = base;
	}
}
export class TyMemref {
	static readonly type = "memref";
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
export class TyNotSupported {
	static readonly type = "notSupported";
	type: "notSupported" = "notSupported";
	msg: string;

	constructor(
		msg: string,
	) {
		this.msg = msg;
	}
}
export class TyPtr {
	static readonly type = "ptr";
	type: "ptr" = "ptr";
	base: TyNode;

	constructor(
		base: TyNode,
	) {
		this.base = base;
	}
}
export class TySOA {
	static readonly type = "soa";
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
	static readonly type = "ssa";
	type: "ssa" = "ssa";

	constructor(
	) {
	}
}
export class TyScalar {
	static readonly type = "scalar";
	type: "scalar" = "scalar";
	name: Scalar;

	constructor(
		name: Scalar,
	) {
		this.name = name;
	}
}
export class TyStruct {
	static readonly type = "struct";
	type: "struct" = "struct";
	name: string;

	constructor(
		name: string,
	) {
		this.name = name;
	}
}
export class UnaryOp {
	static readonly op = "unary";
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
	static readonly op = "var";
	op: "var" = "var";
	name: string;
	indices: (number | string | VarOp)[] = [];
	type: TyNode | null = null;

	constructor(
		name: string,
		indices: (number | string | VarOp)[] = [],
		type_: TyNode | null = null,
	) {
		this.name = name;
		this.indices = indices;
		this.type = type_;
	}
}
export class WhileOp {
	static readonly op = "while";
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
