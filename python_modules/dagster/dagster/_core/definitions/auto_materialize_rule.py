class MaterializeOnCronRule(
    AutoMaterializeRule,
    NamedTuple(
        "_MaterializeOnCronRule",
        [("cron_schedule", str), ("timezone", str), ("all_partitions", bool)],
    ),
):
    @property
    def decision_type(self) -> AutoMaterializeDecisionType:
        return AutoMaterializeDecisionType.MATERIALIZE

    @property
    def description(self) -> str:
        return f"not materialized since last cron schedule tick of '{self.cron_schedule}' (timezone: {self.timezone})"

    def missed_cron_ticks(self, context: RuleEvaluationContext) -> Sequence[datetime.datetime]:
        """Returns the cron ticks which have been missed since the previous cursor was generated."""
        if not context.cursor.latest_evaluation_timestamp:
            previous_dt = next(
                reverse_cron_string_iterator(
                    end_timestamp=context.evaluation_time.timestamp(),
                    cron_string=self.cron_schedule,
                    execution_timezone=self.timezone,
                )
            )
            return [previous_dt]
        missed_ticks = []
        for dt in cron_string_iterator(
            start_timestamp=context.cursor.latest_evaluation_timestamp,
            cron_string=self.cron_schedule,
            execution_timezone=self.timezone,
        ):
            if dt > context.evaluation_time:
                break
            missed_ticks.append(dt)
        return missed_ticks

    def get_asset_partitions_to_request(
        self, context: RuleEvaluationContext
    ) -> AbstractSet[AssetKeyPartitionKey]:
        missed_ticks = self.missed_cron_ticks(context)

        if not missed_ticks:
            return set()

        partitions_def = context.asset_graph.get_partitions_def(context.asset_key)
        if partitions_def is None:
            return {AssetKeyPartitionKey(context.asset_key)}

        # if all_partitions is set, then just return all partitions if any ticks have been missed
        if self.all_partitions:
            return {
                AssetKeyPartitionKey(context.asset_key, partition_key)
                for partition_key in partitions_def.get_partition_keys(
                    current_time=context.evaluation_time
                )
            }

        # for partitions_defs without a time component, just return the last partition if any ticks
        # have been missed
        time_partitions_def = get_time_partitions_def(partitions_def)
        if time_partitions_def is None:
            return {
                AssetKeyPartitionKey(context.asset_key, partitions_def.get_last_partition_key())
            }

        missed_time_partition_keys = filter(
            None,
            [
                time_partitions_def.get_last_partition_key(current_time=missed_tick)
                for missed_tick in missed_ticks
            ],
        )
        # for multi partitions definitions, request to materialize all partitions for each missed
        # cron schedule tick
        if isinstance(partitions_def, MultiPartitionsDefinition):
            return {
                AssetKeyPartitionKey(context.asset_key, partition_key)
                for time_partition_key in missed_time_partition_keys
                for partition_key in partitions_def.get_multipartition_keys_with_dimension_value(
                    partitions_def.time_window_dimension.name,
                    time_partition_key,
                    dynamic_partitions_store=context.instance_queryer,
                )
            }
        else:
            return {
                AssetKeyPartitionKey(context.asset_key, time_partition_key)
                for time_partition_key in missed_time_partition_keys
            }

    def evaluate_for_asset(self, context: RuleEvaluationContext) -> RuleEvaluationResults:
        asset_partitions_to_request = self.get_asset_partitions_to_request(context)
        asset_partitions_by_evaluation_data = defaultdict(set)
        if asset_partitions_to_request:
            asset_partitions_by_evaluation_data[None].update(asset_partitions_to_request)
        return self.add_evaluation_data_from_previous_tick(
            context,
            asset_partitions_by_evaluation_data,
            should_use_past_data_fn=lambda ap: not context.materialized_requested_or_discarded_since_previous_tick(
                ap
            ),
        )


