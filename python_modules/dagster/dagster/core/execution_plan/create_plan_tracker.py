from collections import namedtuple
import uuid

from dagster import check
from dagster.core.definitions.dependency import Solid


def create_new_plan_id():
    return str(uuid.uuid4())


def create_plan_tracker(pipeline):
    root_plan_id = create_new_plan_id()

    # Solids that reside within a given plan, in topological order
    # PlanId => List[SolidName]
    solid_names_by_plan_id = {root_plan_id: []}

    # Maintains the order we saw builders as we proceeded through the solid graph in
    # topological order.
    plan_order = [root_plan_id]

    # SolidName ==> Stack[PlanId]
    plan_stacks = {}

    def _set_plan_stack(solid, plan_stack):
        check.inst_param(solid, 'solid', Solid)
        check.list_param(plan_stack, 'plan_stack', of_type=str)
        check.param_invariant(bool(plan_stack), 'plan_stack', 'Must have at least one plan')

        if solid.name not in plan_stacks:
            plan_stacks[solid.name] = plan_stack
            current_plan_id = plan_stack[-1]
            solid_names_by_plan_id[current_plan_id].append(solid.name)
            return

        # For now we have a strict policy that plans stacks for all
        # inputs must be identical. This, for example, ends up
        # disallowing situations where a solid has one input
        # that is a fan-out dependency on a Sequence output but
        # but also has an input that is just a normal input.
        if plan_stack != plan_stacks[solid.name]:
            from dagster import DagsterInvariantViolationError

            raise DagsterInvariantViolationError('stack mismatch!')

    def _set_root_plan_stack(solid):
        return _set_plan_stack(solid, [root_plan_id])

    dep_structure = pipeline.dependency_structure

    for solid in pipeline.solids:
        if not solid.definition.input_defs:
            _set_root_plan_stack(solid)
            continue

        for input_def in solid.definition.input_defs:
            input_handle = solid.input_handle(input_def.name)
            if not dep_structure.has_dep(input_handle):
                _set_root_plan_stack(solid)
                continue

            prev_output_handle = dep_structure.get_dep_output_handle(input_handle)
            prev_plan_stack = plan_stacks[prev_output_handle.solid.name]
            dep_def = dep_structure.get_dep_def(input_handle)

            if dep_def.is_fanout:
                # fanout means we push a new plan builder onto the stack
                new_plan_id = create_new_plan_id()
                solid_names_by_plan_id[new_plan_id] = []

                plan_order.append(new_plan_id)
                _set_plan_stack(solid, prev_plan_stack + [new_plan_id])
            elif dep_def.is_fanin:
                # fanin means we pop a plan builder off the stack
                _set_plan_stack(solid, prev_plan_stack[:-1])
            else:
                # normal dependency means we maintain current stack
                _set_plan_stack(solid, prev_plan_stack)

    return PlanTracker(solid_names_by_plan_id, plan_stacks, plan_order)


class PlanTracker(namedtuple('PlanTracker', 'solid_names_by_plan_id plan_stacks plan_order')):
    '''
    PlanTracker tracks about the execution plan and the subplans that comprise it.

    Attributes:
        - solid_names_by_plan_id (Dict[str, List[str]]): Solid names indexed by plan_id
        - plan_stacks (Dict[str, List[str]]): Plan stack index by solid name. 
            Every solid knows prior to execution the stack of plans in context
            for that solid. This is where that information is record.
        - plan_order: Plan_id ordered in forward topological order. It is safe
            to construct the actual plans in the reverse order of this ordering.
            This guarantees that any dependant plans are constructed before their
            parent plans.
    '''

    def __new__(cls, solid_names_by_plan_id, plan_stacks, plan_order):
        return super(PlanTracker, cls).__new__(
            cls,
            check.dict_param(
                solid_names_by_plan_id, 'solid_names_by_plan_id', key_type=str, value_type=list
            ),
            check.dict_param(plan_stacks, 'plan_stacks', key_type=str, value_type=list),
            check.list_param(plan_order, 'plan_order', of_type=str),
        )
