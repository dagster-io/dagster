ALL_STORED_JOB_STATE_QUERY = """
    query jobStates($repositoryOriginId: String, $repositorySelectorId: String, $jobType: InstigationType, $statuses: [String!]) {
        schedules {
            jobStates(repositoryOriginId: $repositoryOriginId, repositorySelectorId: $repositorySelectorId, jobType: $jobType, statuses: $statuses)
        }
    }
"""


ADD_JOB_STATE_MUTATION = """
    mutation addJobStateMutation($serializedJobState: String!) {
        schedules {
            addJobState(serializedJobState: $serializedJobState) {
                ok
            }
        }
    }
"""

CREATE_JOB_TICK_MUTATION = """
    mutation createJobTickMutation($serializedJobTickData: String!) {
        schedules {
            createJobTick(serializedJobTickData: $serializedJobTickData) {
                tickId
            }
        }
    }
"""

UPDATE_JOB_TICK_MUTATION = """
    mutation updateJobTickMutation($tickId: BigInt! $serializedJobTickData: String!) {
        schedules {
            updateJobTick(tickId: $tickId, serializedJobTickData: $serializedJobTickData) {
                ok
            }
        }
    }
"""


GET_JOB_STATE_QUERY = """
    query jobState($jobOriginId: String!, $selectorId: String) {
        schedules {
            jobState(jobOriginId: $jobOriginId, selectorId: $selectorId)
        }
    }
"""

GET_JOB_TICKS_QUERY = """
    query jobTicks($jobOriginId: String!, $selectorId: String, $before: Float, $after: Float, $limit: Int, $statuses: [InstigationTickStatus!]) {
        schedules {
            jobTicks(jobOriginId: $jobOriginId, selectorId: $selectorId, before: $before, after: $after, limit: $limit, statuses: $statuses)
        }
    }
"""

UPDATE_JOB_STATE_MUTATION = """
    mutation updateJobStateMutation($serializedJobState: String!) {
        schedules {
            updateJobState(serializedJobState: $serializedJobState) {
                ok
            }
        }
    }
"""