@whitelist_for_serdes
@experimental
class AutoMaterializeAssetPartitionsFilter(
    NamedTuple(
        "_AutoMaterializeAssetPartitionsFilter",
        [("latest_run_required_tags", Optional[Mapping[str, str]])],
    )
):
    """A filter that can be applied to an asset partition, during auto-materialize evaluation, and
    returns a boolean for whether it passes.

    Attributes:
        latest_run_required_tags (Optional[Sequence[str]]): `passes` returns
            True if the run responsible for the latest materialization of the asset partition
            has all of these tags.
    """

    @property
    def description(self) -> str:
        return f"latest run includes required tags: {self.latest_run_required_tags}"

    def passes(
        self, context: RuleEvaluationContext, asset_partitions: Iterable[AssetKeyPartitionKey]
    ) -> Iterable[AssetKeyPartitionKey]:
        if self.latest_run_required_tags is None:
            return asset_partitions

        will_update_asset_partitions: Set[AssetKeyPartitionKey] = set()

        asset_partitions_by_latest_run_id: Dict[str, Set[AssetKeyPartitionKey]] = defaultdict(set)
        for asset_partition in asset_partitions:
            if context.will_update_asset_partition(asset_partition):
                will_update_asset_partitions.add(asset_partition)
            else:
                record = context.instance_queryer.get_latest_materialization_or_observation_record(
                    asset_partition
                )

                if record is None:
                    raise RuntimeError(
                        f"No materialization record found for asset partition {asset_partition}"
                    )

                asset_partitions_by_latest_run_id[record.run_id].add(asset_partition)

        if len(asset_partitions_by_latest_run_id) > 0:
            run_ids_with_required_tags = context.instance_queryer.instance.get_run_ids(
                filters=RunsFilter(
                    run_ids=list(asset_partitions_by_latest_run_id.keys()),
                    tags=self.latest_run_required_tags,
                )
            )
        else:
            run_ids_with_required_tags = set()

        updated_partitions_with_required_tags = {
            asset_partition
            for run_id, run_id_asset_partitions in asset_partitions_by_latest_run_id.items()
            if run_id in run_ids_with_required_tags
            for asset_partition in run_id_asset_partitions
        }

        if self.latest_run_required_tags.items() <= context.auto_materialize_run_tags.items():
            return will_update_asset_partitions | updated_partitions_with_required_tags
        else:
            return updated_partitions_with_required_tags

    def __hash__(self):
        return hash(frozenset((self.latest_run_required_tags or {}).items()))


