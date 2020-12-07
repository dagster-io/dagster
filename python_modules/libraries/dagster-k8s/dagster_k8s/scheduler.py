import time

import kubernetes
from dagster import DagsterInstance, Field, Noneable, StringSource, check
from dagster.core.host_representation import ExternalSchedule
from dagster.core.scheduler import DagsterSchedulerError, Scheduler
from dagster.serdes import ConfigurableClass, ConfigurableClassData
from dagster.utils import merge_dicts
from dagster_k8s.job import DagsterK8sJobConfig, construct_dagster_k8s_job, get_k8s_job_name


class K8sScheduler(Scheduler, ConfigurableClass):
    """Scheduler implementation on top of Kubernetes CronJob.

    Enable this scheduler by adding it to your dagster.yaml, or by configuring the scheduler
    section of the Helm chart
    https://github.com/dagster-io/dagster/tree/master/helm"""

    def __init__(
        self,
        dagster_home,
        service_account_name,
        instance_config_map,
        postgres_password_secret,
        job_image,
        load_incluster_config=True,
        scheduler_namespace="default",
        image_pull_policy="Always",
        image_pull_secrets=None,
        kubeconfig_file=None,
        inst_data=None,
        env_config_maps=None,
        env_secrets=None,
    ):
        self._inst_data = check.opt_inst_param(inst_data, "inst_data", ConfigurableClassData)

        if load_incluster_config:
            check.invariant(
                kubeconfig_file is None,
                "`kubeconfig_file` is set but `load_incluster_config` is True.",
            )
            kubernetes.config.load_incluster_config()
        else:
            check.opt_str_param(kubeconfig_file, "kubeconfig_file")
            kubernetes.config.load_kube_config(kubeconfig_file)

        self._api = kubernetes.client.BatchV1beta1Api()
        self._namespace = check.str_param(scheduler_namespace, "scheduler_namespace")
        self.grace_period_seconds = 5  # This should be passed in via config

        self.job_config = DagsterK8sJobConfig(
            job_image=check.str_param(job_image, "job_image"),
            dagster_home=check.str_param(dagster_home, "dagster_home"),
            image_pull_policy=check.str_param(image_pull_policy, "image_pull_policy"),
            image_pull_secrets=check.opt_list_param(
                image_pull_secrets, "image_pull_secrets", of_type=dict
            ),
            service_account_name=check.str_param(service_account_name, "service_account_name"),
            instance_config_map=check.str_param(instance_config_map, "instance_config_map"),
            postgres_password_secret=check.str_param(
                postgres_password_secret, "postgres_password_secret"
            ),
            env_config_maps=check.opt_list_param(env_config_maps, "env_config_maps", of_type=str),
            env_secrets=check.opt_list_param(env_secrets, "env_secrets", of_type=str),
        )

    @property
    def inst_data(self):
        return self._inst_data

    @classmethod
    def config_type(cls):
        job_cfg = DagsterK8sJobConfig.config_type()

        scheduler_extra_cfg = {
            "scheduler_namespace": Field(StringSource, is_required=True),
            "load_incluster_config": Field(bool, is_required=False, default_value=True),
            "kubeconfig_file": Field(Noneable(StringSource), is_required=False, default_value=None),
        }
        return merge_dicts(job_cfg, scheduler_extra_cfg)

    @classmethod
    def from_config_value(cls, inst_data, config_value):
        return cls(inst_data=inst_data, **config_value)

    def debug_info(self):
        return "Running K8s CronJob(s):\n{jobs}\n".format(
            jobs="\n".join([str(job) for job in self.get_all_cron_jobs()])
        )

    def wipe(self, instance):
        # Note: This method deletes schedules from ALL repositories
        check.inst_param(instance, "instance", DagsterInstance)

        self._api.delete_collection_namespaced_cron_job(namespace=self._namespace)
        time.sleep(self.grace_period_seconds)

        # Verify that no cron jobs are running
        running_cron_job_count = len(self.get_all_cron_jobs())
        if running_cron_job_count != 0:
            raise DagsterSchedulerError(
                "Attempted to delete all K8s CronJobs but failed. There are "
                "still {} running schedules".format(running_cron_job_count)
            )

    def _job_template(self, external_schedule):
        check.inst_param(external_schedule, "external_schedule", ExternalSchedule)

        local_target = external_schedule.get_external_origin()

        job_config = self.job_config

        external_schedule_name = external_schedule.name
        job_name = get_k8s_job_name(external_schedule_name)
        pod_name = job_name

        job_template = construct_dagster_k8s_job(
            job_config=job_config,
            args=[
                "dagster",
                "api",
                "launch_scheduled_execution",
                "/tmp/launch_scheduled_execution_output",  # https://bugs.python.org/issue20074 prevents using /dev/stdout
                "--schedule_name",
                external_schedule_name,
            ]
            + local_target.get_repo_cli_args().split(" "),
            job_name=job_name,
            pod_name=pod_name,
            component="scheduled_job",
        )
        return job_template

    def _start_cron_job(self, external_schedule):
        check.inst_param(external_schedule, "external_schedule", ExternalSchedule)

        job_template = self._job_template(external_schedule)

        cron_job_spec = kubernetes.client.V1beta1CronJobSpec(
            schedule=external_schedule.cron_schedule, job_template=job_template
        )

        schedule_origin_id = external_schedule.get_external_origin_id()
        cron_job = kubernetes.client.V1beta1CronJob(
            spec=cron_job_spec, metadata={"name": schedule_origin_id}
        )

        existing_cron_job = self.get_cron_job(schedule_origin_id=schedule_origin_id)
        if existing_cron_job:
            # patch_namespaced_cron_job will cause the containers array to be additive
            # https://blog.atomist.com/kubernetes-apply-replace-patch/
            self._api.replace_namespaced_cron_job(
                name=schedule_origin_id, body=cron_job, namespace=self._namespace
            )
        else:
            self._api.create_namespaced_cron_job(body=cron_job, namespace=self._namespace)

        time.sleep(self.grace_period_seconds)

    # Update the existing K8s CronJob if it exists; else, create it.
    def start_schedule(self, instance, external_schedule):
        check.inst_param(instance, "instance", DagsterInstance)
        check.inst_param(external_schedule, "external_schedule", ExternalSchedule)

        self._start_cron_job(external_schedule)

        # Verify that the cron job is running
        cron_job = self.get_cron_job(schedule_origin_id=external_schedule.get_external_origin_id())
        if not cron_job:
            raise DagsterSchedulerError(
                "Attempted to add K8s CronJob for schedule {schedule_name}, but failed. "
                "The schedule {schedule_name} is not running.".format(
                    schedule_name=external_schedule.name
                )
            )
        return

    def refresh_schedule(self, instance, external_schedule):
        check.inst_param(instance, "instance", DagsterInstance)
        check.inst_param(external_schedule, "external_schedule", ExternalSchedule)

        self.start_schedule(instance, external_schedule)

    def running_schedule_count(self, instance, schedule_origin_id):
        check.str_param(schedule_origin_id, "schedule_origin_id")

        if self.get_cron_job(schedule_origin_id):
            return 1
        else:
            return 0

    def get_cron_job(self, schedule_origin_id):
        check.str_param(schedule_origin_id, "schedule_origin_id")

        cron_jobs = self._api.list_namespaced_cron_job(namespace=self._namespace)
        for item in cron_jobs.items:
            if schedule_origin_id == item.metadata.name:
                return item
        return None

    def get_all_cron_jobs(self):
        return self._api.list_namespaced_cron_job(namespace=self._namespace).items

    def _end_cron_job(self, schedule_origin_id):
        check.str_param(schedule_origin_id, "schedule_origin_id")

        self._api.delete_namespaced_cron_job(name=schedule_origin_id, namespace=self._namespace)
        time.sleep(self.grace_period_seconds)

    def stop_schedule(self, instance, schedule_origin_id):
        check.inst_param(instance, "instance", DagsterInstance)
        check.str_param(schedule_origin_id, "schedule_origin_id")

        if self.get_cron_job(schedule_origin_id):
            self._end_cron_job(schedule_origin_id=schedule_origin_id)

        cron_job = self.get_cron_job(schedule_origin_id)
        if cron_job:
            schedule = self._get_schedule_state(instance, schedule_origin_id)

            raise DagsterSchedulerError(
                "Attempted to remove existing K8s CronJob for schedule "
                "{schedule_name}, but failed. Schedule is still running.".format(
                    schedule_name=schedule.name
                )
            )

    def get_logs_path(self, instance, schedule_origin_id):
        raise NotImplementedError("To get logs, inspect the corresponding K8s CronJob")
