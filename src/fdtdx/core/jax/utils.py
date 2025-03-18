from typing import Literal
import jax


def check_shape_dtype(
    arrays: dict[str, jax.Array] | jax.Array,
    expected_shape_dtypes: dict[str, jax.ShapeDtypeStruct] | jax.ShapeDtypeStruct,
    method: Literal["exact", "arrays_only"] = "exact"
):
    if isinstance(arrays, jax.Array) == isinstance(expected_shape_dtypes, dict):
        arr_str = f"{arrays.shape}" if isinstance(arrays, jax.Array) else str(arrays.keys())
        raise Exception(
            f"Got different structures in arrays: {expected_shape_dtypes=}, \n{arr_str=}"
        )
    if not isinstance(arrays, dict):
        arrays = {'dummy': arrays}
    if not isinstance(expected_shape_dtypes, dict):
        expected_shape_dtypes = {'dummy': expected_shape_dtypes}
    if method == "exact" and len(arrays) != len(expected_shape_dtypes):
        raise Exception(
            f"Arrays and expected dict have different lengths: "
            f"{arrays.keys()=} \n\n but {expected_shape_dtypes=}"
        )
    for k, arr in arrays.items():
        exp_shape_dtype = expected_shape_dtypes[k]
        if arr.dtype != exp_shape_dtype.dtype:
            raise Exception(f"Wrong dtype: {exp_shape_dtype.dtype} != {arr.dtype}")
        if arr.shape != exp_shape_dtype.shape:
            raise Exception(f"Wrong shape: {exp_shape_dtype.shape} != {arr.shape}")