@whitelist_for_serdes
class MaterializeOnParentUpdatedRule(
    AutoMaterializeRule,
    NamedTuple(
        "_MaterializeOnParentUpdatedRule",
        [("updated_parent_filter", Optional[AutoMaterializeAssetPartitionsFilter])],
    ),
):
    def __new__(cls, updated_parent_filter: Optional[AutoMaterializeAssetPartitionsFilter] = None):
        return super().__new__(cls, updated_parent_filter=updated_parent_filter)

    @property
    def decision_type(self) -> AutoMaterializeDecisionType:
        return AutoMaterializeDecisionType.MATERIALIZE

    @property
    def description(self) -> str:
        base = "upstream data has changed since latest materialization"
        if self.updated_parent_filter is not None:
            return f"{base} and matches filter '{self.updated_parent_filter.description}'"
        else:
            return base

    def evaluate_for_asset(self, context: RuleEvaluationContext) -> RuleEvaluationResults:
        """Evaluates the set of asset partitions of this asset whose parents have been updated,
        or will update on this tick.
        """
        asset_partitions_by_updated_parents: Mapping[
            AssetKeyPartitionKey, Set[AssetKeyPartitionKey]
        ] = defaultdict(set)
        asset_partitions_by_will_update_parents: Mapping[
            AssetKeyPartitionKey, Set[AssetKeyPartitionKey]
        ] = defaultdict(set)

        subset_to_evaluate = context.candidate_has_parents_that_have_or_will_update_subset
        for asset_partition in subset_to_evaluate.asset_partitions:
            parent_asset_partitions = context.asset_graph.get_parents_partitions(
                dynamic_partitions_store=context.instance_queryer,
                current_time=context.instance_queryer.evaluation_time,
                asset_key=asset_partition.asset_key,
                partition_key=asset_partition.partition_key,
            ).parent_partitions

            updated_parent_asset_partitions = context.instance_queryer.get_parent_asset_partitions_updated_after_child(
                asset_partition,
                parent_asset_partitions,
                # do a precise check for updated parents, factoring in data versions, as long as
                # we're within reasonable limits on the number of partitions to check
                respect_materialization_data_versions=context.daemon_context.respect_materialization_data_versions
                and len(parent_asset_partitions) + subset_to_evaluate.size < 100,
                # ignore self-dependencies when checking for updated parents, to avoid historical
                # rematerializations from causing a chain of materializations to be kicked off
                ignored_parent_keys={context.asset_key},
            )
            for parent in updated_parent_asset_partitions:
                asset_partitions_by_updated_parents[parent].add(asset_partition)

            for parent in parent_asset_partitions:
                if context.will_update_asset_partition(parent):
                    asset_partitions_by_will_update_parents[parent].add(asset_partition)

        updated_and_will_update_parents = (
            asset_partitions_by_updated_parents.keys()
            | asset_partitions_by_will_update_parents.keys()
        )
        filtered_updated_and_will_update_parents = (
            self.updated_parent_filter.passes(context, updated_and_will_update_parents)
            if self.updated_parent_filter
            else updated_and_will_update_parents
        )

        updated_parent_assets_by_asset_partition: Dict[
            AssetKeyPartitionKey, Set[AssetKey]
        ] = defaultdict(set)
        will_update_parent_assets_by_asset_partition: Dict[
            AssetKeyPartitionKey, Set[AssetKey]
        ] = defaultdict(set)

        for updated_or_will_update_parent in filtered_updated_and_will_update_parents:
            for child in asset_partitions_by_updated_parents.get(updated_or_will_update_parent, []):
                updated_parent_assets_by_asset_partition[child].add(
                    updated_or_will_update_parent.asset_key
                )

            for child in asset_partitions_by_will_update_parents.get(
                updated_or_will_update_parent, []
            ):
                will_update_parent_assets_by_asset_partition[child].add(
                    updated_or_will_update_parent.asset_key
                )

        asset_partitions_by_evaluation_data = defaultdict(set)
        for asset_partition in (
            updated_parent_assets_by_asset_partition.keys()
            | will_update_parent_assets_by_asset_partition.keys()
        ):
            asset_partitions_by_evaluation_data[
                ParentUpdatedRuleEvaluationData(
                    updated_asset_keys=frozenset(
                        updated_parent_assets_by_asset_partition.get(asset_partition, [])
                    ),
                    will_update_asset_keys=frozenset(
                        will_update_parent_assets_by_asset_partition.get(asset_partition, [])
                    ),
                )
            ].add(asset_partition)

        return self.add_evaluation_data_from_previous_tick(
            context,
            asset_partitions_by_evaluation_data,
            should_use_past_data_fn=lambda ap: not context.materialized_requested_or_discarded_since_previous_tick(
                ap
            ),
        )


@whitelist_for_serdes
class MaterializeOnMissingRule(AutoMaterializeRule, NamedTuple("_MaterializeOnMissingRule", [])):
    @property
    def decision_type(self) -> AutoMaterializeDecisionType:
        return AutoMaterializeDecisionType.MATERIALIZE

    @property
    def description(self) -> str:
        return "materialization is missing"

    def evaluate_for_asset(self, context: RuleEvaluationContext) -> RuleEvaluationResults:
        """Evaluates the set of asset partitions for this asset which are missing and were not
        previously discarded. Currently only applies to root asset partitions and asset partitions
        with updated parents.
        """
        asset_partitions_by_evaluation_data = defaultdict(set)

        missing_asset_partitions = set(
            context.never_materialized_requested_or_discarded_root_subset.asset_partitions
        )
        # in addition to missing root asset partitions, check any asset partitions with updated
        # parents to see if they're missing
        for candidate in context.subset_with_updated_parents_since_previous_tick.asset_partitions:
            if not context.instance_queryer.asset_partition_has_materialization_or_observation(
                candidate
            ):
                missing_asset_partitions |= {candidate}

        if missing_asset_partitions:
            asset_partitions_by_evaluation_data[None] = missing_asset_partitions

        return self.add_evaluation_data_from_previous_tick(
            context,
            asset_partitions_by_evaluation_data,
            should_use_past_data_fn=lambda ap: ap not in missing_asset_partitions
            and not context.materialized_requested_or_discarded_since_previous_tick(ap),
        )


