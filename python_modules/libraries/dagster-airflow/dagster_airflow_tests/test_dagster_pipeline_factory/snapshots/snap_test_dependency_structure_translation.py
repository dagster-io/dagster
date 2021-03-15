# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import Snapshot

snapshots = Snapshot()

snapshots['test_complex_dag 1'] = '''{
  "__class__": "DependencyStructureSnapshot",
  "solid_invocation_snaps": [
    {
      "__class__": "SolidInvocationSnap",
      "input_dep_snaps": [
        {
          "__class__": "InputDependencySnap",
          "input_name": "airflow_task_ready",
          "is_dynamic_collect": false,
          "upstream_output_snaps": [
            {
              "__class__": "OutputHandleSnap",
              "output_name": "airflow_task_complete",
              "solid_name": "airflow_create_entry_group"
            }
          ]
        }
      ],
      "is_dynamic_mapped": false,
      "solid_def_name": "airflow_create_entry_gcs",
      "solid_name": "airflow_create_entry_gcs",
      "tags": {}
    },
    {
      "__class__": "SolidInvocationSnap",
      "input_dep_snaps": [
        {
          "__class__": "InputDependencySnap",
          "input_name": "airflow_task_ready",
          "is_dynamic_collect": false,
          "upstream_output_snaps": [
            {
              "__class__": "OutputHandleSnap",
              "output_name": "airflow_task_complete",
              "solid_name": "airflow_create_entry_gcs"
            }
          ]
        }
      ],
      "is_dynamic_mapped": false,
      "solid_def_name": "airflow_create_entry_gcs_result",
      "solid_name": "airflow_create_entry_gcs_result",
      "tags": {}
    },
    {
      "__class__": "SolidInvocationSnap",
      "input_dep_snaps": [
        {
          "__class__": "InputDependencySnap",
          "input_name": "airflow_task_ready",
          "is_dynamic_collect": false,
          "upstream_output_snaps": [
            {
              "__class__": "OutputHandleSnap",
              "output_name": "airflow_task_complete",
              "solid_name": "airflow_create_entry_gcs"
            }
          ]
        }
      ],
      "is_dynamic_mapped": false,
      "solid_def_name": "airflow_create_entry_gcs_result2",
      "solid_name": "airflow_create_entry_gcs_result2",
      "tags": {}
    },
    {
      "__class__": "SolidInvocationSnap",
      "input_dep_snaps": [
        {
          "__class__": "InputDependencySnap",
          "input_name": "airflow_task_ready",
          "is_dynamic_collect": false,
          "upstream_output_snaps": []
        }
      ],
      "is_dynamic_mapped": false,
      "solid_def_name": "airflow_create_entry_group",
      "solid_name": "airflow_create_entry_group",
      "tags": {}
    },
    {
      "__class__": "SolidInvocationSnap",
      "input_dep_snaps": [
        {
          "__class__": "InputDependencySnap",
          "input_name": "airflow_task_ready",
          "is_dynamic_collect": false,
          "upstream_output_snaps": [
            {
              "__class__": "OutputHandleSnap",
              "output_name": "airflow_task_complete",
              "solid_name": "airflow_create_entry_group"
            }
          ]
        }
      ],
      "is_dynamic_mapped": false,
      "solid_def_name": "airflow_create_entry_group_result",
      "solid_name": "airflow_create_entry_group_result",
      "tags": {}
    },
    {
      "__class__": "SolidInvocationSnap",
      "input_dep_snaps": [
        {
          "__class__": "InputDependencySnap",
          "input_name": "airflow_task_ready",
          "is_dynamic_collect": false,
          "upstream_output_snaps": [
            {
              "__class__": "OutputHandleSnap",
              "output_name": "airflow_task_complete",
              "solid_name": "airflow_create_entry_group"
            }
          ]
        }
      ],
      "is_dynamic_mapped": false,
      "solid_def_name": "airflow_create_entry_group_result2",
      "solid_name": "airflow_create_entry_group_result2",
      "tags": {}
    },
    {
      "__class__": "SolidInvocationSnap",
      "input_dep_snaps": [
        {
          "__class__": "InputDependencySnap",
          "input_name": "airflow_task_ready",
          "is_dynamic_collect": false,
          "upstream_output_snaps": [
            {
              "__class__": "OutputHandleSnap",
              "output_name": "airflow_task_complete",
              "solid_name": "airflow_create_tag_template_field"
            }
          ]
        }
      ],
      "is_dynamic_mapped": false,
      "solid_def_name": "airflow_create_tag",
      "solid_name": "airflow_create_tag",
      "tags": {}
    },
    {
      "__class__": "SolidInvocationSnap",
      "input_dep_snaps": [
        {
          "__class__": "InputDependencySnap",
          "input_name": "airflow_task_ready",
          "is_dynamic_collect": false,
          "upstream_output_snaps": [
            {
              "__class__": "OutputHandleSnap",
              "output_name": "airflow_task_complete",
              "solid_name": "airflow_create_tag"
            }
          ]
        }
      ],
      "is_dynamic_mapped": false,
      "solid_def_name": "airflow_create_tag_result",
      "solid_name": "airflow_create_tag_result",
      "tags": {}
    },
    {
      "__class__": "SolidInvocationSnap",
      "input_dep_snaps": [
        {
          "__class__": "InputDependencySnap",
          "input_name": "airflow_task_ready",
          "is_dynamic_collect": false,
          "upstream_output_snaps": [
            {
              "__class__": "OutputHandleSnap",
              "output_name": "airflow_task_complete",
              "solid_name": "airflow_create_tag"
            }
          ]
        }
      ],
      "is_dynamic_mapped": false,
      "solid_def_name": "airflow_create_tag_result2",
      "solid_name": "airflow_create_tag_result2",
      "tags": {}
    },
    {
      "__class__": "SolidInvocationSnap",
      "input_dep_snaps": [
        {
          "__class__": "InputDependencySnap",
          "input_name": "airflow_task_ready",
          "is_dynamic_collect": false,
          "upstream_output_snaps": [
            {
              "__class__": "OutputHandleSnap",
              "output_name": "airflow_task_complete",
              "solid_name": "airflow_create_entry_gcs"
            }
          ]
        }
      ],
      "is_dynamic_mapped": false,
      "solid_def_name": "airflow_create_tag_template",
      "solid_name": "airflow_create_tag_template",
      "tags": {}
    },
    {
      "__class__": "SolidInvocationSnap",
      "input_dep_snaps": [
        {
          "__class__": "InputDependencySnap",
          "input_name": "airflow_task_ready",
          "is_dynamic_collect": false,
          "upstream_output_snaps": [
            {
              "__class__": "OutputHandleSnap",
              "output_name": "airflow_task_complete",
              "solid_name": "airflow_create_tag_template"
            }
          ]
        }
      ],
      "is_dynamic_mapped": false,
      "solid_def_name": "airflow_create_tag_template_field",
      "solid_name": "airflow_create_tag_template_field",
      "tags": {}
    },
    {
      "__class__": "SolidInvocationSnap",
      "input_dep_snaps": [
        {
          "__class__": "InputDependencySnap",
          "input_name": "airflow_task_ready",
          "is_dynamic_collect": false,
          "upstream_output_snaps": [
            {
              "__class__": "OutputHandleSnap",
              "output_name": "airflow_task_complete",
              "solid_name": "airflow_create_tag_template_field"
            }
          ]
        }
      ],
      "is_dynamic_mapped": false,
      "solid_def_name": "airflow_create_tag_template_field_result",
      "solid_name": "airflow_create_tag_template_field_result",
      "tags": {}
    },
    {
      "__class__": "SolidInvocationSnap",
      "input_dep_snaps": [
        {
          "__class__": "InputDependencySnap",
          "input_name": "airflow_task_ready",
          "is_dynamic_collect": false,
          "upstream_output_snaps": [
            {
              "__class__": "OutputHandleSnap",
              "output_name": "airflow_task_complete",
              "solid_name": "airflow_create_tag_template"
            }
          ]
        }
      ],
      "is_dynamic_mapped": false,
      "solid_def_name": "airflow_create_tag_template_result",
      "solid_name": "airflow_create_tag_template_result",
      "tags": {}
    },
    {
      "__class__": "SolidInvocationSnap",
      "input_dep_snaps": [
        {
          "__class__": "InputDependencySnap",
          "input_name": "airflow_task_ready",
          "is_dynamic_collect": false,
          "upstream_output_snaps": [
            {
              "__class__": "OutputHandleSnap",
              "output_name": "airflow_task_complete",
              "solid_name": "airflow_create_tag_template"
            }
          ]
        }
      ],
      "is_dynamic_mapped": false,
      "solid_def_name": "airflow_create_tag_template_result2",
      "solid_name": "airflow_create_tag_template_result2",
      "tags": {}
    },
    {
      "__class__": "SolidInvocationSnap",
      "input_dep_snaps": [
        {
          "__class__": "InputDependencySnap",
          "input_name": "airflow_task_ready",
          "is_dynamic_collect": false,
          "upstream_output_snaps": [
            {
              "__class__": "OutputHandleSnap",
              "output_name": "airflow_task_complete",
              "solid_name": "airflow_create_entry_gcs"
            },
            {
              "__class__": "OutputHandleSnap",
              "output_name": "airflow_task_complete",
              "solid_name": "airflow_delete_entry_group"
            },
            {
              "__class__": "OutputHandleSnap",
              "output_name": "airflow_task_complete",
              "solid_name": "airflow_get_entry"
            },
            {
              "__class__": "OutputHandleSnap",
              "output_name": "airflow_task_complete",
              "solid_name": "airflow_lookup_entry"
            },
            {
              "__class__": "OutputHandleSnap",
              "output_name": "airflow_task_complete",
              "solid_name": "airflow_search_catalog"
            },
            {
              "__class__": "OutputHandleSnap",
              "output_name": "airflow_task_complete",
              "solid_name": "airflow_update_entry"
            }
          ]
        }
      ],
      "is_dynamic_mapped": false,
      "solid_def_name": "airflow_delete_entry",
      "solid_name": "airflow_delete_entry",
      "tags": {}
    },
    {
      "__class__": "SolidInvocationSnap",
      "input_dep_snaps": [
        {
          "__class__": "InputDependencySnap",
          "input_name": "airflow_task_ready",
          "is_dynamic_collect": false,
          "upstream_output_snaps": [
            {
              "__class__": "OutputHandleSnap",
              "output_name": "airflow_task_complete",
              "solid_name": "airflow_create_entry_group"
            },
            {
              "__class__": "OutputHandleSnap",
              "output_name": "airflow_task_complete",
              "solid_name": "airflow_delete_tag_template"
            },
            {
              "__class__": "OutputHandleSnap",
              "output_name": "airflow_task_complete",
              "solid_name": "airflow_get_entry_group"
            },
            {
              "__class__": "OutputHandleSnap",
              "output_name": "airflow_task_complete",
              "solid_name": "airflow_search_catalog"
            }
          ]
        }
      ],
      "is_dynamic_mapped": false,
      "solid_def_name": "airflow_delete_entry_group",
      "solid_name": "airflow_delete_entry_group",
      "tags": {}
    },
    {
      "__class__": "SolidInvocationSnap",
      "input_dep_snaps": [
        {
          "__class__": "InputDependencySnap",
          "input_name": "airflow_task_ready",
          "is_dynamic_collect": false,
          "upstream_output_snaps": [
            {
              "__class__": "OutputHandleSnap",
              "output_name": "airflow_task_complete",
              "solid_name": "airflow_create_tag"
            },
            {
              "__class__": "OutputHandleSnap",
              "output_name": "airflow_task_complete",
              "solid_name": "airflow_list_tags"
            },
            {
              "__class__": "OutputHandleSnap",
              "output_name": "airflow_task_complete",
              "solid_name": "airflow_search_catalog"
            },
            {
              "__class__": "OutputHandleSnap",
              "output_name": "airflow_task_complete",
              "solid_name": "airflow_update_tag"
            }
          ]
        }
      ],
      "is_dynamic_mapped": false,
      "solid_def_name": "airflow_delete_tag",
      "solid_name": "airflow_delete_tag",
      "tags": {}
    },
    {
      "__class__": "SolidInvocationSnap",
      "input_dep_snaps": [
        {
          "__class__": "InputDependencySnap",
          "input_name": "airflow_task_ready",
          "is_dynamic_collect": false,
          "upstream_output_snaps": [
            {
              "__class__": "OutputHandleSnap",
              "output_name": "airflow_task_complete",
              "solid_name": "airflow_delete_tag_template_field"
            },
            {
              "__class__": "OutputHandleSnap",
              "output_name": "airflow_task_complete",
              "solid_name": "airflow_get_tag_template"
            },
            {
              "__class__": "OutputHandleSnap",
              "output_name": "airflow_task_complete",
              "solid_name": "airflow_search_catalog"
            },
            {
              "__class__": "OutputHandleSnap",
              "output_name": "airflow_task_complete",
              "solid_name": "airflow_update_tag_template"
            }
          ]
        }
      ],
      "is_dynamic_mapped": false,
      "solid_def_name": "airflow_delete_tag_template",
      "solid_name": "airflow_delete_tag_template",
      "tags": {}
    },
    {
      "__class__": "SolidInvocationSnap",
      "input_dep_snaps": [
        {
          "__class__": "InputDependencySnap",
          "input_name": "airflow_task_ready",
          "is_dynamic_collect": false,
          "upstream_output_snaps": [
            {
              "__class__": "OutputHandleSnap",
              "output_name": "airflow_task_complete",
              "solid_name": "airflow_create_tag_template"
            },
            {
              "__class__": "OutputHandleSnap",
              "output_name": "airflow_task_complete",
              "solid_name": "airflow_create_tag_template_field"
            },
            {
              "__class__": "OutputHandleSnap",
              "output_name": "airflow_task_complete",
              "solid_name": "airflow_delete_tag"
            },
            {
              "__class__": "OutputHandleSnap",
              "output_name": "airflow_task_complete",
              "solid_name": "airflow_rename_tag_template_field"
            },
            {
              "__class__": "OutputHandleSnap",
              "output_name": "airflow_task_complete",
              "solid_name": "airflow_search_catalog"
            }
          ]
        }
      ],
      "is_dynamic_mapped": false,
      "solid_def_name": "airflow_delete_tag_template_field",
      "solid_name": "airflow_delete_tag_template_field",
      "tags": {}
    },
    {
      "__class__": "SolidInvocationSnap",
      "input_dep_snaps": [
        {
          "__class__": "InputDependencySnap",
          "input_name": "airflow_task_ready",
          "is_dynamic_collect": false,
          "upstream_output_snaps": [
            {
              "__class__": "OutputHandleSnap",
              "output_name": "airflow_task_complete",
              "solid_name": "airflow_create_entry_gcs"
            }
          ]
        }
      ],
      "is_dynamic_mapped": false,
      "solid_def_name": "airflow_get_entry",
      "solid_name": "airflow_get_entry",
      "tags": {}
    },
    {
      "__class__": "SolidInvocationSnap",
      "input_dep_snaps": [
        {
          "__class__": "InputDependencySnap",
          "input_name": "airflow_task_ready",
          "is_dynamic_collect": false,
          "upstream_output_snaps": [
            {
              "__class__": "OutputHandleSnap",
              "output_name": "airflow_task_complete",
              "solid_name": "airflow_create_entry_group"
            }
          ]
        }
      ],
      "is_dynamic_mapped": false,
      "solid_def_name": "airflow_get_entry_group",
      "solid_name": "airflow_get_entry_group",
      "tags": {}
    },
    {
      "__class__": "SolidInvocationSnap",
      "input_dep_snaps": [
        {
          "__class__": "InputDependencySnap",
          "input_name": "airflow_task_ready",
          "is_dynamic_collect": false,
          "upstream_output_snaps": [
            {
              "__class__": "OutputHandleSnap",
              "output_name": "airflow_task_complete",
              "solid_name": "airflow_get_entry_group"
            }
          ]
        }
      ],
      "is_dynamic_mapped": false,
      "solid_def_name": "airflow_get_entry_group_result",
      "solid_name": "airflow_get_entry_group_result",
      "tags": {}
    },
    {
      "__class__": "SolidInvocationSnap",
      "input_dep_snaps": [
        {
          "__class__": "InputDependencySnap",
          "input_name": "airflow_task_ready",
          "is_dynamic_collect": false,
          "upstream_output_snaps": [
            {
              "__class__": "OutputHandleSnap",
              "output_name": "airflow_task_complete",
              "solid_name": "airflow_get_entry"
            }
          ]
        }
      ],
      "is_dynamic_mapped": false,
      "solid_def_name": "airflow_get_entry_result",
      "solid_name": "airflow_get_entry_result",
      "tags": {}
    },
    {
      "__class__": "SolidInvocationSnap",
      "input_dep_snaps": [
        {
          "__class__": "InputDependencySnap",
          "input_name": "airflow_task_ready",
          "is_dynamic_collect": false,
          "upstream_output_snaps": [
            {
              "__class__": "OutputHandleSnap",
              "output_name": "airflow_task_complete",
              "solid_name": "airflow_create_tag_template"
            }
          ]
        }
      ],
      "is_dynamic_mapped": false,
      "solid_def_name": "airflow_get_tag_template",
      "solid_name": "airflow_get_tag_template",
      "tags": {}
    },
    {
      "__class__": "SolidInvocationSnap",
      "input_dep_snaps": [
        {
          "__class__": "InputDependencySnap",
          "input_name": "airflow_task_ready",
          "is_dynamic_collect": false,
          "upstream_output_snaps": [
            {
              "__class__": "OutputHandleSnap",
              "output_name": "airflow_task_complete",
              "solid_name": "airflow_get_tag_template"
            }
          ]
        }
      ],
      "is_dynamic_mapped": false,
      "solid_def_name": "airflow_get_tag_template_result",
      "solid_name": "airflow_get_tag_template_result",
      "tags": {}
    },
    {
      "__class__": "SolidInvocationSnap",
      "input_dep_snaps": [
        {
          "__class__": "InputDependencySnap",
          "input_name": "airflow_task_ready",
          "is_dynamic_collect": false,
          "upstream_output_snaps": [
            {
              "__class__": "OutputHandleSnap",
              "output_name": "airflow_task_complete",
              "solid_name": "airflow_create_tag"
            }
          ]
        }
      ],
      "is_dynamic_mapped": false,
      "solid_def_name": "airflow_list_tags",
      "solid_name": "airflow_list_tags",
      "tags": {}
    },
    {
      "__class__": "SolidInvocationSnap",
      "input_dep_snaps": [
        {
          "__class__": "InputDependencySnap",
          "input_name": "airflow_task_ready",
          "is_dynamic_collect": false,
          "upstream_output_snaps": [
            {
              "__class__": "OutputHandleSnap",
              "output_name": "airflow_task_complete",
              "solid_name": "airflow_list_tags"
            }
          ]
        }
      ],
      "is_dynamic_mapped": false,
      "solid_def_name": "airflow_list_tags_result",
      "solid_name": "airflow_list_tags_result",
      "tags": {}
    },
    {
      "__class__": "SolidInvocationSnap",
      "input_dep_snaps": [
        {
          "__class__": "InputDependencySnap",
          "input_name": "airflow_task_ready",
          "is_dynamic_collect": false,
          "upstream_output_snaps": [
            {
              "__class__": "OutputHandleSnap",
              "output_name": "airflow_task_complete",
              "solid_name": "airflow_create_entry_gcs"
            }
          ]
        }
      ],
      "is_dynamic_mapped": false,
      "solid_def_name": "airflow_lookup_entry",
      "solid_name": "airflow_lookup_entry",
      "tags": {}
    },
    {
      "__class__": "SolidInvocationSnap",
      "input_dep_snaps": [
        {
          "__class__": "InputDependencySnap",
          "input_name": "airflow_task_ready",
          "is_dynamic_collect": false,
          "upstream_output_snaps": [
            {
              "__class__": "OutputHandleSnap",
              "output_name": "airflow_task_complete",
              "solid_name": "airflow_lookup_entry"
            }
          ]
        }
      ],
      "is_dynamic_mapped": false,
      "solid_def_name": "airflow_lookup_entry_result",
      "solid_name": "airflow_lookup_entry_result",
      "tags": {}
    },
    {
      "__class__": "SolidInvocationSnap",
      "input_dep_snaps": [
        {
          "__class__": "InputDependencySnap",
          "input_name": "airflow_task_ready",
          "is_dynamic_collect": false,
          "upstream_output_snaps": [
            {
              "__class__": "OutputHandleSnap",
              "output_name": "airflow_task_complete",
              "solid_name": "airflow_create_tag_template_field"
            },
            {
              "__class__": "OutputHandleSnap",
              "output_name": "airflow_task_complete",
              "solid_name": "airflow_update_tag_template_field"
            }
          ]
        }
      ],
      "is_dynamic_mapped": false,
      "solid_def_name": "airflow_rename_tag_template_field",
      "solid_name": "airflow_rename_tag_template_field",
      "tags": {}
    },
    {
      "__class__": "SolidInvocationSnap",
      "input_dep_snaps": [
        {
          "__class__": "InputDependencySnap",
          "input_name": "airflow_task_ready",
          "is_dynamic_collect": false,
          "upstream_output_snaps": [
            {
              "__class__": "OutputHandleSnap",
              "output_name": "airflow_task_complete",
              "solid_name": "airflow_create_entry_gcs"
            },
            {
              "__class__": "OutputHandleSnap",
              "output_name": "airflow_task_complete",
              "solid_name": "airflow_create_entry_group"
            },
            {
              "__class__": "OutputHandleSnap",
              "output_name": "airflow_task_complete",
              "solid_name": "airflow_create_tag"
            },
            {
              "__class__": "OutputHandleSnap",
              "output_name": "airflow_task_complete",
              "solid_name": "airflow_create_tag_template"
            },
            {
              "__class__": "OutputHandleSnap",
              "output_name": "airflow_task_complete",
              "solid_name": "airflow_create_tag_template_field"
            }
          ]
        }
      ],
      "is_dynamic_mapped": false,
      "solid_def_name": "airflow_search_catalog",
      "solid_name": "airflow_search_catalog",
      "tags": {}
    },
    {
      "__class__": "SolidInvocationSnap",
      "input_dep_snaps": [
        {
          "__class__": "InputDependencySnap",
          "input_name": "airflow_task_ready",
          "is_dynamic_collect": false,
          "upstream_output_snaps": [
            {
              "__class__": "OutputHandleSnap",
              "output_name": "airflow_task_complete",
              "solid_name": "airflow_search_catalog"
            }
          ]
        }
      ],
      "is_dynamic_mapped": false,
      "solid_def_name": "airflow_search_catalog_result",
      "solid_name": "airflow_search_catalog_result",
      "tags": {}
    },
    {
      "__class__": "SolidInvocationSnap",
      "input_dep_snaps": [
        {
          "__class__": "InputDependencySnap",
          "input_name": "airflow_task_ready",
          "is_dynamic_collect": false,
          "upstream_output_snaps": [
            {
              "__class__": "OutputHandleSnap",
              "output_name": "airflow_task_complete",
              "solid_name": "airflow_create_entry_gcs"
            }
          ]
        }
      ],
      "is_dynamic_mapped": false,
      "solid_def_name": "airflow_update_entry",
      "solid_name": "airflow_update_entry",
      "tags": {}
    },
    {
      "__class__": "SolidInvocationSnap",
      "input_dep_snaps": [
        {
          "__class__": "InputDependencySnap",
          "input_name": "airflow_task_ready",
          "is_dynamic_collect": false,
          "upstream_output_snaps": [
            {
              "__class__": "OutputHandleSnap",
              "output_name": "airflow_task_complete",
              "solid_name": "airflow_create_tag"
            }
          ]
        }
      ],
      "is_dynamic_mapped": false,
      "solid_def_name": "airflow_update_tag",
      "solid_name": "airflow_update_tag",
      "tags": {}
    },
    {
      "__class__": "SolidInvocationSnap",
      "input_dep_snaps": [
        {
          "__class__": "InputDependencySnap",
          "input_name": "airflow_task_ready",
          "is_dynamic_collect": false,
          "upstream_output_snaps": [
            {
              "__class__": "OutputHandleSnap",
              "output_name": "airflow_task_complete",
              "solid_name": "airflow_create_tag_template"
            }
          ]
        }
      ],
      "is_dynamic_mapped": false,
      "solid_def_name": "airflow_update_tag_template",
      "solid_name": "airflow_update_tag_template",
      "tags": {}
    },
    {
      "__class__": "SolidInvocationSnap",
      "input_dep_snaps": [
        {
          "__class__": "InputDependencySnap",
          "input_name": "airflow_task_ready",
          "is_dynamic_collect": false,
          "upstream_output_snaps": [
            {
              "__class__": "OutputHandleSnap",
              "output_name": "airflow_task_complete",
              "solid_name": "airflow_create_tag_template_field"
            }
          ]
        }
      ],
      "is_dynamic_mapped": false,
      "solid_def_name": "airflow_update_tag_template_field",
      "solid_name": "airflow_update_tag_template_field",
      "tags": {}
    }
  ]
}'''

