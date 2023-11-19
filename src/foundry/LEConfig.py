"""LEConfig module: contains the level editor configuration variables"""

from panda3d.core import ConfigVariableList, ConfigVariableString, ConfigVariableDouble, ConfigVariableInt

unit_scale = ConfigVariableDouble(
  "unit-scale", 16.0,
  "Specify the unit scale multiplier."
)

fgd_files = ConfigVariableList(
  "fgd-file",
  "List of FGD files that are to be loaded by the level editor")

default_material = ConfigVariableString(
  "default-material",
  "materials/brick/brickwall001.mto",
  #"maps/smiley.txo",
  "The default material to use for solids")

default_point_entity = ConfigVariableString(
  "default-point-entity", "prop_static",
  "The default point entity")

default_solid_entity = ConfigVariableString(
  "default-solid-entity", "func_wall",
  "The default solid/brush entity. Brushes that get tied to entities are this "
  "entity by default.")

default_texture_scale = ConfigVariableDouble(
  "default-texture-scale", 1.0,
  "The default texture scale for solid faces.")

default_lightmap_scale = ConfigVariableInt(
  "default-lightmap-scale", 16,
  "The default lightmap scale for solid faces. Lower value = more detailed")

default_prop_model = ConfigVariableString(
  "default-prop-model", "models/misc/smiley.bam",
  "The default model used when placing a prop_static or prop_dynamic entity.")