@whitelist_for_serdes
class SkipOnParentOutdatedRule(AutoMaterializeRule, NamedTuple("_SkipOnParentOutdatedRule", [])):
    @property
    def decision_type(self) -> AutoMaterializeDecisionType:
        return AutoMaterializeDecisionType.SKIP

    @property
    def description(self) -> str:
        return "waiting on upstream data to be up to date"

    def evaluate_for_asset(self, context: RuleEvaluationContext) -> RuleEvaluationResults:
        asset_partitions_by_evaluation_data = defaultdict(set)

        # only need to evaluate net-new candidates and candidates whose parents have changed
        subset_to_evaluate = (
            context.candidate_not_evaluated_on_previous_tick_subset
            | context.candidate_has_parents_that_have_or_will_update_subset
        )
        for candidate in subset_to_evaluate.asset_partitions:
            outdated_ancestors = set()
            # find the root cause of why this asset partition's parents are outdated (if any)
            for parent in context.get_parents_that_will_not_be_materialized_on_current_tick(
                asset_partition=candidate
            ):
                if context.instance_queryer.have_ignorable_partition_mapping_for_outdated(
                    candidate.asset_key, parent.asset_key
                ):
                    continue
                outdated_ancestors.update(
                    context.instance_queryer.get_outdated_ancestors(asset_partition=parent)
                )
            if outdated_ancestors:
                asset_partitions_by_evaluation_data[
                    WaitingOnAssetsRuleEvaluationData(frozenset(outdated_ancestors))
                ].add(candidate)

        return self.add_evaluation_data_from_previous_tick(
            context,
            asset_partitions_by_evaluation_data,
            should_use_past_data_fn=lambda ap: ap not in subset_to_evaluate,
        )


@whitelist_for_serdes
class SkipOnNotAllParentsUpdatedRule(
    AutoMaterializeRule,
    NamedTuple(
        "_SkipOnNotAllParentsUpdatedRule", [("require_update_for_all_parent_partitions", bool)]
    ),
):
    """An auto-materialize rule that enforces that an asset can only be materialized if all parents
    have been materialized since the asset's last materialization.

    Attributes:
        require_update_for_all_parent_partitions (Optional[bool]): Applies only to an unpartitioned
            asset or an asset partition that depends on more than one partition in any upstream asset.
            If true, requires all upstream partitions in each upstream asset to be materialized since
            the downstream asset's last materialization in order to update it. If false, requires at
            least one upstream partition in each upstream asset to be materialized since the downstream
            asset's last materialization in order to update it. Defaults to false.
    """

    @property
    def decision_type(self) -> AutoMaterializeDecisionType:
        return AutoMaterializeDecisionType.SKIP

    @property
    def description(self) -> str:
        if self.require_update_for_all_parent_partitions is False:
            return "waiting on upstream data to be updated"
        else:
            return "waiting until all upstream partitions are updated"

    def evaluate_for_asset(
        self,
        context: RuleEvaluationContext,
    ) -> RuleEvaluationResults:
        asset_partitions_by_evaluation_data = defaultdict(set)

        # only need to evaluate net-new candidates and candidates whose parents have changed
        subset_to_evaluate = (
            context.candidate_not_evaluated_on_previous_tick_subset
            | context.candidate_has_parents_that_have_or_will_update_subset
        )
        for candidate in subset_to_evaluate.asset_partitions:
            parent_partitions = context.asset_graph.get_parents_partitions(
                context.instance_queryer,
                context.instance_queryer.evaluation_time,
                context.asset_key,
                candidate.partition_key,
            ).parent_partitions

            updated_parent_partitions = (
                context.instance_queryer.get_parent_asset_partitions_updated_after_child(
                    candidate,
                    parent_partitions,
                    context.daemon_context.respect_materialization_data_versions,
                    ignored_parent_keys=set(),
                )
                | set().union(
                    *[
                        context.will_materialize_mapping.get(parent, set())
                        for parent in context.asset_graph.get_parents(context.asset_key)
                    ]
                )
            )

            if self.require_update_for_all_parent_partitions:
                # All upstream partitions must be updated in order for the candidate to be updated
                non_updated_parent_keys = {
                    parent.asset_key for parent in parent_partitions - updated_parent_partitions
                }
            else:
                # At least one upstream partition in each upstream asset must be updated in order
                # for the candidate to be updated
                parent_asset_keys = context.asset_graph.get_parents(context.asset_key)
                updated_parent_partitions_by_asset_key = context.get_asset_partitions_by_asset_key(
                    updated_parent_partitions
                )
                non_updated_parent_keys = {
                    parent
                    for parent in parent_asset_keys
                    if not updated_parent_partitions_by_asset_key.get(parent)
                }

            # do not require past partitions of this asset to be updated
            non_updated_parent_keys -= {context.asset_key}

            if non_updated_parent_keys:
                asset_partitions_by_evaluation_data[
                    WaitingOnAssetsRuleEvaluationData(frozenset(non_updated_parent_keys))
                ].add(candidate)

        return self.add_evaluation_data_from_previous_tick(
            context,
            asset_partitions_by_evaluation_data,
            should_use_past_data_fn=lambda ap: ap not in subset_to_evaluate,
        )