snapshots['test_diamond_task_dag 1'] = '''{
  "__class__": "DependencyStructureSnapshot",
  "solid_invocation_snaps": [
    {
      "__class__": "SolidInvocationSnap",
      "input_dep_snaps": [
        {
          "__class__": "InputDependencySnap",
          "input_name": "airflow_task_ready",
          "is_dynamic_collect": false,
          "upstream_output_snaps": []
        }
      ],
      "is_dynamic_mapped": false,
      "solid_def_name": "airflow_dummy_operator_1",
      "solid_name": "airflow_dummy_operator_1",
      "tags": {}
    },
    {
      "__class__": "SolidInvocationSnap",
      "input_dep_snaps": [
        {
          "__class__": "InputDependencySnap",
          "input_name": "airflow_task_ready",
          "is_dynamic_collect": false,
          "upstream_output_snaps": [
            {
              "__class__": "OutputHandleSnap",
              "output_name": "airflow_task_complete",
              "solid_name": "airflow_dummy_operator_1"
            }
          ]
        }
      ],
      "is_dynamic_mapped": false,
      "solid_def_name": "airflow_dummy_operator_2",
      "solid_name": "airflow_dummy_operator_2",
      "tags": {}
    },
    {
      "__class__": "SolidInvocationSnap",
      "input_dep_snaps": [
        {
          "__class__": "InputDependencySnap",
          "input_name": "airflow_task_ready",
          "is_dynamic_collect": false,
          "upstream_output_snaps": [
            {
              "__class__": "OutputHandleSnap",
              "output_name": "airflow_task_complete",
              "solid_name": "airflow_dummy_operator_1"
            }
          ]
        }
      ],
      "is_dynamic_mapped": false,
      "solid_def_name": "airflow_dummy_operator_3",
      "solid_name": "airflow_dummy_operator_3",
      "tags": {}
    },
    {
      "__class__": "SolidInvocationSnap",
      "input_dep_snaps": [
        {
          "__class__": "InputDependencySnap",
          "input_name": "airflow_task_ready",
          "is_dynamic_collect": false,
          "upstream_output_snaps": [
            {
              "__class__": "OutputHandleSnap",
              "output_name": "airflow_task_complete",
              "solid_name": "airflow_dummy_operator_2"
            },
            {
              "__class__": "OutputHandleSnap",
              "output_name": "airflow_task_complete",
              "solid_name": "airflow_dummy_operator_3"
            }
          ]
        }
      ],
      "is_dynamic_mapped": false,
      "solid_def_name": "airflow_dummy_operator_4",
      "solid_name": "airflow_dummy_operator_4",
      "tags": {}
    }
  ]
}'''

