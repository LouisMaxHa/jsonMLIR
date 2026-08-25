import sys

def SetReal3(result, v1, ope: str, v2, skip_att_v2=False):
    return [
        Set(
            Var(result[0], result[1:] + [attribut]),
            Binary(
                ope,
                Var(v1[0], v1[1:] + [attribut]),
                Var(v2[0], v2[1:] + ([attribut] if not skip_att_v2 else [])),
            ),
        )
        for attribut in ["x", "y", "z"]
    ]


def CopyReal3(result, source):
    return [
        Set(Var(result[0], result[1:] + [attribut]), Var(source[0], source[1:] + [attribut]))
        for attribut in ["x", "y", "z"]
    ]


def CrossReal3(result, v1, v2):
    """result = v1 × v2"""
    return [
        Set(
            Var(result[0], result[1:] + ["x"]),
            Binary(
                "-f",
                Binary("*f", Var(v1[0], v1[1:] + ["y"]), Var(v2[0], v2[1:] + ["z"])),
                Binary("*f", Var(v1[0], v1[1:] + ["z"]), Var(v2[0], v2[1:] + ["y"])),
            ),
        ),
        Set(
            Var(result[0], result[1:] + ["y"]),
            Binary(
                "-f",
                Binary("*f", Var(v1[0], v1[1:] + ["z"]), Var(v2[0], v2[1:] + ["x"])),
                Binary("*f", Var(v1[0], v1[1:] + ["x"]), Var(v2[0], v2[1:] + ["z"])),
            ),
        ),
        Set(
            Var(result[0], result[1:] + ["z"]),
            Binary(
                "-f",
                Binary("*f", Var(v1[0], v1[1:] + ["x"]), Var(v2[0], v2[1:] + ["y"])),
                Binary("*f", Var(v1[0], v1[1:] + ["y"]), Var(v2[0], v2[1:] + ["x"])),
            ),
        ),
    ]


def SumReal3(result, terms):
    ops = CopyReal3(result, [terms[0]])
    for term in terms[1:]:
        ops += SetReal3(result, result, "+f", [term])
    return ops


def flatten(lst):
    flat_list = []
    for element in lst:
        if isinstance(element, list):
            flat_list.extend(flatten(element))
        else:
            flat_list.append(element)
    return flat_list


# Normales : (nom, noeud_a, noeud_b, index centre de face)
_NORMALS = [
    ("n1a04", 0, 3, 0), ("n1a03", 3, 2, 0), ("n1a02", 2, 1, 0), ("n1a01", 1, 0, 0),
    ("n2a05", 0, 4, 1), ("n2a12", 4, 7, 1), ("n2a08", 7, 3, 1), ("n2a04", 3, 0, 1),
    ("n3a01", 0, 1, 2), ("n3a06", 1, 5, 2), ("n3a09", 5, 4, 2), ("n3a05", 4, 0, 2),
    ("n4a09", 4, 5, 3), ("n4a10", 5, 6, 3), ("n4a11", 6, 7, 3), ("n4a12", 7, 4, 3),
    ("n5a02", 1, 2, 4), ("n5a07", 2, 6, 4), ("n5a10", 6, 5, 4), ("n5a06", 5, 1, 4),
    ("n6a03", 2, 3, 5), ("n6a08", 3, 7, 5), ("n6a11", 7, 6, 5), ("n6a07", 6, 2, 5),
]

# cqs[i] = (five * sum(five_terms) + sum(one_terms)) / 12
_CQS = [
    (["n1a01", "n1a04", "n2a04", "n2a05", "n3a05", "n3a01"],
     ["n1a02", "n1a03", "n2a08", "n2a12", "n3a06", "n3a09"]),
    (["n1a01", "n1a02", "n3a01", "n3a06", "n5a06", "n5a02"],
     ["n1a04", "n1a03", "n3a09", "n3a05", "n5a10", "n5a07"]),
    (["n1a02", "n1a03", "n5a07", "n5a02", "n6a07", "n6a03"],
     ["n1a01", "n1a04", "n5a06", "n5a10", "n6a11", "n6a08"]),
    (["n1a03", "n1a04", "n2a08", "n2a04", "n6a08", "n6a03"],
     ["n1a01", "n1a02", "n2a05", "n2a12", "n6a07", "n6a11"]),
    (["n2a05", "n2a12", "n3a05", "n3a09", "n4a09", "n4a12"],
     ["n2a08", "n2a04", "n3a01", "n3a06", "n4a10", "n4a11"]),
    (["n3a06", "n3a09", "n4a09", "n4a10", "n5a10", "n5a06"],
     ["n3a01", "n3a05", "n4a12", "n4a11", "n5a07", "n5a02"]),
    (["n4a11", "n4a10", "n5a10", "n5a07", "n6a07", "n6a11"],
     ["n4a12", "n4a09", "n5a06", "n5a02", "n6a03", "n6a08"]),
    (["n2a08", "n2a12", "n4a12", "n4a11", "n6a11", "n6a08"],
     ["n2a04", "n2a05", "n4a09", "n4a10", "n6a07", "n6a03"]),
]