@whitelist_for_serdes
class SkipOnRequiredButNonexistentParentsRule(
    AutoMaterializeRule, NamedTuple("_SkipOnRequiredButNonexistentParentsRule", [])
):
    @property
    def decision_type(self) -> AutoMaterializeDecisionType:
        return AutoMaterializeDecisionType.SKIP

    @property
    def description(self) -> str:
        return "required parent partitions do not exist"

    def evaluate_for_asset(self, context: RuleEvaluationContext) -> RuleEvaluationResults:
        asset_partitions_by_evaluation_data = defaultdict(set)

        subset_to_evaluate = (
            context.candidate_not_evaluated_on_previous_tick_subset
            | context.candidate_has_parents_that_have_or_will_update_subset
        )
        for candidate in subset_to_evaluate.asset_partitions:
            nonexistent_parent_partitions = context.asset_graph.get_parents_partitions(
                context.instance_queryer,
                context.instance_queryer.evaluation_time,
                candidate.asset_key,
                candidate.partition_key,
            ).required_but_nonexistent_parents_partitions

            nonexistent_parent_keys = {parent.asset_key for parent in nonexistent_parent_partitions}
            if nonexistent_parent_keys:
                asset_partitions_by_evaluation_data[
                    WaitingOnAssetsRuleEvaluationData(frozenset(nonexistent_parent_keys))
                ].add(candidate)

        return self.add_evaluation_data_from_previous_tick(
            context,
            asset_partitions_by_evaluation_data,
            should_use_past_data_fn=lambda ap: ap not in subset_to_evaluate,
        )


@whitelist_for_serdes
class DiscardOnMaxMaterializationsExceededRule(
    AutoMaterializeRule, NamedTuple("_DiscardOnMaxMaterializationsExceededRule", [("limit", int)])
):
    @property
    def decision_type(self) -> AutoMaterializeDecisionType:
        return AutoMaterializeDecisionType.DISCARD

    @property
    def description(self) -> str:
        return f"exceeds {self.limit} materialization(s) per minute"

    def evaluate_for_asset(self, context: RuleEvaluationContext) -> RuleEvaluationResults:
        # the set of asset partitions which exceed the limit
        rate_limited_asset_partitions = set(
            sorted(
                context.candidate_subset.asset_partitions,
                key=lambda x: sort_key_for_asset_partition(context.asset_graph, x),
            )[self.limit :]
        )
        if rate_limited_asset_partitions:
            return [(None, rate_limited_asset_partitions)]
        return []
