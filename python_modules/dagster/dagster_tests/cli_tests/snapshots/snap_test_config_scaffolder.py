# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import Snapshot


snapshots = Snapshot()

snapshots['test_basic_ops_config 1'] = {
    'execution': {
        'config': {
            'in_process': {
                'marker_to_close': '',
                'retries': {
                    'disabled': {
                    },
                    'enabled': {
                    }
                }
            },
            'multiprocess': {
                'max_concurrent': 0,
                'retries': {
                    'disabled': {
                    },
                    'enabled': {
                    }
                },
                'start_method': {
                    'forkserver': {
                        'preload_modules': [
                        ]
                    },
                    'spawn': {
                    }
                },
                'tag_concurrency_limits': [
                ]
            }
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
    'ops': {
        'required_field_op': {
            'config': {
                'required_int': 0
            }
        }
    },
    'resources': {
        'io_manager': {
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
                },
                'start_method': {
                    'forkserver': {
                        'preload_modules': [
                        ]
                    },
                    'spawn': {
                    }
                },
                'tag_concurrency_limits': [
                ]
            }
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
                },
                'start_method': {
                    'forkserver': {
                        'preload_modules': [
                        ]
                    },
                    'spawn': {
                    }
                },
                'tag_concurrency_limits': [
                ]
            }
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
    }
}
