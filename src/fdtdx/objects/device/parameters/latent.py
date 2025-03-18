from abc import ABC, abstractmethod
import math
from typing import Self

import jax
import jax.numpy as jnp

from fdtdx.config import SimulationConfig
from fdtdx.core.jax.pytrees import ExtendedTreeClass, extended_autoinit, frozen_field, frozen_private_field
from fdtdx.materials import ContinuousMaterialRange, Material


@extended_autoinit
class LatentParamsTransformation(ExtendedTreeClass, ABC):
    _material: dict[str, Material] | ContinuousMaterialRange = frozen_private_field()
    _config: SimulationConfig = frozen_private_field()
    _output_shape_dtypes: dict[str, jax.ShapeDtypeStruct] = frozen_private_field()
    _input_shape_dtypes: dict[str, jax.ShapeDtypeStruct] = frozen_private_field()

    @abstractmethod
    def transform(
        self,
        input_params: dict[str, jax.Array] | jax.Array,
    ) -> dict[str, jax.Array]:
        del input_params
        raise NotImplementedError()

    @abstractmethod
    def _compute_input_shape_dtypes(
        self,
        output_shape_dtypes: dict[str, jax.ShapeDtypeStruct] | jax.ShapeDtypeStruct,
    ) -> dict[str, jax.ShapeDtypeStruct] | jax.ShapeDtypeStruct:
        raise NotImplementedError()

    def init_module(
        self: Self,
        config: SimulationConfig,
        material: dict[str, Material] | ContinuousMaterialRange,
        output_shape_dtypes: dict[str, jax.ShapeDtypeStruct] | jax.ShapeDtypeStruct,
    ) -> Self:
        self = self.aset("_config", config)
        self = self.aset("_material", material)
        self = self.aset("_output_shape_dtypes", output_shape_dtypes)
        input_shape_dtypes = self._compute_input_shape_dtypes(self._output_shape_dtypes)
        self = self.aset("_input_shape_dtypes", input_shape_dtypes)
        return self


@extended_autoinit
class SameShapeDtypeLatentTransform(LatentParamsTransformation, ABC):
    def _compute_input_shape_dtypes(
        self,
        output_shape_dtypes: dict[str, jax.ShapeDtypeStruct] | jax.ShapeDtypeStruct,
    ) -> dict[str, jax.ShapeDtypeStruct] | jax.ShapeDtypeStruct:
        return output_shape_dtypes


@extended_autoinit
class StandardToInversePermittivityRange(SameShapeDtypeLatentTransform):
    """Maps standard [0,1] range to inverse permittivity range.

    Linearly maps values from [0,1] to the range between minimum and maximum
    inverse permittivity values allowed by the material configuration.
    """

    def transform(
        self,
        input_params: dict[str, jax.Array] | jax.Array,
    ) -> dict[str, jax.Array] | jax.Array:
        # determine minimum and maximum allowed permittivity
        max_inv_perm, min_inv_perm = -math.inf, math.inf
        if isinstance(self._material, dict):
            for k, v in self._material.items():
                p = 1 / v.permittivity
                if p > max_inv_perm:
                    max_inv_perm = p
                if p < min_inv_perm:
                    min_inv_perm = p
        elif isinstance(self._material, ContinuousMaterialRange):
            start_perm = self._material.start_material.permittivity
            end_perm = self._material.end_material.permittivity
            max_inv_perm = max(start_perm, end_perm)
            min_inv_perm = min(start_perm, end_perm)

        # transform
        if isinstance(input_params, dict):
            result = {}
            for k, v in input_params.items():
                mapped = v * (max_inv_perm - min_inv_perm) + min_inv_perm
                result[k] = mapped
        else:
            result = input_params * (max_inv_perm - min_inv_perm) + min_inv_perm
        return result


@extended_autoinit
class StandardToCustomRange(SameShapeDtypeLatentTransform):
    """Maps standard [0,1] range to custom range [min_value, max_value].

    Linearly maps values from [0,1] to a custom range specified by min_value
    and max_value parameters.

    Attributes:
        min_value: Minimum value of target range
        max_value: Maximum value of target range
    """

    min_value: float = frozen_field(default=0)
    max_value: float = frozen_field(default=1)

    def transform(
        self,
        input_params: dict[str, jax.Array] | jax.Array,
    ) -> dict[str, jax.Array] | jax.Array:
        if isinstance(input_params, dict):
            result = {}
            for k, v in input_params.items():
                mapped = v * (self.max_value - self.min_value) + self.min_value
                result[k] = mapped
        else:
            result = input_params * (self.max_value - self.min_value) + self.min_value
        return result


@extended_autoinit
class StandardToPlusOneMinusOneRange(StandardToCustomRange):
    """Maps standard [0,1] range to [-1,1] range.

    Special case of StandardToCustomRange that maps to [-1,1] range.
    Used for symmetric value ranges around zero.

    Attributes:
        min_value: Fixed to -1
        max_value: Fixed to 1
    """

    min_value: float = frozen_field(default=-1, init=False)
    max_value: float = frozen_field(default=1, init=False)



# @extended_autoinit
# class ContinuousPermittivityTransition(ConstraintModule):
#     """Maps continuous values to smoothly interpolated permittivity values.

#     Instead of discretizing to the nearest material index, this module performs
#     smooth interpolation between the allowed permittivity values based on the
#     input parameters. This enables continuous transitions between materials.

#     The interpolation is done in the permittivity domain (not inverse permittivity)
#     to maintain physical correctness of the material properties.

#     Note: This module only works with exactly two materials (e.g. air and silicon).
#     """

#     def input_interface(
#         self,
#         output_interface: ConstraintInterface,
#     ) -> ConstraintInterface:
#         if output_interface.type != "inv_permittivity":
#             raise Exception(
#                 "After ContinuousPermittivityTransition can only follow a module using inverse permittivities"
#             )
#         if len(self._allowed_permittivities) != 2:
#             raise Exception(
#                 f"ContinuousPermittivityTransition only works with exactly 2 materials, got {len(self._allowed_permittivities)}"
#             )
#         return ConstraintInterface(
#             type="latent",
#             shapes=output_interface.shapes,
#         )

#     def transform(
#         self,
#         input_params: dict[str, jax.Array],
#     ) -> dict[str, jax.Array]:
#         if len(self._allowed_permittivities) != 2:
#             raise Exception(
#                 f"ContinuousPermittivityTransition only works with exactly 2 materials, got {len(self._allowed_permittivities)}"
#             )

#         result = {}
#         for k, v in input_params.items():
#             # Scale input to [0, 1] range for interpolation
#             v_scaled = (v - v.min()) / (v.max() - v.min())

#             # Get permittivity values for interpolation
#             lower_perm = self._allowed_permittivities[0]
#             upper_perm = self._allowed_permittivities[1]

#             # Interpolate in permittivity domain
#             interpolated_perms = (1 - v_scaled) * lower_perm + v_scaled * upper_perm

#             # Convert to inverse permittivity
#             interpolated_inv_perms = 1.0 / interpolated_perms

#             result[k] = interpolated_inv_perms.astype(self._config.dtype)
#         return result
