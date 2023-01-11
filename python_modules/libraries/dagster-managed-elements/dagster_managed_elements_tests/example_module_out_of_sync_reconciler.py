from dagster_managed_elements import ManagedElementDiff

from dagster_managed_elements_tests.example_reconciler import MyManagedElementReconciler

# Additions on check, deletions on apply
my_reconciler = MyManagedElementReconciler(
    diff=ManagedElementDiff()
    .add("foo", "bar")
    .add("same", "as")
    .with_nested("nested", ManagedElementDiff().add("qwerty", "uiop").add("new", "field")),
    apply_diff=ManagedElementDiff()
    .delete("foo", "bar")
    .delete("same", "as")
    .with_nested("nested", ManagedElementDiff().delete("qwerty", "uiop").delete("new", "field")),
)
