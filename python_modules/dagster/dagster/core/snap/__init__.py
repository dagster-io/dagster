'''
This module contains serializable classes that contain all the meta information
in our definitions and type systems. The purpose to be able to power our graphql
interface without having access to all the definitions in and types in process.

This will have a number of uses, but the most immediately germane are:

1) Persist *historical* pipeline and repository structures. This
will enable, in the short term, for the user to be able to go to a historical
run and view the meta information at that point in time.
2) Cache the meta information about a repository when, for example, interacting
with a repository that is not in the same process but is instead resident in
a container. This way one does not have query the meta information about
a pipeline/repository in the critical path of a user interaction.

I suspect also that the ability to hash the entire construct of meta information
to identify the repository will also end up being quite useful.

    -- schrockn 11-22-2019

'''
