Types and values
================

Ty nodes
~~~~~~~~

.. autoclass:: jsonmlir.variables.ty.ty.TyNodeBase
.. autoclass:: jsonmlir.variables.ty.ty_scalar.TyScalar
.. autoclass:: jsonmlir.variables.ty.ty_struct.TyStruct
.. autoclass:: jsonmlir.variables.ty.ty_memref.TyMemref
.. autoclass:: jsonmlir.variables.ty.ty_buffer.TyBuffer
.. autoclass:: jsonmlir.variables.ty.ty_ptr.TyPtr
.. autoclass:: jsonmlir.variables.ty.ty_SSA.TySSA
.. autoclass:: jsonmlir.variables.ty.ty_SOA.TySOA
.. autoclass:: jsonmlir.variables.ty.ty_mdspan.TyMdspan
.. autoclass:: jsonmlir.variables.ty.ty_not_supported.TyNotSupported

.. autofunction:: jsonmlir.variables.ty.ty.dump_ty
.. autofunction:: jsonmlir.variables.ty.ty.parse_ty

Val nodes
~~~~~~~~~

.. autoclass:: jsonmlir.variables.val.val.ValNode
.. autoclass:: jsonmlir.variables.val.val_scalar.ValScalar
.. autoclass:: jsonmlir.variables.val.val_struct.ValStruct
.. autoclass:: jsonmlir.variables.val.val_memref.ValMemref
.. autoclass:: jsonmlir.variables.val.val_buffer.ValBuffer
.. autoclass:: jsonmlir.variables.val.val_ptr.ValPtr
.. autoclass:: jsonmlir.variables.val.val_SSA.ValSSA
.. autoclass:: jsonmlir.variables.val.val_SOA.ValSOA
.. autoclass:: jsonmlir.variables.val.val_mdspan.ValMdspan

.. automodule:: jsonmlir.variables.factory
   :members:

.. automodule:: jsonmlir.variables.memory
   :members: