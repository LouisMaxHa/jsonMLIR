# Memory layout of cnc.nodes
_Exported on 7/27/2026 at 09:41:53 GMT+2 from Cursor (3.5.33)_

---

**User**

@microhydro/src/MicroHydroModule.cc:795 Quelle est l'agencement en mémoire de ce cnc.nodes(cid) ?
Analyse le fichier llvm @microhydro/MicroHydroModule.ll et di tmoi ce qui se cache derrière le pointeur 

---

**Cursor**

Je vais examiner le code autour de `cnc.nodes(cid)` et analyser le LLVM pour identifier l’agencement mémoire derrière ce pointeur.

Je lis les définitions LLVM de `nodes()`, `itemsIds()` et `localId()` pour reconstituer exactement le layout.

`cnc.nodes(cid)` renvoie une **vue CSR** sur les IDs locaux des nœuds de la maille — pas une copie.

## Type LLVM de `nodes`

```101:101:microhydro/MicroHydroModule.ll
%"class.Arcane::impl::ItemLocalIdListContainerView" = type { ptr, i32, i32 }
```

(aliasé en `ItemLocalIdListViewT<Node>` / retourné en ABI comme `{ ptr, i64 }` : les deux `i32` sont packés dans l’`i64`)

| Champ | Type | Rôle |
|-------|------|------|
| `0` | `ptr` | pointeur vers un tableau de `i32` (IDs locaux de nœuds) |
| `1` | `i32` | `local_id_offset` (ici **0**) |
| `2` | `i32` | `size` (nb de nœuds de la maille, typ. **8** pour un hexa) |

## Ce que cache le `ptr`

Ce n’est **pas** un tableau alloué pour la maille. C’est un pointeur **au milieu** du tableau plat de connectivité cell→node.

`cnc` (`ItemConnectivityContainerView`) vaut :

```63:63:microhydro/MicroHydroModule.ll
%"class.Arcane::ItemConnectivityContainerView" = type { ptr, ptr, ptr, i32, i32 }
```

Dans `itemsIds` (appelé par `nodes`) :

```35495:35515:microhydro/MicroHydroModule.ll
  %10 = getelementptr inbounds nuw %"class.Arcane::ItemConnectivityContainerView", ptr %9, i32 0, i32 1
  ...
  %15 = load i32, ptr %14, align 4          ; offset = indexes[cid]
  %16 = getelementptr inbounds nuw %"class.Arcane::ItemConnectivityContainerView", ptr %9, i32 0, i32 0
  ...
  %20 = getelementptr inbounds i32, ptr %17, i64 %19  ; &items[offset]
  %22 = getelementptr inbounds nuw %"class.Arcane::ItemConnectivityContainerView", ptr %9, i32 0, i32 2
  ...
  %27 = load i32, ptr %26, align 4          ; size = nb[cid]
  call void ...ItemLocalIdListViewT...(..., ptr %21, i32 %27, i32 noundef 0)
```

Donc côté `cnc` :

| Champ | Contenu |
|-------|---------|
| `0` | `items` — `i32[]` plat de tous les nœuds connectés |
| `1` | `indexes` — `i32[]`, début de chaque maille dans `items` |
| `2` | `nb` — `i32[]`, nombre de nœuds par maille |

Schéma mémoire :

```
indexes:  [0, 8, 16, ...]     ← indexes[cid]
nb:       [8, 8, 8, ...]      ← size
items:    [n0,n1,...,n7, n0',n1',...]
               ▲
               nodes.ptr = &items[indexes[cid]]
               → size i32 contigus (souvent 8)
```

## Accès `nodes[i]`

`operator[]` → `localId(i)` :

```26916:26925:microhydro/MicroHydroModule.ll
  %10 = getelementptr inbounds i32, ptr %7, i64 %9
  %11 = load i32, ptr %10, align 4
  ...
  %14 = add nsw i32 %11, %13
  ret i32 %14
```

Donc : **`nodes[i] = items[indexes[cid] + i] + local_id_offset`**, avec `local_id_offset = 0` ici → un simple `Int32` (`NodeLocalId`).

En résumé : derrière le pointeur, une **slice de `i32` consécutifs** dans le tableau CSR global des connectivités cell→node, pas des `Node` ni des coordonnées.