snapshots['test_multi_leaf_dag 1'] = '''{
  "__class__": "DependencyStructureSnapshot",
  "solid_invocation_snaps": [
    {
      "__class__": "SolidInvocationSnap",
      "input_dep_snaps": [
        {
          "__class__": "InputDependencySnap",
          "input_name": "airflow_task_ready",
          "is_dynamic_collect": false,
          "upstream_output_snaps": []
        }
      ],
      "is_dynamic_mapped": false,
      "solid_def_name": "airflow_dummy_operator_1",
      "solid_name": "airflow_dummy_operator_1",
      "tags": {}
    },
    {
      "__class__": "SolidInvocationSnap",
      "input_dep_snaps": [
        {
          "__class__": "InputDependencySnap",
          "input_name": "airflow_task_ready",
          "is_dynamic_collect": false,
          "upstream_output_snaps": [
            {
              "__class__": "OutputHandleSnap",
              "output_name": "airflow_task_complete",
              "solid_name": "airflow_dummy_operator_1"
            }
          ]
        }
      ],
      "is_dynamic_mapped": false,
      "solid_def_name": "airflow_dummy_operator_2",
      "solid_name": "airflow_dummy_operator_2",
      "tags": {}
    },
    {
      "__class__": "SolidInvocationSnap",
      "input_dep_snaps": [
        {
          "__class__": "InputDependencySnap",
          "input_name": "airflow_task_ready",
          "is_dynamic_collect": false,
          "upstream_output_snaps": [
            {
              "__class__": "OutputHandleSnap",
              "output_name": "airflow_task_complete",
              "solid_name": "airflow_dummy_operator_1"
            }
          ]
        }
      ],
      "is_dynamic_mapped": false,
      "solid_def_name": "airflow_dummy_operator_3",
      "solid_name": "airflow_dummy_operator_3",
      "tags": {}
    },
    {
      "__class__": "SolidInvocationSnap",
      "input_dep_snaps": [
        {
          "__class__": "InputDependencySnap",
          "input_name": "airflow_task_ready",
          "is_dynamic_collect": false,
          "upstream_output_snaps": [
            {
              "__class__": "OutputHandleSnap",
              "output_name": "airflow_task_complete",
              "solid_name": "airflow_dummy_operator_1"
            }
          ]
        }
      ],
      "is_dynamic_mapped": false,
      "solid_def_name": "airflow_dummy_operator_4",
      "solid_name": "airflow_dummy_operator_4",
      "tags": {}
    }
  ]
}'''