def emit_normal(name, na, nb, face_idx):
    """n = 0.5 * cross(node[na] - face[face_idx], node[nb] - face[face_idx])"""
    return [
        Alloca(f"{name}_a", TyStruct("Real3")),
        Alloca(f"{name}_b", TyStruct("Real3")),
        Alloca(name, TyStruct("Real3")),
        *SetReal3([f"{name}_a"], ["node_coord", na], "-f", ["face_coord", face_idx]),
        *SetReal3([f"{name}_b"], ["node_coord", nb], "-f", ["face_coord", face_idx]),
        *CrossReal3([name], [f"{name}_a"], [f"{name}_b"]),
        *SetReal3([name], [name], "*f", ["demi"], skip_att_v2=True),
    ]


def emit_cqs(i, five_terms, one_terms):
    return [
        Alloca(f"sum5_{i}", TyStruct("Real3")),
        Alloca(f"sum1_{i}", TyStruct("Real3")),
        *SumReal3([f"sum5_{i}"], five_terms),
        *SumReal3([f"sum1_{i}"], one_terms),
        *SetReal3([f"sum5_{i}"], [f"sum5_{i}"], "*f", ["five"], skip_att_v2=True),
        *SetReal3([f"sum5_{i}"], [f"sum5_{i}"], "+f", [f"sum1_{i}"]),
        *SetReal3([f"sum5_{i}"], [f"sum5_{i}"], "*f", ["real_1div12"], skip_att_v2=True),
        *CopyReal3(["cqs", i], [f"sum5_{i}"]),
    ]


from jsonmlir.operations.dsl import (
    Alloca,
    Binary,
    Call,
    Const,
    DefineFunction,
    DefineStruct,
    Function,
    Math,
    Module,
    Set,
    Var,
    While,
)
from jsonmlir.pipeline.compiler import compiler
from jsonmlir.utils.enum_scalars import Scalar
from jsonmlir.variables.ty.ty_memref import TyMemref
from jsonmlir.variables.ty.ty_ptr import TyPtr
from jsonmlir.variables.ty.ty_scalar import TyScalar
from jsonmlir.variables.ty.ty_struct import TyStruct

