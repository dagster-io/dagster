# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import Snapshot

snapshots = Snapshot()

snapshots['test_basic_solids_config 1'] = {
    'execution': {
        'in_process': {
            'config': {
                'marker_to_close': '',
                'retries': {
                    'disabled': {
                    },
                    'enabled': {
                    }
                }
            }
        },
        'multiprocess': {
            'config': {
                'max_concurrent': 0,
                'retries': {
                    'disabled': {
                    },
                    'enabled': {
                    }
                }
            }
        }
    },
    'intermediate_storage': {
        'filesystem': {
            'config': {
                'base_dir': ''
            }
        },
        'in_memory': {
            'config': 'AnyType'
        }
    },
    'loggers': {
        'console': {
            'config': {
                'log_level': '',
                'name': ''
            }
        }
    },
    'resources': {
        'io_manager': {
            'config': 'AnyType'
        }
    },
    'solids': {
        'required_field_solid': {
            'config': {
                'required_int': 0
            }
        }
    },
    'storage': {
        'filesystem': {
            'config': {
                'base_dir': ''
            }
        },
        'in_memory': {
            'config': 'AnyType'
        }
    }
}

snapshots['test_two_modes 1'] = {
}

snapshots['test_two_modes 2'] = {
    'execution': {
        'in_process': {
            'config': {
                'marker_to_close': '',
                'retries': {
                    'disabled': {
                    },
                    'enabled': {
                    }
                }
            }
        },
        'multiprocess': {
            'config': {
                'max_concurrent': 0,
                'retries': {
                    'disabled': {
                    },
                    'enabled': {
                    }
                }
            }
        }
    },
    'intermediate_storage': {
        'filesystem': {
            'config': {
                'base_dir': ''
            }
        },
        'in_memory': {
            'config': 'AnyType'
        }
    },
    'loggers': {
        'console': {
            'config': {
                'log_level': '',
                'name': ''
            }
        }
    },
    'resources': {
        'io_manager': {
            'config': 'AnyType'
        },
        'value': {
            'config': {
                'mode_one_field': ''
            }
        }
    },
    'solids': {
    },
    'storage': {
        'filesystem': {
            'config': {
                'base_dir': ''
            }
        },
        'in_memory': {
            'config': 'AnyType'
        }
    }
}

snapshots['test_two_modes 3'] = {
}

snapshots['test_two_modes 4'] = {
    'execution': {
        'in_process': {
            'config': {
                'marker_to_close': '',
                'retries': {
                    'disabled': {
                    },
                    'enabled': {
                    }
                }
            }
        },
        'multiprocess': {
            'config': {
                'max_concurrent': 0,
                'retries': {
                    'disabled': {
                    },
                    'enabled': {
                    }
                }
            }
        }
    },
    'intermediate_storage': {
        'filesystem': {
            'config': {
                'base_dir': ''
            }
        },
        'in_memory': {
            'config': 'AnyType'
        }
    },
    'loggers': {
        'console': {
            'config': {
                'log_level': '',
                'name': ''
            }
        }
    },
    'resources': {
        'io_manager': {
            'config': 'AnyType'
        },
        'value': {
            'config': {
                'mode_two_field': 0
            }
        }
    },
    'solids': {
    },
    'storage': {
        'filesystem': {
            'config': {
                'base_dir': ''
            }
        },
        'in_memory': {
            'config': 'AnyType'
        }
    }
}