snapshots['test_multi_root_dag 1'] = '''{
  "__class__": "DependencyStructureSnapshot",
  "solid_invocation_snaps": [
    {
      "__class__": "SolidInvocationSnap",
      "input_dep_snaps": [
        {
          "__class__": "InputDependencySnap",
          "input_name": "airflow_task_ready",
          "is_dynamic_collect": false,
          "upstream_output_snaps": []
        }
      ],
      "is_dynamic_mapped": false,
      "solid_def_name": "airflow_dummy_operator_1",
      "solid_name": "airflow_dummy_operator_1",
      "tags": {}
    },
    {
      "__class__": "SolidInvocationSnap",
      "input_dep_snaps": [
        {
          "__class__": "InputDependencySnap",
          "input_name": "airflow_task_ready",
          "is_dynamic_collect": false,
          "upstream_output_snaps": []
        }
      ],
      "is_dynamic_mapped": false,
      "solid_def_name": "airflow_dummy_operator_2",
      "solid_name": "airflow_dummy_operator_2",
      "tags": {}
    },
    {
      "__class__": "SolidInvocationSnap",
      "input_dep_snaps": [
        {
          "__class__": "InputDependencySnap",
          "input_name": "airflow_task_ready",
          "is_dynamic_collect": false,
          "upstream_output_snaps": []
        }
      ],
      "is_dynamic_mapped": false,
      "solid_def_name": "airflow_dummy_operator_3",
      "solid_name": "airflow_dummy_operator_3",
      "tags": {}
    },
    {
      "__class__": "SolidInvocationSnap",
      "input_dep_snaps": [
        {
          "__class__": "InputDependencySnap",
          "input_name": "airflow_task_ready",
          "is_dynamic_collect": false,
          "upstream_output_snaps": [
            {
              "__class__": "OutputHandleSnap",
              "output_name": "airflow_task_complete",
              "solid_name": "airflow_dummy_operator_1"
            },
            {
              "__class__": "OutputHandleSnap",
              "output_name": "airflow_task_complete",
              "solid_name": "airflow_dummy_operator_2"
            },
            {
              "__class__": "OutputHandleSnap",
              "output_name": "airflow_task_complete",
              "solid_name": "airflow_dummy_operator_3"
            }
          ]
        }
      ],
      "is_dynamic_mapped": false,
      "solid_def_name": "airflow_dummy_operator_4",
      "solid_name": "airflow_dummy_operator_4",
      "tags": {}
    }
  ]
}'''