module = Module([
    DefineStruct(
        "Real3", 24, [
            ("x", "f64", 0, 8),
            ("y", "f64", 8, 8),
            ("z", "f64", 16, 8),
        ]
    ),
    # CSR cell→node (LLVM: { ptr, ptr, ptr, i32, i32 }, 32 octets)
    DefineStruct(
        "ItemConnectivityContainerView", 32, [
            ("items", TyPtr(TyMemref([None], TyScalar(Scalar.i32))), 0, 8),
            ("indexes", TyPtr(TyMemref([None], TyScalar(Scalar.i32))), 8, 8),
            ("nb", TyPtr(TyMemref([None], TyScalar(Scalar.i32))), 16, 8),
            ("unused0", TyScalar(Scalar.i32), 24, 4),
            ("unused1", TyScalar(Scalar.i32), 28, 4),
        ]
    ),
    # Vue retournée par cnc.nodes(cid) (LLVM: { ptr, i32, i32 }, 16 octets)
    DefineStruct(
        "ItemLocalIdListContainerView", 16, [
            ("m_local_ids", TyPtr(TyMemref([None], TyScalar(Scalar.i32))), 0, 8),
            ("m_local_id_offset", TyScalar(Scalar.i32), 8, 4),
            ("m_size", TyScalar(Scalar.i32), 12, 4),
        ]
    ),
    DefineStruct(
        "ComputeGeometricValuesView", 80, [
            ("in_node_coord", TyPtr(TyMemref([None], TyStruct("Real3"))), 0, 16),
            ("in_out_cell_cqs", TyPtr(TyMemref([None, 8], TyStruct("Real3"))), 16, 16),
            ("in_out_volume", TyPtr(TyMemref([None], TyScalar(Scalar.f64))), 32, 16),
            ("out_old_volume", TyPtr(TyMemref([None], TyScalar(Scalar.f64))), 48, 16),
            ("out_caracteristic_length", TyPtr(TyMemref([None], TyScalar(Scalar.f64))), 64, 16),
        ]
    ),
    DefineFunction(
        "normL2",
        [("r1", TyStruct("Real3"))],
        [TyScalar(Scalar.f64)],
    ),
    Function(
        "normL2", [
            ("r1", TyStruct("Real3"))
        ], [Math("sqrt",
                Binary("+f",
                    Binary("*f", Var("r1", ["x"]), Var("r1", ["x"])),
                    Binary("+f",
                        Binary("*f", Var("r1", ["y"]), Var("r1", ["y"])),
                        Binary("*f", Var("r1", ["z"]), Var("r1", ["z"]))
                    )
                )
            )
        ],
    ),
    DefineFunction(
        "dot",
        [("r1", TyStruct("Real3")), ("r2", TyStruct("Real3"))],
        [TyScalar(Scalar.f64)],
    ),
    Function(
        "dot",
        [
            ("r1", TyStruct("Real3")),
            ("r2", TyStruct("Real3")),
        ],
        [
            Binary(
                "+f",
                Binary("*f", Var("r1", ["x"]), Var("r2", ["x"])),
                Binary(
                    "+f",
                    Binary("*f", Var("r1", ["y"]), Var("r2", ["y"])),
                    Binary("*f", Var("r1", ["z"]), Var("r2", ["z"])),
                ),
            )
        ],
    ),
    # MicroHydroModule::computeCQs (l.626-726)
    DefineFunction(
        "computeCQs",
        [
            ("node_coord", TyMemref([8], TyStruct("Real3"))),
            ("face_coord", TyMemref([6], TyStruct("Real3"))),
            ("cqs", TyMemref([8], TyStruct("Real3"))),
        ],
        [],
    ),
    Function(
        "computeCQs",
        [
            ("node_coord", TyMemref([8], TyStruct("Real3"))),
            ("face_coord", TyMemref([6], TyStruct("Real3"))),
            ("cqs", TyMemref([8], TyStruct("Real3"))),
        ],
        [
            Set(Var("demi", type=TyScalar(Scalar.f64)), Const(0.5, type="f64")),
            Set(Var("five", type=TyScalar(Scalar.f64)), Const(5.0, type="f64")),
            Set(Var("real_1div12", type=TyScalar(Scalar.f64)), Const(1.0 / 12.0, type="f64")),
            *flatten([emit_normal(name, na, nb, fi) for name, na, nb, fi in _NORMALS]),
            *flatten([emit_cqs(i, five, one) for i, (five, one) in enumerate(_CQS)])
        ],
    ),
    Function(
        "main_ciface", [
            ("cnc", TyStruct("ItemConnectivityContainerView")),
            ("in_node_coord", TyMemref([None], TyStruct("Real3"))),
            ("cid", TyScalar(Scalar.i64)),
            ("in_out_cell_cqs", TyMemref([8], TyStruct("Real3"))),
            ("in_out_volume", TyMemref([100], TyScalar(Scalar.f64))),
            ("out_old_volume", TyMemref([100], TyScalar(Scalar.f64))),
            ("out_caracteristic_length", TyMemref([100], TyScalar(Scalar.f64))),
        ], [  # pyright: ignore[reportUnknownArgumentType]
            # --- cnc.nodes(cid) : slice CSR items[indexes[cid] .. + nb[cid]] ---
            Set(
                Var("nodes_offset", type=TyScalar(Scalar.i32)),
                Var("cnc", ["indexes", "*", Var("cid")]),
            ),
            Set(
                Var("nodes_size", type=TyScalar(Scalar.i32)),
                Var("cnc", ["nb", "*", Var("cid")]),
            ),
            Alloca("nodes", TyStruct("ItemLocalIdListContainerView")),
            Set(Var("nodes", ["m_local_id_offset"]), Const(0, type=Scalar.i32)),
            Set(Var("nodes", ["m_size"]), Var("nodes_size")),
            # Matérialise nodes[i] = items[indexes[cid] + i] (+ offset 0)
            Alloca("nodes_ids", TyMemref([8], TyScalar(Scalar.i32))),
            *flatten([
                [
                    Set(
                        Var("tmp_idx", type=TyScalar(Scalar.i32)),
                        Binary("+", Var("nodes_offset"), Const(i, type=Scalar.i32)),
                    ),
                    Set(
                        Var("nodes_ids", [i]),
                        Var("cnc", ["items", "*", Var("tmp_idx")]),
                    ),
                ]
                for i in range(8)
            ]),

            # Copie locale des coordonnées : coord[i] = in_node_coord[nodes[i]]
            Alloca("coord", TyMemref([8], TyStruct("Real3"))),
            *flatten([
                [
                    Set(Var("nid", type=TyScalar(Scalar.i32)), Var("nodes_ids", [i])),
                    *[
                        Set(
                            Var("coord", [i, attribut]),
                            Var("in_node_coord", [Var("nid"), attribut]),
                        )
                        for attribut in ["x", "y", "z"]
                    ],
                ]
                for i in range(8)
            ]),

            # Centres des faces
            Alloca("face_coord", TyMemref([6], TyStruct("Real3"))),
            Set(Var("c025", type=TyScalar(Scalar.f64)), Const(0.25, type="f64")),
            *flatten([
                SetReal3(["face_coord", i], ["coord", a], "+f", ["coord", b])
                + SetReal3(["face_coord", i], ["face_coord", i], "+f", ["coord", c])
                + SetReal3(["face_coord", i], ["face_coord", i], "+f", ["coord", d])
                + SetReal3(["face_coord", i], ["face_coord", i], "*f", ["c025"], skip_att_v2=True)
                for i, (a, b, c, d) in enumerate([
                    (0, 3, 2, 1),
                    (0, 4, 7, 3),
                    (0, 1, 5, 4),
                    (4, 5, 6, 7),
                    (1, 2, 6, 5),
                    (2, 3, 7, 6),
                ])
            ]),

            # Longueur caractéristique
            Alloca("median1", TyStruct("Real3")),
            Alloca("median2", TyStruct("Real3")),
            Alloca("median3", TyStruct("Real3")),
            *SetReal3(["median1"], ["face_coord", 0], "-f", ["face_coord", 3]),
            *SetReal3(["median2"], ["face_coord", 2], "-f", ["face_coord", 5]),
            *SetReal3(["median3"], ["face_coord", 1], "-f", ["face_coord", 4]),
            Set(Var("d1", type=TyScalar(Scalar.f64)), Call("normL2", [Var("median1")])),
            Set(Var("d2", type=TyScalar(Scalar.f64)), Call("normL2", [Var("median2")])),
            Set(Var("d3", type=TyScalar(Scalar.f64)), Call("normL2", [Var("median3")])),
            Set(
                Var("dx_numerator", type=TyScalar(Scalar.f64)),
                Binary("*f", Var("d1"), Binary("*f", Var("d2"), Var("d3"))),
            ),
            Set(
                Var("dx_denominator", type=TyScalar(Scalar.f64)),
                Binary(
                    "+f",
                    Binary("*f", Var("d1"), Var("d2")),
                    Binary(
                        "+f",
                        Binary("*f", Var("d1"), Var("d3")),
                        Binary("*f", Var("d2"), Var("d3")),
                    ),
                ),
            ),
            Set(
                Var("out_caracteristic_length", [Var("cid")]),
                Binary("/f", Var("dx_numerator"), Var("dx_denominator")),
            ),

            # Résultantes aux sommets
            Call("computeCQs", [Var("coord"), Var("face_coord"), Var("in_out_cell_cqs")]),

            # Volume : sum(dot(coord[i], cqs[i])) / 3
            Set(Var("volume", type=TyScalar(Scalar.f64)), Const(0.0, type="f64")),
            Set(Var("i", type=TyScalar(Scalar.i64)), Const(0, type="i64")),
            While(
                Binary("<", Var("i"), Const(8, type="i64")), [
                    Set(
                        Var("volume"), Binary("+f",
                            Var("volume"),
                            Call("dot",[
                                Var("coord", [Var("i")]),
                                Var("in_out_cell_cqs", [Var("i")]),
                            ]),
                        ),
                    ),
                    Set(Var("i"), Binary("+", Var("i"), Const(1, type="i64"))),
                ],
            ),
            Set(Var("volume"), Binary("/f", Var("volume"), Const(3.0, type="f64"))),
            Set(Var("out_old_volume", [Var("cid")]), Var("in_out_volume", [Var("cid")])),
            Set(Var("in_out_volume", [Var("cid")]), Var("volume")),

            Const(0, type=Scalar.i64),
        ],
    ),
])

compiler(module, [__file__, "--output-name", "librairie4"] + sys.argv[1:])
