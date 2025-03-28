# re-export of dagster_shared.record to ease migration
# should be removed once call-sites migrated

from dagster_shared.record import (
    IHaveNew as IHaveNew,
    ImportFrom as ImportFrom,
    LegacyNamedTupleMixin as LegacyNamedTupleMixin,
    as_dict as as_dict,
    as_dict_for_new as as_dict_for_new,
    copy as copy,
    get_original_class as get_original_class,
    get_record_annotations as get_record_annotations,
    has_generated_new as has_generated_new,
    is_record as is_record,
    record as record,
    record_custom as record_custom,
    replace as replace,
)
