from dagster_managed_stacks import ManagedStackDiff
from dagster_managed_stacks_tests.example_reconciler import MyManagedStackReconciler

my_reconciler = MyManagedStackReconciler(
    ManagedStackDiff()
    .add("foo", "bar")
    .add("same", "as")
    .with_nested("nested", ManagedStackDiff().add("qwerty", "uiop").add("new", "field"))
)

my_other_reconciler = MyManagedStackReconciler(ManagedStackDiff().delete("foo", "bar"))