snapshots['test_one_task_dag 1'] = '''{
  "__class__": "DependencyStructureSnapshot",
  "solid_invocation_snaps": [
    {
      "__class__": "SolidInvocationSnap",
      "input_dep_snaps": [
        {
          "__class__": "InputDependencySnap",
          "input_name": "airflow_task_ready",
          "is_dynamic_collect": false,
          "upstream_output_snaps": []
        }
      ],
      "is_dynamic_mapped": false,
      "solid_def_name": "airflow_dummy_operator",
      "solid_name": "airflow_dummy_operator",
      "tags": {}
    }
  ]
}'''

snapshots['test_two_task_dag_no_dep 1'] = '''{
  "__class__": "DependencyStructureSnapshot",
  "solid_invocation_snaps": [
    {
      "__class__": "SolidInvocationSnap",
      "input_dep_snaps": [
        {
          "__class__": "InputDependencySnap",
          "input_name": "airflow_task_ready",
          "is_dynamic_collect": false,
          "upstream_output_snaps": []
        }
      ],
      "is_dynamic_mapped": false,
      "solid_def_name": "airflow_dummy_operator_1",
      "solid_name": "airflow_dummy_operator_1",
      "tags": {}
    },
    {
      "__class__": "SolidInvocationSnap",
      "input_dep_snaps": [
        {
          "__class__": "InputDependencySnap",
          "input_name": "airflow_task_ready",
          "is_dynamic_collect": false,
          "upstream_output_snaps": []
        }
      ],
      "is_dynamic_mapped": false,
      "solid_def_name": "airflow_dummy_operator_2",
      "solid_name": "airflow_dummy_operator_2",
      "tags": {}
    }
  ]
}'''

snapshots['test_two_task_dag_with_dep 1'] = '''{
  "__class__": "DependencyStructureSnapshot",
  "solid_invocation_snaps": [
    {
      "__class__": "SolidInvocationSnap",
      "input_dep_snaps": [
        {
          "__class__": "InputDependencySnap",
          "input_name": "airflow_task_ready",
          "is_dynamic_collect": false,
          "upstream_output_snaps": []
        }
      ],
      "is_dynamic_mapped": false,
      "solid_def_name": "airflow_dummy_operator_1",
      "solid_name": "airflow_dummy_operator_1",
      "tags": {}
    },
    {
      "__class__": "SolidInvocationSnap",
      "input_dep_snaps": [
        {
          "__class__": "InputDependencySnap",
          "input_name": "airflow_task_ready",
          "is_dynamic_collect": false,
          "upstream_output_snaps": [
            {
              "__class__": "OutputHandleSnap",
              "output_name": "airflow_task_complete",
              "solid_name": "airflow_dummy_operator_1"
            }
          ]
        }
      ],
      "is_dynamic_mapped": false,
      "solid_def_name": "airflow_dummy_operator_2",
      "solid_name": "airflow_dummy_operator_2",
      "tags": {}
    }
  ]
}'''
