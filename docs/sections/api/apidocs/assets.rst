.. currentmodule:: dagster

Asset Stores (Experimental)
=======

Asset Stores
-----

Asset stores are user-provided objects that specify how to store step outputs and retrieve step inputs.

.. autoclass:: AssetStore
    :members:


Asset Stores as Resources
-----

Asset stores are used as resources, which enables users to supply different asset stores for
the same solid outputs in different modes.

.. autofunction:: mem_asset_store

.. autofunction:: fs_asset_store

.. autofunction:: custom_path_fs_asset_store