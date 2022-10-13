from dagster_managed_stacks import ManagedStackDiff
from dagster_managed_stacks_tests.example_reconciler import MyManagedStackReconciler

# Additions on check, deletions on apply
my_reconciler = MyManagedStackReconciler(
    diff=ManagedStackDiff()
    .add("foo", "bar")
    .add("same", "as")
    .with_nested("nested", ManagedStackDiff().add("qwerty", "uiop").add("new", "field")),
    apply_diff=ManagedStackDiff()
    .delete("foo", "bar")
    .delete("same", "as")
    .with_nested("nested", ManagedStackDiff().delete("qwerty", "uiop").delete("new", "field")),
)
